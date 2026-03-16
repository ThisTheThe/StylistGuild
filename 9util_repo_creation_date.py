#!/usr/bin/env python3
"""
Add GitHub repository creation dates to community_css_themes_tag_browser.json

Processes entries in batches with delays to avoid rate limiting.
Resumes from where it left off if interrupted.
"""

import json
import time
import requests
from pathlib import Path
from datetime import datetime
from typing import Optional


class CreationDateAdder:
    def __init__(self, json_path: str, github_token: Optional[str] = None):
        self.json_path = Path(json_path)
        self.github_token = github_token
        self.batch_size = 10  # Process 10 repos at a time
        self.delay_seconds = 5  # Wait 5 seconds between batches
        self.rate_limit_wait = 60  # Wait 1 hour if rate limited
        
    def load_data(self) -> list:
        """Load the JSON file"""
        try:
            with open(self.json_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"❌ File not found: {self.json_path}")
            return []
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON: {e}")
            return []
    
    def save_data(self, data: list):
        """Save the JSON file with backup"""
        # Create timestamped backup to avoid conflicts
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        backup_path = self.json_path.with_suffix(f'.{timestamp}.backup')
        if self.json_path.exists():
            self.json_path.rename(backup_path)
            print(f"📦 Backup created: {backup_path}")
        
        # Save new data
        with open(self.json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"💾 Saved to: {self.json_path}")
    
    def get_repo_creation_date(self, repo: str) -> Optional[str]:
        """
        Fetch creation date from GitHub API
        Returns ISO format date string or special error values
        """
        url = f"https://api.github.com/repos/{repo}"
        headers = {"Accept": "application/vnd.github.v3+json"}
        
        if self.github_token:
            headers["Authorization"] = f"token {self.github_token}"
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                created_at = data.get("created_at")
                print(f"  ✅ {repo}: {created_at}")
                return created_at
            elif response.status_code == 404:
                print(f"  ❌ {repo}: NOT_FOUND")
                return "NOT_FOUND"
            elif response.status_code == 403:
                # Check if it's rate limit
                if 'X-RateLimit-Remaining' in response.headers:
                    remaining = response.headers.get('X-RateLimit-Remaining')
                    if remaining == '0':
                        reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
                        wait_seconds = max(reset_time - time.time(), self.rate_limit_wait) / 60
                        print(f"  ⏸️  Rate limit hit. Waiting {wait_seconds/60:.1f} minutes...")
                        time.sleep(wait_seconds)
                        return self.get_repo_creation_date(repo)  # Retry
                return "RATE_LIMITED"
            else:
                print(f"  ⚠️  {repo}: API_ERROR_{response.status_code}")
                return f"API_ERROR_{response.status_code}"
                
        except requests.RequestException as e:
            print(f"  ⚠️  {repo}: NETWORK_ERROR")
            return "NETWORK_ERROR"
    
    def process_entries(self):
        """Main processing loop"""
        data = self.load_data()
        if not data:
            return
        
        total = len(data)
        processed = 0
        updated = 0
        skipped = 0
        errors = 0
        
        print(f"\n🚀 Processing {total} repositories...")
        print(f"📊 Batch size: {self.batch_size}, Delay: {self.delay_seconds}s\n")
        
        for i, entry in enumerate(data):
            repo = entry.get("repo")
            
            # Skip if already has creation date
            if "repo_created" in entry:
                skipped += 1
                continue
            
            if not repo:
                print(f"  ⚠️  Entry {i}: Missing repo field")
                entry["repo_created"] = "MISSING_REPO"
                errors += 1
                continue
            
            # Fetch creation date
            creation_date = self.get_repo_creation_date(repo)
            entry["repo_created"] = creation_date
            
            if creation_date and not creation_date.startswith(("NOT_FOUND", "API_ERROR", "NETWORK_ERROR", "RATE_LIMITED")):
                updated += 1
            else:
                errors += 1
            
            processed += 1
            
            # Save progress after each batch
            if processed % self.batch_size == 0:
                self.save_data(data)
                remaining = total - (i + 1)
                print(f"\n💾 Progress saved: {processed}/{total} processed, {remaining} remaining")
                
                if remaining > 0:
                    print(f"⏳ Waiting {self.delay_seconds} seconds before next batch...\n")
                    time.sleep(self.delay_seconds)
        
        # Final save
        self.save_data(data)
        
        # Summary
        print("\n" + "="*60)
        print("📊 SUMMARY")
        print("="*60)
        print(f"Total entries:     {total}")
        print(f"Processed:         {processed}")
        print(f"Successfully added: {updated}")
        print(f"Skipped (already had date): {skipped}")
        print(f"Errors:            {errors}")
        print("="*60)


def main():
    print("="*60)
    print("GitHub Repository Creation Date Adder")
    print("="*60)
    
    # Get JSON file path
    json_path = input("\nEnter path to JSON file (or press Enter for default): ").strip()
    if not json_path:
        json_path = "community-css-themes-tag-browser.json"
    
    # Ask about GitHub token
    print("\n💡 Using a GitHub token increases rate limits (5000/hour vs 60/hour)")
    use_token = input("Do you have a GitHub token? (y/n): ").strip().lower()
    
    token = None
    if use_token == 'y':
        token = input("Enter your GitHub token: ").strip()
    
    # Confirm
    print(f"\n📄 File: {json_path}")
    print(f"🔑 Token: {'Yes' if token else 'No (60 requests/hour limit)'}")
    
    confirm = input("\nProceed? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Cancelled.")
        return
    
    # Run the processor
    adder = CreationDateAdder(json_path, token)
    adder.process_entries()


if __name__ == "__main__":
    main()
    input("")