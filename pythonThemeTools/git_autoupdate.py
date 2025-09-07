import os
import sys
import subprocess
import logging
import shutil
from pathlib import Path

class GitAutoUpdater:
    def __init__(self, repo_url=None, branch="main", script_dir=None):
        """
        Initialize the Git auto-updater
        
        Args:
            repo_url (str): The Git repository URL to clone if no repo exists
            branch (str): The branch to track (default: main)
            script_dir (str): Directory containing the script (default: current working directory)
        """
        self.repo_url = repo_url
        self.branch = branch
        # Default to current working directory (where main script runs from)
        self.script_dir = Path(script_dir) if script_dir else Path.cwd()
        
        # Set up logging
        logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
        self.logger = logging.getLogger(__name__)
    
    def run_command(self, command, cwd=None):
        """Run a shell command and return the result"""
        try:
            result = subprocess.run(
                command, 
                shell=True, 
                cwd=cwd or self.script_dir,
                capture_output=True, 
                text=True, 
                check=True
            )
            return result.stdout.strip(), result.stderr.strip()
        except subprocess.CalledProcessError as e:
            raise Exception(f"Command failed: {command}\nError: {e.stderr}")
    
    def is_git_repo(self):
        """Check if current directory is a git repository"""
        git_dir = self.script_dir / '.git'
        return git_dir.exists() and git_dir.is_dir()
    
    def get_current_commit(self):
        """Get the current commit hash"""
        stdout, _ = self.run_command("git rev-parse HEAD")
        return stdout
    
    def get_remote_commit(self):
        """Get the latest commit hash from remote"""
        # Fetch latest changes without merging
        self.run_command("git fetch origin")
        stdout, _ = self.run_command(f"git rev-parse origin/{self.branch}")
        return stdout
    
    def is_up_to_date(self):
        """Check if local repository is up to date with remote"""
        try:
            local_commit = self.get_current_commit()
            remote_commit = self.get_remote_commit()
            return local_commit == remote_commit
        except Exception as e:
            self.logger.error(f"Failed to check if up to date: {e}")
            return False
    
    def pull_updates(self):
        """Pull latest changes from remote repository"""
        try:
            self.logger.info("Pulling latest changes...")
            stdout, stderr = self.run_command(f"git pull origin {self.branch}")
            if stdout:
                self.logger.info(f"Pull result: {stdout}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to pull updates: {e}")
            return False
    
    def remove_readonly_and_delete(self, path):
        """Remove read-only attributes and delete files/folders (Windows-safe)"""
        def handle_remove_readonly(func, path, exc):
            """Error handler to remove read-only attribute"""
            if os.path.exists(path):
                os.chmod(path, 0o777)  # Make writable
                func(path)
        
        if path.exists():
            shutil.rmtree(path, onerror=handle_remove_readonly)
    
    def clone_repository(self):
        """Clone the repository if it doesn't exist"""
        if not self.repo_url:
            raise ValueError("Repository URL is required to clone a new repo")
        
        try:
            self.logger.info(f"Cloning repository from {self.repo_url}...")
            
            # Clone to a temporary directory first
            temp_dir = self.script_dir / "temp_clone"
            
            # Remove temp directory if it exists (Windows-safe)
            self.remove_readonly_and_delete(temp_dir)
            
            self.run_command(f"git clone {self.repo_url} {temp_dir}")
            
            # Move .git directory (cross-platform)
            git_source = temp_dir / ".git"
            git_dest = self.script_dir / ".git"
            
            # Remove existing .git if present
            self.remove_readonly_and_delete(git_dest)
            shutil.copytree(git_source, git_dest)
            
            # Copy all files except .git (cross-platform)
            for item in temp_dir.iterdir():
                if item.name == '.git':
                    continue
                    
                dest_path = self.script_dir / item.name
                
                try:
                    if item.is_file():
                        if dest_path.exists():
                            # Remove read-only and delete
                            os.chmod(dest_path, 0o777)
                            dest_path.unlink()
                        shutil.copy2(item, dest_path)
                    elif item.is_dir():
                        if dest_path.exists():
                            self.remove_readonly_and_delete(dest_path)
                        shutil.copytree(item, dest_path)
                except PermissionError as e:
                    self.logger.warning(f"Permission error copying {item.name}: {e}")
                    continue
            
            # Clean up temp directory (Windows-safe)
            self.remove_readonly_and_delete(temp_dir)
            
            self.logger.info("Repository cloned successfully")
            return True
            
        except Exception as e:
            # Try to clean up temp directory even on failure
            try:
                temp_dir = self.script_dir / "temp_clone"
                self.remove_readonly_and_delete(temp_dir)
            except:
                pass
            
            self.logger.error(f"Failed to clone repository: {e}")
            return False
    
    def check_and_update(self):
        """Main method to check for updates and apply them if necessary"""
        self.logger.info("Starting auto-update check...")
        
        # Check if this is a git repository
        if not self.is_git_repo():
            self.logger.info("No git repository found")
            if self.repo_url:
                self.logger.info("Attempting to clone repository...")
                if self.clone_repository():
                    self.logger.info("Repository setup complete")
                    return True
                else:
                    self.logger.error("Failed to setup repository")
                    return False
            else:
                self.logger.error("No repository URL provided for cloning")
                return False
        
        # Git repo exists, check for updates
        self.logger.info("Git repository found, checking for updates...")
        
        try:
            if self.is_up_to_date():
                self.logger.info("Repository is up to date")
                return True
            else:
                self.logger.info("Updates available, pulling changes...")
                if self.pull_updates():
                    self.logger.info("Update completed successfully")
                    return True
                else:
                    self.logger.error("Update failed")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Error during update check: {e}")
            self.logger.info("Attempting to force pull...")
            
            # Try a force pull as last resort
            try:
                self.run_command("git reset --hard HEAD")
                if self.pull_updates():
                    self.logger.info("Force pull completed successfully")
                    return True
                else:
                    self.logger.error("Force pull failed")
                    return False
            except Exception as e2:
                self.logger.error(f"Force pull also failed: {e2}")
                return False


def auto_update_check(repo_url=None, branch="main", restart_on_update=False, safe_restart=True):
    """
    Convenience function to perform auto-update check
    
    Args:
        repo_url (str): Git repository URL for cloning if needed
        branch (str): Branch to track
        restart_on_update (bool): Whether to restart the script after update
        safe_restart (bool): If True, only restart if no critical operations are running
        
    Returns:
        dict: {'success': bool, 'updated': bool, 'needs_restart': bool}
    """
    updater = GitAutoUpdater(repo_url=repo_url, branch=branch)
    
    # Store original commit for comparison
    original_commit = None
    if updater.is_git_repo():
        try:
            original_commit = updater.get_current_commit()
        except:
            pass
    
    # Perform update check
    success = updater.check_and_update()
    updated = False
    needs_restart = False
    
    # Check if we need to restart
    if success and updater.is_git_repo():
        try:
            current_commit = updater.get_current_commit()
            if original_commit and original_commit != current_commit:
                updated = True
                needs_restart = True
                
                if restart_on_update:
                    if safe_restart:
                        updater.logger.info("Script was updated. Please restart manually for changes to take effect.")
                    else:
                        updater.logger.info("Script was updated, restarting...")
                        os.execv(sys.executable, [sys.executable] + sys.argv)
        except Exception as e:
            updater.logger.error(f"Failed to check for restart: {e}")
    
    return {
        'success': success,
        'updated': updated, 
        'needs_restart': needs_restart
    }


# Example usage
if __name__ == "__main__":
    # Example 1: Basic usage with repository URL
    repo_url = "https://github.com/yourusername/yourrepo.git"
    
    # Perform auto-update check
    if auto_update_check(repo_url=repo_url, branch="main", restart_on_update=True):
        print("Auto-update check completed")
    else:
        print("Auto-update check failed")
    
    # Your main script logic goes here
    print("Running main application...")
    
    # Example 2: Manual usage with more control
    # updater = GitAutoUpdater(
    #     repo_url="https://github.com/yourusername/yourrepo.git",
    #     branch="develop"
    # )
    # 
    # if updater.check_and_update():
    #     print("Update check successful")
    # else:
    #     print("Update check failed")
