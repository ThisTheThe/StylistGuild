#!/usr/bin/env python3
"""
Validator Module

Handles validation of URLs, data integrity, and theme data completeness.
"""

import re
import requests
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse
import time
from concurrent.futures import ThreadPoolExecutor, as_completed


class ValidationResult:
    """Container for validation results."""
    
    def __init__(self, field: str, is_valid: bool, message: str = "", severity: str = "error"):
        self.field = field
        self.is_valid = is_valid
        self.message = message
        self.severity = severity  # error, warning, info
    
    def __repr__(self):
        status = "✓" if self.is_valid else "✗"
        return f"{status} {self.field}: {self.message}"


class Validator:
    """
    Validates theme data, URLs, and data integrity.
    """
    
    def __init__(self, config=None):
        """
        Initialize validator with configuration.
        
        Args:
            config: Configuration object with validation settings
        """
        self.config = config or self._get_default_config()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Obsidian-Theme-Validator/1.0'
        })
    
    def _get_default_config(self):
        """Default validation configuration."""
        return {
            'url_timeout': 10,
            'github_timeout': 15,
            'max_concurrent_validations': 5,
            'required_fields': ['repo', 'tags', 'screenshot-main'],
            'optional_fields': ['screenshots-side', 'notes'],
            'max_side_screenshots': 10,
            'min_tag_count': 1,
            'max_tag_count': 10
        }
    
    def validate_url(self, url: str, timeout: Optional[int] = None) -> ValidationResult:
        """
        Validate that a URL is accessible.
        
        Args:
            url: URL to validate
            timeout: Request timeout in seconds
            
        Returns:
            ValidationResult object
        """
        if not url or not url.strip():
            return ValidationResult("url", False, "URL is empty")
        
        url = url.strip()
        
        # Basic URL format validation
        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return ValidationResult("url", False, "Invalid URL format")
        except Exception:
            return ValidationResult("url", False, "Invalid URL format")
        
        # Check if URL is accessible
        try:
            timeout = timeout or self.config['url_timeout']
            response = self.session.head(url, timeout=timeout, allow_redirects=True)
            
            if response.status_code == 200:
                return ValidationResult("url", True, "URL is accessible")
            elif response.status_code == 404:
                return ValidationResult("url", False, "URL not found (404)")
            elif response.status_code == 403:
                return ValidationResult("url", False, "Access forbidden (403)", "warning")
            else:
                return ValidationResult("url", False, f"HTTP {response.status_code}", "warning")
                
        except requests.exceptions.Timeout:
            return ValidationResult("url", False, "URL request timed out", "warning")
        except requests.exceptions.ConnectionError:
            return ValidationResult("url", False, "Connection error", "warning")
        except Exception as e:
            return ValidationResult("url", False, f"Network error: {str(e)}", "warning")
    
    def validate_github_repo(self, repo: str) -> ValidationResult:
        """
        Validate GitHub repository exists and is accessible.
        
        Args:
            repo: Repository in format 'username/repository'
            
        Returns:
            ValidationResult object
        """
        if not repo or not repo.strip():
            return ValidationResult("github_repo", False, "Repository field is empty")
        
        repo = repo.strip()
        
        # Validate format
        if not re.match(r'^[a-zA-Z0-9\-_\.]+/[a-zA-Z0-9\-_\.]+$', repo):
            return ValidationResult("github_repo", False, "Invalid repository format (should be 'user/repo')")
        
        # Check if repository exists
        try:
            api_url = f"https://api.github.com/repos/{repo}"
            timeout = self.config['github_timeout']
            
            response = self.session.get(api_url, timeout=timeout)
            
            if response.status_code == 200:
                repo_data = response.json()
                if repo_data.get('archived', False):
                    return ValidationResult("github_repo", True, "Repository exists but is archived", "warning")
                return ValidationResult("github_repo", True, "Repository exists and is accessible")
            elif response.status_code == 404:
                return ValidationResult("github_repo", False, "Repository not found")
            elif response.status_code == 403:
                # Rate limited or access forbidden
                return ValidationResult("github_repo", False, "GitHub API access limited", "warning")
            else:
                return ValidationResult("github_repo", False, f"GitHub API error: {response.status_code}", "warning")
                
        except requests.exceptions.Timeout:
            return ValidationResult("github_repo", False, "GitHub API request timed out", "warning")
        except requests.exceptions.ConnectionError:
            return ValidationResult("github_repo", False, "Connection to GitHub failed", "warning")
        except Exception as e:
            return ValidationResult("github_repo", False, f"GitHub validation error: {str(e)}", "warning")
    
    def validate_screenshot_urls(self, theme_data: Dict) -> List[ValidationResult]:
        """
        Validate all screenshot URLs in theme data.
        
        Args:
            theme_data: Theme data dictionary
            
        Returns:
            List of ValidationResult objects
        """
        results = []
        
        # Validate main screenshot
        main_screenshot = theme_data.get('screenshot-main', '')
        if main_screenshot:
            result = self.validate_url(main_screenshot)
            result.field = 'screenshot-main'
            results.append(result)
        else:
            results.append(ValidationResult('screenshot-main', False, "Main screenshot is required"))
        
        # Validate side screenshots
        side_screenshots = theme_data.get('screenshots-side', [])
        if isinstance(side_screenshots, list):
            if len(side_screenshots) > self.config['max_side_screenshots']:
                results.append(ValidationResult(
                    'screenshots-side', False, 
                    f"Too many side screenshots ({len(side_screenshots)}, max {self.config['max_side_screenshots']})"
                ))
            
            for i, url in enumerate(side_screenshots):
                if url:  # Skip empty URLs
                    result = self.validate_url(url)
                    result.field = f'screenshots-side[{i}]'
                    results.append(result)
        
        return results
    
    def validate_tags(self, theme_data: Dict, valid_tags: Optional[List[str]] = None) -> List[ValidationResult]:
        """
        Validate theme tags.
        
        Args:
            theme_data: Theme data dictionary
            valid_tags: Optional list of valid tag names
            
        Returns:
            List of ValidationResult objects
        """
        results = []
        tags = theme_data.get('tags', [])
        
        if not tags:
            results.append(ValidationResult('tags', False, "At least one tag is required"))
            return results
        
        if not isinstance(tags, list):
            results.append(ValidationResult('tags', False, "Tags must be a list"))
            return results
        
        # Check tag count
        if len(tags) < self.config['min_tag_count']:
            results.append(ValidationResult('tags', False, f"Minimum {self.config['min_tag_count']} tag(s) required"))
        
        if len(tags) > self.config['max_tag_count']:
            results.append(ValidationResult('tags', False, f"Maximum {self.config['max_tag_count']} tags allowed"))
        
        # Validate individual tags
        for tag in tags:
            if not tag or not tag.strip():
                results.append(ValidationResult('tags', False, "Empty tag found"))
                continue
            
            tag = tag.strip()
            
            # Check tag format (lowercase, underscores, alphanumeric)
            if not re.match(r'^[a-z0-9_]+$', tag):
                results.append(ValidationResult('tags', False, f"Invalid tag format: '{tag}' (use lowercase, numbers, underscores only)"))
            
            # Check against valid tags list if provided
            if valid_tags and tag not in valid_tags:
                results.append(ValidationResult('tags', False, f"Unknown tag: '{tag}'", "warning"))
        
        # Check for duplicates
        if len(tags) != len(set(tags)):
            duplicates = [tag for tag in set(tags) if tags.count(tag) > 1]
            results.append(ValidationResult('tags', False, f"Duplicate tags found: {duplicates}"))
        
        if not results:
            results.append(ValidationResult('tags', True, f"All {len(tags)} tags are valid"))
        
        return results
    
    def validate_required_fields(self, theme_data: Dict) -> List[ValidationResult]:
        """
        Validate that all required fields are present and non-empty.
        
        Args:
            theme_data: Theme data dictionary
            
        Returns:
            List of ValidationResult objects
        """
        results = []
        
        for field in self.config['required_fields']:
            value = theme_data.get(field)
            
            if value is None:
                results.append(ValidationResult(field, False, f"Required field '{field}' is missing"))
            elif isinstance(value, str) and not value.strip():
                results.append(ValidationResult(field, False, f"Required field '{field}' is empty"))
            elif isinstance(value, list) and not value:
                results.append(ValidationResult(field, False, f"Required field '{field}' is empty list"))
            else:
                results.append(ValidationResult(field, True, f"Required field '{field}' is present"))
        
        return results
    
    def validate_completion_status(self, theme_data: Dict) -> ValidationResult:
        """
        Determine the completion status of a theme based on validation results.
        
        Args:
            theme_data: Theme data dictionary
            
        Returns:
            ValidationResult with completion status
        """
        # Check required fields
        required_results = self.validate_required_fields(theme_data)
        missing_required = [r for r in required_results if not r.is_valid]
        
        if missing_required:
            return ValidationResult('completion_status', False, 'incomplete', 'info')
        
        # Check optional fields
        optional_missing = []
        for field in self.config['optional_fields']:
            value = theme_data.get(field)
            if not value or (isinstance(value, str) and not value.strip()):
                optional_missing.append(field)
        
        if optional_missing:
            return ValidationResult('completion_status', True, 'needs_review', 'info')
        
        return ValidationResult('completion_status', True, 'complete', 'info')
    
    def validate_theme_full(self, theme_data: Dict, valid_tags: Optional[List[str]] = None) -> List[ValidationResult]:
        """
        Perform comprehensive validation of a theme.
        
        Args:
            theme_data: Theme data dictionary
            valid_tags: Optional list of valid tag names
            
        Returns:
            List of all ValidationResult objects
        """
        results = []
        
        # Validate required fields
        results.extend(self.validate_required_fields(theme_data))
        
        # Validate tags
        results.extend(self.validate_tags(theme_data, valid_tags))
        
        # Validate repository
        repo = theme_data.get('repo', '')
        if repo:
            results.append(self.validate_github_repo(repo))
        
        # Validate screenshot URLs
        results.extend(self.validate_screenshot_urls(theme_data))
        
        # Determine completion status
        results.append(self.validate_completion_status(theme_data))
        
        return results
    
    def validate_theme_batch(self, themes_data: Dict[str, Dict], valid_tags: Optional[List[str]] = None) -> Dict[str, List[ValidationResult]]:
        """
        Validate multiple themes with concurrent processing.
        
        Args:
            themes_data: Dictionary mapping repo names to theme data
            valid_tags: Optional list of valid tag names
            
        Returns:
            Dictionary mapping repo names to validation results
        """
        results = {}
        max_workers = self.config['max_concurrent_validations']
        
        def validate_single(repo_theme_pair):
            repo, theme_data = repo_theme_pair
            return repo, self.validate_theme_full(theme_data, valid_tags)
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all validation tasks
            future_to_repo = {
                executor.submit(validate_single, (repo, theme_data)): repo 
                for repo, theme_data in themes_data.items()
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_repo):
                try:
                    repo, validation_results = future.result()
                    results[repo] = validation_results
                except Exception as e:
                    repo = future_to_repo[future]
                    results[repo] = [ValidationResult('validation', False, f"Validation error: {str(e)}")]
        
        return results
    
    def get_validation_summary(self, validation_results: Dict[str, List[ValidationResult]]) -> Dict:
        """
        Generate a summary of validation results.
        
        Args:
            validation_results: Dictionary mapping repo names to validation results
            
        Returns:
            Summary dictionary with counts and statistics
        """
        summary = {
            'total_themes': len(validation_results),
            'error_count': 0,
            'warning_count': 0,
            'themes_with_errors': [],
            'themes_with_warnings': [],
            'common_issues': {}
        }
        
        for repo, results in validation_results.items():
            has_errors = False
            has_warnings = False
            
            for result in results:
                if not result.is_valid:
                    if result.severity == 'error':
                        summary['error_count'] += 1
                        has_errors = True
                    elif result.severity == 'warning':
                        summary['warning_count'] += 1
                        has_warnings = True
                    
                    # Track common issues
                    issue_key = f"{result.field}:{result.message}"
                    summary['common_issues'][issue_key] = summary['common_issues'].get(issue_key, 0) + 1
            
            if has_errors:
                summary['themes_with_errors'].append(repo)
            if has_warnings:
                summary['themes_with_warnings'].append(repo)
        
        return summary
    
    def __del__(self):
        """Cleanup session on destruction."""
        if hasattr(self, 'session'):
            self.session.close()
