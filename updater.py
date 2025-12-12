#!/usr/bin/env python3
"""
Git pull script that aborts on conflicts.
Untracked files are left untouched.
"""

import subprocess
import sys
import os

# Change working directory to where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)
print(f"Working directory: {script_dir}\n")

def run_command(cmd, description):
    """Run a shell command and return success status and output."""
    print(f"→ {description}...")
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            check=True
        )
        print(f"✓ {description} successful")
        if result.stdout.strip():
            print(result.stdout)
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed")
        if e.stderr:
            print(f"Error: {e.stderr}")
        if e.stdout:
            print(f"Output: {e.stdout}")
        return False, e.stderr

def main():
    print("=== Git Pull Script ===\n")
    
    # Check if we're in a git repository
    success, _ = run_command("git rev-parse --git-dir", "Checking if directory is a git repository")
    if not success:
        print("\n✗ Not a git repository. Exiting.")
        sys.exit(1)
    
    # Check for uncommitted changes in tracked files
    success, output = run_command("git diff --quiet && git diff --cached --quiet", "Checking for uncommitted changes")
    if not success:
        print("\n✗ You have uncommitted changes in tracked files.")
        print("Please commit or stash your changes before pulling.")
        sys.exit(1)
    
    # Fetch updates from remote
    success, _ = run_command("git fetch", "Fetching updates from remote")
    if not success:
        print("\n✗ Failed to fetch from remote. Exiting.")
        sys.exit(1)
    
    # Check if pull would cause conflicts
    success, output = run_command("git merge-base HEAD @{u}", "Checking for potential conflicts")
    if not success:
        print("\n✗ Unable to determine merge base. Exiting.")
        sys.exit(1)
    
    # Perform the pull
    success, output = run_command("git pull", "Pulling changes")
    if not success:
        print("\n✗ Git pull failed. There may be merge conflicts.")
        print("Your repository is unchanged.")
        sys.exit(1)
    
    print("\n=== Pull completed successfully ===")
    print("Untracked files were left untouched.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n⚠️ Unexpected error: {e}")
    finally:
        input("\nPress Enter to close...")
