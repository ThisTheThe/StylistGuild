#!/usr/bin/env python3
"""
Debloated Batch Processor Module
Streamlined version with only essential functionality
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

    # ============================================================================
    # MAIN INTERACTIVE MENU SYSTEM
    # ============================================================================

    def run_interactive_menu(self):
        """Main interactive menu loop"""
        while True:
            self._display_main_menu()
            choice = input("\n➤ Enter your choice (1-6): ").strip()
            
            try:
                if choice == '1':
                    self._menu_process_missing_entries()
                elif choice == '2':
                    self._menu_synchronization_status()
                elif choice == '3':
                    self._menu_view_statistics()
                elif choice == '4':
                    self._menu_render_themes()
                elif choice == '5':
                    self._menu_configuration()
                elif choice == '6':
                    print("👋 Goodbye!")
                    break
                else:
                    print("❌ Invalid choice. Please select 1-6.")
                    
            except KeyboardInterrupt:
                print("\n\nℹ️ Operation cancelled by user.")
                continue
            except Exception as e:
                print(f"\n❌ Error: {str(e)}")
                print("Press Enter to continue...")
                input()
                continue
                
            if choice != '6':
                input("\n⏸️ Press Enter to continue...")

    def _display_main_menu(self):
        """Display the main menu"""
        print("\n" + "="*70)
        print("🎨 THEME BATCH PROCESSOR (DEBLOATED)".center(70))
        print("="*70)
        
        menu_items = [
            ("1", "Process Missing Addon Entries (Interactive)", "🔄"),
            ("2", "Check Synchronization Status", "🔍"),
            ("3", "View Statistics & File Status", "📊"),
            ("4", "Render Theme Pages", "🎨"),
            ("5", "Configuration", "⚙️"),
            ("6", "Exit", "🚪")
        ]
        
        for num, title, emoji in menu_items:
            print(f"{emoji} {num:>2}. {title}")
        
        print("="*70)
        print(f"📁 Working directory: {os.getcwd()}")
        print(f"📄 Official JSON: {self.official_path}")
        print(f"🏷️  Addon JSON: {self.addon_path}")
        print("="*70)

    # ============================================================================
    # MENU IMPLEMENTATIONS
    # ============================================================================

    def _menu_process_missing_entries(self):
        """Process missing addon entries (Interactive mode only)"""
        print("\n" + "🔄 PROCESS MISSING ADDON ENTRIES (INTERACTIVE)".center(60, "="))
        
        results = self.process_missing_entries_interactive()
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
        
        choice = input("\n➤ Select option (1-3): ").strip()
        
        if choice == '1':
            self._configure_file_paths()
        elif choice == '2':
            self._configure_tag_macros()
        elif choice == '3':
            self._show_current_settings()

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

    # ============================================================================
    # CORE PROCESSING LOGIC
    # ============================================================================

    def process_missing_entries_interactive(self) -> Dict[str, Any]:
        """Process missing addon entries with interactive mode"""
        print("🔄 Starting interactive processing of missing addon entries...")
        
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

    def interactive_entry_builder(self, official_entry: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Interactive UI for building addon entries"""
        repo = official_entry.get("repo")
        name = official_entry.get("name")
        author = official_entry.get("author")
        official_screenshot = official_entry.get("screenshot", "")
        modes = official_entry.get("modes", [])
        
        print(f"\n🎨 Creating addon entry for: {name} by {author}")
        print(f"📁 Repository: {repo}")
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

        # Save the addon JSON immediately after creating each entry
        addon_data = self.load_addon_data()
        addon_data.append(addon_entry)
        if self.save_addon_data(addon_data):
            print(f"✅ Successfully saved addon entry for {repo}")
            return addon_entry
        else:
            print(f"❌ Failed to save addon data for {repo}")
            return None

        

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
    print("🎨 Theme Batch Processor (Debloated)")
    print("=" * 40)
    
    # Initialize processor
    processor = BatchProcessor()
    
    # Run interactive menu
    processor.run_interactive_menu()


if __name__ == "__main__":
    main()