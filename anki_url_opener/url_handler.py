"""
URL handling functionality for AnkiVoice add-on
"""
import os
import sys
import platform
import subprocess
import re
from typing import Dict, Any, Optional

from aqt.utils import showInfo, tooltip

from .logger import log_info, log_error, log_debug


def replace_placeholders(template: str, field_content: str) -> str:
    """Replace placeholders in a URL template with actual content
    
    Args:
        template: URL template with placeholders like {{field_content}}
        field_content: Content to insert into the template
        
    Returns:
        str: URL with placeholders replaced
    """
    # Replace {{field_content}} placeholder
    url = template.replace("{{field_content}}", field_content)
    
    log_debug(f"URL template '{template}' with content '{field_content}' -> '{url}'")
    return url


def open_url(url: str, application: str = None) -> bool:
    """Open a URL using the specified application
    
    Args:
        url: The URL to open
        application: Path to the application to use (or None for system default)
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        system = platform.system()
        
        if application:
            log_info(f"Opening URL '{url}' with application '{application}'")
        else:
            log_info(f"Opening URL '{url}' with system default browser")
        
        # If no specific application is provided, use system default
        if not application:
            if system == "Darwin":  # macOS
                subprocess.Popen(["open", url])
            elif system == "Windows":
                subprocess.Popen(["start", url], shell=True)
            else:  # Linux
                subprocess.Popen(["xdg-open", url])
        else:
            # Use specified application
            if system == "Darwin":  # macOS
                # For .app bundles
                if application.endswith(".app"):
                    subprocess.Popen(["open", "-a", application, url])
                else:
                    subprocess.Popen([application, url])
            elif system == "Windows":
                subprocess.Popen([application, url])
            else:  # Linux
                subprocess.Popen([application, url])
        
        return True
    
    except Exception as e:
        log_error(f"Error opening URL '{url}'", e)
        showInfo(f"Error opening URL: {str(e)}")
        return False


def process_url_for_card(card, field_name: str, url_template: str, application: str = None) -> bool:
    """Process a URL template for a specific card and open it
    
    Args:
        card: Anki card object
        field_name: Name of the field to extract content from
        url_template: URL template with placeholders
        application: Path to the application to use (or None for system default)
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Validate card object
        if not card:
            log_error("Card object is None")
            return False
        
        log_info(f"Processing URL for card {card.id}, field: '{field_name}'")
        
        # Get the note from the card
        try:
            note = card.note()
        except Exception as e:
            log_error(f"Failed to get note from card {card.id}", e)
            return False
        
        # Validate note object
        if not note:
            log_error(f"Note object is None for card {card.id}")
            return False
        
        # Extract field content
        field_content = ""
        if field_name in note:
            # Get the raw content (may contain HTML)
            raw_content = note[field_name]
            
            # Strip HTML tags if present
            field_content = re.sub(r'<[^>]+>', '', raw_content)
            
            # Trim whitespace
            field_content = field_content.strip()
            
            log_debug(f"Extracted field content: '{field_content}'")
        else:
            log_error(f"Field '{field_name}' not found in card {card.id}")
            tooltip(f"Field '{field_name}' not found in card")
            return False
        
        # Skip if empty field
        if not field_content:
            log_debug(f"Field '{field_name}' is empty in card {card.id}, skipping")
            return False
        
        # Replace placeholders in URL template
        url = replace_placeholders(url_template, field_content)
        
        # Open the URL
        return open_url(url, application)
    
    except Exception as e:
        log_error(f"Error processing URL for card", e)
        # Don't show popup to avoid interrupting review
        return False 