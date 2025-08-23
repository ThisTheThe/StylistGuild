#!/usr/bin/env python3
"""
Screenshot Manager Module
Handles validation, caching, and management of theme screenshots
"""

import os
import requests
import hashlib
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from urllib.parse import urlparse, urljoin
import re


class ScreenshotManager:
    def __init__(self, cache_dir: str = "screenshot_cache", timeout: int = 10):
        """
        Initialize the ScreenshotManager
        
        Args:
            cache_dir: Directory to store cached screenshots
            timeout: Request timeout in seconds
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def validate_screenshot_urls(self, urls_list: List[str], 
                                check_accessibility: bool = True) -> Dict[str, Any]:
        """
        Validate a list of screenshot URLs
        
        Args:
            urls_list: List of URLs to validate
            check_accessibility: Whether to actually fetch URLs to check accessibility
            
        Returns:
            Dict: Validation results with valid/invalid URLs and details
        """
        results = {
            "valid_urls": [],
            "invalid_urls": [],
            "accessible_urls": [],
            "inaccessible_urls": [],
            "format_errors": [],
            "access_errors": []
        }
        
        for url in urls_list:
            # Basic format validation
            if self._is_valid_url_format(url):
                results["valid_urls"].append(url)
                
                # Check accessibility if requested
                if check_accessibility:
                    accessibility_result = self._check_url_accessibility(url)
                    if accessibility_result["accessible"]:
                        results["accessible_ur