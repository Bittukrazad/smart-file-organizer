# FILE: app/core/duplicate_detector.py
"""Duplicate file detection"""
import hashlib
from pathlib import Path
from typing import Set, Dict, Tuple
import logging

logger = logging.getLogger("FileOrganizer")

class DuplicateDetector:
    """Detect duplicate files using SHA-256 hashing"""
    
    def __init__(self):
        self._hashes: Set[str] = set()
        self._file_map: Dict[str, Path] = {}
    
    def compute_hash(self, file_path: Path) -> str:
        """Compute SHA-256 hash of file"""
        hasher = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception as e:
            logger.error(f"Error hashing {file_path}: {e}")
            raise
    
    def is_duplicate(self, file_path: Path) -> Tuple[bool, Path]:
        """Check if file is duplicate. Returns (is_dup, original_path)"""
        try:
            file_hash = self.compute_hash(file_path)
            
            if file_hash in self._hashes:
                original = self._file_map.get(file_hash)
                logger.warning(f"Duplicate detected: {file_path.name}")
                return True, original
            
            self._hashes.add(file_hash)
            self._file_map[file_hash] = file_path
            return False, None
            
        except Exception as e:
            logger.error(f"Error checking duplicate for {file_path}: {e}")
            return False, None
    
    def clear(self):
        """Clear hash cache"""
        self._hashes.clear()
        self._file_map.clear()