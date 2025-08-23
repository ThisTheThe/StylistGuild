#!/usr/bin/env python3
"""
JSON Validator Module
Validates theme JSON data against expected schemas
"""

import json
import re
from typing import Dict, List, Any, Optional, Union
from urllib.parse import urlparse


class JsonValidator:
    def __init__(self):
        """Initialize the JsonValidator with predefined schemas"""
        self.official_schema = self._get_official_schema()
        self.addon_schema = self._get_addon_schema()
    
    def _get_official_schema(self) -> Dict[str, Any]:
        """
        Define the expected schema for official theme JSON entries
        
        Returns:
            Dict: Schema definition
        """
        return {
            "required_fields": ["name", "author", "repo", "screenshot", "modes"],
            "field_types": {
                "name": str,
                "author": str,
                "repo": str,
                "screenshot": str,
                "modes": list
            },
            "field_constraints": {
                "modes": lambda x: all(mode in ["dark", "light"] for mode in x) and len(x) > 0,
                "repo": lambda x: self._is_valid_github_repo(x),
                "name": lambda x: len(x.strip()) > 0,
                "author": lambda x: len(x.strip()) > 0,
                "screenshot": lambda x: len(x.strip()) > 0
            }
        }
    
    def _get_addon_schema(self) -> Dict[str, Any]:
        """
        Define the expected schema for addon theme JSON entries
        
        Returns:
            Dict: Schema definition
        """
        return {
            "required_fields": ["repo", "screenshot-main", "screenshots-side", "tags"],
            "field_types": {
                "repo": str,
                "screenshot-main": str,
                "screenshots-side": list,
                "tags": list
            },
            "field_constraints": {
                "repo": lambda x: self._is_valid_github_repo(x),
                "screenshot-main": lambda x: isinstance(x, str),  # Can be empty
                "screenshots-side": lambda x: all(isinstance(url, str) for url in x),
                "tags": lambda x: all(isinstance(tag, str) and len(tag.strip()) > 0 for tag in x)
            }
        }
    
    def _is_valid_github_repo(self, repo_string: str) -> bool:
        """
        Validate if a string follows the GitHub repo format (username/repository)
        
        Args:
            repo_string: String to validate
            
        Returns:
            bool: True if valid GitHub repo format
        """
        if not isinstance(repo_string, str):
            return False
        
        # Pattern: username/repository (allowing alphanumeric, hyphens, underscores, dots)
        pattern = r'^[a-zA-Z0-9._-]+/[a-zA-Z0-9._-]+$'
        return bool(re.match(pattern, repo_string))
    
    def _is_valid_url(self, url_string: str) -> bool:
        """
        Basic URL validation
        
        Args:
            url_string: String to validate as URL
            
        Returns:
            bool: True if appears to be a valid URL
        """
        if not isinstance(url_string, str) or len(url_string) == 0:
            return False
        
        try:
            result = urlparse(url_string)
            return all([result.scheme, result.netloc])
        except:
            return False
    
    def validate_entry_schema(self, entry: Dict[str, Any], schema_type: str) -> Dict[str, Any]:
        """
        Validate a single entry against the specified schema
        
        Args:
            entry: Dictionary to validate
            schema_type: "official" or "addon"
            
        Returns:
            Dict: Validation results with is_valid, errors, warnings
        """
        schema = self.official_schema if schema_type == "official" else self.addon_schema
        
        result = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "missing_fields": [],
            "type_errors": [],
            "constraint_violations": []
        }
        
        # Check required fields
        for field in schema["required_fields"]:
            if field not in entry:
                result["missing_fields"].append(field)
                result["is_valid"] = False
        
        # Check field types and constraints
        for field, value in entry.items():
            # Check type
            if field in schema["field_types"]:
                expected_type = schema["field_types"][field]
                if not isinstance(value, expected_type):
                    result["type_errors"].append(f"Field '{field}' should be {expected_type.__name__}, got {type(value).__name__}")
                    result["is_valid"] = False
                
                # Check constraints
                if field in schema["field_constraints"]:
                    try:
                        constraint_func = schema["field_constraints"][field]
                        if not constraint_func(value):
                            result["constraint_violations"].append(f"Field '{field}' violates constraint")
                            result["is_valid"] = False
                    except Exception as e:
                        result["constraint_violations"].append(f"Error checking constraint for '{field}': {str(e)}")
                        result["is_valid"] = False
        
        # Compile all errors
        result["errors"] = result["missing_fields"] + result["type_errors"] + result["constraint_violations"]
        
        return result
    
    def validate_official_schema(self, data: Union[List[Dict], Dict]) -> Dict[str, Any]:
        """
        Validate official theme JSON data
        
        Args:
            data: Single entry dict or list of entry dicts
            
        Returns:
            Dict: Comprehensive validation results
        """
        if isinstance(data, dict):
            data = [data]
        
        results = {
            "is_valid": True,
            "total_entries": len(data),
            "valid_entries": 0,
            "invalid_entries": 0,
            "entry_results": [],
            "summary_errors": []
        }
        
        for i, entry in enumerate(data):
            entry_result = self.validate_entry_schema(entry, "official")
            entry_result["index"] = i
            entry_result["repo"] = entry.get("repo", f"entry_{i}")
            
            results["entry_results"].append(entry_result)
            
            if entry_result["is_valid"]:
                results["valid_entries"] += 1
            else:
                results["invalid_entries"] += 1
                results["is_valid"] = False
        
        return results
    
    def validate_addon_schema(self, data: Union[List[Dict], Dict]) -> Dict[str, Any]:
        """
        Validate addon theme JSON data
        
        Args:
            data: Single entry dict or list of entry dicts
            
        Returns:
            Dict: Comprehensive validation results
        """
        if isinstance(data, dict):
            data = [data]
        
        results = {
            "is_valid": True,
            "total_entries": len(data),
            "valid_entries": 0,
            "invalid_entries": 0,
            "entry_results": [],
            "summary_errors": []
        }
        
        for i, entry in enumerate(data):
            entry_result = self.validate_entry_schema(entry, "addon")
            entry_result["index"] = i
            entry_result["repo"] = entry.get("repo", f"entry_{i}")
            
            results["entry_results"].append(entry_result)
            
            if entry_result["is_valid"]:
                results["valid_entries"] += 1
            else:
                results["invalid_entries"] += 1
                results["is_valid"] = False
        
        return results
    
    def check_required_fields(self, entry: Dict[str, Any], schema_type: str) -> List[str]:
        """
        Check for missing required fields in an entry
        
        Args:
            entry: Dictionary to check
            schema_type: "official" or "addon"
            
        Returns:
            List[str]: List of missing required field names
        """
        schema = self.official_schema if schema_type == "official" else self.addon_schema
        missing_fields = []
        
        for field in schema["required_fields"]:
            if field not in entry or entry[field] is None:
                missing_fields.append(field)
        
        return missing_fields
    
    def validate_url_fields(self, entry: Dict[str, Any], schema_type: str) -> Dict[str, List[str]]:
        """
        Validate URL fields in theme entries
        
        Args:
            entry: Dictionary to validate
            schema_type: "official" or "addon"
            
        Returns:
            Dict: Results with valid_urls and invalid_urls lists
        """
        result = {"valid_urls": [], "invalid_urls": []}
        
        if schema_type == "official":
            # Check screenshot field
            if "screenshot" in entry:
                url = entry["screenshot"]
                # For official, screenshot might just be a filename
                if url and (self._is_valid_url(url) or url.endswith(('.png', '.jpg', '.jpeg', '.gif'))):
                    result["valid_urls"].append(("screenshot", url))
                else:
                    result["invalid_urls"].append(("screenshot", url))
        
        elif schema_type == "addon":
            # Check screenshot-main
            if "screenshot-main" in entry and entry["screenshot-main"]:
                url = entry["screenshot-main"]
                if self._is_valid_url(url) or url.endswith(('.png', '.jpg', '.jpeg', '.gif')):
                    result["valid_urls"].append(("screenshot-main", url))
                else:
                    result["invalid_urls"].append(("screenshot-main", url))
            
            # Check screenshots-side
            if "screenshots-side" in entry:
                for i, url in enumerate(entry["screenshots-side"]):
                    if self._is_valid_url(url):
                        result["valid_urls"].append((f"screenshots-side[{i}]", url))
                    else:
                        result["invalid_urls"].append((f"screenshots-side[{i}]", url))
        
        return result
    
    def print_validation_report(self, results: Dict[str, Any], schema_type: str):
        """
        Print a formatted validation report
        
        Args:
            results: Results from validate_official_schema or validate_addon_schema
            schema_type: "official" or "addon"
        """
        print("=" * 60)
        print(f"{schema_type.upper()} THEME JSON VALIDATION REPORT")
        print("=" * 60)
        print(f"Total entries: {results['total_entries']}")
        print(f"Valid entries: {results['valid_entries']}")
        print(f"Invalid entries: {results['invalid_entries']}")
        print(f"Overall valid: {'✓' if results['is_valid'] else '✗'}")
        print()
        
        if results['invalid_entries'] > 0:
            print("VALIDATION ERRORS:")
            print("-" * 40)
            for entry_result in results['entry_results']:
                if not entry_result['is_valid']:
                    repo = entry_result['repo']
                    print(f"\n{repo}:")
                    for error in entry_result['errors']:
                        print(f"  ✗ {error}")
        
        if results['is_valid']:
            print("All entries passed validation! ✓")
        
        print("=" * 60)
    
    def get_validation_summary(self, data: Union[List[Dict], Dict], schema_type: str) -> str:
        """
        Get a brief validation summary string
        
        Args:
            data: Theme data to validate
            schema_type: "official" or "addon"
            
        Returns:
            str: Summary string
        """
        if schema_type == "official":
            results = self.validate_official_schema(data)
        else:
            results = self.validate_addon_schema(data)
        
        status = "VALID" if results['is_valid'] else "INVALID"
        return f"{status}: {results['valid_entries']}/{results['total_entries']} entries passed validation"


# Example usage and testing
if __name__ == "__main__":
    validator = JsonValidator()
    
    # Test official entry
    official_test = {
        "name": "Atom",
        "author": "kognise",
        "repo": "kognise/obsidian-atom",
        "screenshot": "screenshot-hybrid.png",
        "modes": ["dark", "light"]
    }
    
    # Test addon entry
    addon_test = {
        "repo": "kognise/obsidian-atom",
        "screenshot-main": "screenshot-hybrid.png",
        "screenshots-side": [
            "https://example.com/screenshot1.png",
            "https://example.com/screenshot2.png"
        ],
        "tags": ["dark", "minimal"]
    }
    
    # Validate entries
    print("Testing official entry validation:")
    official_results = validator.validate_official_schema(official_test)
    validator.print_validation_report(official_results, "official")
    
    print("\n" + "="*60 + "\n")
    
    print("Testing addon entry validation:")
    addon_results = validator.validate_addon_schema(addon_test)
    validator.print_validation_report(addon_results, "addon")
