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
        
        # Confirm
        confirm = input("Save this addon entry? (y/n): ").lower().strip()
        if confirm == 'y':
            return addon_entry
        else:
            return None
    
    def bulk_tag_assignment(self, repos_list: List[str], tags: List[str]) -> bool:
        """
        Assign tags to multiple repos at once
        
        Args:
            repos_list: List of repository identifiers
            tags: List of tags to assign
            
        Returns:
            bool: True if successful
        """
        try:
            addon_data = self._load_addon_data()
            updated_count = 0
            
            for repo in repos_list:
                # Find the entry
                for entry in addon_data:
                    if entry.get("repo") == repo:
                        # Merge tags (avoid duplicates)
                        existing_tags = set(entry.get("tags", []))
                        new_tags = existing_tags.union(set(tags))
                        entry["tags"] = sorted(list(new_tags))
                        updated_count += 1
                        break
            
            if updated_count > 0:
                self._save_addon_data(addon_data)
                print(f"✓ Updated tags for {updated_count} repositories")
                return True
            else:
                print("✗ No matching repositories found")
                return False
                
        except Exception as e:
            print(f"✗ Error in bulk tag assignment: {str(e)}")
            return False
    
    def validate_all_data(self) -> Dict[str, Any]:
        """
        Validate both official and addon JSON files
        
        Returns:
            Dict: Validation results for both files
        """
        results = {
            "official": {"valid": False, "results": None},
            "addon": {"valid": False, "results": None}
        }
        
        try:
            # Load and validate official data
            if self.synchronizer._official_data is None:
                self.synchronizer.load_json_files()
            
            if self.synchronizer._official_data:
                official_validation = self.validator.validate_official_schema(self.synchronizer._official_data)
                results["official"]["valid"] = official_validation["is_valid"]
                results["official"]["results"] = official_validation
            
            # Load and validate addon data
            if self.synchronizer._addon_data:
                addon_validation = self.validator.validate_addon_schema(self.synchronizer._addon_data)
                results["addon"]["valid"] = addon_validation["is_valid"]
                results["addon"]["results"] = addon_validation
            
        except Exception as e:
            print(f"Error during validation: {str(e)}")
        
        return results
    
    def clean_orphaned_entries(self, confirm: bool = True) -> Dict[str, Any]:
        """
        Remove orphaned entries from addon JSON
        
        Args:
            confirm: Whether to ask for confirmation before removing
            
        Returns:
            Dict: Cleanup results
        """
        orphaned_entries = self.synchronizer.find_orphaned_addon_entries()
        
        if not orphaned_entries:
            print("✓ No orphaned entries found")
            return {"removed": 0, "kept": 0}
        
        print(f"Found {len(orphaned_entries)} orphaned addon entries:")
        for entry in orphaned_entries:
            print(f"  - {entry.get('repo')}")
        
        if confirm:
            remove = input(f"\nRemove all {len(orphaned_entries)} orphaned entries? (y/n): ").lower().strip()
            if remove != 'y':
                return {"removed": 0, "kept": len(orphaned_entries)}
        
        # Remove orphaned entries
        try:
            addon_data = self._load_addon_data()
            orphaned_repos = {entry.get("repo") for entry in orphaned_entries}
            
            cleaned_data = [entry for entry in addon_data 
                          if entry.get("repo") not in orphaned_repos]
            
            removed_count = len(addon_data) - len(cleaned_data)
            
            if self._save_addon_data(cleaned_data):
                print(f"✓ Removed {removed_count} orphaned entries")
                return {"removed": removed_count, "kept": 0}
            else:
                print("✗ Failed to save cleaned data")
                return {"removed": 0, "kept": len(orphaned_entries)}
                
        except Exception as e:
            print(f"✗ Error cleaning orphaned entries: {str(e)}")
            return {"removed": 0, "kept": len(orphaned_entries)}
    
    def export_missing_entries_report(self, output_path: str = "missing_entries_report.txt") -> bool:
        """
        Export a report of missing entries to a text file
        
        Args:
            output_path: Path to save the report
            
        Returns:
            bool: True if successful
        """
        try:
            missing_entries = self.synchronizer.find_missing_addon_entries()
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("MISSING ADDON ENTRIES REPORT\n")
                f.write("=" * 50 + "\n\n")
                f.write(f"Generated entries that need addon data: {len(missing_entries)}\n\n")
                
                for i, entry in enumerate(missing_entries, 1):
                    f.write(f"{i}. {entry.get('name', 'Unknown')}\n")
                    f.write(f"   Author: {entry.get('author', 'Unknown')}\n")
                    f.write(f"   Repo: {entry.get('repo', 'Unknown')}\n")
                    f.write(f"   Screenshot: {entry.get('screenshot', 'None')}\n")
                    f.write(f"   Modes: {', '.join(entry.get('modes', []))}\n")
                    f.write("\n")
            
            print(f"✓ Report exported to {output_path}")
            return True
            
        except Exception as e:
            print(f"✗ Error exporting report: {str(e)}")
            return False
    
    def _create_minimal_addon_entry(self, official_entry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a minimal addon entry from official entry
        
        Args:
            official_entry: Official theme data
            
        Returns:
            Dict: Minimal addon entry
        """
        return {
            "repo": official_entry.get("repo"),
            "screenshot-main": official_entry.get("screenshot", ""),
            "screenshots-side": [],
            "tags": []
        }
    
    def _load_addon_data(self) -> List[Dict[str, Any]]:
        """Load addon JSON data, return empty list if file doesn't exist"""
        if not self.synchronizer._addon_data:
            self.synchronizer.load_json_files()
        return self.synchronizer._addon_data or []
    
    def _save_addon_data(self, data: List[Dict[str, Any]]) -> bool:
        """Save addon data to JSON file"""
        try:
            # Create backup
            if self.addon_path.exists():
                backup_path = self.addon_path.with_suffix('.json.backup')
                self.addon_path.rename(backup_path)
                print(f"Created backup: {backup_path}")
            
            # Save new data
            with open(self.addon_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # Update synchronizer's cached data
            self.synchronizer._addon_data = data
            
            return True
            
        except Exception as e:
            print(f"Error saving addon data: {str(e)}")
            return False
    
    def _print_processing_summary(self, results: Dict[str, Any]):
        """Print a summary of processing results"""
        print("\n" + "=" * 60)
        print("BATCH PROCESSING SUMMARY")
        print("=" * 60)
        print(f"Processed: {results['processed']}")
        print(f"Skipped: {results['skipped']}")
        print(f"Errors: {results['errors']}")
        
        if results.get('error_details'):
            print("\nErrors encountered:")
            for error in results['error_details']:
                print(f"  ✗ {error}")
        
        print("=" * 60)
    
    def run_interactive_session(self):
        """Run an interactive batch processing session"""
        print("=" * 60)
        print("THEME BATCH PROCESSOR - Interactive Session")
        print("=" * 60)
        
        while True:
            print("\nAvailable operations:")
            print("1. Process missing addon entries")
            print("2. Validate all data")
            print("3. Clean orphaned entries")
            print("4. Export missing entries report")
            print("5. Show sync status")
            print("6. Bulk tag assignment")
            print("7. Exit")
            
            choice = input("\nSelect operation (1-7): ").strip()
            
            if choice == '1':
                self.process_missing_entries(interactive=True)
            elif choice == '2':
                validation_results = self.validate_all_data()
                if validation_results["official"]["results"]:
                    self.validator.print_validation_report(validation_results["official"]["results"], "official")
                if validation_results["addon"]["results"]:
                    self.validator.print_validation_report(validation_results["addon"]["results"], "addon")
            elif choice == '3':
                self.clean_orphaned_entries(confirm=True)
            elif choice == '4':
                filename = input("Report filename (press enter for 'missing_entries_report.txt'): ").strip()
                if not filename:
                    filename = "missing_entries_report.txt"
                self.export_missing_entries_report(filename)
            elif choice == '5':
                self.synchronizer.print_sync_report()
            elif choice == '6':
                repos_input = input("Repository identifiers (comma-separated): ").strip()
                tags_input = input("Tags to assign (comma-separated): ").strip()
                if repos_input and tags_input:
                    repos = [r.strip() for r in repos_input.split(",")]
                    tags = [t.strip() for t in tags_input.split(",")]
                    self.bulk_tag_assignment(repos, tags)
            elif choice == '7':
                print("Goodbye!")
                break
            else:
                print("Invalid choice. Please select 1-7.")


# Example usage and testing
if __name__ == "__main__":
    # Example usage
    processor = BatchProcessor()
    
    # You can run different operations:
    
    # 1. Interactive session
    processor.run_interactive_session()
    
    # OR run specific operations programmatically:
    # processor.process_missing_entries(interactive=False)  # Non-interactive processing
    # processor.validate_all_data()
    # processor.clean_orphaned_entries(confirm=False)
    # processor.export_missing_entries_report()