"""
Git-based auto-updater module for Python scripts.
Handles repository initialization, updates, and script restart.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


REPO_URL = "https://github.com/ThisTheThe/StylistGuild.git"


def run_git_command(cmd, cwd=None, capture_output=True):
    """
    Run a git command and return result with clear error handling.
    
    Args:
        cmd: List of command parts (e.g., ['git', 'status'])
        cwd: Working directory (defaults to current directory)
        capture_output: Whether to capture output or print directly
    
    Returns:
        tuple: (success: bool, output: str, error: str)
    """
    try:
        if cwd is None:
            cwd = os.getcwd()
            
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=capture_output,
            text=True,
            timeout=30
        )
        
        success = result.returncode == 0
        output = result.stdout.strip() if capture_output else ""
        error = result.stderr.strip() if capture_output else ""
        
        return success, output, error
        
    except subprocess.TimeoutExpired:
        return False, "", "Git command timed out after 30 seconds"
    except FileNotFoundError:
        return False, "", "Git is not installed or not in PATH"
    except Exception as e:
        return False, "", f"Unexpected error running git command: {str(e)}"


def is_git_repo():
    """Check if current directory is a git repository."""
    success, _, _ = run_git_command(['git', 'rev-parse', '--git-dir'])
    return success


def has_local_changes():
    """Check if there are uncommitted local changes."""
    success, output, error = run_git_command(['git', 'status', '--porcelain'])
    if not success:
        print(f"Error checking git status: {error}")
        return False
    return bool(output.strip())


def get_remote_url():
    """Get the current remote origin URL."""
    success, output, error = run_git_command(['git', 'remote', 'get-url', 'origin'])
    if not success:
        return None
    return output.strip()


def prompt_user_for_conflicts():
    """
    Prompt user for how to handle local changes.
    
    Returns:
        str: 'stash', 'reset', 'abort'
    """
    print("\n⚠️  Local changes detected!")
    print("You have uncommitted changes in your repository.")
    
    # Show what files are changed
    success, status_output, _ = run_git_command(['git', 'status', '--porcelain'])
    if success and status_output:
        print("\nChanged files:")
        for line in status_output.split('\n')[:10]:  # Show first 10
            if line.strip():
                status = line[:2]
                filename = line[3:]
                if status.strip() == 'M':
                    print(f"   📝 Modified: {filename}")
                elif status.strip() == 'A':
                    print(f"   ➕ Added: {filename}")
                elif status.strip() == 'D':
                    print(f"   ❌ Deleted: {filename}")
                elif status.strip() == '??':
                    print(f"   📄 Untracked: {filename}")
                else:
                    print(f"   {status} {filename}")
    
    print("\nOptions:")
    print("1. Stash changes and update (saves ALL changes including untracked files)")
    print("2. Reset tracked changes only (keeps untracked files, with backup option)")
    print("3. Abort update (keep current version)")
    
    while True:
        choice = input("\nEnter choice (1/2/3): ").strip()
        if choice == '1':
            return 'stash'
        elif choice == '2':
            return 'reset'
        elif choice == '3':
            return 'abort'
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")


def handle_local_changes(strategy):
    """
    Handle local changes based on user strategy.
    
    Args:
        strategy: 'stash', 'reset', or 'abort'
    
    Returns:
        bool: True if ready to proceed with update, False if aborted
    """
    if strategy == 'abort':
        print("Update aborted by user.")
        return False
    
    elif strategy == 'stash':
        print("Stashing local changes...")
        success, output, error = run_git_command(['git', 'stash', 'push', '-m', 'Auto-update stash'])
        if not success:
            print(f"❌ Failed to stash changes: {error}")
            return False
        print("✅ Local changes stashed successfully")
        return True
    
    elif strategy == 'reset':
        print("Resetting local changes...")
        success, output, error = run_git_command(['git', 'reset', '--hard', 'HEAD'])
        if not success:
            print(f"❌ Failed to reset changes: {error}")
            return False
        
        # Clean untracked files
        success, output, error = run_git_command(['git', 'clean', '-fd'])
        if not success:
            print(f"⚠️  Warning: Failed to clean untracked files: {error}")
        
        print("✅ Local changes reset successfully")
        return True
    
    return False


def clone_repository():
    """
    Clone the repository to current directory.
    
    Returns:
        bool: True if successful, False otherwise
    """
    current_dir = Path.cwd()
    print(f"📥 Cloning repository to {current_dir}...")
    
    success, output, error = run_git_command(['git', 'clone', REPO_URL, '.'])
    if not success:
        print(f"❌ Failed to clone repository: {error}")
        return False
    
    print("✅ Repository cloned successfully")
    return True


def fetch_and_check_updates():
    """
    Fetch from remote and check if updates are available.
    
    Returns:
        tuple: (bool: updates_available, str: current_hash, str: remote_hash)
    """
    print("🔍 Checking for updates...")
    
    # Fetch from remote
    success, output, error = run_git_command(['git', 'fetch', 'origin'])
    if not success:
        print(f"❌ Failed to fetch from remote: {error}")
        return False, None, None
    
    # Get current commit hash
    success, current_hash, error = run_git_command(['git', 'rev-parse', 'HEAD'])
    if not success:
        print(f"❌ Failed to get current commit: {error}")
        return False, None, None
    
    # Get remote commit hash
    success, remote_hash, error = run_git_command(['git', 'rev-parse', 'origin/main'])
    if not success:
        # Try 'master' branch if 'main' doesn't exist
        success, remote_hash, error = run_git_command(['git', 'rev-parse', 'origin/master'])
        if not success:
            print(f"❌ Failed to get remote commit: {error}")
            return False, None, None
    
    updates_available = current_hash.strip() != remote_hash.strip()
    return updates_available, current_hash.strip(), remote_hash.strip()


def pull_updates():
    """
    Pull updates from remote repository.
    
    Returns:
        bool: True if successful, False otherwise
    """
    print("📥 Pulling updates...")
    
    success, output, error = run_git_command(['git', 'pull', 'origin'])
    if not success:
        print(f"❌ Failed to pull updates: {error}")
        return False
    
    print("✅ Updates pulled successfully")
    return True


def restart_script():
    """Restart the current Python script."""
    print("🔄 Restarting script...")
    
    # Get the current script path and arguments
    script_path = sys.argv[0]
    script_args = sys.argv[1:]
    
    # Restart using os.execv
    try:
        os.execv(sys.executable, [sys.executable, script_path] + script_args)
    except Exception as e:
        print(f"❌ Failed to restart script: {e}")
        print("Please restart manually.")
        sys.exit(1)


def check_and_update():
    """
    Main function to check for updates and update if necessary.
    
    Returns:
        bool: True if script should restart, False if no updates or error
    """
    print("🚀 Checking for updates...")
    
    # Check if we're in a git repository
    if not is_git_repo():
        print("📂 No git repository found in current directory")
        
        if os.listdir('.'):  # Directory is not empty
            print("❌ Current directory is not empty. Cannot initialize repository.")
            print("Please run from an empty directory or existing git repository.")
            return False
        
        # Clone repository
        if not clone_repository():
            return False
        
        print("✅ Repository initialized! Restart required.")
        return True
    
    # Verify we're connected to the correct repository
    current_remote = get_remote_url()
    if current_remote and current_remote != REPO_URL:
        print(f"⚠️  Warning: Repository remote URL mismatch!")
        print(f"Current: {current_remote}")
        print(f"Expected: {REPO_URL}")
        print("Please check your repository configuration.")
        return False
    
    # Check for local changes to tracked files only
    if has_tracked_changes():
        if not prompt_user_for_conflicts():
            return False
        
        if not handle_local_changes():
            return False
    
    # Check for updates
    updates_available, current_hash, remote_hash, current_branch = fetch_and_check_updates()
    if updates_available is False:  # Error occurred
        return False
    
    if not updates_available:
        print("✅ Already up to date!")
        return False
    
    print(f"🆕 Updates available!")
    print(f"Current ({current_branch}): {current_hash[:8]}...")
    print(f"Remote:  {remote_hash[:8]}...")
    
    # Pull updates
    if not pull_updates():
        return False
    
    # Verify the update actually worked
    print("🔍 Verifying update...")
    success, new_hash, error = run_git_command(['git', 'rev-parse', 'HEAD'])
    if success:
        if new_hash.strip() == remote_hash:
            print(f"✅ Update verified! Now at {new_hash[:8]}...")
        else:
            print(f"⚠️  Warning: Expected {remote_hash[:8]} but got {new_hash[:8]}")
            print("Update may not have completed fully.")
    
    print("✅ Update completed! Script will restart.")
    return True


if __name__ == "__main__":
    # Test the updater
    should_restart = check_and_update()
    if should_restart:
        restart_script()
    else:
        print("No restart needed.")
