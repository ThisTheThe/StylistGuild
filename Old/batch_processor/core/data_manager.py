#!/usr/bin/env python3
"""
Data Manager Module

Handles JSON file operations, data loading/saving, and data integrity management.
"""

import json
import os
import shutil
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
import requests
from urllib.parse import urlparse


class DataManager:
    """
    Manages all data operations for the batch theme processor.
    Handles loading, saving, and syncing of JSON data files.
    """
    
    def __init__(self, config=None):
        """
        Initialize DataManager with configuration.
        
        Args:
            config: Configuration object with paths and settings
        """
        self.config = config or self._get_default_config()
        self.ensure_data_directories()
    
    def _get_default_config(self):
        """Default configuration if none provided."""
        return {
            'official_json_url': 'https://raw.githubusercontent.com/obsidianmd/obsidian-releases/master/community-css-themes.json',
            'official_json_path': './data/community-css-themes.json',
            'addon_json_path': './data/community-css-themes-tag-browser.json',
            'tag_definitions_path': './data/tag-definitions.json',
            'backup_dir': './backups',
            'data_dir': './data'
        }
    
    def ensure_data_directories(self):
        """Create necessary directories if they don't exist."""
        directories = [
            self.config['data_dir'],
            self.config['backup_dir']
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
    
    def load_json_file(self, file_path: str) -> Optional[Dict]:
        """
        Load JSON data from a file with error handling.
        
        Args:
            file_path: Path to the JSON file
            
        Returns:
            Loaded JSON data or None if failed
        """
        if not os.path.exists(file_path):
            print(f"WARNING: File '{file_path}' not found.")
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"Successfully loaded '{file_path}'")
            return data
        except json.JSONDecodeError as e:
            print(f"ERROR: Invalid JSON in '{file_path}': {e}")
            return None
        except Exception as e:
            print(f"ERROR: Could not read '{file_path}': {e}")
            return None
    
    def save_json_file(self, data: Any, file_path: str, backup: bool = True) -> bool:
        """
        Save JSON data to a file with optional backup.
        
        Args:
            data: Data to save as JSON
            file_path: Target file path
            backup: Whether to create backup before saving
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create backup if requested and file exists
            if backup and os.path.exists(file_path):
                backup_success = self.create_backup(file_path)
                if not backup_success:
                    print(f"WARNING: Failed to create backup for '{file_path}', proceeding anyway...")
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Save with pretty formatting
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"Successfully saved '{file_path}'")
            return True
            
        except Exception as e:
            print(f"ERROR: Could not save '{file_path}': {e}")
            return False
    
    def create_backup(self, file_path: str) -> bool:
        """
        Create a timestamped backup of a file.
        
        Args:
            file_path: File to backup
            
        Returns:
            True if backup created successfully
        """
        if not os.path.exists(file_path):
            return False
        
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = os.path.basename(file_path)
            backup_filename = f"{timestamp}_{filename}"
            backup_path = os.path.join(self.config['backup_dir'], backup_filename)
            
            shutil.copy2(file_path, backup_path)
            print(f"Backup created: '{backup_path}'")
            return True
            
        except Exception as e:
            print(f"ERROR: Could not create backup: {e}")
            return False
    
    def load_official_json(self, use_cached: bool = True) -> Optional[List[Dict]]:
        """
        Load official theme JSON data, either from cache or download fresh.
        
        Args:
            use_cached: Whether to use cached version if available
            
        Returns:
            List of theme dictionaries or None if failed
        """
        cached_path = self.config['official_json_path']
        
        # Use cached version if requested and exists
        if use_cached and os.path.exists(cached_path):
            cached_data = self.load_json_file(cached_path)
            if cached_data:
                print(f"Using cached official JSON from '{cached_path}'")
                return cached_data
        
        # Download fresh copy
        print("Downloading latest official JSON...")
        downloaded_data = self.download_official_json()
        
        if downloaded_data:
            # Save as new cached copy
            self.save_json_file(downloaded_data, cached_path, backup=True)
            return downloaded_data
        
        # Fall back to cached if download failed
        if os.path.exists(cached_path):
            print("Download failed, falling back to cached version...")
            return self.load_json_file(cached_path)
        
        return None
    
    def download_official_json(self) -> Optional[List[Dict]]:
        """
        Download official theme JSON from GitHub.
        
        Returns:
            Downloaded JSON data or None if failed
        """
        try:
            url = self.config['official_json_url']
            print(f"Downloading from: {url}")
            
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            print(f"Successfully downloaded {len(data)} themes")
            return data
            
        except requests.exceptions.RequestException as e:
            print(f"ERROR: Network error downloading official JSON: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"ERROR: Invalid JSON in downloaded data: {e}")
            return None
        except Exception as e:
            print(f"ERROR: Unexpected error downloading official JSON: {e}")
            return None
    
    def load_addon_json(self) -> Dict[str, Dict]:
        """
        Load addon theme data, creating empty structure if not found.
        
        Returns:
            Dictionary mapping repo names to addon data
        """
        addon_path = self.config['addon_json_path']
        addon_data = self.load_json_file(addon_path)
        
        if addon_data is None:
            print(f"Creating new addon JSON file at '{addon_path}'")
            addon_data = {}
            self.save_json_file(addon_data, addon_path, backup=False)
        
        return addon_data
    
    def save_addon_json(self, addon_data: Dict[str, Dict]) -> bool:
        """
        Save addon theme data with backup.
        
        Args:
            addon_data: Dictionary mapping repo names to addon data
            
        Returns:
            True if successful
        """
        addon_path = self.config['addon_json_path']
        return self.save_json_file(addon_data, addon_path, backup=True)
    
    def load_tag_definitions(self) -> Dict[str, Dict]:
        """
        Load tag definitions, creating default structure if not found.
        
        Returns:
            Dictionary mapping tag IDs to tag definitions
        """
        tag_path = self.config['tag_definitions_path']
        tag_data = self.load_json_file(tag_path)
        
        if tag_data is None:
            print(f"Creating default tag definitions at '{tag_path}'")
            tag_data = self._create_default_tag_definitions()
            self.save_json_file(tag_data, tag_path, backup=False)
        
        return tag_data
    
    def save_tag_definitions(self, tag_data: Dict[str, Dict]) -> bool:
        """
        Save tag definitions with backup.
        
        Args:
            tag_data: Dictionary mapping tag IDs to tag definitions
            
        Returns:
            True if successful
        """
        tag_path = self.config['tag_definitions_path']
        return self.save_json_file(tag_data, tag_path, backup=True)
    
    def _create_default_tag_definitions(self) -> Dict[str, Dict]:
        """Create default tag definitions structure."""
        return {
            "color_schemes": {
                "display_name": "Color Schemes",
                "description": "Themes organized by color palette approach",
                "parent": None,
                "children": ["dark_theme", "light_theme", "colorful"],
                "page_template": "tag-page-template.md"
            },
            "dark_theme": {
                "display_name": "Dark Theme",
                "description": "Dark color schemes for low-light environments",
                "parent": "color_schemes",
                "children": [],
                "page_template": "tag-page-template.md"
            },
            "light_theme": {
                "display_name": "Light Theme", 
                "description": "Light color schemes for bright environments",
                "parent": "color_schemes",
                "children": [],
                "page_template": "tag-page-template.md"
            },
            "minimal": {
                "display_name": "Minimal",
                "description": "Clean, distraction-free themes",
                "parent": None,
                "children": [],
                "page_template": "tag-page-template.md"
            }
        }
    
    def detect_new_themes(self, official_data: List[Dict], addon_data: Dict[str, Dict]) -> List[Dict]:
        """
        Detect themes in official JSON that don't exist in addon JSON.
        
        Args:
            official_data: List of official theme dictionaries
            addon_data: Dictionary mapping repo names to addon data
            
        Returns:
            List of new theme dictionaries
        """
        official_repos = {theme['repo'] for theme in official_data}
        addon_repos = set(addon_data.keys())
        
        new_repos = official_repos - addon_repos
        new_themes = [theme for theme in official_data if theme['repo'] in new_repos]
        
        print(f"Found {len(new_themes)} new themes not in addon data")
        return new_themes
    
    def detect_deleted_themes(self, official_data: List[Dict], addon_data: Dict[str, Dict]) -> List[str]:
        """
        Detect addon themes that no longer exist in official JSON.
        
        Args:
            official_data: List of official theme dictionaries  
            addon_data: Dictionary mapping repo names to addon data
            
        Returns:
            List of repo names that are deleted
        """
        official_repos = {theme['repo'] for theme in official_data}
        addon_repos = set(addon_data.keys())
        
        # Only consider themes not already marked as deleted
        active_addon_repos = {
            repo for repo, data in addon_data.items() 
            if data.get('metadata', {}).get('completion_status') != 'deleted'
        }
        
        deleted_repos = active_addon_repos - official_repos
        
        print(f"Found {len(deleted_repos)} themes that appear to be deleted")
        return list(deleted_repos)
    
    def get_sync_summary(self, official_data: List[Dict], addon_data: Dict[str, Dict]) -> Dict:
        """
        Generate a comprehensive sync summary.
        
        Args:
            official_data: List of official theme dictionaries
            addon_data: Dictionary mapping repo names to addon data
            
        Returns:
            Dictionary with sync statistics and details
        """
        new_themes = self.detect_new_themes(official_data, addon_data)
        deleted_repos = self.detect_deleted_themes(official_data, addon_data)
        
        # Count completion statuses
        status_counts = {}
        for repo, data in addon_data.items():
            status = data.get('metadata', {}).get('completion_status', 'incomplete')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            'total_official': len(official_data),
            'total_addon': len(addon_data),
            'new_themes': new_themes,
            'deleted_repos': deleted_repos,
            'status_counts': status_counts,
            'sync_timestamp': datetime.now().isoformat()
        }
    
    def cleanup_old_backups(self, keep_days: int = 30) -> int:
        """
        Remove backup files older than specified days.
        
        Args:
            keep_days: Number of days to keep backups
            
        Returns:
            Number of files removed
        """
        backup_dir = self.config['backup_dir']
        if not os.path.exists(backup_dir):
            return 0
        
        cutoff_time = datetime.now().timestamp() - (keep_days * 24 * 60 * 60)
        removed_count = 0
        
        try:
            for filename in os.listdir(backup_dir):
                file_path = os.path.join(backup_dir, filename)
                if os.path.isfile(file_path):
                    file_time = os.path.getmtime(file_path)
                    if file_time < cutoff_time:
                        os.remove(file_path)
                        removed_count += 1
            
            if removed_count > 0:
                print(f"Cleaned up {removed_count} old backup files")
            
            return removed_count
            
        except Exception as e:
            print(f"ERROR: Could not cleanup backups: {e}")
            return 0
