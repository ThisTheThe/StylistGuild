#!/usr/bin/env python3
"""
Standalone Theme Renderer
Separated rendering functionality that can be run independently from the batch processor
"""

import os
import json
from typing import Dict, List, Any
from pathlib import Path

# Import the renderer and file manager
try:
    from pythonThemeTools.theme_renderer import ThemeRenderer
    from pythonThemeTools.file_manager import FileManager
except ImportError as e:
    print(f"Error importing required modules: {e}")
    print("Make sure pythonThemeTools package is available")
    exit(1)


class StandaloneThemeRenderer:
    def __init__(self, 
                 official_json_path: str = "community-css-themes.json",
                 addon_json_path: str = "community-css-themes-tag-browser.json"):
        """
        Initialize the standalone renderer
        
        Args:
            official_json_path: Path to official themes JSON
            addon_json_path: Path to addon themes JSON  
        """
        self.file_manager = FileManager()
        self.official_path = official_json_path
        self.addon_path = addon_json_path
        self.renderer = ThemeRenderer()
        
        print(f"Standalone Theme Renderer initialized")
        print(f"Official JSON: {self.official_path}")
        print(f"Addon JSON: {self.addon_path}")

    def load_theme_data(self) -> tuple[List[Dict], List[Dict]]:
        """Load both official and addon theme data"""
        official_data = self.file_manager.load_json_data(self.official_path, "Official themes")
        addon_data = self.file_manager.load_json_data(self.addon_path, "Addon themes")
        return official_data, addon_data

    def prepare_themes_for_rendering(self, official_data: List[Dict], addon_data: List[Dict]) -> tuple[List[Dict], List[str]]:
        """
        Prepare themes for rendering by merging official and addon data
        
        Returns:
            tuple: (complete_themes, incomplete_theme_names)
        """
        # Create addon lookup
        addon_lookup = {theme.get("repo"): theme for theme in addon_data}
        
        complete_themes = []
        incomplete_themes = []
        
        for official_theme in official_data:
            repo = official_theme.get("repo")
            if not repo:
                continue
                
            addon_theme = addon_lookup.get(repo)
            if addon_theme:
                # Merge data for renderer - FIXED FORMAT
                merged_theme = {
                    "title": official_theme.get("name"),
                    "repository_link": f"https://github.com/{repo}",  # Full GitHub URL
                    "tags_list": addon_theme.get("tags", []),
                    "main_screenshot_url": addon_theme.get("screenshot-main", official_theme.get("screenshot", "")),
                    "additional_image_urls": addon_theme.get("screenshots-side", [])
                }
                complete_themes.append(merged_theme)
            else:
                incomplete_themes.append(official_theme.get("name", repo))
        
        return complete_themes, incomplete_themes

    def render_all_themes(self, force: bool = False) -> Dict[str, Any]:
        """
        Render all themes with complete data
        
        Args:
            force: If True, skip confirmation prompt
            
        Returns:
            Dict with rendering results
        """
        print("Loading theme data...")
        official_data, addon_data = self.load_theme_data()
        
        if not official_data:
            return {"error": "No official theme data found. Cannot render pages."}
        
        complete_themes, incomplete_themes = self.prepare_themes_for_rendering(official_data, addon_data)
        
        print(f"Theme Analysis:")
        print(f"  Complete themes (with addon data): {len(complete_themes)}")
        print(f"  Incomplete themes (missing addon data): {len(incomplete_themes)}")
        
        if incomplete_themes:
            print(f"\nSkipping {len(incomplete_themes)} themes without addon data:")
            for name in incomplete_themes[:5]:
                print(f"    • {name}")
            if len(incomplete_themes) > 5:
                print(f"    • ... and {len(incomplete_themes) - 5} more")
        
        if not complete_themes:
            return {"error": "No themes with complete data to render."}
        
        # Confirmation prompt unless forced
        if not force:
            confirm = input(f"\nRender {len(complete_themes)} theme pages? (y/n): ").strip().lower()
            if confirm != 'y':
                return {"cancelled": True, "message": "Rendering cancelled."}
        
        try:
            print(f"Starting render process...")
            results = self.renderer.batch_render_themes(complete_themes)
            
            print("\nRendering completed!")
            return {
                "success": True,
                "themes_rendered": len(complete_themes),
                "themes_skipped": len(incomplete_themes),
                "results": results
            }
            
        except Exception as e:
            error_msg = f"Rendering failed: {e}"
            print(f"Error: {error_msg}")
            return {"error": error_msg}

    def render_theme_range(self, range_input: str) -> Dict[str, Any]:
        """
        Render a specific range of themes
        
        Args:
            range_input: Range specification like "1-25", "1,5,10-15", etc.
            
        Returns:
            Dict with rendering results
        """
        official_data, addon_data = self.load_theme_data()
        complete_themes, incomplete_themes = self.prepare_themes_for_rendering(official_data, addon_data)
        
        if not complete_themes:
            return {"error": "No themes with complete data to render."}
        
        # Parse range
        selected_themes = self._parse_range_selection(range_input, complete_themes)
        if not selected_themes:
            return {"error": "Invalid range or no themes selected."}
        
        print(f"Selected {len(selected_themes)} themes from range '{range_input}'")
        
        try:
            results = self.renderer.batch_render_themes(selected_themes)
            
            return {
                "success": True,
                "themes_rendered": len(selected_themes),
                "range": range_input,
                "results": results
            }
            
        except Exception as e:
            error_msg = f"Range rendering failed: {e}"
            print(f"Error: {error_msg}")
            return {"error": error_msg}

    def _parse_range_selection(self, range_input: str, all_themes: List[Dict]) -> List[Dict]:
        """Parse range input and return selected themes"""
        if not range_input or range_input.lower() == 'all':
            return all_themes
        
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
                    if end >= len(all_themes):
                        end = len(all_themes) - 1
                    selected_indices.update(range(start, end + 1))
                else:
                    # Single number like "5"
                    index = int(part) - 1  # Convert to 0-indexed
                    if 0 <= index < len(all_themes):
                        selected_indices.add(index)
            
            return [all_themes[i] for i in sorted(selected_indices)]
            
        except (ValueError, IndexError) as e:
            print(f"Invalid range format: {range_input}")
            print("Examples: '1-25', '1,5,10-15', 'all', '50'")
            return []

    def show_theme_list(self, limit: int = 10) -> None:
        """Show available themes for rendering"""
        official_data, addon_data = self.load_theme_data()
        complete_themes, incomplete_themes = self.prepare_themes_for_rendering(official_data, addon_data)
        
        print(f"\nAvailable themes for rendering ({len(complete_themes)} total):")
        print("-" * 60)
        
        for i, theme in enumerate(complete_themes[:limit], 1):
            title = theme.get("title", "Unknown")
            repo = theme.get("repository_link", "")
            tags = theme.get("tags_list", [])
            tag_preview = ", ".join(tags[:3])
            if len(tags) > 3:
                tag_preview += f" (+{len(tags)-3} more)"
            
            print(f"{i:3}. {title}")
            print(f"     {repo}")
            print(f"     Tags: [{tag_preview}]")
        
        if len(complete_themes) > limit:
            print(f"     ... and {len(complete_themes) - limit} more themes")
        
        if incomplete_themes:
            print(f"\nThemes without addon data ({len(incomplete_themes)}):")
            for name in incomplete_themes[:5]:
                print(f"  • {name}")
            if len(incomplete_themes) > 5:
                print(f"  • ... and {len(incomplete_themes) - 5} more")

    def interactive_menu(self):
        """Interactive menu for theme rendering"""
        while True:
            print("\n" + "="*60)
            print("STANDALONE THEME RENDERER".center(60))
            print("="*60)
            print("1. Render All Themes")
            print("2. Render Theme Range")
            print("3. Show Theme List")
            print("4. Show Statistics")
            print("5. Change File Paths")
            print("6. Exit")
            print("="*60)
            
            choice = input("\nEnter your choice (1-6): ").strip()
            
            try:
                if choice == '1':
                    result = self.render_all_themes()
                    self._print_result(result)
                elif choice == '2':
                    range_input = input("Enter range (e.g., '1-25', '1,5,10-15'): ").strip()
                    if range_input:
                        result = self.render_theme_range(range_input)
                        self._print_result(result)
                elif choice == '3':
                    limit = input("Show how many themes? (default 10): ").strip()
                    limit = int(limit) if limit.isdigit() else 10
                    self.show_theme_list(limit)
                elif choice == '4':
                    self._show_statistics()
                elif choice == '5':
                    self._change_file_paths()
                elif choice == '6':
                    print("Goodbye!")
                    break
                else:
                    print("Invalid choice. Please select 1-6.")
                    
            except KeyboardInterrupt:
                print("\nOperation cancelled by user.")
                continue
            except Exception as e:
                print(f"Error: {str(e)}")
                continue
                
            if choice != '6':
                input("\nPress Enter to continue...")

    def _print_result(self, result: Dict[str, Any]):
        """Print rendering result"""
        if result.get("error"):
            print(f"Error: {result['error']}")
        elif result.get("cancelled"):
            print(result["message"])
        elif result.get("success"):
            print(f"Success! Rendered {result['themes_rendered']} themes")
            if result.get("themes_skipped"):
                print(f"Skipped {result['themes_skipped']} themes without complete data")
            if result.get("results"):
                print("Details:", result["results"])
        else:
            print("Unexpected result:", result)

    def _show_statistics(self):
        """Show theme statistics"""
        print("\nTheme Statistics:")
        print("-" * 40)
        
        official_data, addon_data = self.load_theme_data()
        complete_themes, incomplete_themes = self.prepare_themes_for_rendering(official_data, addon_data)
        
        print(f"Official themes: {len(official_data)}")
        print(f"Addon entries: {len(addon_data)}")
        print(f"Renderable themes: {len(complete_themes)}")
        print(f"Missing addon data: {len(incomplete_themes)}")
        
        if len(official_data) > 0:
            completion_rate = (len(complete_themes) / len(official_data)) * 100
            print(f"Completion rate: {completion_rate:.1f}%")
        
        # Tag statistics
        if complete_themes:
            all_tags = []
            for theme in complete_themes:
                all_tags.extend(theme.get("tags_list", []))
            
            if all_tags:
                unique_tags = set(all_tags)
                print(f"\nTag Statistics:")
                print(f"Unique tags: {len(unique_tags)}")
                print(f"Total tag usages: {len(all_tags)}")
                
                # Most common tags
                tag_counts = {}
                for tag in all_tags:
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1
                
                sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
                print("Most common tags:")
                for tag, count in sorted_tags[:8]:
                    print(f"  {tag}: {count}")

    def _change_file_paths(self):
        """Change file paths"""
        print(f"\nCurrent paths:")
        print(f"Official JSON: {self.official_path}")
        print(f"Addon JSON: {self.addon_path}")
        
        new_official = input(f"\nNew official JSON path (Enter to keep current): ").strip()
        new_addon = input(f"New addon JSON path (Enter to keep current): ").strip()
        
        if new_official:
            self.official_path = new_official
        if new_addon:
            self.addon_path = new_addon
        
        if new_official or new_addon:
            print("Paths updated successfully")


def main():
    """Main entry point"""
    print("Standalone Theme Renderer")
    print("=" * 50)
    
    # Check if running with command line arguments
    import sys
    
    if len(sys.argv) > 1:
        # Command line mode
        renderer = StandaloneThemeRenderer()
        
        if sys.argv[1] == "render-all":
            result = renderer.render_all_themes(force=True)
            print("Result:", result)
        elif sys.argv[1] == "render-range" and len(sys.argv) > 2:
            range_input = sys.argv[2]
            result = renderer.render_theme_range(range_input)
            print("Result:", result)
        elif sys.argv[1] == "list":
            limit = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else 10
            renderer.show_theme_list(limit)
        elif sys.argv[1] == "stats":
            renderer._show_statistics()
        else:
            print("Usage:")
            print("  python standalone_theme_renderer.py render-all")
            print("  python standalone_theme_renderer.py render-range '1-25'")
            print("  python standalone_theme_renderer.py list [count]")
            print("  python standalone_theme_renderer.py stats")
    else:
        # Interactive mode
        renderer = StandaloneThemeRenderer()
        renderer.interactive_menu()


if __name__ == "__main__":
    main()
