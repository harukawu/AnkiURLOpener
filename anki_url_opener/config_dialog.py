"""
Configuration dialog for AnkiURLOpener add-on
"""
from aqt.qt import *
from aqt import mw
from aqt.utils import showInfo, tooltip, qconnect

import os
import sys
import json
import platform
import glob
from typing import List, Dict, Any, Optional

# Import constants from __init__.py
from . import USER_FILES_PATH, CONFIG_PATH, ADDON_PATH


class ProfileSelector(QComboBox):
    """Dropdown for selecting and managing profiles"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # Fix for PyQt6 compatibility
        # QSizePolicy.Expanding is now QSizePolicy.Policy.Expanding
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.reload_profiles()
    
    def reload_profiles(self):
        """Reload profiles from the config"""
        current_text = self.currentText()
        self.clear()
        
        config = mw.addonManager.getConfig(__name__.split('.')[0])
        if not config:
            return
            
        active_profile = config.get("active_profile", "default")
        
        # Add all profiles
        profiles = list(config.get("profiles", {}).keys())
        if not profiles:
            # Add default profile if none exist
            self.addItem("default")
            return
            
        for profile_name in profiles:
            self.addItem(profile_name)
        
        # Try to restore previous selection first
        if current_text:
            index = self.findText(current_text)
            if index >= 0:
                self.setCurrentIndex(index)
                return
                
        # Set active profile if no previous selection
        index = self.findText(active_profile)
        if index >= 0:
            self.setCurrentIndex(index)


class ConfigDialog(QDialog):
    """Main configuration dialog for AnkiURLOpener"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AnkiURLOpener Configuration")
        self.setMinimumWidth(500)
        
        # Load configuration
        self.addon_name = __name__.split('.')[0]
        self.config = mw.addonManager.getConfig(self.addon_name)
        if not self.config:
            showInfo("Could not load configuration. Using default settings.")
            self.config = {
                "active_profile": "default",
                "profiles": {
                    "default": {
                        "field_name": "Front",
                        "url_template": "https://www.google.com/search?q={{field_content}}",
                        "application": "",
                        "enabled": True,
                        "decks": []
                    }
                }
            }
            # Save default config
            mw.addonManager.writeConfig(self.addon_name, self.config)
            
        # Load profiles from files first to ensure they're all available
        self.load_profiles_from_files()
        
        # Get active profile name
        self.active_profile = self.config.get("active_profile", "default")
        
        # Set up the UI
        self.setup_ui()
        
        # Load initial values
        self.load_profile_data()
    
    def setup_ui(self):
        """Set up the dialog UI components"""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Profile selection section
        profile_group = QGroupBox("Profile")
        profile_layout = QHBoxLayout()
        profile_group.setLayout(profile_layout)
        
        profile_label = QLabel("Active Profile:")
        self.profile_selector = ProfileSelector()
        qconnect(self.profile_selector.currentIndexChanged, self.on_profile_changed)
        
        profile_layout.addWidget(profile_label)
        profile_layout.addWidget(self.profile_selector)
        
        # Profile action buttons
        profile_actions = QHBoxLayout()
        self.new_profile_btn = QPushButton("New")
        self.delete_profile_btn = QPushButton("Delete")
        self.save_profile_btn = QPushButton("Save Profile")
        qconnect(self.new_profile_btn.clicked, self.on_new_profile)
        qconnect(self.delete_profile_btn.clicked, self.on_delete_profile)
        qconnect(self.save_profile_btn.clicked, self.on_save_profile)
        
        profile_actions.addWidget(self.new_profile_btn)
        profile_actions.addWidget(self.delete_profile_btn)
        profile_actions.addWidget(self.save_profile_btn)
        profile_actions.addStretch()
        
        # Configuration section
        config_group = QGroupBox("Configuration")
        config_layout = QFormLayout()
        config_group.setLayout(config_layout)
        
        # Field name selection
        self.field_name = QComboBox()
        self.load_available_fields()
        
        # URL template
        self.url_template = QLineEdit()
        
        # Application selection
        self.application = QLineEdit()
        self.app_browse_btn = QPushButton("Browse...")
        qconnect(self.app_browse_btn.clicked, self.on_browse_app)
        
        app_layout = QHBoxLayout()
        app_layout.addWidget(self.application)
        app_layout.addWidget(self.app_browse_btn)
        
        # Enabled checkbox
        self.enabled = QCheckBox("Enabled")
        
        # Deck list section
        deck_list_label = QLabel("Decks (this profile will be used for these decks):")
        self.deck_list = QListWidget()
        self.deck_list.setMaximumHeight(100)
        
        deck_buttons_layout = QHBoxLayout()
        self.add_deck_btn = QPushButton("Add Deck")
        self.remove_deck_btn = QPushButton("Remove Deck")
        qconnect(self.add_deck_btn.clicked, self.on_add_deck)
        qconnect(self.remove_deck_btn.clicked, self.on_remove_deck)
        deck_buttons_layout.addWidget(self.add_deck_btn)
        deck_buttons_layout.addWidget(self.remove_deck_btn)
        deck_buttons_layout.addStretch()
        
        # Add widgets to form
        config_layout.addRow("Field Name:", self.field_name)
        config_layout.addRow("URL Template:", self.url_template)
        config_layout.addRow("Application:", app_layout)
        config_layout.addRow("", self.enabled)
        config_layout.addRow(deck_list_label)
        config_layout.addRow(self.deck_list)
        config_layout.addRow(deck_buttons_layout)
        
        # Add all components to main layout
        layout.addWidget(profile_group)
        layout.addLayout(profile_actions)
        layout.addWidget(config_group)
        
        # Buttons at the bottom
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        qconnect(buttons.accepted, self.on_accept)
        qconnect(buttons.rejected, self.reject)
        layout.addWidget(buttons)
    
    def load_available_fields(self):
        """Load available fields from Anki"""
        self.field_name.clear()
        
        # Get all field names from all note types
        field_names = set()
        for model in mw.col.models.all():
            for field in model['flds']:
                field_names.add(field['name'])
        
        # Sort and add to combo box
        field_names = sorted(list(field_names))
        self.field_name.addItems(field_names)
    
    def load_profile_data(self):
        """Load the current profile data into UI fields"""
        # First try to get from main config
        profile_data = self.config.get("profiles", {}).get(self.active_profile, {})
        
        # If no data in main config, try to load from profile file
        if not profile_data:
            profile_path = os.path.join(CONFIG_PATH, f"{self.active_profile}.json")
            if os.path.exists(profile_path):
                try:
                    with open(profile_path, "r", encoding="utf-8") as f:
                        profile_data = json.load(f)
                    # Update main config with this data
                    if "profiles" not in self.config:
                        self.config["profiles"] = {}
                    self.config["profiles"][self.active_profile] = profile_data
                except Exception as e:
                    showInfo(f"Error loading profile file: {str(e)}")
        
        # Fall back to default values if still no data
        if not profile_data:
            profile_data = {
                "field_name": "Front",
                "url_template": "https://www.google.com/search?q={{field_content}}",
                "application": "",
                "enabled": True,
                "decks": []
            }
        
        # Set values in UI
        # Set field name if it exists in the list
        field_name = profile_data.get("field_name", "Front")
        index = self.field_name.findText(field_name)
        if index >= 0:
            self.field_name.setCurrentIndex(index)
        elif self.field_name.count() > 0:
            self.field_name.setCurrentIndex(0)
        
        self.url_template.setText(profile_data.get("url_template", ""))
        self.application.setText(profile_data.get("application", ""))
        self.enabled.setChecked(profile_data.get("enabled", True))
        
        # Load deck list
        self.deck_list.clear()
        decks = profile_data.get("decks", [])
        for deck in decks:
            self.deck_list.addItem(deck)
    
    def save_profile_data(self):
        """Save the current UI values to the active profile"""
        # Get current profile name
        profile_name = self.profile_selector.currentText()
        
        # Check if profile name changed
        old_profile_name = self.active_profile
        profile_renamed = (old_profile_name != profile_name and old_profile_name in self.config.get("profiles", {}))
        
        # Get deck list from UI
        decks = []
        for i in range(self.deck_list.count()):
            decks.append(self.deck_list.item(i).text())
        
        # Create profile data from UI
        profile_data = {
            "field_name": self.field_name.currentText(),
            "url_template": self.url_template.text(),
            "application": self.application.text(),
            "enabled": self.enabled.isChecked(),
            "decks": decks
        }
        
        # Update config
        self.config["active_profile"] = profile_name
        if "profiles" not in self.config:
            self.config["profiles"] = {}
        self.config["profiles"][profile_name] = profile_data
        
        # If profile was renamed, remove the old profile
        if profile_renamed:
            del self.config["profiles"][old_profile_name]
            # Remove old profile file
            old_profile_path = os.path.join(CONFIG_PATH, f"{old_profile_name}.json")
            if os.path.exists(old_profile_path):
                os.remove(old_profile_path)
        
        # Save config to disk
        mw.addonManager.writeConfig(self.addon_name, self.config)
        
        # Save profile to user_files directory
        profile_path = os.path.join(CONFIG_PATH, f"{profile_name}.json")
        with open(profile_path, "w", encoding="utf-8") as f:
            json.dump(profile_data, f, indent=4)
        
        # Update active profile name
        self.active_profile = profile_name
    
    def on_profile_changed(self, index):
        """Handle profile selection change"""
        if index < 0:
            return
        
        # Get the new profile name
        new_profile_name = self.profile_selector.currentText()
        
        # Update active profile
        self.active_profile = new_profile_name
        
        # Load new profile data
        self.load_profile_data()
        
        # Update active profile in the config (without saving current form data to it)
        self.config["active_profile"] = new_profile_name
        mw.addonManager.writeConfig(self.addon_name, self.config)
    
    def on_new_profile(self):
        """Create a new profile"""
        profile_name, ok = QInputDialog.getText(
            self, "New Profile", "Enter new profile name:")
        
        if ok and profile_name:
            # Check if profile already exists
            if profile_name in self.config.get("profiles", {}):
                showInfo(f"Profile '{profile_name}' already exists.")
                return
            
            # Create new profile with default values
            if "profiles" not in self.config:
                self.config["profiles"] = {}
            
            self.config["profiles"][profile_name] = {
                "field_name": "Front",
                "url_template": "https://www.google.com/search?q={{field_content}}",
                "application": "",
                "enabled": True,
                "decks": []
            }
            
            # Save to disk
            mw.addonManager.writeConfig(self.addon_name, self.config)
            
            # Reload profiles and select new one
            self.profile_selector.reload_profiles()
            index = self.profile_selector.findText(profile_name)
            if index >= 0:
                self.profile_selector.setCurrentIndex(index)
    
    def on_delete_profile(self):
        """Delete the current profile"""
        profile_name = self.profile_selector.currentText()
        
        # Don't allow deleting the last profile
        if len(self.config.get("profiles", {})) <= 1:
            showInfo("Cannot delete the last profile.")
            return
        
        # Confirm deletion
        if not askUser(f"Delete profile '{profile_name}'?"):
            return
        
        # Remove profile
        if "profiles" in self.config and profile_name in self.config["profiles"]:
            del self.config["profiles"][profile_name]
            
            # Set active profile to first available
            self.config["active_profile"] = next(iter(self.config["profiles"]))
            
            # Save config
            mw.addonManager.writeConfig(self.addon_name, self.config)
            
            # Delete profile file from user_files
            profile_path = os.path.join(CONFIG_PATH, f"{profile_name}.json")
            if os.path.exists(profile_path):
                os.remove(profile_path)
            
            # Reload profiles
            self.profile_selector.reload_profiles()
    
    def on_browse_app(self):
        """Open file dialog to select an application"""
        if platform.system() == "Darwin":  # macOS
            app_path, _ = QFileDialog.getOpenFileName(
                self, "Select Application", "/Applications", "Applications (*.app)"
            )
        elif platform.system() == "Windows":
            app_path, _ = QFileDialog.getOpenFileName(
                self, "Select Application", "", "Applications (*.exe)"
            )
        else:  # Linux
            app_path, _ = QFileDialog.getOpenFileName(
                self, "Select Application", "/usr/bin", "All Files (*)"
            )
        
        if app_path:
            self.application.setText(app_path)
    
    def on_add_deck(self):
        """Add a deck to the profile's deck list"""
        # Get all deck names
        deck_names = [deck.name for deck in mw.col.decks.all_names_and_ids()]
        
        if not deck_names:
            showInfo("No decks found in your collection.")
            return
        
        # Show dialog to select deck
        deck_name, ok = QInputDialog.getItem(
            self, "Select Deck", "Choose a deck to add:", deck_names, 0, False
        )
        
        if ok and deck_name:
            # Check if deck is already in the list
            for i in range(self.deck_list.count()):
                if self.deck_list.item(i).text() == deck_name:
                    showInfo(f"Deck '{deck_name}' is already in the list.")
                    return
            
            # Add to list
            self.deck_list.addItem(deck_name)
    
    def on_remove_deck(self):
        """Remove selected deck from the profile's deck list"""
        current_item = self.deck_list.currentItem()
        if current_item:
            self.deck_list.takeItem(self.deck_list.row(current_item))
        else:
            showInfo("Please select a deck to remove.")
    
    def on_save_profile(self):
        """Save the current profile data"""
        # Save the current profile
        self.save_profile_data()
        
        # Show confirmation
        tooltip("Profile saved", parent=self)
    
    def on_accept(self):
        """Save configuration and close dialog"""
        # Save current profile data
        self.save_profile_data()
        
        # Close dialog
        self.accept()

    def load_profiles_from_files(self):
        """Load profile files from user_files directory into main config"""
        # Look for profile files
        profile_files = glob.glob(os.path.join(CONFIG_PATH, "*.json"))
        
        # Ensure profiles section exists in config
        if "profiles" not in self.config:
            self.config["profiles"] = {}
            
        for profile_file in profile_files:
            # Get profile name from filename
            basename = os.path.basename(profile_file)
            profile_name = os.path.splitext(basename)[0]
            
            try:
                # Load profile data
                with open(profile_file, "r", encoding="utf-8") as f:
                    profile_data = json.load(f)
                
                # Add to config if not already present or update existing
                self.config["profiles"][profile_name] = profile_data
            except Exception as e:
                showInfo(f"Error loading profile file {basename}: {str(e)}")
        
        # Save updated config
        mw.addonManager.writeConfig(self.addon_name, self.config)


# Function to open the config dialog directly
def show_config_dialog():
    """Open the configuration dialog"""
    dialog = ConfigDialog(mw)
    return dialog.exec()


# Function to ask for confirmation
def askUser(text, parent=None, defaultNo=False, title="AnkiURLOpener"):
    """Show a yes/no dialog with provided text."""
    if defaultNo:
        default = QMessageBox.StandardButton.No
    else:
        default = QMessageBox.StandardButton.Yes
        
    return QMessageBox.question(
        parent, title, text,
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        default
    ) == QMessageBox.StandardButton.Yes 