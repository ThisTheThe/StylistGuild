#!/usr/bin/env python3
"""
File Manager Module
Handles file operations, backups, and updates for theme JSON files
"""

import json
import shutil
import os
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path


class FileManager:
    def __init__(self, backup_dir: str = "backups"):
        """
        Initialize the FileManager
        
        Args:
            backup_dir: Directory to store backup files
        """
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
    
    def load_json_dict(self, file_path: str, description: str = "JSON file") -> Dict[str, Any]:
        """
        Load JSON data that should be a dictionary (like tag macros)
        
        Args:
            file_path: Path to JSON file
            description: Description for error messages
            
        Returns:
            Dictionary from JSON file, empty dict if error
        """
        path = Path(file_path)
        
        try:
            if not path.exists():
                print(f"Info: {description} file not found at {path} (this is normal for first run)")
                return {}
                
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            if not isinstance(data, dict):
                print(f"Warning: {description} should contain a dict, found {type(data).__name__}")
                return {}
                
            print(f"✅ Loaded {len(data)} entries from {description.lower()}")
            return data
            
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON in {description.lower()}: {str(e)}")
            return {}
        except Exception as e:
            print(f"❌ Error loading {description.lower()}: {str(e)}")
            return {}
            
    def load_json_data(self, file_path: str, description: str = "JSON file") -> List[Dict[str, Any]]:
        """
        Centralized JSON loading with consistent error handling
        
        Args:
            file_path: Path to JSON file
            description: Description for error messages (e.g., "Official themes", "Addon themes")
            
        Returns:
            List of dictionaries from JSON file, empty list if error
        """
        path = Path(file_path)
        
        try:
            if not path.exists():
                print(f"Info: {description} file not found at {path} (this is normal for first run)")
                return []
                
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            if not isinstance(data, list):
                print(f"Warning: {description} should contain a list, found {type(data).__name__}")
                return []
                
            print(f"✅ Loaded {len(data)} entries from {description.lower()}")
            return data
            
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON in {description.lower()}: {str(e)}")
            return []
        except Exception as e:
            print(f"❌ Error loading {description.lower()}: {str(e)}")
            return []

    def save_json_data(self, file_path: str, data: List[Dict[str, Any]], 
                      description: str = "JSON file", create_backup: bool = True) -> bool:
        """
        Centralized JSON saving with optional backup
        
        Args:
            file_path: Path to save JSON file
            data: List of dictionaries to save
            description: Description for messages
            create_backup: Whether to create backup before saving
            
        Returns:
            bool: True if save successful
        """
        path = Path(file_path)
        
        try:
            # Create backup if file exists and backup requested
            if create_backup and path.exists():
                backup_results = self.backup_json_files([str(path)], "pre_save")
                if not backup_results.get(str(path), False):
                    print(f"⚠️ Failed to create backup of {description.lower()}, continuing anyway...")
            
            # Ensure parent directory exists
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save JSON with pretty formatting
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Saved {len(data)} entries to {description.lower()}")
            return True
            
        except Exception as e:
            print(f"❌ Error saving {description.lower()}: {str(e)}")
            return False

    def load_both_json_files(self, official_path: str, addon_path: str) -> tuple[List[Dict], List[Dict]]:
        """
        Load both official and addon JSON files
        
        Returns:
            Tuple of (official_data, addon_data)
        """
        official_data = self.load_json_data(official_path, "Official themes")
        addon_data = self.load_json_data(addon_path, "Addon themes")
        return official_data, addon_data

    def validate_json_structure(self, file_path: str, expected_keys: List[str], 
                              description: str = "JSON file") -> Dict[str, Any]:
        """
        Validate JSON file structure and required keys
        
        Args:
            file_path: Path to JSON file
            expected_keys: List of required keys for each entry
            description: Description for messages
            
        Returns:
            Dict with validation results
        """
        data = self.load_json_data(file_path, description)
        
        if not data:
            return {"valid": False, "entries": 0, "errors": [f"No data loaded from {description}"]}
        
        results = {
            "valid": True,
            "entries": len(data),
            "valid_entries": 0,
            "errors": []
        }
        
        for i, entry in enumerate(data):
            if not isinstance(entry, dict):
                results["errors"].append(f"Entry {i+1}: Not a dictionary")
                results["valid"] = False
                continue
                
            missing_keys = [key for key in expected_keys if key not in entry]
            if missing_keys:
                repo = entry.get("repo", f"entry {i+1}")
                results["errors"].append(f"{repo}: Missing keys: {missing_keys}")
                results["valid"] = False
            else:
                results["valid_entries"] += 1
        
        return results

    def print_file_status_report(self, official_path: str, addon_path: str):
        """
        Print comprehensive file status report
        """
        print("\n" + "="*60)
        print("FILE STATUS REPORT")
        print("="*60)
        
        # Get file stats
        stats = self.get_file_stats([official_path, addon_path])
        
        for file_path, file_stats in stats.items():
            file_type = "Official themes" if "community-css-themes.json" in file_path else "Addon themes"
            print(f"\n{file_type}: {file_path}")
            
            if not file_stats.get("exists", False):
                print("  ❌ File not found")
                continue
                
            if "error" in file_stats:
                print(f"  ❌ Error: {file_stats['error']}")
                continue
                
            print(f"  ✅ Size: {file_stats['size_mb']} MB ({file_stats['size_bytes']} bytes)")
            print(f"  📅 Modified: {file_stats['modified']}")
            print(f"  📊 Entries: {file_stats['entry_count']}")
            print(f"  🔧 Valid JSON: {'✅' if file_stats['valid_json'] else '❌'}")
        
        print("="*60)
    
    def backup_json_files(self, file_paths: List[str], 
                         backup_suffix: Optional[str] = None) -> Dict[str, bool]:
        """
        Create timestamped backups of JSON files
        
        Args:
            file_paths: List of file paths to backup
            backup_suffix: Optional suffix for backup files
            
        Returns:
            Dict: Results of backup operations {filepath: success_bool}
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if backup_suffix:
            timestamp = f"{timestamp}_{backup_suffix}"
        
        results = {}
        
        for file_path in file_paths:
            source_path = Path(file_path)
            
            if not source_path.exists():
                print(f"Warning: {file_path} does not exist, skipping backup")
                results[file_path] = False
                continue
            
            try:
                # Create backup filename
                backup_filename = f"{source_path.stem}_{timestamp}{source_path.suffix}"
                backup_path = self.backup_dir / backup_filename
                
                # Copy file
                shutil.copy2(source_path, backup_path)
                print(f"✓ Backed up {file_path} to {backup_path}")
                results[file_path] = True
                
            except Exception as e:
                print(f"✗ Failed to backup {file_path}: {str(e)}")
                results[file_path] = False
        
        return results
    
    def restore_from_backup(self, original_path: str, 
                          backup_filename: Optional[str] = None) -> bool:
        """
        Restore a file from backup
        
        Args:
            original_path: Path where the file should be restored
            backup_filename: Specific backup file to restore from (if None, uses latest)
            
        Returns:
            bool: True if restoration successful
        """
        try:
            original_file = Path(original_path)
            
            if backup_filename:
                backup_path = self.backup_dir / backup_filename
                if not backup_path.exists():
                    print(f"✗ Backup file {backup_filename} not found")
                    return False
            else:
                # Find latest backup for this file
                backup_pattern = f"{original_file.stem}_*{original_file.suffix}"
                backup_files = list(self.backup_dir.glob(backup_pattern))
                
                if not backup_files:
                    print(f"✗ No backup files found for {original_path}")
                    return False
                
                # Sort by modification time, get newest
                backup_path = max(backup_files, key=lambda p: p.stat().st_mtime)
                print(f"Using latest backup: {backup_path.name}")
            
            # Restore the file
            shutil.copy2(backup_path, original_file)
            print(f"✓ Restored {original_path} from backup")
            return True
            
        except Exception as e:
            print(f"✗ Failed to restore {original_path}: {str(e)}")
            return False
    
    def list_backups(self, file_pattern: str = "*") -> List[Dict[str, Any]]:
        """
        List available backup files
        
        Args:
            file_pattern: Pattern to filter backup files
            
        Returns:
            List of backup file information dictionaries
        """
        backup_files = []
        
        for backup_path in self.backup_dir.glob(f"{file_pattern}*"):
            if backup_path.is_file():
                stat = backup_path.stat()
                backup_files.append({
                    "filename": backup_path.name,
                    "path": str(backup_path),
                    "size": stat.st_size,
                    "created": datetime.fromtimestamp(stat.st_mtime),
                    "size_mb": round(stat.st_size / (1024 * 1024), 2)
                })
        
        # Sort by creation time (newest first)
        backup_files.sort(key=lambda x: x["created"], reverse=True)
        return backup_files
    
    def merge_official_updates(self, new_official_path: str, 
                             current_official_path: str,
                             addon_path: str) -> Dict[str, Any]:
        """
        Handle when official JSON gets updated - merge changes while preserving addon data
        
        Args:
            new_official_path: Path to new official JSON
            current_official_path: Path to current official JSON
            addon_path: Path to addon JSON
            
        Returns:
            Dict: Results of merge operation
        """
        try:
            # Load all three files
            with open(new_official_path, 'r', encoding='utf-8') as f:
                new_official = json.load(f)
            
            current_official = []
            if Path(current_official_path).exists():
                with open(current_official_path, 'r', encoding='utf-8') as f:
                    current_official = json.load(f)
            
            addon_data = []
            if Path(addon_path).exists():
                with open(addon_path, 'r', encoding='utf-8') as f:
                    addon_data = json.load(f)
            
            # Create repo sets for comparison
            current_repos = {theme.get("repo") for theme in current_official}
            new_repos = {theme.get("repo") for theme in new_official}
            addon_repos = {theme.get("repo") for theme in addon_data}
            
            # Analyze changes
            added_repos = new_repos - current_repos
            removed_repos = current_repos - new_repos
            
            results = {
                "new_themes_count": len(new_official),
                "current_themes_count": len(current_official),
                "addon_entries_count": len(addon_data),
                "themes_added": len(added_repos),
                "themes_removed": len(removed_repos),
                "added_repos": list(added_repos),
                "removed_repos": list(removed_repos),
                "orphaned_addon_entries": [],
                "backup_created": False
            }
            
            # Create backup before making changes
            backup_results = self.backup_json_files([current_official_path, addon_path], 
                                                   "pre_merge")
            results["backup_created"] = all(backup_results.values())
            
            # Update official file
            shutil.copy2(new_official_path, current_official_path)
            print(f"✓ Updated official themes file with {len(new_official)} themes")
            
            # Check for orphaned addon entries
            orphaned_addon_repos = addon_repos - new_repos
            if orphaned_addon_repos:
                results["orphaned_addon_entries"] = list(orphaned_addon_repos)
                print(f"Warning: {len(orphaned_addon_repos)} addon entries may be orphaned")
            
            return results
            
        except Exception as e:
            print(f"✗ Error merging official updates: {str(e)}")
            return {"error": str(e)}
    
    def export_reports(self, data: Dict[str, Any], 
                      output_path: str, 
                      report_format: str = 'txt') -> bool:
        """
        Export various reports in different formats
        
        Args:
            data: Report data to export
            output_path: Path to save the report
            report_format: Format ('txt', 'json', 'csv')
            
        Returns:
            bool: True if export successful
        """
        try:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            if report_format.lower() == 'json':
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False, default=str)
                    
            elif report_format.lower() == 'csv':
                # For CSV, we need to flatten the data structure
                self._export_csv_report(data, output_file)
                    
            else:  # Default to txt
                self._export_txt_report(data, output_file)
            
            print(f"✓ Report exported to {output_file}")
            return True
            
        except Exception as e:
            print(f"✗ Error exporting report: {str(e)}")
            return False
    
    def _export_txt_report(self, data: Dict[str, Any], output_file: Path):
        """Export data as formatted text report"""
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("THEME DATA REPORT\n")
            f.write("=" * 50 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            for key, value in data.items():
                f.write(f"{key.replace('_', ' ').title()}: ")
                
                if isinstance(value, list):
                    f.write(f"{len(value)} items\n")
                    for i, item in enumerate(value[:10], 1):  # Show first 10 items
                        f.write(f"  {i}. {item}\n")
                    if len(value) > 10:
                        f.write(f"  ... and {len(value) - 10} more\n")
                elif isinstance(value, dict):
                    f.write("(nested data)\n")
                    for sub_key, sub_value in value.items():
                        f.write(f"  {sub_key}: {sub_value}\n")
                else:
                    f.write(f"{value}\n")
                f.write("\n")
    
    def _export_csv_report(self, data: Dict[str, Any], output_file: Path):
        """Export data as CSV (simplified version)"""
        import csv
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Key', 'Value', 'Type'])
            
            for key, value in data.items():
                if isinstance(value, (list, dict)):
                    writer.writerow([key, str(len(value)) if isinstance(value, list) else 'nested', type(value).__name__])
                else:
                    writer.writerow([key, value, type(value).__name__])
    
    def cleanup_old_backups(self, days_to_keep: int = 30) -> Dict[str, int]:
        """
        Remove backup files older than specified days
        
        Args:
            days_to_keep: Number of days to keep backups
            
        Returns:
            Dict: Cleanup results {removed: count, kept: count, errors: count}
        """
        cutoff_time = datetime.now().timestamp() - (days_to_keep * 24 * 60 * 60)
        
        results = {"removed": 0, "kept": 0, "errors": 0}
        
        for backup_file in self.backup_dir.iterdir():
            if backup_file.is_file():
                try:
                    if backup_file.stat().st_mtime < cutoff_time:
                        backup_file.unlink()
                        results["removed"] += 1
                        print(f"Removed old backup: {backup_file.name}")
                    else:
                        results["kept"] += 1
                except Exception as e:
                    print(f"Error removing {backup_file.name}: {str(e)}")
                    results["errors"] += 1
        
        print(f"Cleanup complete: {results['removed']} removed, {results['kept']} kept")
        return results
    
    def validate_json_syntax(self, file_path: str) -> Tuple[bool, Optional[str]]:
        """
        Validate JSON file syntax
        
        Args:
            file_path: Path to JSON file
            
        Returns:
            Tuple: (is_valid, error_message)
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                json.load(f)
            return True, None
        except json.JSONDecodeError as e:
            return False, f"JSON syntax error: {str(e)}"
        except FileNotFoundError:
            return False, "File not found"
        except Exception as e:
            return False, f"Error reading file: {str(e)}"
    
    def get_file_stats(self, file_paths: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Get statistics for multiple files
        
        Args:
            file_paths: List of file paths to analyze
            
        Returns:
            Dict: File statistics
        """
        stats = {}
        
        for file_path in file_paths:
            path = Path(file_path)
            
            if not path.exists():
                stats[file_path] = {"exists": False}
                continue
            
            try:
                file_stat = path.stat()
                
                # Try to load as JSON to get entry count
                entry_count = 0
                is_valid_json = False
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            entry_count = len(data)
                        is_valid_json = True
                except:
                    pass
                
                stats[file_path] = {
                    "exists": True,
                    "size_bytes": file_stat.st_size,
                    "size_mb": round(file_stat.st_size / (1024 * 1024), 2),
                    "modified": datetime.fromtimestamp(file_stat.st_mtime),
                    "entry_count": entry_count,
                    "valid_json": is_valid_json
                }
                
            except Exception as e:
                stats[file_path] = {"exists": True, "error": str(e)}
        
        return stats
    
    def print_backup_report(self):
        """Print a formatted report of available backups"""
        backups = self.list_backups()
        
        print("=" * 60)
        print("BACKUP FILES REPORT")
        print("=" * 60)
        print(f"Total backups: {len(backups)}")
        print(f"Backup directory: {self.backup_dir}")
        print()
        
        if not backups:
            print("No backup files found.")
            return
        
        print("Recent backups:")
        print("-" * 60)
        print(f"{'Filename':<30} {'Size (MB)':<10} {'Created':<20}")
        print("-" * 60)
        
        for backup in backups[:10]:  # Show first 10
            print(f"{backup['filename']:<30} {backup['size_mb']:<10} {backup['created'].strftime('%Y-%m-%d %H:%M'):<20}")
        
        if len(backups) > 10:
            print(f"... and {len(backups) - 10} more backup files")
        
        print("=" * 60)


# Example usage and testing
if __name__ == "__main__":
    file_manager = FileManager()
    
    # Example operations:
    
    # 1. Create backups
    files_to_backup = ["community-css-themes.json", "community-css-themes-tag-browser.json"]
    backup_results = file_manager.backup_json_files(files_to_backup, "test")
    print("Backup results:", backup_results)
    
    # 2. Show backup report
    file_manager.print_backup_report()
    
    # 3. Get file statistics
    stats = file_manager.get_file_stats(files_to_backup)
    print("\nFile statistics:")
    for file_path, file_stats in stats.items():
        print(f"{file_path}: {file_stats}")
    
    # 4. Cleanup old backups (example - don't actually run without confirming)
    # cleanup_results = file_manager.cleanup_old_backups(days_to_keep=7)
    # print("Cleanup results:", cleanup_results)