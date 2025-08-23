#!/usr/bin/env python3
"""
GitHub Utilities Module
Handles GitHub-related operations for the theme batch processor
"""

import webbrowser
import re
import requests
from typing import Dict, Optional, Tuple
from urllib.parse import urlparse


def open_github_repo(repo: str) -> bool:
    """
    Open the GitHub repository page in the default web browser.
    
    Args:
        repo: The repository identifier in the format "owner/repo-name".
        
    Returns:
        bool: True if browser opened successfully
    """
    if not repo:
        print("❌ No repository specified")
        return False
        
    # Clean the repo string in case it has extra whitespace
    repo = repo.strip()
    
    if not validate_repo_format(repo):
        print(f"❌ Invalid repository format: {repo}")
        print("Expected format: owner/repo-name")
        return False
        
    url = f"https://github.com/{repo}"
    try:
        webbrowser.open(url)
        print(f"✅ Opened GitHub repository in browser: {url}")
        return True
    except Exception as e:
        print(f"⚠️ Could not open browser: {str(e)}")
        print(f"You can manually visit: {url}")
        return False


def extract_repo_from_url(github_url: str) -> Optional[str]:
    """
    Extract owner/repo from various GitHub URL formats
    
    Args:
        github_url: GitHub URL in various formats
        
    Returns:
        str: Extracted "owner/repo" or None if invalid
        
    Examples:
        >>> extract_repo_from_url("https://github.com/microsoft/vscode")
        "microsoft/vscode"
        >>> extract_repo_from_url("git@github.com:microsoft/vscode.git")
        "microsoft/vscode"
    """
    if not github_url:
        return None
    
    # Different patterns for various GitHub URL formats
    patterns = [
        r"github\.com[/:]([^/\s]+/[^/\s]+?)(?:\.git|/.*)?(?:\s|$)",  # HTTPS and SSH
        r"^([^/\s]+/[^/\s]+?)(?:\.git)?(?:/.*)?$",  # Just owner/repo format
    ]
    
    for pattern in patterns:
        match = re.search(pattern, github_url.strip())
        if match:
            repo = match.group(1)
            # Clean up any extra components and validate
            repo_parts = repo.split("/")[:2]  # Take only first two parts
            if len(repo_parts) == 2:
                clean_repo = "/".join(repo_parts)
                if validate_repo_format(clean_repo):
                    return clean_repo
    
    return None


def validate_repo_format(repo: str) -> bool:
    """
    Validate repository format (owner/repo)
    
    Args:
        repo: Repository string to validate
        
    Returns:
        bool: True if valid format
        
    Examples:
        >>> validate_repo_format("microsoft/vscode")
        True
        >>> validate_repo_format("invalid")
        False
        >>> validate_repo_format("user/repo/extra")
        False
    """
    if not repo or not isinstance(repo, str):
        return False
    
    # Split by forward slash
    parts = repo.strip().split("/")
    
    # Must have exactly 2 parts
    if len(parts) != 2:
        return False
    
    owner, repo_name = parts
    
    # Both parts must be non-empty
    if not owner or not repo_name:
        return False
    
    # Check for valid GitHub username/repo characters
    # GitHub allows alphanumeric, hyphens, underscores, and periods
    valid_pattern = r"^[a-zA-Z0-9._-]+$"
    
    return bool(re.match(valid_pattern, owner) and re.match(valid_pattern, repo_name))


def get_repo_info(repo: str, github_token: Optional[str] = None) -> Dict[str, any]:
    """
    Fetch repository information from GitHub API
    
    Args:
        repo: Repository in format "owner/repo"
        github_token: Optional GitHub API token for higher rate limits
        
    Returns:
        Dict with repo information or error details
    """
    if not validate_repo_format(repo):
        return {"error": f"Invalid repository format: {repo}"}
    
    url = f"https://api.github.com/repos/{repo}"
    headers = {"Accept": "application/vnd.github.v3+json"}
    
    if github_token:
        headers["Authorization"] = f"token {github_token}"
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            return {
                "name": data.get("name"),
                "full_name": data.get("full_name"),
                "description": data.get("description"),
                "html_url": data.get("html_url"),
                "created_at": data.get("created_at"),
                "updated_at": data.get("updated_at"),
                "language": data.get("language"),
                "stargazers_count": data.get("stargazers_count"),
                "forks_count": data.get("forks_count"),
                "topics": data.get("topics", []),
                "archived": data.get("archived", False),
                "private": data.get("private", False)
            }
        elif response.status_code == 404:
            return {"error": f"Repository {repo} not found"}
        elif response.status_code == 403:
            return {"error": "GitHub API rate limit exceeded"}
        else:
            return {"error": f"GitHub API error: {response.status_code}"}
            
    except requests.RequestException as e:
        return {"error": f"Network error: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


def parse_github_url(url: str) -> Dict[str, Optional[str]]:
    """
    Parse a GitHub URL and extract components
    
    Args:
        url: GitHub URL to parse
        
    Returns:
        Dict with parsed components
        
    Example:
        >>> parse_github_url("https://github.com/microsoft/vscode/blob/main/README.md")
        {
            "owner": "microsoft",
            "repo": "vscode", 
            "full_repo": "microsoft/vscode",
            "branch": "main",
            "path": "README.md"
        }
    """
    result = {
        "owner": None,
        "repo": None,
        "full_repo": None,
        "branch": None,
        "path": None,
        "type": None  # blob, tree, etc.
    }
    
    try:
        parsed = urlparse(url)
        
        if "github.com" not in parsed.netloc:
            return result
        
        # Split the path
        path_parts = [part for part in parsed.path.split("/") if part]
        
        if len(path_parts) >= 2:
            result["owner"] = path_parts[0]
            result["repo"] = path_parts[1]
            result["full_repo"] = f"{path_parts[0]}/{path_parts[1]}"
            
            # If there are more parts, try to parse them
            if len(path_parts) >= 4:
                result["type"] = path_parts[2]  # blob, tree, etc.
                result["branch"] = path_parts[3]
                
                if len(path_parts) > 4:
                    result["path"] = "/".join(path_parts[4:])
    
    except Exception:
        pass  # Return empty result on any parsing error
    
    return result


def format_repo_url(repo: str, path: Optional[str] = None, 
                   branch: Optional[str] = None) -> str:
    """
    Format a GitHub URL from repository and optional path/branch
    
    Args:
        repo: Repository in format "owner/repo"
        path: Optional file/directory path
        branch: Optional branch name (defaults to main)
        
    Returns:
        Formatted GitHub URL
    """
    if not validate_repo_format(repo):
        raise ValueError(f"Invalid repository format: {repo}")
    
    base_url = f"https://github.com/{repo}"
    
    if path:
        branch = branch or "main"
        # Determine if it's a file or directory (simple heuristic)
        url_type = "blob" if "." in path.split("/")[-1] else "tree"
        base_url = f"{base_url}/{url_type}/{branch}/{path}"
    
    return base_url


# Utility function for the batch processor
def prompt_for_repo_confirmation(repo: str) -> bool:
    """
    Ask user to confirm they want to work with a repository
    
    Args:
        repo: Repository identifier
        
    Returns:
        bool: True if user confirms
    """
    if not validate_repo_format(repo):
        print(f"❌ Invalid repository format: {repo}")
        return False
    
    print(f"\n📁 Working with repository: {repo}")
    print(f"🌐 GitHub URL: https://github.com/{repo}")
    
    while True:
        choice = input("Continue with this repository? (y/n): ").strip().lower()
        if choice in ['y', 'yes']:
            return True
        elif choice in ['n', 'no']:
            return False
        else:
            print("Please enter 'y' or 'n'")


# Example usage and testing
if __name__ == "__main__":
    # Test the functions
    test_repos = [
        "microsoft/vscode",
        "facebook/react", 
        "invalid",
        "too/many/parts"
    ]
    
    print("Testing repository validation:")
    for repo in test_repos:
        is_valid = validate_repo_format(repo)
        print(f"  {repo}: {'✅' if is_valid else '❌'}")
    
    print("\nTesting URL extraction:")
    test_urls = [
        "https://github.com/microsoft/vscode",
        "git@github.com:facebook/react.git",
        "https://github.com/torvalds/linux/blob/master/README"
    ]
    
    for url in test_urls:
        repo = extract_repo_from_url(url)
        print(f"  {url} → {repo}")
    
    # Test opening a repo (uncomment to actually open browser)
    # open_github_repo("microsoft/vscode")