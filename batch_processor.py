#!/usr/bin/env python3
"""
Debloated Batch Processor Module with Multi-Peer Range Support
Streamlined version with only essential functionality + range-based collaboration
"""

import os
from typing import Dict, List, Optional, Any
from pathlib import Path
import json
import re
from datetime import datetime

# Import our modular components
try:
    from pythonThemeTools.file_manager import FileManager
    from pythonThemeTools.data_synchronizer import DataSynchronizer
    from pythonThemeTools.json_validator import JsonValidator
    from pythonThemeTools.github_utils import (
        open_github_repo, 
        validate_repo_format, 
        extract_repo_from_url
    )
    from pythonThemeTools.theme_renderer import ThemeRenderer
except ImportError as e:
    print(f"⚠️ Import error: {e}")
    print("Some features may not work properly.")
    # Create minimal fallbacks
    class FileManager:
        def __init__(self): pass
        def load_json_data(self, path, desc): return []
        def save_json_data(self, path, data, desc, **kwargs): return True
        def get_file_stats(self, files): return {}
    class DataSynchronizer:
        def __init__(self, *args): pass
        def find_missing_addon_entries(self): return []
    class JsonValidator:
        def __init__(self): pass
    class ThemeRenderer:
        def __init__(self): pass
        def batch_render_themes(self, themes): return {}
    def open_github_repo(repo): print(f"Would open: https://github.com/{repo}")
    def validate_repo_format(repo): return "/" in repo
    def extract_repo_from_url(url): 
        if "github.com" in url and "/" in url:
            parts = url.split("/")
            if len(parts) >= 5: return f"{parts[-2]}/{parts[-1]}"
        return None


class BatchProcessor:
    def __init__(self, 
                 official_json_path: str = "community-css-themes.json",
                 addon_json_path: str = "community-css-themes-tag-browser.json",
                 macros_path: Optional[str] = "tag_macros.json"):
        """
        Initialize the BatchProcessor with integrated file and GitHub operations
        
        Args:
            official_json_path: Path to official themes JSON
            addon_json_path: Path to addon themes JSON  
            macros_path: Path to tag macros JSON
        """
        # Core file operations
        self.file_manager = FileManager()
        self.official_path = official_json_path
        self.addon_path = addon_json_path
        
        # Data processing components
        self.synchronizer = DataSynchronizer(official_json_path, addon_json_path)
        
        # Load configuration
        self.tag_macros = self._load_tag_macros(macros_path)
        
        print(f"✅ BatchProcessor initialized")
        print(f"   Official JSON: {self.official_path}")
        print(f"   Addon JSON: {self.addon_path}")

    def _load_tag_macros(self, macros_path: Optional[str]) -> Dict[str, str]:
        """Load tag macros using FileManager"""
        default_macros = {
            "m": "minimalistic",
            "d": "dark", 
            "l": "light",
            "p": "productivity",
            "g": "gaming",
            "c": "colorful",
            "s": "simple",
            "md": "modern",
            "ret": "retro"
        }
        
        if not macros_path or not Path(macros_path).exists():
            print(f"ℹ️ Using default tag macros (no {macros_path} found)")
            return default_macros
            
        try:
            macros_data = self.file_manager.load_json_data(macros_path, "Tag macros")
            if isinstance(macros_data, dict):
                print(f"✅ Loaded {len(macros_data)} tag macros")
                return macros_data
            else:
                print("⚠️ Invalid macros format, using defaults")
                return default_macros
        except Exception as e:
            print(f"⚠️ Error loading macros: {e}, using defaults")
            return default_macros

    # ============================================================================
    # CORE DATA OPERATIONS
    # ============================================================================

    def load_official_data(self) -> List[Dict[str, Any]]:
        """Load official themes data"""
        return self.file_manager.load_json_data(self.official_path, "Official themes")

    def load_addon_data(self) -> List[Dict[str, Any]]:
        """Load addon themes data"""
        return self.file_manager.load_json_data(self.addon_path, "Addon themes")

    def save_addon_data(self, data: List[Dict[str, Any]]) -> bool:
        """Save addon themes data with backup"""
        return self.file_manager.save_json_data(self.addon_path, data, "Addon themes", create_backup=True)

    def load_both_datasets(self) -> tuple[List[Dict], List[Dict]]:
        """Load both official and addon data"""
        official_data = self.load_official_data()
        addon_data = self.load_addon_data()
        return official_data, addon_data

    def load_user_addon_data(self, author: str) -> List[Dict[str, Any]]:
        """Load user-specific addon data"""
        user_file = self._get_user_addon_filename(author)
        return self.file_manager.load_json_data(user_file, f"User addon themes ({author})")

    def save_user_addon_data(self, author: str, data: List[Dict[str, Any]]) -> bool:
        """Save user-specific addon data"""
        user_file = self._get_user_addon_filename(author)
        return self.file_manager.save_json_data(user_file, data, f"User addon themes ({author})", create_backup=True)

    def _get_user_addon_filename(self, author: str) -> str:
        """Generate user-specific addon filename"""
        # Sanitize author name for filename
        sanitized_author = re.sub(r'[^\w\-_]', '_', author.lower())
        base_name = Path(self.addon_path).stem  # Remove .json
        return f"{base_name}-{sanitized_author}.json"

    # ============================================================================
    # RANGE PARSING UTILITIES
    # ============================================================================

    def _parse_range_selection(self, range_input: str, all_entries: List[Dict]) -> List[Dict]:
        """
        Parse range input and return selected entries
        
        Examples:
        - "1-25" -> entries 0-24 (0-indexed)
        - "1,5,10-15" -> entries [0, 4, 9, 10, 11, 12, 13, 14]
        - "all" -> all entries
        - "50" -> just entry 49 (0-indexed)
        """
        if not range_input or range_input.lower() == 'all':
            return all_entries
        
        selected_indices = set()
        
        try:
            for part in range_input.split(','):
                part = part.strip()
                if '-' in part:
                    # Range like "1-25"
                    start_str, end_str = part.split('-', 1)
                    start = int(start_str.strip()) - 1  # Convert to 0-indexed
                    end = int(end_str.strip()) - 1      # Convert to 0-indexed
                    if start < 0:
                        start = 0
                    if end >= len(all_entries):
                        end = len(all_entries) - 1
                    selected_indices.update(range(start, end + 1))
                else:
                    # Single number like "5"
                    index = int(part) - 1  # Convert to 0-indexed
                    if 0 <= index < len(all_entries):
                        selected_indices.add(index)
            
            # Return selected entries
            return [all_entries[i] for i in sorted(selected_indices)]
            
        except (ValueError, IndexError) as e:
            print(f"⚠️ Invalid range format: {range_input}")
            print("   Examples: '1-25', '1,5,10-15', 'all', '50'")
            return []

    # ============================================================================
    # MAIN INTERACTIVE MENU SYSTEM
    # ============================================================================

    def run_interactive_menu(self):
        """Main interactive menu loop"""
        while True:
            self._display_main_menu()
            choice = input("\n➤ Enter your choice (1-7): ").strip()
            
            try:
                if choice == '1':
                    self._menu_process_missing_entries()
                elif choice == '2':
                    self._menu_process_missing_entries_range()
                elif choice == '3':
                    self._menu_synchronization_status()
                elif choice == '4':
                    self._menu_view_statistics()
                elif choice == '5':
                    self._menu_render_themes()
                elif choice == '6':
                    self._menu_configuration()
                elif choice == '7':
                    print("👋 Goodbye!")
                    break
                else:
                    print("❌ Invalid choice. Please select 1-7.")
                    
            except KeyboardInterrupt:
                print("\n\nℹ️ Operation cancelled by user.")
                continue
            except Exception as e:
                print(f"\n❌ Error: {str(e)}")
                print("Press Enter to continue...")
                input()
                continue
                
            if choice != '7':
                input("\n⏸️ Press Enter to continue...")

    def _display_main_menu(self):
        """Display the main menu"""
        print("\n" + "="*70)
        print("🎨 THEME BATCH PROCESSOR (MULTI-PEER)".center(70))
        print("="*70)
        
        menu_items = [
            ("1", "Process Missing Addon Entries (All/Interactive)", "🔥"),
            ("2", "Process Missing Addon Entries (Range/Multi-Peer)", "👥"),
            ("3", "Check Synchronization Status", "🔍"),
            ("4", "View Statistics & File Status", "📊"),
            ("5", "Render Theme Pages", "🎨"),
            ("6", "Configuration", "⚙️"),
            ("7", "Exit", "🚪")
        ]
        
        for num, title, emoji in menu_items:
            print(f"{emoji} {num:>2}. {title}")
        
        print("="*70)
        print(f"📁 Working directory: {os.getcwd()}")
        print(f"📄 Official JSON: {self.official_path}")
        print(f"🏷️  Addon JSON: {self.addon_path}")
        
        # Show existing user files
        user_files = self._find_user_addon_files()
        if user_files:
            print(f"👥 User files found: {', '.join(user_files)}")
        
        print("="*70)

    def _find_user_addon_files(self) -> List[str]:
        """Find existing user addon files"""
        base_name = Path(self.addon_path).stem
        pattern = f"{base_name}-*.json"
        
        user_files = []
        for file_path in Path(".").glob(pattern):
            if file_path.name != self.addon_path:  # Exclude main addon file
                user_files.append(file_path.name)
        
        return sorted(user_files)

    # ============================================================================
    # MENU IMPLEMENTATIONS
    # ============================================================================

    def _menu_process_missing_entries(self):
        """Process missing addon entries (Interactive mode only)"""
        print("\n" + "🔥 PROCESS MISSING ADDON ENTRIES (INTERACTIVE)".center(60, "="))
        
        results = self.process_missing_entries_interactive()
        self._print_processing_summary(results)

    def _menu_process_missing_entries_range(self):
        """Process missing addon entries with range selection (Multi-Peer mode)"""
        print("\n" + "👥 PROCESS MISSING ADDON ENTRIES (RANGE/MULTI-PEER)".center(60, "="))
        
        results = self.process_missing_entries_range()
        self._print_processing_summary(results)

    def _menu_synchronization_status(self):
        """Check synchronization status between official and addon data"""
        print("\n" + "🔍 SYNCHRONIZATION STATUS".center(60, "="))
        
        try:
            # Load both datasets
            official_data, addon_data = self.load_both_datasets()
            
            if not official_data:
                print("❌ No official data loaded - cannot check sync status")
                return
            
            # Create repo sets for comparison
            official_repos = {entry.get("repo") for entry in official_data if entry.get("repo")}
            addon_repos = {entry.get("repo") for entry in addon_data if entry.get("repo")}
            
            missing_in_addon = official_repos - addon_repos
            extra_in_addon = addon_repos - official_repos
            
            # Print summary
            print(f"📊 Synchronization Summary:")
            print(f"  Official themes: {len(official_repos)}")
            print(f"  Addon entries: {len(addon_repos)}")
            print(f"  Missing in addon: {len(missing_in_addon)}")
            print(f"  Extra in addon: {len(extra_in_addon)}")
            
            if len(official_repos) > 0:
                sync_percentage = (len(addon_repos) / len(official_repos)) * 100
                print(f"  Sync percentage: {sync_percentage:.1f}%")
            
            # Also check user files
            user_files = self._find_user_addon_files()
            if user_files:
                print(f"\n👥 User files status:")
                total_user_entries = 0
                for user_file in user_files:
                    user_data = self.file_manager.load_json_data(user_file, f"User file {user_file}")
                    user_repos = {entry.get("repo") for entry in user_data if entry.get("repo")}
                    total_user_entries += len(user_repos)
                    author = user_file.replace(Path(self.addon_path).stem + "-", "").replace(".json", "")
                    print(f"  {author}: {len(user_repos)} entries")
                
                print(f"  Total user entries: {total_user_entries}")
                if missing_in_addon:
                    remaining_work = len(missing_in_addon) - total_user_entries
                    print(f"  Remaining work: {max(0, remaining_work)} themes")
            
            # Show details if requested
            if missing_in_addon and len(missing_in_addon) <= 20:
                print(f"\n❌ Missing addon entries ({len(missing_in_addon)}):")
                for i, repo in enumerate(sorted(list(missing_in_addon)), 1):
                    # Find the theme name
                    theme_name = "Unknown"
                    for theme in official_data:
                        if theme.get("repo") == repo:
                            theme_name = theme.get("name", "Unknown")
                            break
                    print(f"  {i:2}. {theme_name} ({repo})")
            elif missing_in_addon:
                print(f"\n❌ {len(missing_in_addon)} missing entries (use range mode to process subsets)")
                    
        except Exception as e:
            print(f"❌ Error checking synchronization: {e}")

    def _menu_view_statistics(self):
        """View comprehensive statistics using FileManager"""
        print("\n" + "📊 STATISTICS & FILE STATUS".center(60, "="))
        
        # Use FileManager's file status report
        if hasattr(self.file_manager, 'print_file_status_report'):
            self.file_manager.print_file_status_report(self.official_path, self.addon_path)
        else:
            # Fallback to basic file stats
            stats = self.file_manager.get_file_stats([self.official_path, self.addon_path])
            for file_path, file_stats in stats.items():
                file_type = "Official" if "tag-browser" not in file_path else "Addon"
                print(f"\n📄 {file_type}: {file_path}")
                if file_stats.get("exists"):
                    print(f"  Size: {file_stats.get('size_mb', 0)} MB")
                    print(f"  Entries: {file_stats.get('entry_count', 0)}")
                    print(f"  Valid JSON: {'✅' if file_stats.get('valid_json') else '❌'}")
                else:
                    print("  ❌ File not found")
        
        # User files statistics
        user_files = self._find_user_addon_files()
        if user_files:
            print(f"\n👥 User Files ({len(user_files)} found):")
            total_user_entries = 0
            for user_file in user_files:
                try:
                    user_data = self.file_manager.load_json_data(user_file, f"User file")
                    author = user_file.replace(Path(self.addon_path).stem + "-", "").replace(".json", "")
                    entry_count = len(user_data) if user_data else 0
                    total_user_entries += entry_count
                    
                    # Get file size
                    file_size = Path(user_file).stat().st_size / 1024 / 1024 if Path(user_file).exists() else 0
                    
                    print(f"  📄 {author}: {entry_count} entries, {file_size:.2f} MB")
                except Exception as e:
                    print(f"  ❌ {user_file}: Error reading ({e})")
            
            print(f"  📊 Total user entries: {total_user_entries}")
        
        # Add tag statistics
        addon_data = self.load_addon_data()
        if addon_data:
            all_tags = []
            for entry in addon_data:
                all_tags.extend(entry.get("tags", []))
            
            if all_tags:
                unique_tags = set(all_tags)
                print(f"\n🏷️ Tag Statistics:")
                print(f"  Unique tags: {len(unique_tags)}")
                print(f"  Total tag usages: {len(all_tags)}")
                
                # Most common tags
                tag_counts = {}
                for tag in all_tags:
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1
                
                sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
                print("  Most common tags:")
                for tag, count in sorted_tags[:8]:
                    print(f"    {tag}: {count}")

    def _menu_render_themes(self):
        """Render theme pages using ThemeRenderer"""
        print("\n" + "🎨 RENDER THEME PAGES".center(60, "="))
        
        official_data, addon_data = self.load_both_datasets()
        
        if not official_data:
            print("❌ No official theme data found. Cannot render pages.")
            return
        
        # Create addon lookup
        addon_lookup = {theme.get("repo"): theme for theme in addon_data}
        
        # Find themes with complete data
        complete_themes = []
        incomplete_themes = []
        
        for official_theme in official_data:
            repo = official_theme.get("repo")
            if not repo:
                continue
                
            addon_theme = addon_lookup.get(repo)
            if addon_theme:
                # Merge data for renderer
                merged_theme = {
                    "title": official_theme.get("name"),
                    "repository_link": repo,
                    "tags_list": addon_theme.get("tags", []),
                    "main_screenshot_url": addon_theme.get("screenshot-main", official_theme.get("screenshot", "")),
                    "additional_image_urls": addon_theme.get("screenshots-side", [])
                }
                complete_themes.append(merged_theme)
            else:
                incomplete_themes.append(official_theme.get("name", repo))
        
        print(f"📊 Theme Analysis:")
        print(f"  Complete themes (with addon data): {len(complete_themes)}")
        print(f"  Incomplete themes (missing addon data): {len(incomplete_themes)}")
        
        if incomplete_themes:
            print(f"\n⚠️ Skipping {len(incomplete_themes)} themes without addon data:")
            for name in incomplete_themes[:5]:
                print(f"    • {name}")
            if len(incomplete_themes) > 5:
                print(f"    • ... and {len(incomplete_themes) - 5} more")
        
        if not complete_themes:
            print("❌ No themes with complete data to render.")
            return
        
        # Confirm rendering
        confirm = input(f"\n🚀 Render {len(complete_themes)} theme pages? (y/n): ").strip().lower()
        if confirm != 'y':
            print("❌ Rendering cancelled.")
            return
        
        try:
            print(f"🎨 Starting render process...")
            renderer = ThemeRenderer()
            results = renderer.batch_render_themes(complete_themes)
            
            print("\n✅ Rendering completed!")
            if isinstance(results, dict):
                for key, value in results.items():
                    print(f"  {key}: {value}")
            
        except Exception as e:
            print(f"❌ Rendering failed: {e}")

    def _menu_configuration(self):
        """Configuration options"""
        print("\n" + "⚙️ CONFIGURATION".center(60, "="))
        
        print("1. 🔧 Change file paths")
        print("2. 🏷️ View/edit tag macros")
        print("3. 📋 Show current settings")
        print("4. 🔄 Merge user files")
        
        choice = input("\n➤ Select option (1-4): ").strip()
        
        if choice == '1':
            self._configure_file_paths()
        elif choice == '2':
            self._configure_tag_macros()
        elif choice == '3':
            self._show_current_settings()
        elif choice == '4':
            self._merge_user_files()

    # ============================================================================
    # CONFIGURATION HELPERS
    # ============================================================================

    def _configure_file_paths(self):
        """Configure file paths"""
        print(f"\nCurrent paths:")
        print(f"  Official JSON: {self.official_path}")
        print(f"  Addon JSON: {self.addon_path}")
        
        new_official = input(f"\nNew official JSON path (Enter to keep current): ").strip()
        new_addon = input(f"New addon JSON path (Enter to keep current): ").strip()
        
        if new_official:
            self.official_path = new_official
        if new_addon:
            self.addon_path = new_addon
        
        if new_official or new_addon:
            # Reinitialize synchronizer with new paths
            self.synchronizer = DataSynchronizer(self.official_path, self.addon_path)
            print("✅ Paths updated and synchronizer reinitialized")

    def _configure_tag_macros(self):
        """Configure tag macros"""
        print(f"\nCurrent tag macros:")
        for macro, expansion in self.tag_macros.items():
            print(f"  {macro} → {expansion}")
        
        print(f"\nOptions:")
        print(f"1. Add new macro")
        print(f"2. Remove macro")
        
        choice = input("Select (1-2): ").strip()
        
        if choice == '1':
            macro = input("Macro shortcut: ").strip()
            expansion = input("Expansion: ").strip()
            if macro and expansion:
                self.tag_macros[macro] = expansion
                print(f"✅ Added: {macro} → {expansion}")
        elif choice == '2':
            macro = input("Macro to remove: ").strip()
            if macro in self.tag_macros:
                del self.tag_macros[macro]
                print(f"✅ Removed macro: {macro}")
            else:
                print(f"❌ Macro '{macro}' not found")

    def _show_current_settings(self):
        """Show current configuration"""
        print(f"\n📋 Current Configuration:")
        print(f"  Official JSON: {self.official_path}")
        print(f"  Addon JSON: {self.addon_path}")
        print(f"  Working directory: {os.getcwd()}")
        print(f"  Tag macros: {len(self.tag_macros)} defined")
        
        # Show file status
        official_exists = Path(self.official_path).exists()
        addon_exists = Path(self.addon_path).exists()
        print(f"\n📊 File Status:")
        print(f"  Official JSON: {'✅ Found' if official_exists else '❌ Not found'}")
        print(f"  Addon JSON: {'✅ Found' if addon_exists else '❌ Not found'}")
        
        # Show user files
        user_files = self._find_user_addon_files()
        if user_files:
            print(f"  User files: {len(user_files)} found")
            for user_file in user_files:
                author = user_file.replace(Path(self.addon_path).stem + "-", "").replace(".json", "")
                print(f"    • {author}: {user_file}")

    def _merge_user_files(self):
        """Merge all user files into main addon file"""
        print("\n🔄 MERGE USER FILES")
        print("="*40)
        
        user_files = self._find_user_addon_files()
        if not user_files:
            print("❌ No user files found to merge.")
            return
        
        print(f"📋 Found {len(user_files)} user files:")
        for user_file in user_files:
            author = user_file.replace(Path(self.addon_path).stem + "-", "").replace(".json", "")
            print(f"  • {author}: {user_file}")
        
        confirm = input(f"\n⚠️ Merge all user files into {self.addon_path}? (y/n): ").strip().lower()
        if confirm != 'y':
            print("❌ Merge cancelled.")
            return
        
        try:
            # Load main addon data
            main_addon_data = self.load_addon_data()
            main_repos = {entry.get("repo") for entry in main_addon_data if entry.get("repo")}
            
            merged_count = 0
            duplicate_count = 0
            error_count = 0
            
            # Process each user file
            for user_file in user_files:
                try:
                    user_data = self.file_manager.load_json_data(user_file, f"User file {user_file}")
                    author = user_file.replace(Path(self.addon_path).stem + "-", "").replace(".json", "")
                    
                    for entry in user_data:
                        repo = entry.get("repo")
                        if repo and repo not in main_repos:
                            # Add author attribution
                            entry["_author"] = author
                            entry["_merged_at"] = datetime.now().isoformat()
                            
                            main_addon_data.append(entry)
                            main_repos.add(repo)
                            merged_count += 1
                        elif repo:
                            duplicate_count += 1
                            
                except Exception as e:
                    print(f"❌ Error processing {user_file}: {e}")
                    error_count += 1
            
            # Save merged data
            if merged_count > 0:
                if self.save_addon_data(main_addon_data):
                    print(f"\n✅ Merge completed!")
                    print(f"  Merged entries: {merged_count}")
                    print(f"  Duplicates skipped: {duplicate_count}")
                    print(f"  Errors: {error_count}")
                    print(f"  Total entries: {len(main_addon_data)}")
                    
                    # Offer to backup user files
                    backup_choice = input(f"\n📦 Backup user files before deletion? (y/n): ").strip().lower()
                    if backup_choice == 'y':
                        backup_dir = Path("user_files_backup")
                        backup_dir.mkdir(exist_ok=True)
                        for user_file in user_files:
                            backup_path = backup_dir / user_file
                            Path(user_file).rename(backup_path)
                        print(f"✅ User files backed up to {backup_dir}/")
                    else:
                        # Just delete user files
                        for user_file in user_files:
                            Path(user_file).unlink(missing_ok=True)
                        print("🗑️ User files deleted.")
                else:
                    print("❌ Failed to save merged data.")
            else:
                print("ℹ️ No new entries to merge.")
                
        except Exception as e:
            print(f"❌ Merge failed: {e}")

    # ============================================================================
    # CORE PROCESSING LOGIC - ENHANCED WITH RANGE SUPPORT
    # ============================================================================

    def process_missing_entries_interactive(self) -> Dict[str, Any]:
        """Process missing addon entries with interactive mode (original method)"""
        print("🔥 Starting interactive processing of missing addon entries...")
        
        # Get missing entries using synchronizer
        try:
            missing_entries = self.synchronizer.find_missing_addon_entries()
        except Exception as e:
            print(f"❌ Error finding missing entries: {e}")
            return {"processed": 0, "skipped": 0, "errors": 1, "error_details": [str(e)]}
        
        if not missing_entries:
            print("✅ No missing addon entries found. Everything is in sync!")
            return {"processed": 0, "skipped": 0, "errors": 0}
        
        print(f"📊 Found {len(missing_entries)} missing addon entries.")
        
        results = {
            "processed": 0,
            "skipped": 0,
            "errors": 0,
            "created_entries": [],
            "error_details": []
        }
        
        # Load existing addon data
        addon_data = self.load_addon_data()
        
        for i, official_entry in enumerate(missing_entries, 1):
            repo = official_entry.get("repo", "unknown")
            name = official_entry.get("name", "Unknown")
            
            print(f"\n[{i}/{len(missing_entries)}] Processing: {name} ({repo})")
            
            try:
                addon_entry = self.interactive_entry_builder(official_entry)
                if addon_entry:
                    addon_data.append(addon_entry)
                    results["created_entries"].append(addon_entry)
                    results["processed"] += 1
                    print(f"✅ Created addon entry for {repo}")
                else:
                    results["skipped"] += 1
                    print(f"⭕ Skipped {repo}")
                    
            except Exception as e:
                results["errors"] += 1
                error_msg = f"Error processing {repo}: {str(e)}"
                results["error_details"].append(error_msg)
                print(f"❌ {error_msg}")
        
        # Save all changes at once using FileManager
        if results["processed"] > 0:
            print(f"\n💾 Saving {results['processed']} new entries...")
            if self.save_addon_data(addon_data):
                print(f"✅ Successfully saved {len(addon_data)} total addon entries")
            else:
                print(f"❌ Failed to save addon data")
                results["errors"] += 1
        
        return results

    def process_missing_entries_range(self) -> Dict[str, Any]:
        """Process missing addon entries with range selection and separate user files"""
        print("👥 Starting range-based processing for multi-peer collaboration...")
        
        # Get missing entries using synchronizer
        try:
            missing_entries = self.synchronizer.find_missing_addon_entries()
        except Exception as e:
            print(f"❌ Error finding missing entries: {e}")
            return {"processed": 0, "skipped": 0, "errors": 1, "error_details": [str(e)]}
        
        if not missing_entries:
            print("✅ No missing addon entries found. Everything is in sync!")
            return {"processed": 0, "skipped": 0, "errors": 0}
        
        print(f"📊 Found {len(missing_entries)} total missing addon entries.")
        
        # Show some examples of what needs to be processed
        print(f"\n📋 Sample missing themes:")
        for i, entry in enumerate(missing_entries[:5], 1):
            name = entry.get("name", "Unknown")
            repo = entry.get("repo", "unknown")
            print(f"  {i:2}. {name} ({repo})")
        if len(missing_entries) > 5:
            print(f"  ... and {len(missing_entries) - 5} more")
        
        # Get range selection
        print(f"\n🎯 Range Selection:")
        print(f"   Enter range to work on (1-{len(missing_entries)})")
        print(f"   Examples: '1-25', '26-50', '1,5,10-15', 'all'")
        range_input = input("➤ Range: ").strip()
        
        if not range_input:
            print("❌ No range specified. Cancelled.")
            return {"processed": 0, "skipped": 0, "errors": 0}
        
        # Parse range and get selected entries
        selected_entries = self._parse_range_selection(range_input, missing_entries)
        if not selected_entries:
            print("❌ Invalid range or no entries selected.")
            return {"processed": 0, "skipped": 0, "errors": 0}
        
        print(f"✅ Selected {len(selected_entries)} themes to process")
        
        # Get author name
        author = input("\n👤 Enter your author name: ").strip()
        if not author:
            print("❌ No author name provided. Cancelled.")
            return {"processed": 0, "skipped": 0, "errors": 0}
        
        # Sanitize author name
        sanitized_author = re.sub(r'[^\w\-_]', '_', author.lower())
        user_addon_file = self._get_user_addon_filename(sanitized_author)
        
        print(f"📄 Will save to: {user_addon_file}")
        
        # Check if user file already exists
        existing_user_data = []
        if Path(user_addon_file).exists():
            existing_user_data = self.load_user_addon_data(sanitized_author)
            print(f"📂 Found existing user file with {len(existing_user_data)} entries")
            
            resume_choice = input("Resume work in existing file? (y/n): ").strip().lower()
            if resume_choice != 'y':
                print("❌ Cancelled to avoid overwriting existing work.")
                return {"processed": 0, "skipped": 0, "errors": 0}
        
        # Confirm processing
        confirm = input(f"\n🚀 Process {len(selected_entries)} themes as '{author}'? (y/n): ").strip().lower()
        if confirm != 'y':
            print("❌ Processing cancelled.")
            return {"processed": 0, "skipped": 0, "errors": 0}
        
        # Process selected entries
        results = {
            "processed": 0,
            "skipped": 0,
            "errors": 0,
            "created_entries": [],
            "error_details": [],
            "author": author,
            "user_file": user_addon_file
        }
        
        # Use existing user data as starting point
        user_addon_data = existing_user_data.copy()
        existing_repos = {entry.get("repo") for entry in user_addon_data if entry.get("repo")}
        
        for i, official_entry in enumerate(selected_entries, 1):
            repo = official_entry.get("repo", "unknown")
            name = official_entry.get("name", "Unknown")
            
            # Skip if already processed by this user
            if repo in existing_repos:
                print(f"[{i}/{len(selected_entries)}] ⭕ Skipping {name} (already processed by {author})")
                results["skipped"] += 1
                continue
            
            print(f"\n[{i}/{len(selected_entries)}] Processing: {name} ({repo})")
            
            try:
                addon_entry = self.interactive_entry_builder(official_entry, author=author)
                if addon_entry:
                    # Add author attribution
                    addon_entry["_author"] = author
                    addon_entry["_created_at"] = datetime.now().isoformat()
                    
                    user_addon_data.append(addon_entry)
                    existing_repos.add(repo)
                    results["created_entries"].append(addon_entry)
                    results["processed"] += 1
                    
                    # Save incrementally after each entry
                    if self.save_user_addon_data(sanitized_author, user_addon_data):
                        print(f"✅ Saved entry for {repo}")
                    else:
                        print(f"⚠️ Warning: Failed to save entry for {repo}")
                else:
                    results["skipped"] += 1
                    print(f"⭕ Skipped {repo}")
                    
            except KeyboardInterrupt:
                print(f"\n\n⚠️ Processing interrupted by user after {results['processed']} entries.")
                print(f"💾 Your work has been saved to: {user_addon_file}")
                break
            except Exception as e:
                results["errors"] += 1
                error_msg = f"Error processing {repo}: {str(e)}"
                results["error_details"].append(error_msg)
                print(f"❌ {error_msg}")
        
        # Final save
        if results["processed"] > 0:
            print(f"\n💾 Final save of {len(user_addon_data)} total entries...")
            if self.save_user_addon_data(sanitized_author, user_addon_data):
                print(f"✅ Successfully saved user file: {user_addon_file}")
            else:
                print(f"❌ Failed to save user file")
                results["errors"] += 1
        
        return results

    def interactive_entry_builder(self, official_entry: Dict[str, Any], author: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Interactive UI for building addon entries with optional author context"""
        repo = official_entry.get("repo")
        name = official_entry.get("name")
        author_field = official_entry.get("author")
        official_screenshot = official_entry.get("screenshot", "")
        modes = official_entry.get("modes", [])
        
        author_context = f" as {author}" if author else ""
        print(f"\n🎨 Creating addon entry{author_context} for: {name} by {author_field}")
        print(f"🔗 Repository: {repo}")
        print(f"📸 Official screenshot: {official_screenshot}")
        print("-" * 50)

        # Calculate default tags FIRST
        default_tags = []
        if 'dark' in modes:
            default_tags.append('dark')
        if 'light' in modes:
            default_tags.append('light')
        if 'dark' in modes and 'light' in modes:
            default_tags.append('dark_and_light')
        
        # Show default tags to user
        print(f"\n📋 Default tags based on modes '{modes}': {', '.join(default_tags)}")
        print("   (You can override these with your own tags)")

        # Offer to open the GitHub page
        print(f"\n🌐 Opening GitHub repository...")
        open_github_repo(repo)
        
        # Build addon entry
        addon_entry = {
            "repo": repo,
            "screenshot-main": "",
            "screenshots-side": [],
            "tags": []
        }
        
        # Tags
        print("\n1. 🏷️ Tags (comma-separated, e.g. 'dark, minimal, productivity')")
        print("   You can use macros like 'm' for 'minimalistic'")
        print(f"   Current default tags: {', '.join(default_tags)}")
        print("   Type 'skip' to skip this theme, 'exit' to quit")
        tags_input = input("   Tags: ").strip()
        
        if tags_input.lower() == 'exit':
            return None
        if tags_input.lower() == 'skip':
            return None
            
        tags = []
        if tags_input:
            for part in tags_input.split(","):
                stripped = part.strip()
                if stripped:
                    expanded = self.tag_macros.get(stripped, stripped)
                    tags.append(expanded)
                    
        # Handle 'notm' special case
        if 'notm' not in tags:
            default_tags.append('minimalistic')
        
        if 'notm' in tags:
            tags.remove('notm')
            
        # Combine user tags with remaining defaults
        final_tags = sorted(set(tags + default_tags))
        addon_entry['tags'] = final_tags
        
        # Screenshot main
        print(f"\n2. 📸 Main screenshot (current: '{official_screenshot}')")
        print("   Options: [enter] to use official, or provide new URL/filename")
        main_screenshot = input("   Main screenshot: ").strip()
        if main_screenshot.lower() == 'exit':
            return None
        addon_entry["screenshot-main"] = main_screenshot if main_screenshot else official_screenshot
        
        # Additional screenshots
        print("\n3. 🖼️ Additional screenshots (URLs, one per line, empty line to finish)")
        screenshots_side = []
        while True:
            url = input("   Screenshot URL: ").strip()
            if url.lower() == 'exit':
                return None
            if not url:
                break
            screenshots_side.append(url)
        addon_entry["screenshots-side"] = screenshots_side
        
        # Show preview
        print("\n" + "="*50)
        print("📄 ADDON ENTRY PREVIEW:")
        print(json.dumps(addon_entry, indent=2))
        print("="*50)
        
        # Quick confirmation
        confirm = input("💾 Save this entry? (y/n): ").strip().lower()
        if confirm == 'y':
            return addon_entry
        else:
            print("❌ Entry discarded")
            return None

    def _print_processing_summary(self, results: Dict[str, Any]):
        """Print a summary of processing results"""
        print("\n" + "="*50)
        print("📋 PROCESSING SUMMARY")
        print("="*50)
        print(f"✅ Processed: {results['processed']}")
        print(f"⭕ Skipped: {results['skipped']}")
        print(f"❌ Errors: {results['errors']}")
        
        # Show author and file info for range processing
        if results.get("author"):
            print(f"👤 Author: {results['author']}")
        if results.get("user_file"):
            print(f"📄 Saved to: {results['user_file']}")
        
        if results.get("error_details"):
            print("\n🔍 Error Details:")
            for error in results["error_details"]:
                print(f"  • {error}")
        
        # Show some created entries
        if results.get("created_entries") and len(results["created_entries"]) > 0:
            print(f"\n📋 Sample created entries:")
            for i, entry in enumerate(results["created_entries"][:3], 1):
                repo = entry.get("repo", "unknown")
                tags = ", ".join(entry.get("tags", [])[:3])
                print(f"  {i}. {repo} → [{tags}]")
            if len(results["created_entries"]) > 3:
                remaining = len(results["created_entries"]) - 3
                print(f"  ... and {remaining} more")


def main():
    """Main entry point for standalone execution"""
    print("🎨 Theme Batch Processor (Multi-Peer Edition)")
    print("=" * 50)
    
    # Initialize processor
    processor = BatchProcessor()
    
    # Run interactive menu
    processor.run_interactive_menu()


if __name__ == "__main__":
    main()