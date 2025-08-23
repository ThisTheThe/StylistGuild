#!/usr/bin/env python3
"""
Batch Processor Module
Main orchestrator for handling batch operations on theme data
"""

import json
import os
from typing import Dict, List, Optional, Any
from pathlib import Path

# Import our other modules
try:
    from .data_synchronizer import DataSynchronizer
    from .json_validator import JsonValidator
    from .theme_data_collector import get_user_input, collect_theme_data
except ImportError:
    # For standalone testing, import without relative imports
    import sys
    sys.path.append(os.path.dirname(__file__))
    try:
        from data_synchronizer import DataSynchronizer
        from json_validator import JsonValidator
        # Note: theme_data_collector functions would need to be available
    except ImportError:
        print("Warning: Some dependencies not found. Some features may not work.")


class BatchProcessor:
    def __init__(self, official_json_path: str = "community-css-themes.json",
                 addon_json_path: str = "community-css-themes-tag-browser.json"):
        """
        Initialize the BatchProcessor
        
        Args:
            official_json_path: Path to official themes JSON
            addon_json_path: Path to addon themes JSON
        """
        self.synchronizer = DataSynchronizer(official_json_path, addon_json_path)
        self.validator = JsonValidator()
        self.official_path = Path(official_json_path)
        self.addon_path = Path(addon_json_path)
        
    def process_missing_entries(self, interactive: bool = True) -> Dict[str, Any]:
        """
        Main orchestrator for handling missing addon entries
        
        Args:
            interactive: Whether to prompt user for each missing entry
            
        Returns:
            Dict: Processing results summary
        """
        print("Starting batch processing of missing addon entries...")
        
        # Get missing entries
        missing_entries = self.synchronizer.find_missing_addon_entries()
        
        if not missing_entries:
            print("✓ No missing addon entries found. Everything is in sync!")
            return {"processed": 0, "skipped": 0, "errors": 0}
        
        print(f"Found {len(missing_entries)} missing addon entries.")
        
        results = {
            "processed": 0,
            "skipped": 0,
            "errors": 0,
            "created_entries": [],
            "error_details": []
        }
        
        # Load existing addon data
        addon_data = self._load_addon_data()
        
        for i, official_entry in enumerate(missing_entries, 1):
            repo = official_entry.get("repo", "unknown")
            name = official_entry.get("name", "Unknown")
            
            print(f"\n[{i}/{len(missing_entries)}] Processing: {name} ({repo})")
            
            try:
                if interactive:
                    addon_entry = self.interactive_entry_builder(official_entry)
                    if addon_entry:
                        addon_data.append(addon_entry)
                        results["created_entries"].append(addon_entry)
                        results["processed"] += 1
                        print(f"✓ Created addon entry for {repo}")
                    else:
                        results["skipped"] += 1
                        print(f"⊘ Skipped {repo}")
                else:
                    # Non-interactive: create minimal entries
                    addon_entry = self._create_minimal_addon_entry(official_entry)
                    addon_data.append(addon_entry)
                    results["created_entries"].append(addon_entry)
                    results["processed"] += 1
                    print(f"✓ Created minimal addon entry for {repo}")
                    
            except Exception as e:
                results["errors"] += 1
                error_msg = f"Error processing {repo}: {str(e)}"
                results["error_details"].append(error_msg)
                print(f"✗ {error_msg}")
        
        # Save updated addon data
        if results["processed"] > 0:
            if self._save_addon_data(addon_data):
                print(f"\n✓ Successfully saved {results['processed']} new addon entries")
            else:
                print(f"\n✗ Failed to save addon data")
                results["errors"] += 1
        
        self._print_processing_summary(results)
        return results
    
    def interactive_entry_builder(self, official_entry: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Interactive UI for building addon entries
        
        Args:
            official_entry: The official theme entry to base addon entry on
            
        Returns:
            Dict or None: New addon entry or None if skipped
        """
        repo = official_entry.get("repo")
        name = official_entry.get("name")
        author = official_entry.get("author")
        official_screenshot = official_entry.get("screenshot", "")
        
        print(f"\nCreating addon entry for: {name} by {author}")
        print(f"Repository: {repo}")
        print(f"Official screenshot: {official_screenshot}")
        print("-" * 50)
        
        # Ask if user wants to create entry
        create = input("Create addon entry for this theme? (y/n/q for quit): ").lower().strip()
        if create == 'q':
            return None
        if create != 'y':
            return None
        
        # Build addon entry
        addon_entry = {
            "repo": repo,
            "screenshot-main": "",
            "screenshots-side": [],
            "tags": []
        }
        
        # Screenshot main
        print(f"\n1. Main screenshot (current: '{official_screenshot}')")
        print("   Options: [enter] to use official, or provide new URL/filename")
        main_screenshot = input("   Main screenshot: ").strip()
        addon_entry["screenshot-main"] = main_screenshot if main_screenshot else official_screenshot
        
        # Additional screenshots
        print("\n2. Additional screenshots (URLs, one per line, empty line to finish)")
        screenshots_side = []
        while True:
            url = input("   Screenshot URL: ").strip()
            if not url:
                break
            screenshots_side.append(url)
        addon_entry["screenshots-side"] = screenshots_side
        
        # Tags
        print("\n3. Tags (comma-separated, e.g. 'dark, minimal, productivity')")
        tags_input = input("   Tags: ").strip()
        if tags_input:
            tags = [tag.strip() for tag in tags_input.split(",") if tag.strip()]
            addon_entry["tags"] = tags
        
        # Show preview
        print("\n" + "="*50)
        print("ADDON ENTRY PREVIEW:")
        print(json.dumps(addon_entry, indent=2))
        print("="*50)
        
        #