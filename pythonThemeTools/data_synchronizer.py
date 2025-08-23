#!/usr/bin/env python3
"""
Data Synchronizer Module
Handles comparison and synchronization between official and addon JSON files
"""

import json
import os
from typing import Dict, List, Set, Optional
from pathlib import Path


class DataSynchronizer:
    def __init__(self, official_json_path: str = "community-css-themes.json", 
                 addon_json_path: str = "community-css-themes-tag-browser.json"):
        """
        Initialize the DataSynchronizer with paths to JSON files
        
        Args:
            official_json_path: Path to the official community themes JSON
            addon_json_path: Path to the addon themes JSON with tags and extra screenshots
        """
        self.official_path = Path(official_json_path)
        self.addon_path = Path(addon_json_path)
        self._official_data = None
        self._addon_data = None
        
    def load_json_files(self) -> bool:
        """
        Load both JSON files into memory
        
        Returns:
            bool: True if both files loaded successfully, False otherwise
        """
        try:
            # Load official JSON
            if self.official_path.exists():
                with open(self.official_path, 'r', encoding='utf-8') as f:
                    self._official_data = json.load(f)
            else:
                print(f"Warning: Official JSON file not found at {self.official_path}")
                self._official_data = []
            
            # Load addon JSON
            if self.addon_path.exists():
                with open(self.addon_path, 'r', encoding='utf-8') as f:
                    self._addon_data = json.load(f)
            else:
                print(f"Info: Addon JSON file not found at {self.addon_path}, creating empty structure")
                self._addon_data = []
                
            return True
            
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON format - {e}")
            return False
        except Exception as e:
            print(f"Error loading JSON files: {e}")
            return False
    
    def get_official_repos(self) -> Set[str]:
        """
        Extract all repo identifiers from official JSON
        
        Returns:
            Set[str]: Set of repo identifiers (e.g., "kognise/obsidian-atom")
        """
        if self._official_data is None:
            self.load_json_files()
            
        repos = set()
        for theme in self._official_data:
            if 'repo' in theme:
                repos.add(theme['repo'])
        return repos
    
    def get_addon_repos(self) -> Set[str]:
        """
        Extract all repo identifiers from addon JSON
        
        Returns:
            Set[str]: Set of repo identifiers
        """
        if self._addon_data is None:
            self.load_json_files()
            
        repos = set()
        for theme in self._addon_data:
            if 'repo' in theme:
                repos.add(theme['repo'])
        return repos
    
    def find_missing_addon_entries(self) -> List[Dict]:
        """
        Find repos that exist in official JSON but not in addon JSON
        
        Returns:
            List[Dict]: List of theme dictionaries that need addon entries
        """
        official_repos = self.get_official_repos()
        addon_repos = self.get_addon_repos()
        missing_repos = official_repos - addon_repos
        
        missing_entries = []
        for theme in self._official_data:
            if theme.get('repo') in missing_repos:
                missing_entries.append(theme)
                
        return missing_entries
    
    def find_orphaned_addon_entries(self) -> List[Dict]:
        """
        Find repos that exist in addon JSON but not in official JSON
        
        Returns:
            List[Dict]: List of addon entries that may be outdated
        """
        official_repos = self.get_official_repos()
        addon_repos = self.get_addon_repos()
        orphaned_repos = addon_repos - official_repos
        
        orphaned_entries = []
        for theme in self._addon_data:
            if theme.get('repo') in orphaned_repos:
                orphaned_entries.append(theme)
                
        return orphaned_entries
    
    def compare_json_files(self) -> Dict[str, any]:
        """
        Comprehensive comparison of both JSON files
        
        Returns:
            Dict containing detailed comparison results
        """
        if not self.load_json_files():
            return {"error": "Failed to load JSON files"}
        
        official_repos = self.get_official_repos()
        addon_repos = self.get_addon_repos()
        
        missing_entries = self.find_missing_addon_entries()
        orphaned_entries = self.find_orphaned_addon_entries()
        
        return {
            "official_count": len(self._official_data),
            "addon_count": len(self._addon_data),
            "official_repos_count": len(official_repos),
            "addon_repos_count": len(addon_repos),
            "missing_addon_entries": missing_entries,
            "orphaned_addon_entries": orphaned_entries,
            "missing_count": len(missing_entries),
            "orphaned_count": len(orphaned_entries),
            "sync_percentage": (len(addon_repos & official_repos) / len(official_repos) * 100) if official_repos else 0
        }
    
    def suggest_cleanup_actions(self) -> Dict[str, List]:
        """
        Analyze data and suggest cleanup actions
        
        Returns:
            Dict with suggested actions categorized by type
        """
        comparison = self.compare_json_files()
        
        suggestions = {
            "add_to_addon": [],
            "remove_from_addon": [],
            "review_required": []
        }
        
        # Suggest additions
        for entry in comparison["missing_addon_entries"]:
            suggestions["add_to_addon"].append({
                "repo": entry.get("repo"),
                "name": entry.get("name"),
                "author": entry.get("author"),
                "action": "Create addon entry with tags and additional screenshots"
            })
        
        # Suggest removals (with caution)
        for entry in comparison["orphaned_addon_entries"]:
            suggestions["remove_from_addon"].append({
                "repo": entry.get("repo"),
                "action": "Verify if theme still exists, consider removing if deprecated"
            })
        
        # General suggestions
        if comparison["sync_percentage"] < 80:
            suggestions["review_required"].append("Low sync percentage - consider batch update")
        
        if comparison["orphaned_count"] > 5:
            suggestions["review_required"].append("Many orphaned entries - cleanup recommended")
            
        return suggestions
    
    def get_theme_by_repo(self, repo: str, source: str = "official") -> Optional[Dict]:
        """
        Get theme data by repository identifier
        
        Args:
            repo: Repository identifier (e.g., "kognise/obsidian-atom")
            source: "official" or "addon"
        
        Returns:
            Dict or None: Theme data if found
        """
        data = self._official_data if source == "official" else self._addon_data
        
        if data is None:
            self.load_json_files()
            data = self._official_data if source == "official" else self._addon_data
        
        for theme in data:
            if theme.get("repo") == repo:
                return theme
        return None
    
    def create_addon_template(self, official_entry: Dict) -> Dict:
        """
        Create a template addon entry based on official entry
        
        Args:
            official_entry: Theme data from official JSON
            
        Returns:
            Dict: Template for addon entry
        """
        return {
            "repo": official_entry.get("repo"),
            "screenshot-main": official_entry.get("screenshot", ""),
            "screenshots-side": [],
            "tags": []
        }
    
    def print_sync_report(self):
        """Print a formatted synchronization report to console"""
        comparison = self.compare_json_files()
        suggestions = self.suggest_cleanup_actions()
        
        print("=" * 60)
        print("THEME DATA SYNCHRONIZATION REPORT")
        print("=" * 60)
        print(f"Official themes count: {comparison['official_count']}")
        print(f"Addon entries count: {comparison['addon_count']}")
        print(f"Sync percentage: {comparison['sync_percentage']:.1f}%")
        print()
        
        print(f"Missing addon entries: {comparison['missing_count']}")
        if comparison['missing_count'] > 0:
            print("  Repos needing addon entries:")
            for entry in comparison['missing_addon_entries'][:5]:  # Show first 5
                print(f"    - {entry.get('repo')} ({entry.get('name')})")
            if comparison['missing_count'] > 5:
                print(f"    ... and {comparison['missing_count'] - 5} more")
        print()
        
        print(f"Orphaned addon entries: {comparison['orphaned_count']}")
        if comparison['orphaned_count'] > 0:
            print("  Repos in addon but not official:")
            for entry in comparison['orphaned_addon_entries']:
                print(f"    - {entry.get('repo')}")
        print()
        
        if suggestions['review_required']:
            print("Review required:")
            for suggestion in suggestions['review_required']:
                print(f"  - {suggestion}")
        
        print("=" * 60)


# Example usage and testing
if __name__ == "__main__":
    # Example usage
    sync = DataSynchronizer()
    sync.print_sync_report()
    
    # Example of getting suggestions
    suggestions = sync.suggest_cleanup_actions()
    print("\nSuggested actions:")
    for action_type, actions in suggestions.items():
        if actions:
            print(f"\n{action_type.replace('_', ' ').title()}:")
            for action in actions:
                print(f"  - {action}")
