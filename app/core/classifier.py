# FILE: app/core/classifier.py
"""File classification logic"""
from pathlib import Path
from typing import Dict, List
import logging

logger = logging.getLogger("FileOrganizer")

class FileClassifier:
    """Classify files into categories"""
    
    EXTENSION_RULES = {
        "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp", ".ico"],
        "Documents": [".pdf", ".docx", ".doc", ".txt", ".odt", ".rtf"],
        "Spreadsheets": [".xlsx", ".xls", ".csv", ".ods"],
        "Presentations": [".pptx", ".ppt", ".odp"],
        "Videos": [".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm"],
        "Audio": [".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a", ".wma"],
        "Archives": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"],
        "Code": [".py", ".java", ".cpp", ".c", ".js", ".ts", ".html", ".css", ".php"],
        "Executables": [".exe", ".msi", ".dmg", ".app", ".deb", ".rpm"]
    }
    
    KEYWORD_RULES = {
        "Finance": ["invoice", "bill", "receipt", "payment", "transaction"],
        "Education": ["assignment", "homework", "project", "syllabus", "lecture"],
        "Work": ["report", "proposal", "meeting", "presentation"],
        "Personal": ["vacation", "family", "personal", "photo"]
    }
    
    def classify_by_extension(self, file: Path) -> str:
        """Classify file by extension"""
        suffix = file.suffix.lower()
        for category, extensions in self.EXTENSION_RULES.items():
            if suffix in extensions:
                return category
        return "Other"
    
    def classify_by_name(self, file: Path) -> str:
        """Classify file by name keywords"""
        name_lower = file.name.lower()
        for category, keywords in self.KEYWORD_RULES.items():
            if any(keyword in name_lower for keyword in keywords):
                return category
        return None
    
    def classify(self, file: Path, use_ai: bool = False) -> str:
        """Main classification method"""
        if use_ai:
            category = self.classify_by_name(file)
            if category:
                logger.info(f"AI classified '{file.name}' as {category}")
                return category
        
        category = self.classify_by_extension(file)
        logger.info(f"Classified '{file.name}' as {category}")
        return category