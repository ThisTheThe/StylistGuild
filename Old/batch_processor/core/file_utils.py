#!/usr/bin/env python3
"""
File Utils Module

Provides file I/O utilities, backup management, and path operations.
"""

import os
import shutil
import glob
import hashlib
from datetime import datetime
from typing import List, Optional, Dict, Tuple
from pathlib import Path
import tempfile
import zipfile

# Ensure we can import from the project root
import sys
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


class FileUtils:
    """
    Utility class for file operations, backup management, and path handling.
    """
    
    def __init__(self, config=None):
        """
        Initialize FileUtils with configuration.
        
        Args:
            config: Configuration object with paths and settings
        """
        if config is None:
            try:
                from shared.config import DEFAULT_CONFIG
                self.config = DEFAULT_CONFIG
            except ImportError:
                self.config = self._get_default_config()
        else:
            self.config = config
    
    def _get_default_config(self):
        """Default configuration if shared config not available."""
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        return {
            'backup_dir': os.path.join(project_root, 'backups'),
            'data_dir': os.path.join(project_root, 'data'),
            'temp_dir': tempfile.gettempdir(),
            'max_backup_age_days': 30,
            'max_backups_per_file': 10
        }
    
    def ensure_directory(self, directory_path: str, create_parents: bool = True) -> bool:
        """
        Ensure a directory exists, creating it if necessary.
        
        Args:
            directory_path: Path to directory
            create_parents: Whether to create parent directories
            
        Returns:
            True if directory exists or was created successfully
        """
        try:
            Path(directory_path).mkdir(parents=create_parents, exist_ok=True)
            return True
        except Exception as e:
            print(f"ERROR: Could not create directory '{directory_path}': {e}")
            return False
    
    def safe_filename(self, filename: str, max_length: int = 255) -> str:
        """
        Convert a string to a safe filename by removing/replacing unsafe characters.
        
        Args:
            filename: Original filename
            max_length: Maximum filename length
            
        Returns:
            Safe filename string
        """
        # Remove/replace unsafe characters
        unsafe_chars = '<>:"/\\|?*'
        safe_name = filename
        
        for char in unsafe_chars:
            safe_name = safe_name.replace(char, '_')
        
        # Remove leading/trailing dots and spaces
        safe_name = safe_name.strip('. ')
        
        # Limit length
        if len(safe_name) > max_length:
            name, ext = os.path.splitext(safe_name)
            max_name_length = max_length - len(ext)
            safe_name = name[:max_name_length] + ext
        
        # Ensure it's not empty
        if not safe_name:
            safe_name = "unnamed"
        
        return safe_name
    
    def get_file_hash(self, file_path: str, algorithm: str = 'md5') -> Optional[str]:
        """
        Calculate hash of a file.
        
        Args:
            file_path: Path to file
            algorithm: Hash algorithm ('md5', 'sha1', 'sha256')
            
        Returns:
            Hex digest of file hash or None if error
        """
        if not os.path.exists(file_path):
            return None
        
        try:
            hash_obj = hashlib.new(algorithm)
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_obj.update(chunk)
            return hash_obj.hexdigest()
        except Exception as e:
            print(f"ERROR: Could not calculate hash for '{file_path}': {e}")
            return None
    
    def files_are_identical(self, file1: str, file2: str) -> bool:
        """
        Check if two files are identical by comparing their hashes.
        
        Args:
            file1: Path to first file
            file2: Path to second file
            
        Returns:
            True if files are identical
        """
        if not (os.path.exists(file1) and os.path.exists(file2)):
            return False
        
        # Quick size check first
        if os.path.getsize(file1) != os.path.getsize(file2):
            return False
        
        # Compare hashes
        hash1 = self.get_file_hash(file1)
        hash2 = self.get_file_hash(file2)
        
        return hash1 is not None and hash1 == hash2
    
    def create_timestamped_backup(self, source_path: str, backup_dir: Optional[str] = None) -> Optional[str]:
        """
        Create a timestamped backup of a file.
        
        Args:
            source_path: Path to file to backup
            backup_dir: Directory to store backup (uses config default if None)
            
        Returns:
            Path to backup file or None if failed
        """
        if not os.path.exists(source_path):
            print(f"WARNING: Source file '{source_path}' does not exist")
            return None
        
        backup_dir = backup_dir or self.config['backup_dir']
        
        if not self.ensure_directory(backup_dir):
            return None
        
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            source_filename = os.path.basename(source_path)
            name, ext = os.path.splitext(source_filename)
            backup_filename = f"{name}_{timestamp}{ext}"
            backup_path = os.path.join(backup_dir, backup_filename)
            
            shutil.copy2(source_path, backup_path)
            print(f"Backup created: '{backup_path}'")
            return backup_path
            
        except Exception as e:
            print(f"ERROR: Could not create backup: {e}")
            return None
    
    def rotate_backups(self, file_pattern: str, max_backups: int = None, backup_dir: Optional[str] = None) -> int:
        """
        Remove old backups, keeping only the most recent ones.
        
        Args:
            file_pattern: Pattern to match backup files (e.g., "theme_*.json")
            max_backups: Maximum number of backups to keep
            backup_dir: Directory containing backups
            
        Returns:
            Number of files removed
        """
        backup_dir = backup_dir or self.config['backup_dir']
        max_backups = max_backups or self.config['max_backups_per_file']
        
        if not os.path.exists(backup_dir):
            return 0
        
        try:
            # Find matching backup files
            search_pattern = os.path.join(backup_dir, file_pattern)
            backup_files = glob.glob(search_pattern)
            
            if len(backup_files) <= max_backups:
                return 0
            
            # Sort by modification time (newest first)
            backup_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            
            # Remove excess backups
            files_to_remove = backup_files[max_backups:]
            removed_count = 0
            
            for file_path in files_to_remove:
                try:
                    os.remove(file_path)
                    removed_count += 1
                except Exception as e:
                    print(f"WARNING: Could not remove backup '{file_path}': {e}")
            
            if removed_count > 0:
                print(f"Rotated backups: removed {removed_count} old backup(s)")
            
            return removed_count
            
        except Exception as e:
            print(f"ERROR: Could not rotate backups: {e}")
            return 0
    
    def cleanup_old_backups(self, max_age_days: int = None, backup_dir: Optional[str] = None) -> int:
        """
        Remove backup files older than specified age.
        
        Args:
            max_age_days: Maximum age in days
            backup_dir: Directory containing backups
            
        Returns:
            Number of files removed
        """
        backup_dir = backup_dir or self.config['backup_dir']
        max_age_days = max_age_days or self.config['max_backup_age_days']
        
        if not os.path.exists(backup_dir):
            return 0
        
        try:
            cutoff_time = datetime.now().timestamp() - (max_age_days * 24 * 60 * 60)
            removed_count = 0
            
            for filename in os.listdir(backup_dir):
                file_path = os.path.join(backup_dir, filename)
                
                if not os.path.isfile(file_path):
                    continue
                
                file_time = os.path.getmtime(file_path)
                if file_time < cutoff_time:
                    try:
                        os.remove(file_path)
                        removed_count += 1
                    except Exception as e:
                        print(f"WARNING: Could not remove old backup '{file_path}': {e}")
            
            if removed_count > 0:
                print(f"Cleaned up {removed_count} old backup file(s)")
            
            return removed_count
            
        except Exception as e:
            print(f"ERROR: Could not cleanup old backups: {e}")
            return 0
    
    def create_archive_backup(self, source_paths: List[str], archive_name: str, backup_dir: Optional[str] = None) -> Optional[str]:
        """
        Create a ZIP archive backup of multiple files/directories.
        
        Args:
            source_paths: List of paths to backup
            archive_name: Name for the archive file (without extension)
            backup_dir: Directory to store archive
            
        Returns:
            Path to created archive or None if failed
        """
        backup_dir = backup_dir or self.config['backup_dir']
        
        if not self.ensure_directory(backup_dir):
            return None
        
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_name = self.safe_filename(archive_name)
            archive_filename = f"{safe_name}_{timestamp}.zip"
            archive_path = os.path.join(backup_dir, archive_filename)
            
            with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for source_path in source_paths:
                    if os.path.exists(source_path):
                        if os.path.isfile(source_path):
                            zipf.write(source_path, os.path.basename(source_path))
                        elif os.path.isdir(source_path):
                            for root, dirs, files in os.walk(source_path):
                                for file in files:
                                    file_path = os.path.join(root, file)
                                    arcname = os.path.relpath(file_path, os.path.dirname(source_path))
                                    zipf.write(file_path, arcname)
                    else:
                        print(f"WARNING: Source path '{source_path}' does not exist, skipping")
            
            print(f"Archive backup created: '{archive_path}'")
            return archive_path
            
        except Exception as e:
            print(f"ERROR: Could not create archive backup: {e}")
            return None
    
    def get_backup_info(self, backup_dir: Optional[str] = None) -> Dict[str, any]:
        """
        Get information about existing backups.
        
        Args:
            backup_dir: Directory containing backups
            
        Returns:
            Dictionary with backup statistics and file info
        """
        backup_dir = backup_dir or self.config['backup_dir']
        
        info = {
            'backup_dir': backup_dir,
            'total_files': 0,
            'total_size_bytes': 0,
            'oldest_backup': None,
            'newest_backup': None,
            'files_by_type': {}
        }
        
        if not os.path.exists(backup_dir):
            return info
        
        try:
            backup_files = []
            
            for filename in os.listdir(backup_dir):
                file_path = os.path.join(backup_dir, filename)
                
                if not os.path.isfile(file_path):
                    continue
                
                file_stat = os.stat(file_path)
                file_info = {
                    'path': file_path,
                    'name': filename,
                    'size': file_stat.st_size,
                    'modified': file_stat.st_mtime
                }
                
                backup_files.append(file_info)
                
                # Update totals
                info['total_files'] += 1
                info['total_size_bytes'] += file_stat.st_size
                
                # Track file types
                ext = os.path.splitext(filename)[1].lower()
                info['files_by_type'][ext] = info['files_by_type'].get(ext, 0) + 1
            
            if backup_files:
                # Sort by modification time
                backup_files.sort(key=lambda x: x['modified'])
                info['oldest_backup'] = backup_files[0]
                info['newest_backup'] = backup_files[-1]
                
                # Convert timestamps to readable format
                info['oldest_backup']['modified_str'] = datetime.fromtimestamp(info['oldest_backup']['modified']).strftime('%Y-%m-%d %H:%M:%S')
                info['newest_backup']['modified_str'] = datetime.fromtimestamp(info['newest_backup']['modified']).strftime('%Y-%m-%d %H:%M:%S')
            
            return info
            
        except Exception as e:
            print(f"ERROR: Could not get backup info: {e}")
            return info
    
    def atomic_write(self, file_path: str, content: str, encoding: str = 'utf-8') -> bool:
        """
        Atomically write content to a file using a temporary file.
        
        Args:
            file_path: Target file path
            content: Content to write
            encoding: File encoding
            
        Returns:
            True if successful
        """
        try:
            # Ensure directory exists
            directory = os.path.dirname(file_path)
            if directory and not self.ensure_directory(directory):
                return False
            
            # Write to temporary file first
            temp_path = file_path + '.tmp'
            
            with open(temp_path, 'w', encoding=encoding) as f:
                f.write(content)
                f.flush()
                os.fsync(f.fileno())  # Ensure data is written to disk
            
            # Atomic move
            if os.name == 'nt':  # Windows
                if os.path.exists(file_path):
                    os.remove(file_path)
            
            shutil.move(temp_path, file_path)
            print(f"Atomically wrote '{file_path}'")
            return True
            
        except Exception as e:
            # Clean up temp file if it exists
            temp_path = file_path + '.tmp'
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except:
                    pass
            
            print(f"ERROR: Could not atomically write '{file_path}': {e}")
            return False
    
    def find_duplicate_files(self, directory: str, extensions: List[str] = None) -> Dict[str, List[str]]:
        """
        Find duplicate files in a directory by comparing hashes.
        
        Args:
            directory: Directory to search
            extensions: List of file extensions to check (e.g., ['.json', '.md'])
            
        Returns:
            Dictionary mapping hash to list of file paths with that hash
        """
        if not os.path.exists(directory):
            return {}
        
        file_hashes = {}
        
        try:
            for root, dirs, files in os.walk(directory):
                for file in files:
                    if extensions:
                        file_ext = os.path.splitext(file)[1].lower()
                        if file_ext not in extensions:
                            continue
                    
                    file_path = os.path.join(root, file)
                    file_hash = self.get_file_hash(file_path)
                    
                    if file_hash:
                        if file_hash not in file_hashes:
                            file_hashes[file_hash] = []
                        file_hashes[file_hash].append(file_path)
            
            # Return only duplicates (hashes with more than one file)
            duplicates = {h: paths for h, paths in file_hashes.items() if len(paths) > 1}
            
            if duplicates:
                print(f"Found {len(duplicates)} sets of duplicate files")
            
            return duplicates
            
        except Exception as e:
            print(f"ERROR: Could not find duplicate files: {e}")
            return {}
    
    def get_directory_size(self, directory: str) -> Tuple[int, int]:
        """
        Calculate total size and file count of a directory.
        
        Args:
            directory: Directory to analyze
            
        Returns:
            Tuple of (total_size_bytes, file_count)
        """
        if not os.path.exists(directory):
            return 0, 0
        
        total_size = 0
        file_count = 0
        
        try:
            for root, dirs, files in os.walk(directory):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        total_size += os.path.getsize(file_path)
                        file_count += 1
                    except (OSError, IOError):
                        # Skip files we can't access
                        continue
            
            return total_size, file_count
            
        except Exception as e:
            print(f"ERROR: Could not calculate directory size: {e}")
            return 0, 0
    
    def format_file_size(self, size_bytes: int) -> str:
        """
        Format file size in human-readable format.
        
        Args:
            size_bytes: Size in bytes
            
        Returns:
            Formatted size string
        """
        if size_bytes == 0:
            return "0 B"
        
        units = ['B', 'KB', 'MB', 'GB', 'TB']
        unit_index = 0
        size = float(size_bytes)
        
        while size >= 1024 and unit_index < len(units) - 1:
            size /= 1024
            unit_index += 1
        
        if unit_index == 0:
            return f"{int(size)} {units[unit_index]}"
        else:
            return f"{size:.1f} {units[unit_index]}"
