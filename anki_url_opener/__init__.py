"""
AnkiURLOpener - Anki add-on for automated URL opening
"""
from aqt import mw
from aqt.qt import *
from aqt.utils import showInfo, qconnect
from aqt import gui_hooks

# Import Python standard libraries
import os
import sys
import json
import subprocess

# Constants
ADDON_PATH = os.path.dirname(__file__)
USER_FILES_PATH = os.path.join(ADDON_PATH, "user_files")
CONFIG_PATH = os.path.join(USER_FILES_PATH, "profiles")

# Ensure directories exist
if not os.path.exists(CONFIG_PATH):
    os.makedirs(CONFIG_PATH, exist_ok=True)

# Menu setup
def setup_menu():
    """Set up the menu items in Anki's interface"""
    # Create main menu
    global addon_menu
    addon_menu = QMenu("AnkiURLOpener", mw)
    mw.form.menuTools.addMenu(addon_menu)
    
    # Add enable/disable toggle
    global toggle_action
    toggle_action = QAction("Enable Add-on", mw)
    toggle_action.setCheckable(True)
    
    # Import here to avoid circular imports
    from .config_manager import is_addon_enabled
    toggle_action.setChecked(is_addon_enabled())
    
    qconnect(toggle_action.triggered, toggle_addon)
    addon_menu.addAction(toggle_action)
    
    # Add separator
    addon_menu.addSeparator()
    
    # Add config action
    config_action = QAction("Configuration", mw)
    qconnect(config_action.triggered, open_config_dialog)
    addon_menu.addAction(config_action)


def toggle_addon():
    """Toggle the add-on on/off"""
    from .config_manager import toggle_addon_enabled
    from .logger import log_info
    
    new_state = toggle_addon_enabled()
    toggle_action.setChecked(new_state)
    
    status = "enabled" if new_state else "disabled"
    log_info(f"Add-on {status}")
    showInfo(f"AnkiURLOpener has been {status}.")

# Config dialog 
def open_config_dialog():
    """Open the configuration dialog"""
    # Import here to avoid circular imports
    from .config_dialog import show_config_dialog
    
    # Open dialog
    show_config_dialog()

# Register hook for card answer shown
def on_answer_shown(card):
    """Function that runs when the answer is shown"""
    # Import here to avoid circular imports
    from .config_manager import get_profile_data, get_profile_for_deck, is_addon_enabled
    from .url_handler import process_url_for_card
    from .logger import log_info, log_error, log_debug
    
    # Wrap in try-except to prevent errors from propagating to Anki
    try:
        # Validate card object
        if not card:
            log_debug("Card object is None, skipping")
            return
        
        # Check if reviewer is in a valid state
        if not mw.reviewer or not mw.reviewer.card:
            log_debug("Reviewer not in valid state, skipping")
            return
        
        # Check if card matches current reviewer card
        if mw.reviewer.card.id != card.id:
            log_debug("Card ID mismatch with reviewer, skipping")
            return
        
        # Check if add-on is globally enabled
        if not is_addon_enabled():
            log_debug("Add-on is globally disabled, skipping")
            return
        
        log_info(f"Card answer shown for card ID: {card.id}")
        
        # Delay execution to let Anki finish internal state updates
        # This prevents race conditions when returning from edit mode
        QTimer.singleShot(100, lambda: process_card_delayed(card))
        
    except Exception as e:
        log_error(f"Error in on_answer_shown hook", e)
        # Don't show error to user to avoid interrupting review


def process_card_delayed(card):
    """Process the card after a short delay to avoid race conditions"""
    from .config_manager import get_profile_data, get_profile_for_deck
    from .url_handler import process_url_for_card
    from .logger import log_info, log_error, log_debug
    
    try:
        # Re-validate card and reviewer state after delay
        if not card:
            log_debug("Card object is None after delay, skipping")
            return
        
        if not mw.reviewer or not mw.reviewer.card:
            log_debug("Reviewer not in valid state after delay, skipping")
            return
        
        if mw.reviewer.card.id != card.id:
            log_debug("Card ID mismatch with reviewer after delay, skipping")
            return
        
        # Get the deck name for this card
        deck_id = card.current_deck_id()
        deck = mw.col.decks.get(deck_id)
        deck_name = deck['name'] if deck else "Unknown"
        
        log_debug(f"Card is from deck: {deck_name}")
        
        # Get the profile to use for this deck
        profile_name = get_profile_for_deck(deck_name)
        log_debug(f"Using profile: {profile_name}")
        
        # Get profile data
        profile = get_profile_data(profile_name)
        
        # Check if profile is enabled
        if not profile.get("enabled", True):
            log_info("Profile is disabled, skipping")
            return
        
        # Get profile settings
        field_name = profile.get("field_name", "Front")
        url_template = profile.get("url_template", "")
        application = profile.get("application", "")
        
        log_debug(f"Profile settings: field='{field_name}', url='{url_template}', app='{application}'")
        
        # Process URL if a template is provided
        if url_template:
            # Get absolute path to application if provided
            app_path = application if application else None
            
            # Process URL and open it
            result = process_url_for_card(card, field_name, url_template, app_path)
            if result:
                log_info("URL processed and opened successfully")
            else:
                log_error("Failed to process URL")
        else:
            log_debug("No URL template provided, skipping URL processing")
            
    except Exception as e:
        log_error(f"Error in process_card_delayed", e)
        # Don't show error to user to avoid interrupting review

# Global references
addon_menu = None
toggle_action = None

# Set up hooks
gui_hooks.reviewer_did_show_answer.append(on_answer_shown)

# Set up menu items when Anki starts
setup_menu() 