#!/usr/bin/env python3
import json
import csv
import os
import shutil
from pathlib import Path
from datetime import datetime

def load_json(filepath):
    """Load JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(data, filepath):
    """Save JSON file with formatting."""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def backup_file(filepath):
    """Create a timestamped backup of a file."""
    if not os.path.exists(filepath):
        return
    
    # Create backups directory if it doesn't exist
    backup_dir = Path('backups')
    backup_dir.mkdir(exist_ok=True)
    
    # Generate timestamped backup filename
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    filename = Path(filepath).name
    backup_path = backup_dir / f"{filename}.{timestamp}.bak"
    
    # Copy file to backup
    shutil.copy2(filepath, backup_path)
    print(f"✓ Backed up: {backup_path}")

def json_to_csv():
    """Convert JSON files to CSV."""
    # Backup existing CSV if it exists
    backup_file('community-css-themes-tag-browser.csv')
    
    # Load existing tag-browser data
    tag_browser = load_json('community-css-themes-tag-browser.json')
    community_themes = load_json('community-css-themes.json')
    
    # Get repos already in tag-browser
    existing_repos = {item['repo'] for item in tag_browser}
    
    # Prepare CSV rows
    rows = []
    
    # Add existing tag-browser entries first
    for item in tag_browser:
        repo_created = item.get('repo_created', '')
        rows.append({
            'github-link': f"https://github.com/{item['repo']}",
            'repo': item['repo'],
            'screenshot-main': item.get('screenshot-main', ''),
            'screenshots-side': '|'.join(item.get('screenshots-side', [])),
            'tags': ','.join(item.get('tags', [])),
            'repo_created': repo_created
        })
    
    # Add new repos from community-css-themes
    for theme in community_themes:
        repo = theme['repo']
        if repo not in existing_repos:
            rows.append({
                'github-link': f"https://github.com/{repo}",
                'repo': repo,
                'screenshot-main': theme.get('screenshot', ''),
                'screenshots-side': '',
                'tags': ','.join(theme.get('modes', [])),
                'repo_created': ''
            })
    
    # Write CSV with pipe delimiter
    with open('community-css-themes-tag-browser.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['github-link', 'repo', 'screenshot-main', 'screenshots-side', 'tags', 'repo_created'], delimiter='|', quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"✓ Converted to CSV: {len(rows)} repos")

def csv_to_json():
    """Convert CSV back to JSON."""
    # Backup existing JSON
    backup_file('community-css-themes-tag-browser.json')
    
    rows = []
    
    with open('community-css-themes-tag-browser.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='|')
        for row in reader:
            # Split screenshots-side by pipe, tags by comma
            screenshots_side = [s.strip() for s in row['screenshots-side'].split('|') if s.strip()]
            tags = [t.strip() for t in row['tags'].split(',') if t.strip()]
            
            entry = {
                'repo': row['repo'],
                'screenshot-main': row['screenshot-main'],
                'screenshots-side': screenshots_side,
                'tags': tags
            }
            
            # Add repo_created if it exists and is not empty
            if row.get('repo_created', '').strip():
                entry['repo_created'] = row['repo_created']
            
            rows.append(entry)
    
    save_json(rows, 'community-css-themes-tag-browser.json')
    print(f"✓ Converted to JSON: {len(rows)} repos")

def show_menu():
    """Display menu and get user choice."""
    print("\n" + "="*50)
    print("JSON-CSV Theme Converter")
    print("="*50)
    print("1. Convert JSON to CSV")
    print("2. Convert CSV to JSON")
    print("3. Exit")
    print("="*50)
    
    while True:
        choice = input("\nEnter your choice (1-3): ").strip()
        if choice in ['1', '2', '3']:
            return choice
        print("Invalid choice. Please enter 1, 2, or 3.")

def main():
    """Main menu-driven conversion."""
    choice = show_menu()
    
    if choice == '1':
        if not os.path.exists('community-css-themes-tag-browser.json'):
            print("Error: community-css-themes-tag-browser.json not found")
            return
        if not os.path.exists('community-css-themes.json'):
            print("Error: community-css-themes.json not found")
            return
        print("\nConverting JSON to CSV...")
        json_to_csv()
    elif choice == '2':
        if not os.path.exists('community-css-themes-tag-browser.csv'):
            print("Error: community-css-themes-tag-browser.csv not found")
            return
        print("\nConverting CSV to JSON...")
        csv_to_json()
    else:
        print("\nExiting...")
        return
    
    print("\nDone!")

if __name__ == '__main__':
    main()
