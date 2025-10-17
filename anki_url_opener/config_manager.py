"""
Configuration management for AnkiURLOpener add-on
"""
from aqt import mw
from aqt.utils import showInfo

import os
import sys
import json
import glob
from typing import Dict, Any, Optional, List

# Import constants from __init__.py
from . import USER_FILES_PATH, CONFIG_PATH, ADDON_PATH


def get_config() -> Dict[str, Any]:
    """Get the current configuration or default if not available"""
    addon_name = __name__.split('.')[0]
    config = mw.addonManager.getConfig(addon_name)
    
    if not config:
        # Load default configuration
        config = {
            "addon_enabled": True,
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
        mw.addonManager.writeConfig(addon_name, config)
    
    # Ensure addon_enabled exists in config (for backwards compatibility)
    if "addon_enabled" not in config:
        config["addon_enabled"] = True
        save_config(config)
    
    return config


def save_config(config: Dict[str, Any]) -> None:
    """Save the configuration to disk"""
    addon_name = __name__.split('.')[0]
    mw.addonManager.writeConfig(addon_name, config)


def get_active_profile() -> str:
    """Get the name of the active profile"""
    config = get_config()
    return config.get("active_profile", "default")


def set_active_profile(profile_name: str) -> bool:
    """Set the active profile
    
    Returns:
        bool: True if successful, False otherwise
    """
    config = get_config()
    
    # Check if profile exists
    if profile_name not in config.get("profiles", {}):
        return False
    
    # Set active profile
    config["active_profile"] = profile_name
    save_config(config)
    return True


def get_profile_data(profile_name: Optional[str] = None) -> Dict[str, Any]:
    """Get the configuration data for a specific profile
    
    Args:
        profile_name: Name of the profile, or None for active profile
        
    Returns:
        Dict containing profile configuration
    """
    config = get_config()
    
    if profile_name is None:
        profile_name = get_active_profile()
    
    # Get profile data or default if not found
    profile_data = config.get("profiles", {}).get(profile_name, {})
    
    if not profile_data:
        # Return default profile data
        profile_data = {
            "field_name": "Front",
            "url_template": "https://www.google.com/search?q={{field_content}}",
            "application": "",
            "enabled": True,
            "decks": []
        }
    
    return profile_data


def save_profile(profile_name: str, profile_data: Dict[str, Any]) -> None:
    """Save a profile configuration
    
    Args:
        profile_name: Name of the profile to save
        profile_data: Configuration data for the profile
    """
    config = get_config()
    
    # Ensure profiles section exists
    if "profiles" not in config:
        config["profiles"] = {}
    
    # Update profile
    config["profiles"][profile_name] = profile_data
    
    # Save to main config
    save_config(config)
    
    # Save to profile file in user_files
    profile_path = os.path.join(CONFIG_PATH, f"{profile_name}.json")
    try:
        with open(profile_path, "w", encoding="utf-8") as f:
            json.dump(profile_data, f, indent=4)
    except Exception as e:
        showInfo(f"Error saving profile file: {str(e)}")


def delete_profile(profile_name: str) -> bool:
    """Delete a profile
    
    Args:
        profile_name: Name of the profile to delete
        
    Returns:
        bool: True if successful, False otherwise
    """
    config = get_config()
    
    # Check if profile exists
    if "profiles" not in config or profile_name not in config["profiles"]:
        return False
    
    # Don't delete the last profile
    if len(config["profiles"]) <= 1:
        return False
    
    # Delete profile
    del config["profiles"][profile_name]
    
    # If we're deleting the active profile, set a new active profile
    if config.get("active_profile") == profile_name:
        # Set first available profile as active
        config["active_profile"] = next(iter(config["profiles"]))
    
    # Save config
    save_config(config)
    
    # Delete profile file from user_files
    profile_path = os.path.join(CONFIG_PATH, f"{profile_name}.json")
    if os.path.exists(profile_path):
        try:
            os.remove(profile_path)
        except Exception as e:
            showInfo(f"Error deleting profile file: {str(e)}")
            return False
    
    return True


def list_profiles() -> List[str]:
    """Get a list of available profile names
    
    Returns:
        List of profile names
    """
    config = get_config()
    return list(config.get("profiles", {}).keys())


def load_profiles_from_files() -> None:
    """Load profile files from user_files directory into main config"""
    config = get_config()
    
    # Ensure profiles section exists
    if "profiles" not in config:
        config["profiles"] = {}
    
    # Look for profile files
    profile_files = glob.glob(os.path.join(CONFIG_PATH, "*.json"))
    
    for profile_file in profile_files:
        # Get profile name from filename
        basename = os.path.basename(profile_file)
        profile_name = os.path.splitext(basename)[0]
        
        try:
            # Load profile data
            with open(profile_file, "r", encoding="utf-8") as f:
                profile_data = json.load(f)
            
            # Add to config if not already present
            if profile_name not in config["profiles"]:
                config["profiles"][profile_name] = profile_data
        except Exception as e:
            showInfo(f"Error loading profile file {basename}: {str(e)}")
    
    # Save config
    save_config(config)


# Initialize by loading profiles from files
load_profiles_from_files()


def get_profile_for_deck(deck_name: str) -> Optional[str]:
    """Get the profile name that should be used for a given deck
    
    Args:
        deck_name: Name of the deck
        
    Returns:
        str: Profile name to use, or None if no profile is configured for this deck
    """
    config = get_config()
    profiles = config.get("profiles", {})
    
    # Check each profile to see if this deck is in its list
    for profile_name, profile_data in profiles.items():
        decks = profile_data.get("decks", [])
        # Check if the deck name matches exactly or is a sub-deck
        for configured_deck in decks:
            if deck_name == configured_deck or deck_name.startswith(configured_deck + "::"):
                return profile_name
    
    # If no profile found, return the active profile as fallback
    return config.get("active_profile", "default")


def is_addon_enabled() -> bool:
    """Check if the add-on is globally enabled
    
    Returns:
        bool: True if enabled, False otherwise
    """
    config = get_config()
    return config.get("addon_enabled", True)


def set_addon_enabled(enabled: bool) -> None:
    """Set the global enabled state of the add-on
    
    Args:
        enabled: True to enable, False to disable
    """
    config = get_config()
    config["addon_enabled"] = enabled
    save_config(config)


def toggle_addon_enabled() -> bool:
    """Toggle the global enabled state of the add-on
    
    Returns:
        bool: New state (True if enabled, False if disabled)
    """
    config = get_config()
    current_state = config.get("addon_enabled", True)
    new_state = not current_state
    config["addon_enabled"] = new_state
    save_config(config)
    return new_state 