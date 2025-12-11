#!/usr/bin/env python3
"""
Quick utility to alphabetize tags in community-css-themes-tag-browser.json
Sorts tags within each theme entry, preserving all other data unchanged.
"""

import json
from pathlib import Path


def alphabetize_tags(json_file_path):
    """
    Load JSON, sort tags arrays alphabetically (case-insensitive), save back.
    
    Args:
        json_file_path: Path to the JSON file to process
    """
    # Load the JSON file
    file_path = Path(json_file_path)
    
    if not file_path.exists():
        print(f"Error: File not found: {json_file_path}")
        return False
    
    print(f"Loading {file_path.name}...")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        themes = json.load(f)
    
    # Sort tags in each theme entry
    modified_count = 0
    for theme in themes:
        if 'tags' in theme and isinstance(theme['tags'], list):
            original_tags = theme['tags'].copy()
            # Case-insensitive alphabetical sort
            theme['tags'] = sorted(theme['tags'], key=str.lower)
            
            if original_tags != theme['tags']:
                modified_count += 1
    
    # Save back to file with same formatting
    print(f"Saving sorted tags back to {file_path.name}...")
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(themes, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Complete! Modified {modified_count} theme(s) out of {len(themes)} total.")
    return True


if __name__ == "__main__":
    # Default file path - adjust if needed
    json_file = "community-css-themes-tag-browser.json"
    
    alphabetize_tags(json_file)
