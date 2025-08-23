#!/usr/bin/env python3
"""
Integrated Batch Processor Module
Streamlined orchestrator using FileManager and GitHub utilities
"""

import os
from typing import Dict, List, Optional, Any
from pathlib import Path
import json

# Import our modular components
try:
    from pythonThemeTools.file_manager import FileManager
    from pythonThemeTools.data_synchronizer import DataSynchronizer
    from pythonThemeTools.json_validator import JsonValidator
    from pythonThemeTools.github_utils import (
        open_github_repo, 
        validate_repo_format, 
        extract_repo_from_url,
        get_repo_info
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
    def get_repo_info(repo): return {"error": "GitHub API not available"}


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
        self.validator = JsonValidator()
        
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
    # CORE DATA OPERATIONS (Using FileManager)
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

    # ============================================================================
    # MAIN INTERACTIVE MENU SYSTEM
    # ============================================================================

    def run_interactive_menu(self):
        """Main interactive menu loop"""
        while True:
            self._display_main_menu()
            choice = input("\n➤ Enter your choice (1-12): ").strip()
            
            try:
                if choice == '1':
                    self._menu_process_missing_entries()
                elif choice == '2':
                    self._menu_validate_json_files()
                elif choice == '3':
                    self._menu_synchronization_status()
                elif choice == '4':
                    self._menu_create_single_entry()
                elif choice == '5':
                    self._menu_view_statistics()
                elif choice == '6':
                    self._menu_backup_operations()
                elif choice == '7':
                    self._menu_file_operations()
                elif choice == '8':
                    self._menu_export_data()
                elif choice == '9':
                    self._menu_github_operations()
                elif choice == '10':
                    self._menu_render_themes()
                elif choice == '11':
                    self._menu_configuration()
                elif choice == '12':
                    print("👋 Goodbye!")
                    break
                else:
                    print("❌ Invalid choice. Please select 1-12.")
                    
            except KeyboardInterrupt:
                print("\n\nℹ️ Operation cancelled by user.")
                continue
            except Exception as e:
                print(f"\n❌ Error: {str(e)}")
                print("Press Enter to continue...")
                input()
                continue
                
            if choice != '12':
                input("\n⏸️ Press Enter to continue...")

    def _display_main_menu(self):
        """Display the main menu"""
        print("\n" + "="*70)
        print("🎨 THEME BATCH PROCESSOR".center(70))
        print("="*70)
        
        menu_items = [
            ("1", "Process Missing Addon Entries", "🔄"),
            ("2", "Validate JSON Files", "✅"),
            ("3", "Check Synchronization Status", "🔍"),
            ("4", "Create Single Addon Entry", "➕"),
            ("5", "View Statistics & File Status", "📊"),
            ("6", "Backup Operations", "💾"),
            ("7", "File Operations", "📁"),
            ("8", "Export Data", "📤"),
            ("9", "GitHub Operations", "🙎"),
            ("10", "Render Theme Pages", "🎨"),
            ("11", "Configuration", "⚙️"),
            ("12", "Exit", "🚪")
        ]
        
        for num, title, emoji in menu_items:
            print(f"{emoji} {num:>2}. {title}")
        
        print("="*70)
        print(f"📍 Working directory: {os.getcwd()}")
        print(f"📄 Official JSON: {self.official_path}")
        print(f"🏷️  Addon JSON: {self.addon_path}")
        print("="*70)

    # ============================================================================
    # MENU IMPLEMENTATIONS
    # ============================================================================

    def _menu_process_missing_entries(self):
        """Process missing addon entries"""
        print("\n" + "🔄 PROCESS MISSING ADDON ENTRIES".center(60, "="))
        
        print("Choose processing mode:")
        print("1. 🎯 Interactive mode (prompt for each entry)")
        print("2. ⚡ Automatic mode (create minimal entries)")
        print("3. 👀 Review mode (show missing entries only)")
        
        mode = input("\n➤ Select mode (1-3): ").strip()
        
        if mode == '1':
            results = self.process_missing_entries(interactive=True)
        elif mode == '2':
            results = self.process_missing_entries(interactive=False)
        elif mode == '3':
            self._review_missing_entries()
            return
        else:
            print("❌ Invalid selection.")
            return
        
        self._print_processing_summary(results)

    def _menu_validate_json_files(self):
        """Validate JSON files using FileManager"""
        print("\n" + "✅ VALIDATE JSON FILES".center(60, "="))
        
        # Validate syntax first using FileManager
        files_to_check = [
            (self.official_path, "Official themes", ["name", "author", "repo", "screenshot"]),
            (self.addon_path, "Addon themes", ["repo", "screenshot-main", "tags"])
        ]
        
        for file_path, description, required_keys in files_to_check:
            print(f"\n🔍 Validating {description}...")
            
            # Check file existence and syntax
            is_valid, error_msg = self.file_manager.validate_json_syntax(file_path)
            if not is_valid:
                print(f"  ❌ {error_msg}")
                continue
            
            # Check structure if FileManager supports it
            if hasattr(self.file_manager, 'validate_json_structure'):
                results = self.file_manager.validate_json_structure(file_path, required_keys, description)
                if results["valid"]:
                    print(f"  ✅ Schema valid - {results['valid_entries']}/{results['entries']} entries")
                else:
                    print(f"  ❌ Schema issues - {results['valid_entries']}/{results['entries']} valid")
                    for error in results["errors"][:3]:
                        print(f"    • {error}")
                    if len(results["errors"]) > 3:
                        print(f"    • ... and {len(results['errors']) - 3} more issues")
            else:
                # Fall back to basic validation
                data = self.file_manager.load_json_data(file_path, description)
                print(f"  ✅ JSON syntax valid - {len(data)} entries loaded")

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
            
            # Show details if requested
            if missing_in_addon:
                print(f"\n❌ Missing addon entries ({len(missing_in_addon)}):")
                for i, repo in enumerate(sorted(list(missing_in_addon))[:10], 1):
                    # Find the theme name
                    theme_name = "Unknown"
                    for theme in official_data:
                        if theme.get("repo") == repo:
                            theme_name = theme.get("name", "Unknown")
                            break
                    print(f"  {i:2}. {theme_name} ({repo})")
                if len(missing_in_addon) > 10:
                    print(f"  ... and {len(missing_in_addon) - 10} more")
            
            if extra_in_addon:
                print(f"\n⚠️ Extra addon entries (not in official): {len(extra_in_addon)}")
                for repo in sorted(list(extra_in_addon))[:5]:
                    print(f"  • {repo}")
                if len(extra_in_addon) > 5:
                    print(f"  ... and {len(extra_in_addon) - 5} more")
                    
        except Exception as e:
            print(f"❌ Error checking synchronization: {e}")

    def _menu_create_single_entry(self):
        """Create a single addon entry interactively"""
        print("\n" + "➕ CREATE SINGLE ADDON ENTRY".center(60, "="))
        
        # Get repository information
        while True:
            repo_input = input("📍 Repository (owner/repo-name or GitHub URL): ").strip()
            if not repo_input:
                print("❌ Repository is required.")
                return
            
            # Try to extract repo from URL if it's a URL
            if "github.com" in repo_input:
                repo = extract_repo_from_url(repo_input)
                if not repo:
                    print("❌ Could not extract repository from URL")
                    continue
                print(f"📍 Extracted repository: {repo}")
            else:
                repo = repo_input
            
            if validate_repo_format(repo):
                break
            else:
                print("❌ Invalid repository format. Expected: owner/repo-name")
        
        # Open GitHub page
        print(f"\n🌐 Opening GitHub repository...")
        open_github_repo(repo)
        
        # Get additional info
        name = input("\n📍 Theme name (optional): ").strip()
        author = input("👤 Author (optional): ").strip()
        modes_input = input("🎨 Supported modes (e.g., 'dark, light'): ").strip()
        modes = [m.strip() for m in modes_input.split(',') if m.strip()] if modes_input else []
        
        # Create mock official entry for the interactive builder
        official_entry = {
            "repo": repo,
            "name": name or "Custom Theme",
            "author": author or "Unknown Author",
            "screenshot": "",
            "modes": modes
        }
        
        # Use interactive builder
        addon_entry = self.interactive_entry_builder(official_entry)
        
        if addon_entry:
            # Load current addon data and add new entry
            addon_data = self.load_addon_data()
            
            # Check if repo already exists
            existing_repos = {entry.get("repo") for entry in addon_data}
            if repo in existing_repos:
                overwrite = input(f"⚠️ Entry for {repo} already exists. Overwrite? (y/n): ").strip().lower()
                if overwrite != 'y':
                    print("❌ Operation cancelled.")
                    return
                # Remove existing entry
                addon_data = [entry for entry in addon_data if entry.get("repo") != repo]
            
            addon_data.append(addon_entry)
            
            if self.save_addon_data(addon_data):
                print("✅ Addon entry created and saved!")
            else:
                print("❌ Failed to save addon entry.")
        else:
            print("❌ Entry creation cancelled.")

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

    def _menu_backup_operations(self):
        """Backup operations using FileManager"""
        print("\n" + "💾 BACKUP OPERATIONS".center(60, "="))
        
        print("1. 📦 Create backups of current files")
        print("2. 📋 List available backups")
        print("3. 📄 Restore from backup")
        print("4. 🧹 Cleanup old backups")
        
        choice = input("\n➤ Select option (1-4): ").strip()
        
        if choice == '1':
            suffix = input("📍 Backup suffix (optional): ").strip()
            files_to_backup = [self.official_path, self.addon_path]
            results = self.file_manager.backup_json_files(files_to_backup, suffix or None)
            
            success_count = sum(results.values())
            print(f"✅ Created {success_count}/{len(files_to_backup)} backups")
            
        elif choice == '2':
            self.file_manager.print_backup_report()
            
        elif choice == '3':
            self._restore_from_backup_menu()
            
        elif choice == '4':
            days_input = input("🗓️ Keep backups newer than (days, default 30): ").strip()
            days = int(days_input) if days_input.isdigit() else 30
            results = self.file_manager.cleanup_old_backups(days)
            print(f"🧹 Cleaned up {results['removed']} old backup files")

    def _menu_file_operations(self):
        """File operations menu"""
        print("\n" + "📁 FILE OPERATIONS".center(60, "="))
        
        print("1. 📄 Compare file sizes")
        print("2. 🔍 Search themes by keyword")
        print("3. 📊 Analyze file structure")
        print("4. 🧹 Clean duplicate entries")
        print("5. 📝 Generate file report")
        
        choice = input("\n➤ Select option (1-5): ").strip()
        
        if choice == '1':
            self._compare_file_sizes()
        elif choice == '2':
            self._search_themes()
        elif choice == '3':
            self._analyze_file_structure()
        elif choice == '4':
            self._clean_duplicates()
        elif choice == '5':
            self._generate_file_report()

    def _menu_github_operations(self):
        """GitHub-related operations"""
        print("\n" + "🙎 GITHUB OPERATIONS".center(60, "="))
        
        print("1. 🌐 Open repository in browser")
        print("2. 📊 Get repository information")
        print("3. ✅ Validate repository format")
        print("4. 🔗 Extract repository from URL")
        
        choice = input("\n➤ Select option (1-4): ").strip()
        
        if choice == '1':
            repo = input("📍 Repository (owner/repo): ").strip()
            if repo:
                open_github_repo(repo)
                
        elif choice == '2':
            repo = input("📍 Repository (owner/repo): ").strip()
            if repo and validate_repo_format(repo):
                print("📍 Fetching repository information...")
                info = get_repo_info(repo)
                if "error" in info:
                    print(f"❌ {info['error']}")
                else:
                    print(f"✅ Repository: {info.get('full_name')}")
                    print(f"📍 Description: {info.get('description', 'No description')}")
                    print(f"⭐ Stars: {info.get('stargazers_count', 0)}")
                    print(f"🍴 Forks: {info.get('forks_count', 0)}")
                    print(f"💻 Language: {info.get('language', 'Unknown')}")
                    if info.get('topics'):
                        print(f"🏷️ Topics: {', '.join(info['topics'])}")
                        
        elif choice == '3':
            repo = input("📍 Repository to validate: ").strip()
            if validate_repo_format(repo):
                print(f"✅ '{repo}' is valid repository format")
            else:
                print(f"❌ '{repo}' is not valid repository format")
                
        elif choice == '4':
            url = input("🔗 GitHub URL: ").strip()
            repo = extract_repo_from_url(url)
            if repo:
                print(f"✅ Extracted repository: {repo}")
            else:
                print("❌ Could not extract repository from URL")

    def _menu_export_data(self):
        """Export data menu"""
        print("\n" + "📤 EXPORT DATA".center(60, "="))
        
        print("1. 📊 Export statistics to text file")
        print("2. 🎯 Export missing entries to JSON")
        print("3. 📄 Export complete addon data")
        print("4. 🔗 Export theme URLs list")
        print("5. 🏷️ Export tag analysis")
        
        choice = input("\n➤ Select option (1-5): ").strip()
        
        if choice == '1':
            self._export_statistics()
        elif choice == '2':
            self._export_missing_entries()
        elif choice == '3':
            self._export_complete_addon_data()
        elif choice == '4':
            self._export_theme_urls()
        elif choice == '5':
            self._export_tag_analysis()

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
        
        print("1. 📧 Change file paths")
        print("2. 🏷️ View/edit tag macros")
        print("3. 📍 Show current settings")
        
        choice = input("\n➤ Select option (1-3): ").strip()
        
        if choice == '1':
            self._configure_file_paths()
        elif choice == '2':
            self._configure_tag_macros()
        elif choice == '3':
            self._show_current_settings()

    # ============================================================================
    # HELPER METHODS FOR MENU IMPLEMENTATIONS
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

    def _compare_file_sizes(self):
        """Compare file sizes between official and addon data"""
        official_size = Path(self.official_path).stat().st_size if Path(self.official_path).exists() else 0
        addon_size = Path(self.addon_path).stat().st_size if Path(self.addon_path).exists() else 0
        
        print(f"\n📊 File Size Comparison:")
        print(f"  Official JSON: {official_size:,} bytes ({official_size/1024:.1f} KB)")
        print(f"  Addon JSON: {addon_size:,} bytes ({addon_size/1024:.1f} KB)")
        
        if official_size > 0 and addon_size > 0:
            ratio = addon_size / official_size
            print(f"  Size ratio (addon/official): {ratio:.2f}")

    def _search_themes(self):
        """Search themes by keyword"""
        keyword = input("🔍 Search keyword: ").strip().lower()
        if not keyword:
            return
        
        official_data, addon_data = self.load_both_datasets()
        found_themes = []
        
        for theme in official_data:
            if (keyword in theme.get("name", "").lower() or 
                keyword in theme.get("author", "").lower() or
                keyword in theme.get("repo", "").lower()):
                found_themes.append(theme)
        
        print(f"\n🎯 Found {len(found_themes)} themes matching '{keyword}':")
        for i, theme in enumerate(found_themes[:10], 1):
            print(f"  {i}. {theme.get('name')} by {theme.get('author')} ({theme.get('repo')})")
        
        if len(found_themes) > 10:
            print(f"  ... and {len(found_themes) - 10} more")

    def _analyze_file_structure(self):
        """Analyze file structure"""
        print("\n📊 File Structure Analysis:")
        
        official_data, addon_data = self.load_both_datasets()
        
        # Analyze official data structure
        if official_data:
            official_keys = set()
            for theme in official_data:
                official_keys.update(theme.keys())
            print(f"  Official data keys: {sorted(official_keys)}")
        
        # Analyze addon data structure
        if addon_data:
            addon_keys = set()
            for theme in addon_data:
                addon_keys.update(theme.keys())
            print(f"  Addon data keys: {sorted(addon_keys)}")

    def _clean_duplicates(self):
        """Clean duplicate entries"""
        print("\n🧹 Cleaning Duplicate Entries:")
        
        addon_data = self.load_addon_data()
        original_count = len(addon_data)
        
        # Remove duplicates based on repo
        seen_repos = set()
        cleaned_data = []
        
        for entry in addon_data:
            repo = entry.get("repo")
            if repo and repo not in seen_repos:
                seen_repos.add(repo)
                cleaned_data.append(entry)
        
        removed_count = original_count - len(cleaned_data)
        print(f"  Removed {removed_count} duplicate entries")
        
        if removed_count > 0:
            confirm = input("Save cleaned data? (y/n): ").strip().lower()
            if confirm == 'y':
                if self.save_addon_data(cleaned_data):
                    print("✅ Cleaned data saved!")
                else:
                    print("❌ Failed to save cleaned data")

    def _generate_file_report(self):
        """Generate comprehensive file report"""
        filename = input("📝 Report filename (default: file_report.txt): ").strip()
        if not filename:
            filename = "file_report.txt"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("Theme Batch Processor File Report\n")
                f.write("=" * 50 + "\n\n")
                
                official_data, addon_data = self.load_both_datasets()
                
                f.write(f"Generated: {Path().cwd()}\n")
                f.write(f"Official JSON: {self.official_path}\n")
                f.write(f"Addon JSON: {self.addon_path}\n\n")
                
                f.write(f"Statistics:\n")
                f.write(f"  Official themes: {len(official_data)}\n")
                f.write(f"  Addon themes: {len(addon_data)}\n")
                
                # Add more report details
                if addon_data:
                    all_tags = []
                    for entry in addon_data:
                        all_tags.extend(entry.get("tags", []))
                    
                    f.write(f"  Total tags: {len(all_tags)}\n")
                    f.write(f"  Unique tags: {len(set(all_tags))}\n")
            
            print(f"✅ Report saved to {filename}")
            
        except Exception as e:
            print(f"❌ Failed to generate report: {e}")

    def _export_statistics(self):
        """Export statistics to text file"""
        filename = input("📊 Statistics filename (default: theme_statistics.txt): ").strip()
        if not filename:
            filename = "theme_statistics.txt"
        
        try:
            official_data, addon_data = self.load_both_datasets()
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("Theme Statistics Report\n")
                f.write("=" * 40 + "\n\n")
                f.write(f"Official themes: {len(official_data)}\n")
                f.write(f"Addon themes: {len(addon_data)}\n")
                
                # Add tag statistics
                if addon_data:
                    all_tags = []
                    for entry in addon_data:
                        all_tags.extend(entry.get("tags", []))
                    
                    tag_counts = {}
                    for tag in all_tags:
                        tag_counts[tag] = tag_counts.get(tag, 0) + 1
                    
                    f.write(f"\nTag Usage:\n")
                    for tag, count in sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:20]:
                        f.write(f"  {tag}: {count}\n")
            
            print(f"✅ Statistics exported to {filename}")
            
        except Exception as e:
            print(f"❌ Export failed: {e}")

    def _export_missing_entries(self):
        """Export missing entries to JSON"""
        try:
            missing_entries = self.synchronizer.find_missing_addon_entries()
            filename = input("🎯 Missing entries filename (default: missing_entries.json): ").strip()
            if not filename:
                filename = "missing_entries.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(missing_entries, f, indent=2)
            
            print(f"✅ Exported {len(missing_entries)} missing entries to {filename}")
            
        except Exception as e:
            print(f"❌ Export failed: {e}")

    def _export_complete_addon_data(self):
        """Export complete addon data"""
        try:
            addon_data = self.load_addon_data()
            filename = input("📄 Addon data filename (default: complete_addon_data.json): ").strip()
            if not filename:
                filename = "complete_addon_data.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(addon_data, f, indent=2)
            
            print(f"✅ Exported {len(addon_data)} addon entries to {filename}")
            
        except Exception as e:
            print(f"❌ Export failed: {e}")

    def _export_theme_urls(self):
        """Export theme URLs list"""
        try:
            official_data = self.load_official_data()
            filename = input("🔗 URLs filename (default: theme_urls.txt): ").strip()
            if not filename:
                filename = "theme_urls.txt"
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("Theme Repository URLs\n")
                f.write("=" * 30 + "\n\n")
                
                for theme in official_data:
                    repo = theme.get("repo")
                    name = theme.get("name", "Unknown")
                    if repo:
                        f.write(f"{name}: https://github.com/{repo}\n")
            
            print(f"✅ Exported {len(official_data)} URLs to {filename}")
            
        except Exception as e:
            print(f"❌ Export failed: {e}")

    def _export_tag_analysis(self):
        """Export tag analysis"""
        try:
            addon_data = self.load_addon_data()
            filename = input("🏷️ Tag analysis filename (default: tag_analysis.txt): ").strip()
            if not filename:
                filename = "tag_analysis.txt"
            
            # Analyze tags
            all_tags = []
            theme_tag_counts = []
            
            for entry in addon_data:
                tags = entry.get("tags", [])
                all_tags.extend(tags)
                theme_tag_counts.append(len(tags))
            
            tag_counts = {}
            for tag in all_tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("Tag Analysis Report\n")
                f.write("=" * 30 + "\n\n")
                f.write(f"Total themes: {len(addon_data)}\n")
                f.write(f"Total tag usages: {len(all_tags)}\n")
                f.write(f"Unique tags: {len(set(all_tags))}\n")
                
                if theme_tag_counts:
                    avg_tags = sum(theme_tag_counts) / len(theme_tag_counts)
                    f.write(f"Average tags per theme: {avg_tags:.1f}\n")
                
                f.write(f"\nMost Popular Tags:\n")
                for tag, count in sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:30]:
                    f.write(f"  {tag}: {count} themes\n")
            
            print(f"✅ Tag analysis exported to {filename}")
            
        except Exception as e:
            print(f"❌ Export failed: {e}")

    def _restore_from_backup_menu(self):
        """Menu for restoring from backup"""
        print("\n📄 Restore from Backup:")
        
        if hasattr(self.file_manager, 'list_backups'):
            backups = self.file_manager.list_backups()
            if not backups:
                print("❌ No backups found")
                return
            
            print("Available backups:")
            for i, backup in enumerate(backups[:10], 1):
                print(f"  {i}. {backup}")
            
            choice = input("Select backup number: ").strip()
            if choice.isdigit() and 1 <= int(choice) <= len(backups):
                backup_file = backups[int(choice) - 1]
                confirm = input(f"Restore from {backup_file}? (y/n): ").strip().lower()
                if confirm == 'y':
                    if self.file_manager.restore_backup(backup_file):
                        print("✅ Backup restored successfully")
                    else:
                        print("❌ Failed to restore backup")
        else:
            print("❌ Backup restoration not available")

    def _review_missing_entries(self):
        """Review missing entries without processing"""
        try:
            missing_entries = self.synchronizer.find_missing_addon_entries()
            
            if not missing_entries:
                print("✅ No missing addon entries found!")
                return
            
            print(f"\n👀 Found {len(missing_entries)} missing addon entries:")
            print("-" * 60)
            
            for i, entry in enumerate(missing_entries[:20], 1):
                name = entry.get("name", "Unknown")
                repo = entry.get("repo", "unknown")
                author = entry.get("author", "Unknown")
                
                print(f"{i:3}. {name}")
                print(f"     Repository: {repo}")
                print(f"     Author: {author}")
                print()
            
            if len(missing_entries) > 20:
                print(f"... and {len(missing_entries) - 20} more entries")
                
        except Exception as e:
            print(f"❌ Error reviewing missing entries: {e}")

    # ============================================================================
    # CORE PROCESSING LOGIC
    # ============================================================================

    def process_missing_entries(self, interactive: bool = True) -> Dict[str, Any]:
        """Process missing addon entries with integrated file operations"""
        print("🔄 Starting batch processing of missing addon entries...")
        
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
        original_count = len(addon_data)
        
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
                        print(f"✅ Created addon entry for {repo}")
                    else:
                        results["skipped"] += 1
                        print(f"⭕ Skipped {repo}")
                else:
                    # Auto mode: create minimal entries
                    addon_entry = self._create_minimal_addon_entry(official_entry)
                    addon_data.append(addon_entry)
                    results["created_entries"].append(addon_entry)
                    results["processed"] += 1
                    print(f"✅ Created minimal addon entry for {repo}")
                    
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
        
        self._print_processing_summary(results)
        return results

    def interactive_entry_builder(self, official_entry: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Interactive UI for building addon entries"""
        repo = official_entry.get("repo")
        name = official_entry.get("name")
        author = official_entry.get("author")
        official_screenshot = official_entry.get("screenshot", "")
        modes = official_entry.get("modes", [])
        
        print(f"\n🎨 Creating addon entry for: {name} by {author}")
        print(f"📍 Repository: {repo}")
        print(f"📸 Official screenshot: {official_screenshot}")
        print("-" * 50)

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
        
        # Screenshot main
        print(f"\n1. 📸 Main screenshot (current: '{official_screenshot}')")
        print("   Options: [enter] to use official, or provide new URL/filename")
        main_screenshot = input("   Main screenshot: ").strip()
        if main_screenshot.lower() == 'exit':
            return None
        addon_entry["screenshot-main"] = main_screenshot if main_screenshot else official_screenshot
        
        # Additional screenshots
        print("\n2. 🖼️ Additional screenshots (URLs, one per line, empty line to finish)")
        screenshots_side = []
        while True:
            url = input("   Screenshot URL: ").strip()
            if url.lower() == 'exit':
                return None
            if not url:
                break
            screenshots_side.append(url)
        addon_entry["screenshots-side"] = screenshots_side
        
        # Tags
        print("\n3. 🏷️ Tags (comma-separated, e.g. 'dark, minimal, productivity')")
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
        
        # Auto-assign dark/light/dark_and_light based on modes
        default_tags = []
        if 'dark' in modes:
            default_tags.append('dark')
        if 'light' in modes:
            default_tags.append('light')
        if 'dark' in modes and 'light' in modes:
            default_tags.append('dark_and_light')
            
        # Add minimalistic unless 'notm' specified
        if 'notm' not in tags:
            default_tags.append('minimalistic')
        
        addon_entry['tags'] = sorted(set(tags + default_tags))
        
        # Show preview
        print("\n" + "="*50)
        print("🔍 ADDON ENTRY PREVIEW:")
        print(json.dumps(addon_entry, indent=2))
        print("="*50)
        
        confirm = input("\n✅ Save this entry? (y/n): ").strip().lower()
        return addon_entry if confirm == 'y' else None

    def _create_minimal_addon_entry(self, official_entry: Dict[str, Any]) -> Dict[str, Any]:
        """Create a minimal addon entry from official entry, with auto dark/light tags"""
        modes = official_entry.get('modes', []) or []
        auto_tags = ['minimalistic']  # Default tag
        
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
            "tags": sorted(auto_tags)
        }

    def _print_processing_summary(self, results: Dict[str, Any]):
        """Print a summary of processing results"""
        print("\n" + "="*50)
        print("📋 PROCESSING SUMMARY")
        print("="*50)
        print(f"✅ Processed: {results['processed']}")
        print(f"⭕ Skipped: {results['skipped']}")
        print(f"❌ Errors: {results['errors']}")
        
        if results.get("error_details"):
            print("\n🔍 Error Details:")
            for error in results["error_details"]:
                print(f"  • {error}")


def main():
    """Main entry point for standalone execution"""
    print("🎨 Theme Batch Processor")
    print("=" * 30)
    
    # Initialize processor
    processor = BatchProcessor()
    
    # Run interactive menu
    processor.run_interactive_menu()


if __name__ == "__main__":
    main()