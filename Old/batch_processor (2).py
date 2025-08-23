#!/usr/bin/env python3
"""
Batch Processor Module
Main orchestrator for handling batch operations on theme data
"""

import json
import os
from typing import Dict, List, Optional, Any
from pathlib import Path
import webbrowser
import datetime

# Import our other modules
try:
    # First try relative imports (if this file is in the pythonThemeTools directory)
    from .data_synchronizer import DataSynchronizer
    from .json_validator import JsonValidator
    from .theme_data_collector import get_user_input, collect_theme_data
    from pythonThemeTools.theme_renderer import ThemeRenderer
except ImportError:
    try:
        # Try importing from pythonThemeTools subdirectory
        from pythonThemeTools.data_synchronizer import DataSynchronizer
        from pythonThemeTools.json_validator import JsonValidator
        from pythonThemeTools.theme_data_collector import get_user_input, collect_theme_data
        from pythonThemeTools.theme_renderer import ThemeRenderer
    except ImportError:
        try:
            # For standalone testing, import without relative imports from same directory
            import sys
            current_dir = os.path.dirname(__file__)
            pythonThemeTools_dir = os.path.join(current_dir, "pythonThemeTools")
            
            # Add both current directory and pythonThemeTools to path
            if current_dir not in sys.path:
                sys.path.append(current_dir)
            if pythonThemeTools_dir not in sys.path:
                sys.path.append(pythonThemeTools_dir)
            
            from data_synchronizer import DataSynchronizer
            from json_validator import JsonValidator
            from theme_data_collector import get_user_input, collect_theme_data
            from theme_renderer import ThemeRenderer
        except ImportError:
            print("Warning: Some dependencies not found in pythonThemeTools directory.")
            print("Expected files: pythonThemeTools/data_synchronizer.py, pythonThemeTools/json_validator.py")
            print("Some features may not work properly.")
            
            # Create dummy classes to prevent crashes
            class DataSynchronizer:
                def __init__(self, *args, **kwargs):
                    pass
                def find_missing_addon_entries(self):
                    return []
            
            class JsonValidator:
                def __init__(self, *args, **kwargs):
                    pass
                def validate_json_file(self, path):
                    return True, []


def open_github_repo(repo: str):
    """
    Open the GitHub repository page in the default web browser.
    
    Args:
        repo: The repository identifier in the format "owner/repo-name".
    """
    url = f"https://github.com/{repo}"
    try:
        webbrowser.open(url)
        print("✅ Opened GitHub repository in browser.")
    except Exception as e:
        print(f"⚠️ Could not open browser: {str(e)}")


class BatchProcessor:
    def __init__(self, official_json_path: str = "community-css-themes.json",
                 addon_json_path: str = "community-css-themes-tag-browser.json",
                 macros_path: Optional[str] = "tag_macros.json"):
        """
        Initialize the BatchProcessor
        
        Args:
            official_json_path: Path to official themes JSON
            addon_json_path: Path to addon themes JSON
            macros_path: Optional path to external JSON file for tag macros
        """
        self.synchronizer = DataSynchronizer(official_json_path, addon_json_path)
        self.validator = JsonValidator()
        self.official_path = Path(official_json_path)
        self.addon_path = Path(addon_json_path)
        
        # Load tag macros from external file if it exists, else use defaults
        self.tag_macros = {
            "m": "minimalistic",
            # Add more default macros here as needed, e.g.
            # "d": "dark",
            # "l": "light",
        }
        if Path(macros_path).exists():
            try:
                with open(macros_path, 'r', encoding='utf-8') as f:
                    loaded_macros = json.load(f)
                if isinstance(loaded_macros, dict):
                    self.tag_macros = loaded_macros
                    print(f"✅ Loaded tag macros from {macros_path}")
                else:
                    print(f"⚠️ Invalid format in {macros_path}; using default macros")
            except Exception as e:
                print(f"⚠️ Error loading macros from {macros_path}: {str(e)}; using default macros")
        else:
            print(f"ℹ️ Macros file {macros_path} not found; using default macros")
        
    def run_interactive_menu(self):
        """
        Main interactive menu for accessing all functionality without command line parameters
        """
        while True:
            self._display_main_menu()
            choice = input("\nEnter your choice (1-9): ").strip()
            
            try:
                if choice == '1':
                    self._menu_process_missing_entries()
                elif choice == '2':
                    self._menu_validate_json_files()
                elif choice == '3':
                    self._menu_sync_data()
                elif choice == '4':
                    self._menu_create_single_entry()
                elif choice == '5':
                    self._menu_view_statistics()
                elif choice == '6':
                    self._menu_configure_paths()
                elif choice == '7':
                    self._menu_export_data()
                elif choice == '8':
                    self._menu_debug_info()
                elif choice == '9':
                    self._menu_render_themes()
                elif choice == '10':
                    print("Goodbye!")
                    break
                else:
                    print("Invalid choice. Please select 1-10.")
                    
            except KeyboardInterrupt:
                print("\n\nOperation cancelled by user.")
                continue
            except Exception as e:
                print(f"\nError: {str(e)}")
                input("Press Enter to continue...")
                continue
                
            input("\nPress Enter to continue...")
    
    def _display_main_menu(self):
        """Display the main menu options"""
        print("\n" + "="*60)
        print("           THEME BATCH PROCESSOR")
        print("="*60)
        print("1. Process Missing Addon Entries (Interactive)")
        print("2. Validate JSON Files")
        print("3. Synchronize Data Files")
        print("4. Create Single Addon Entry")
        print("5. View Statistics & File Status")
        print("6. Configure File Paths")
        print("7. Export Data")
        print("8. Debug Information")
        print("9. Render Theme Pages")
        print("10. Exit")
        print("="*60)
        print(f"Current directory: {os.getcwd()}")
        print(f"Official JSON: {self.official_path}")
        print(f"Addon JSON: {self.addon_path}")
        print("="*60)
    
    def _menu_process_missing_entries(self):
        """Menu option for processing missing entries"""
        print("\n" + "-"*50)
        print("PROCESS MISSING ADDON ENTRIES")
        print("-"*50)
        
        print("Choose processing mode:")
        print("1. Interactive mode (prompt for each entry)")
        print("2. Automatic mode (create minimal entries)")
        print("3. Review mode (show missing entries only)")
        
        mode = input("Select mode (1-3): ").strip()
        
        if mode == '1':
            results = self.process_missing_entries(interactive=True)
        elif mode == '2':
            results = self.process_missing_entries(interactive=False)
        elif mode == '3':
            self._review_missing_entries()
            return
        else:
            print("Invalid selection.")
            return
        
        print(f"\nProcessing completed:")
        print(f"  Processed: {results['processed']}")
        print(f"  Skipped: {results['skipped']}")
        print(f"  Errors: {results['errors']}")
    
    def _menu_validate_json_files(self):
        """Menu option for validating JSON files"""
        print("\n" + "-"*50)
        print("VALIDATE JSON FILES")
        print("-"*50)
        
        files_to_validate = [
            (self.official_path, "Official Themes JSON"),
            (self.addon_path, "Addon Themes JSON")
        ]
        
        for file_path, description in files_to_validate:
            print(f"\nValidating {description}: {file_path}")
            
            if not file_path.exists():
                print(f"  ❌ File not found: {file_path}")
                print(f"  Current working directory: {os.getcwd()}")
                print(f"  Looking for file at: {file_path.absolute()}")
                continue
                
            try:
                # First check if it's valid JSON syntax
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                print(f"  ✅ Valid JSON syntax ({len(data)} entries)")
                
                # Then validate schema if validator is available
                if hasattr(self.validator, 'validate_official_schema'):
                    if 'official' in description.lower():
                        results = self.validator.validate_official_schema(data)
                    else:
                        results = self.validator.validate_addon_schema(data)
                    
                    if results['is_valid']:
                        print(f"  ✅ Schema validation passed")
                    else:
                        print(f"  ❌ Schema validation failed:")
                        print(f"    Valid entries: {results['valid_entries']}/{results['total_entries']}")
                        for entry_result in results['entry_results'][:3]:  # Show first 3 errors
                            if not entry_result['is_valid']:
                                print(f"    - {entry_result['repo']}: {entry_result['errors'][0]}")
                else:
                    print(f"  ⚠️  Schema validator not available, syntax check only")
                    
            except json.JSONDecodeError as e:
                print(f"  ❌ JSON syntax error: {str(e)}")
            except Exception as e:
                print(f"  ❌ Error validating file: {str(e)}")
                print(f"  Error type: {type(e).__name__}")
    
    def _menu_sync_data(self):
        """Menu option for synchronizing data"""
        print("\n" + "-"*50)
        print("SYNCHRONIZE DATA FILES")
        print("-"*50)
        
        # Check if files exist first
        print("File Status:")
        print(f"  Official JSON: {self.official_path} {'✅' if self.official_path.exists() else '❌ NOT FOUND'}")
        print(f"  Addon JSON: {self.addon_path} {'✅' if self.addon_path.exists() else '❌ NOT FOUND'}")
        
        if not self.official_path.exists():
            print(f"\n❌ Cannot synchronize: Official JSON file not found at {self.official_path}")
            print(f"Current working directory: {os.getcwd()}")
            print("Please check the file path or use option 6 to configure paths.")
            return
        
        try:
            # Check if synchronizer is working
            if not hasattr(self.synchronizer, 'find_missing_addon_entries'):
                print("❌ Data synchronizer not properly initialized")
                return
                
            # Show current sync status with detailed debugging
            print("Testing synchronizer...")
            missing = self.synchronizer.find_missing_addon_entries()
            print(f"\nSync Status:")
            print(f"  Missing addon entries: {len(missing)}")
            
            # Additional debugging - check the data manually
            official_data = self._load_official_data()
            addon_data = self._load_addon_data()
            
            print(f"  Manual count check:")
            print(f"    Official themes loaded: {len(official_data)}")
            print(f"    Addon themes loaded: {len(addon_data)}")
            
            if official_data and addon_data:
                official_repos = set()
                addon_repos = set()
                
                for entry in official_data:
                    repo = entry.get('repo')
                    if repo:
                        official_repos.add(repo)
                
                for entry in addon_data:
                    repo = entry.get('repo')
                    if repo:
                        addon_repos.add(repo)
                
                manual_missing = official_repos - addon_repos
                print(f"    Manual missing count: {len(manual_missing)}")
                
                if len(manual_missing) != len(missing):
                    print(f"    ⚠️  MISMATCH: Synchronizer says {len(missing)}, manual count says {len(manual_missing)}")
                    if manual_missing and len(manual_missing) <= 10:
                        print(f"    Manual missing repos: {list(manual_missing)}")
            
            if missing:
                print("\nMissing entries (showing first 10):")
                for i, entry in enumerate(missing[:10], 1):
                    name = entry.get('name', 'Unknown')
                    repo = entry.get('repo', 'unknown')
                    print(f"  {i:2}. {name} ({repo})")
                    
                if len(missing) > 10:
                    print(f"  ... and {len(missing) - 10} more")
            else:
                print("✅ Synchronizer reports all data is synchronized!")
                print("    (But manual count suggests otherwise - check DataSynchronizer implementation)")
                
        except Exception as e:
            print(f"❌ Error checking synchronization: {str(e)}")
            print(f"Error type: {type(e).__name__}")
            import traceback
            print("Traceback:")
            traceback.print_exc()
    
    def _menu_create_single_entry(self):
        """Menu option for creating a single addon entry"""
        print("\n" + "-"*50)
        print("CREATE SINGLE ADDON ENTRY")
        print("-"*50)
        
        # Get repository information
        repo = input("Repository (owner/repo-name): ").strip()
        if not repo:
            print("Repository is required.")
            return

        # Offer to open the GitHub page
        
        open_github_repo(repo)
            
        name = input("Theme name: ").strip()
        author = input("Author: ").strip()
        modes_input = input("Supported modes (comma-separated, e.g. dark, light). Enter to skip: ").strip()
        modes = [m.strip().lower() for m in modes_input.split(',') if m.strip()] if modes_input else []
        
        # Create mock official entry
        official_entry = {
            "repo": repo,
            "name": name or "Unknown Theme",
            "author": author or "Unknown Author",
            "screenshot": "",
            "modes": modes
        }
        
        # Use interactive builder
        addon_entry = self.interactive_entry_builder(official_entry)
        
        if addon_entry:
            # Load and save addon data
            addon_data = self._load_addon_data()
            addon_data.append(addon_entry)
            
            if self._save_addon_data(addon_data):
                print("✅ Addon entry created with auto-tagging and saved immediately!")
            else:
                print("❌ Failed to save addon entry.")
        else:
            print("Entry creation cancelled.")
    
    def _menu_debug_info(self):
        """Menu option for showing debug information"""
        print("\n" + "-"*50)
        print("DEBUG INFORMATION")
        print("-"*50)
        
        print("System Information:")
        import sys
        print(f"  Python version: {sys.version}")
        print(f"  Current working directory: {os.getcwd()}")
        print(f"  Script location: {os.path.dirname(os.path.abspath(__file__))}")
        
        print("\nFile Paths:")
        print(f"  Official JSON path: {self.official_path}")
        print(f"  Official JSON absolute: {self.official_path.absolute()}")
        print(f"  Official JSON exists: {self.official_path.exists()}")
        print(f"  Addon JSON path: {self.addon_path}")
        print(f"  Addon JSON absolute: {self.addon_path.absolute()}")
        print(f"  Addon JSON exists: {self.addon_path.exists()}")
        
        print("\nImported Modules:")
        print(f"  DataSynchronizer: {type(self.synchronizer)}")
        print(f"  JsonValidator: {type(self.validator)}")
        
        print("\nMethods Available:")
        sync_methods = [method for method in dir(self.synchronizer) if not method.startswith('_')]
        validator_methods = [method for method in dir(self.validator) if not method.startswith('_')]
        print(f"  DataSynchronizer methods: {sync_methods}")
        print(f"  JsonValidator methods: {validator_methods}")
        
        print("\nDirectory Contents:")
        current_files = [f for f in os.listdir('.') if f.endswith('.json')]
        print(f"  JSON files in current directory: {current_files}")
        
        # Check pythonThemeTools directory
        pythonThemeTools_path = Path('pythonThemeTools')
        if pythonThemeTools_path.exists():
            python_files = [f for f in os.listdir('pythonThemeTools') if f.endswith('.py')]
            print(f"  Python files in pythonThemeTools/: {python_files}")
        else:
            print(f"  pythonThemeTools directory: NOT FOUND")
            
        # Test a simple operation
        print("\nTesting Operations:")
        try:
            official_data = self._load_official_data()
            print(f"  Official data loaded: {len(official_data)} entries")
            if official_data:
                print(f"  First official entry keys: {list(official_data[0].keys())}")
                print(f"  First official repo: {official_data[0].get('repo', 'NO REPO FIELD')}")
        except Exception as e:
            print(f"  Official data load failed: {str(e)}")
            
        try:
            addon_data = self._load_addon_data()
            print(f"  Addon data loaded: {len(addon_data)} entries")
            if addon_data:
                print(f"  First addon entry keys: {list(addon_data[0].keys())}")
                print(f"  First addon repo: {addon_data[0].get('repo', 'NO REPO FIELD')}")
        except Exception as e:
            print(f"  Addon data load failed: {str(e)}")
            
        # Test synchronizer logic manually
        print("\nTesting Synchronizer Logic:")
        try:
            official_data = self._load_official_data()
            addon_data = self._load_addon_data()
            
            if official_data and addon_data:
                official_repos = {entry.get('repo') for entry in official_data}
                addon_repos = {entry.get('repo') for entry in addon_data}
                
                print(f"  Official repos count: {len(official_repos)}")
                print(f"  Addon repos count: {len(addon_repos)}")
                print(f"  Official repos sample: {list(list(official_repos)[:5])}")
                print(f"  Addon repos sample: {list(list(addon_repos)[:5])}")
                
                missing_repos = official_repos - addon_repos
                extra_repos = addon_repos - official_repos
                
                print(f"  Missing in addon: {len(missing_repos)}")
                if missing_repos:
                    print(f"  Missing repos sample: {list(list(missing_repos)[:5])}")
                print(f"  Extra in addon: {len(extra_repos)}")
                if extra_repos:
                    print(f"  Extra repos sample: {list(list(extra_repos)[:5])}")
                    
        except Exception as e:
            print(f"  Manual synchronizer test failed: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def _menu_view_statistics(self):
        """Menu option for viewing statistics"""
        print("\n" + "-"*50)
        print("DATA STATISTICS & FILE STATUS")
        print("-"*50)
        
        # File existence check
        print("File Status:")
        print(f"  Official JSON: {self.official_path}")
        print(f"    Exists: {'✅' if self.official_path.exists() else '❌'}")
        if self.official_path.exists():
            stat = self.official_path.stat()
            print(f"    Size: {stat.st_size} bytes ({round(stat.st_size/1024, 1)} KB)")
            print(f"    Modified: {datetime.fromtimestamp(stat.st_mtime)}")
            
        print(f"  Addon JSON: {self.addon_path}")
        print(f"    Exists: {'✅' if self.addon_path.exists() else '❌'}")
        if self.addon_path.exists():
            stat = self.addon_path.stat()
            print(f"    Size: {stat.st_size} bytes ({round(stat.st_size/1024, 1)} KB)")
            print(f"    Modified: {datetime.fromtimestamp(stat.st_mtime)}")
        
        try:
            # Official themes stats
            official_data = self._load_official_data()
            print(f"\nOfficial themes: {len(official_data)}")
            
            # Addon themes stats
            addon_data = self._load_addon_data()
            print(f"Addon themes: {len(addon_data)}")
            
            # Missing entries
            if hasattr(self.synchronizer, 'find_missing_addon_entries'):
                try:
                    missing = self.synchronizer.find_missing_addon_entries()
                    print(f"Missing addon entries: {len(missing)}")
                except Exception as e:
                    print(f"Error checking missing entries: {str(e)}")
            else:
                print("Missing entries check: Not available (synchronizer issue)")
            
            # Tag statistics (if addon data exists)
            if addon_data:
                all_tags = []
                for entry in addon_data:
                    all_tags.extend(entry.get("tags", []))
                
                unique_tags = set(all_tags)
                print(f"Unique tags in addon data: {len(unique_tags)}")
                
                if unique_tags:
                    print("Most common tags:")
                    tag_counts = {}
                    for tag in all_tags:
                        tag_counts[tag] = tag_counts.get(tag, 0) + 1
                    
                    sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
                    for tag, count in sorted_tags[:10]:
                        print(f"  {tag}: {count}")
                        
        except Exception as e:
            print(f"❌ Error generating statistics: {str(e)}")
            import traceback
            print("Traceback:")
            traceback.print_exc()
    
    def _menu_configure_paths(self):
        """Menu option for configuring file paths"""
        print("\n" + "-"*50)
        print("CONFIGURE FILE PATHS")
        print("-"*50)
        
        print(f"Current official JSON path: {self.official_path}")
        print(f"Current addon JSON path: {self.addon_path}")
        
        print("\n1. Change official JSON path")
        print("2. Change addon JSON path")
        print("3. Reset to defaults")
        
        choice = input("Select option (1-3): ").strip()
        
        if choice == '1':
            new_path = input("Enter new official JSON path: ").strip()
            if new_path:
                self.official_path = Path(new_path)
                self.synchronizer = DataSynchronizer(str(self.official_path), str(self.addon_path))
                print("✅ Official JSON path updated.")
                
        elif choice == '2':
            new_path = input("Enter new addon JSON path: ").strip()
            if new_path:
                self.addon_path = Path(new_path)
                self.synchronizer = DataSynchronizer(str(self.official_path), str(self.addon_path))
                print("✅ Addon JSON path updated.")
                
        elif choice == '3':
            self.official_path = Path("community-css-themes.json")
            self.addon_path = Path("community-css-themes-tag-browser.json")
            self.synchronizer = DataSynchronizer(str(self.official_path), str(self.addon_path))
            print("✅ Paths reset to defaults.")
    
    def _menu_export_data(self):
        """Menu option for exporting data"""
        print("\n" + "-"*50)
        print("EXPORT DATA")
        print("-"*50)
        
        print("1. Export missing entries to JSON")
        print("2. Export statistics to text file")
        print("3. Export all addon data to JSON")
        
        choice = input("Select export option (1-3): ").strip()
        
        if choice == '1':
            self._export_missing_entries()
        elif choice == '2':
            self._export_statistics()
        elif choice == '3':
            self._export_addon_data()
    
    def _review_missing_entries(self):
        """Review missing entries without processing"""
        missing_entries = self.synchronizer.find_missing_addon_entries()
        
        if not missing_entries:
            print("✅ No missing addon entries found!")
            return
        
        print(f"\nFound {len(missing_entries)} missing addon entries:")
        print("-" * 60)
        
        for i, entry in enumerate(missing_entries, 1):
            name = entry.get("name", "Unknown")
            repo = entry.get("repo", "unknown")
            author = entry.get("author", "Unknown")
            
            print(f"{i:3}. {name}")
            print(f"     Repository: {repo}")
            print(f"     Author: {author}")
            print()
    
    def _export_missing_entries(self):
        """Export missing entries to JSON file"""
        try:
            missing_entries = self.synchronizer.find_missing_addon_entries()
            filename = input("Export filename (default: missing_entries.json): ").strip()
            if not filename:
                filename = "missing_entries.json"
            
            with open(filename, 'w') as f:
                json.dump(missing_entries, f, indent=2)
            
            print(f"✅ Exported {len(missing_entries)} missing entries to {filename}")
            
        except Exception as e:
            print(f"❌ Export failed: {str(e)}")
    
    def _export_statistics(self):
        """Export statistics to text file"""
        try:
            filename = input("Export filename (default: theme_statistics.txt): ").strip()
            if not filename:
                filename = "theme_statistics.txt"
            
            with open(filename, 'w') as f:
                f.write("Theme Data Statistics\n")
                f.write("=" * 50 + "\n\n")
                
                # Add statistics here
                official_data = self._load_official_data()
                addon_data = self._load_addon_data()
                missing = self.synchronizer.find_missing_addon_entries()
                
                f.write(f"Official themes: {len(official_data)}\n")
                f.write(f"Addon themes: {len(addon_data)}\n")
                f.write(f"Missing addon entries: {len(missing)}\n")
                
            print(f"✅ Statistics exported to {filename}")
            
        except Exception as e:
            print(f"❌ Export failed: {str(e)}")
    
    def _export_addon_data(self):
        """Export addon data to JSON file"""
        try:
            addon_data = self._load_addon_data()
            filename = input("Export filename (default: addon_data_export.json): ").strip()
            if not filename:
                filename = "addon_data_export.json"
            
            with open(filename, 'w') as f:
                json.dump(addon_data, f, indent=2)
            
            print(f"✅ Exported {len(addon_data)} addon entries to {filename}")
            
        except Exception as e:
            print(f"❌ Export failed: {str(e)}")
    
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
            print("✅ No missing addon entries found. Everything is in sync!")
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
                        self._save_addon_data(addon_data)  # save immediately
                        results["created_entries"].append(addon_entry)
                        results["processed"] += 1
                        print(f"✅ Created addon entry for {repo}")
                    else:
                        results["skipped"] += 1
                        print(f"⊘ Skipped {repo}")
                else:
                    # Non-interactive: create minimal entries
                    addon_entry = self._create_minimal_addon_entry(official_entry)
                    addon_data.append(addon_entry)
                    self._save_addon_data(addon_data)  # save immediately
                    results["created_entries"].append(addon_entry)
                    results["processed"] += 1
                    print(f"✅ Created minimal addon entry for {repo}")
                    
            except Exception as e:
                results["errors"] += 1
                error_msg = f"Error processing {repo}: {str(e)}"
                results["error_details"].append(error_msg)
                print(f"❌ {error_msg}")
        
        # Save updated addon data
        if results["processed"] > 0:
            if self._save_addon_data(addon_data):
                print(f"\n✅ Successfully saved {results['processed']} new addon entries")
            else:
                print(f"\n❌ Failed to save addon data")
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
        modes = official_entry.get("modes", [])
        
        print(f"\nCreating addon entry for: {name} by {author}")
        print(f"Repository: {repo}")
        print(f"Official screenshot: {official_screenshot}")
        print("-" * 50)

        # Offer to open the GitHub page
        open_github_repo(repo)
        
        # Build addon entry
        addon_entry = {
            "repo": repo,
            "screenshot-main": "",
            "screenshots-side": [],
            "tags": []
        }
        
        # Tags
        print("\n3. Tags (comma-separated, e.g. 'dark, minimal, productivity')")
        print("   You can use macros like 'm' for 'minimalistic'")
        tags_input = input("   Tags: ").strip()
        if tags_input.lower() == 'exit':
            return None
        tags = []
        if tags_input:
            for part in tags_input.split(","):
                stripped = part.strip()
                if stripped:
                    expanded = self.tag_macros.get(stripped, stripped)
                    tags.append(expanded)
        
        # Screenshot main
        print(f"\n1. Main screenshot (current: '{official_screenshot}')")
        print("   Options: [enter] to use official, or provide new URL/filename")
        main_screenshot = input("   Main screenshot: ").strip()
        if main_screenshot.lower() == 'exit':
            return None
        addon_entry["screenshot-main"] = main_screenshot if main_screenshot else official_screenshot
        
        # Additional screenshots
        print("\n2. Additional screenshots (URLs, one per line, empty line to finish)")
        screenshots_side = []
        while True:
            url = input("   Screenshot URL: ").strip()
            if url.lower() == 'exit':
                return None
            if not url:
                break
            screenshots_side.append(url)
        addon_entry["screenshots-side"] = screenshots_side
        
        
        # Auto-assign dark/light/dark_and_light based on modes
        default_tags = []
        if 'dark' in modes:
            default_tags.append('dark')
        if 'light' in modes:
            default_tags.append('light')
        if 'dark' in modes and 'light' in modes:
            default_tags.append('dark_and_light')
            
        print("Notm in tags?")
        if 'notm' in tags:
            print("Yes,  not adding minimalistic.")
        else:
            print("No, adding minimalistic.")
            default_tags.append('minimalistic')
        
        addon_entry['tags'] = sorted(set(tags + default_tags))
        
        # Show preview
        print("\n" + "="*50)
        print("ADDON ENTRY PREVIEW:")
        print(json.dumps(addon_entry, indent=2))
        print("="*50)
        
        return addon_entry
    
    def _create_minimal_addon_entry(self, official_entry: Dict[str, Any]) -> Dict[str, Any]:
        """Create a minimal addon entry from official entry, with auto dark/light tags"""
        modes = official_entry.get('modes', []) or []
        auto_tags = []
        if 'dark' in modes:
            auto_tags.append('dark')
        if 'light' in modes:
            auto_tags.append('light')
        if 'dark' in modes and 'light' in modes:
            auto_tags.append('dark_and_light')
        return {
            "repo": official_entry.get("repo"),
            "screenshot-main": official_entry.get("screenshot", ""),
            "screenshots-side": [],
            "tags": auto_tags
        }
    
    def _load_official_data(self) -> List[Dict[str, Any]]:
        """Load official themes data"""
        try:
            if not self.official_path.exists():
                print(f"Warning: Official JSON file not found at {self.official_path}")
                print(f"Current working directory: {os.getcwd()}")
                return []
                
            with open(self.official_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in official file: {str(e)}")
            return []
        except Exception as e:
            print(f"Error loading official data: {str(e)}")
            return []
    
    def _load_addon_data(self) -> List[Dict[str, Any]]:
        """Load addon themes data"""
        try:
            if not self.addon_path.exists():
                print(f"Info: Addon JSON file not found at {self.addon_path} (this is normal for first run)")
                return []
                
            with open(self.addon_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in addon file: {str(e)}")
            return []
        except Exception as e:
            print(f"Error loading addon data: {str(e)}")
            return []
    
    def _save_addon_data(self, data: List[Dict[str, Any]]) -> bool:
        """Save addon themes data"""
        try:
            with open(self.addon_path, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving addon data: {str(e)}")
            return False
    
    def _print_processing_summary(self, results: Dict[str, Any]):
        """Print a summary of processing results"""
        print("\n" + "="*50)
        print("PROCESSING SUMMARY")
        print("="*50)
        print(f"Processed: {results['processed']}")
        print(f"Skipped: {results['skipped']}")
        print(f"Errors: {results['errors']}")
        
        if results["error_details"]:
            print("\nError Details:")
            for error in results["error_details"]:
                print(f"  - {error}")
                
    def _menu_render_themes(self):
        """
        Loads theme data, renders ONLY themes with complete addon entries,
        and reports which themes were skipped.
        """
        print("\n" + "-" * 50)
        print("RENDER THEME PAGES (COMPLETE ENTRIES ONLY)")
        print("-" * 50)
        
        official_themes = self._load_official_data()
        addon_themes = self._load_addon_data()

        if not official_themes:
            print("❌ Official theme data ('community-css-themes.json') is missing or empty. Cannot render pages.")
            return

        # Create a lookup dictionary for quick access to addon data
        addon_lookup = {theme.get("repo"): theme for theme in addon_themes}
        
        unified_themes_to_render = []
        themes_skipped_for_missing_data = []

        print(f"Analyzing {len(official_themes)} official themes...")
        
        # Process each theme from the official list
        for official_theme in official_themes:
            repo = official_theme.get("repo")
            if not repo:
                print(f"⚠️  Skipping an official theme because it has no 'repo' identifier: {official_theme.get('name', 'Unnamed')}")
                continue

            addon_data = addon_lookup.get(repo)
            
            # If no corresponding addon entry exists, log it and skip rendering.
            if not addon_data:
                themes_skipped_for_missing_data.append(official_theme.get('name', repo))
                continue # This prevents incomplete themes from being rendered.

            # This code only runs if a corresponding addon entry was found.
            merged_theme_data = {
                "title": official_theme.get("name"),
                "repository_link": repo,
                "tags_list": addon_data.get("tags", []),
                "main_screenshot_url": addon_data.get("screenshot-main", official_theme.get("screenshot")),
                "additional_image_urls": addon_data.get("screenshots-side", [])
            }
            unified_themes_to_render.append(merged_theme_data)
    
        # Report on the themes that were skipped.
        if themes_skipped_for_missing_data:
            print("\n" + "!"*60)
            print(f"ℹ️  Skipped {len(themes_skipped_for_missing_data)} themes due to missing addon data.")
            for name in themes_skipped_for_missing_data[:5]: # Show first 5 examples
                print(f"    - {name}")
            if len(themes_skipped_for_missing_data) > 5:
                print(f"    ...and {len(themes_skipped_for_missing_data) - 5} more.")
            print("!"*60 + "\n")

        # Check if there are any themes left to render.
        if not unified_themes_to_render:
            print("❌ No themes with complete addon data were found to render.")
            return
            
        # The rendering process remains the same but now only uses the filtered list.
        try:
            print(f"✅ Found {len(unified_themes_to_render)} themes with complete data. Starting render...")
            renderer = ThemeRenderer()
            # This is the corrected line
            results = renderer.batch_render_themes(unified_themes_to_render)
            
            print("\n" + "-" * 20 + " RENDER COMPLETE " + "-" * 21)
            
            if results and isinstance(results, dict):
                print("📊 Rendering Summary:")
                print(json.dumps(results, indent=2))
            else:
                print("⚠️  The rendering process finished but did not return a valid summary dictionary.")
                print(f"   Received return value: {results}")

        except Exception as e:
            print("\n" + "❌" * 20 + " RENDER FAILED " + "❌" * 21)
            print(f"An unexpected error occurred during the page rendering process.")
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()


def main():
    """Main entry point for standalone execution"""
    print("Theme Batch Processor")
    print("=====================")
    
    # Initialize processor
    processor = BatchProcessor()
    
    # Run interactive menu
    processor.run_interactive_menu()


if __name__ == "__main__":
    main()