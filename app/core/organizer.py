# FILE: app/core/organizer.py
"""Core file organization logic"""
from pathlib import Path
import shutil
import logging
from typing import Tuple
from .classifier import FileClassifier
from .duplicate_detector import DuplicateDetector
from .config import AppConfig
from .database import Database
from .content_analyzer import ContentAnalyzer
from .rules_engine import RulesEngine


logger = logging.getLogger("FileOrganizer")

class FileOrganizer:
    """Core file organization logic with advanced features"""
    
    # UPDATE the __init__ method:
    def __init__(self, config: AppConfig, database: Database = None,
                content_analyzer: ContentAnalyzer = None,
                rules_engine: RulesEngine = None):
        self.config = config
        self.classifier = FileClassifier()
        self.duplicate_detector = DuplicateDetector()
        self.database = database or Database()
        self.content_analyzer = content_analyzer
        self.rules_engine = rules_engine
        self.stats = {
            "processed": 0,
            "duplicates": 0,
            "errors": 0
        }
        self.current_session_id = None
    
    # UPDATE organize_file method to log to database:
    def organize_file(self, file_path: Path) -> Tuple[bool, str, str, int]:
        """
        Organize a single file with database logging, content analysis, and custom rules
        Returns: (success, message, category, file_size_bytes)
        """
        original_path = str(file_path)
        file_size = 0
        file_hash = None
        
        try:
            if not file_path.exists() or not file_path.is_file():
                self.database.log_operation(
                    filename=file_path.name,
                    original_path=original_path,
                    destination_path="",
                    category="",
                    operation_type="organize",
                    success=False,
                    error_message="File not found"
                )
                return False, "File not found", "", 0
            
            # Get file size
            file_size = file_path.stat().st_size
            
            # Check file size limit
            size_mb = file_size / (1024 * 1024)
            if size_mb > self.config.max_file_size_mb:
                msg = f"File too large ({size_mb:.1f}MB)"
                logger.warning(f"{file_path.name}: {msg}")
                
                self.database.log_operation(
                    filename=file_path.name,
                    original_path=original_path,
                    destination_path="",
                    category="",
                    operation_type="organize",
                    file_size=file_size,
                    success=False,
                    error_message=msg
                )
                return False, msg, "", file_size
            
            # Check for duplicates with database
            if self.config.enable_duplicates:
                file_hash = self.duplicate_detector.compute_hash(file_path)
                is_dup = self.database.add_duplicate_hash(file_hash, original_path, file_size)
                
                if is_dup:
                    dest_folder = self.config.duplicate_folder
                    dest_folder.mkdir(parents=True, exist_ok=True)
                    
                    dest_path = self._get_unique_path(dest_folder / file_path.name)
                    shutil.move(str(file_path), str(dest_path))
                    
                    self.stats["duplicates"] += 1
                    self.stats["processed"] += 1
                    
                    # Log to database
                    self.database.log_operation(
                        filename=file_path.name,
                        original_path=original_path,
                        destination_path=str(dest_path),
                        category="Duplicates",
                        operation_type="duplicate",
                        file_size=file_size,
                        file_hash=file_hash,
                        success=True
                    )
                    
                    # Update statistics
                    self.database.update_statistics(
                        category="Duplicates",
                        files_count=1,
                        total_size=file_size,
                        duplicates=1
                    )
                    
                    return True, "Duplicate detected", "Duplicates", file_size
            
            # ENHANCED CLASSIFICATION WITH 3-TIER PRIORITY SYSTEM
            category = None
            metadata = None
            
            # 1. HIGHEST PRIORITY: Check custom rules first
            if self.rules_engine:
                # Get metadata if content analyzer is available
                if self.content_analyzer:
                    try:
                        metadata = self.content_analyzer.analyze_file(file_path)
                    except Exception as e:
                        logger.warning(f"Content analysis failed for {file_path.name}: {e}")
                        metadata = None
                
                # Apply custom rules
                custom_target = self.rules_engine.apply_rules(file_path, metadata)
                if custom_target:
                    category = custom_target
                    logger.info(f"Custom rule applied: {file_path.name} -> {category}")
            
            # 2. MEDIUM PRIORITY: Use content analysis for smarter classification
            if not category and self.content_analyzer and self.config.ai_classification:
                try:
                    # Reuse metadata if already analyzed, otherwise analyze now
                    if metadata is None:
                        metadata = self.content_analyzer.analyze_file(file_path)
                    
                    # Check if content analyzer suggests a category
                    if metadata and metadata.get("suggested_category"):
                        category = metadata["suggested_category"]
                        logger.info(f"Content-based classification: {file_path.name} -> {category}")
                    else:
                        # AI classification enabled but no specific suggestion
                        category = self.classifier.classify(file_path, True)
                except Exception as e:
                    logger.warning(f"Content analysis failed for {file_path.name}: {e}")
                    # Fall through to standard classification
            
            # 3. LOWEST PRIORITY: Fall back to standard classification
            if not category:
                category = self.classifier.classify(file_path, self.config.ai_classification)
                logger.debug(f"Standard classification: {file_path.name} -> {category}")
            
            # Move file to destination
            dest_folder = self.config.organized_folder / category
            dest_folder.mkdir(parents=True, exist_ok=True)
            
            dest_path = self._get_unique_path(dest_folder / file_path.name)
            shutil.move(str(file_path), str(dest_path))
            
            self.stats["processed"] += 1
            
            # Log to database
            self.database.log_operation(
                filename=file_path.name,
                original_path=original_path,
                destination_path=str(dest_path),
                category=category,
                operation_type="organize",
                file_size=file_size,
                file_hash=file_hash,
                success=True
            )
            
            # Update statistics
            self.database.update_statistics(
                category=category,
                files_count=1,
                total_size=file_size
            )
            
            logger.info(f"Organized {file_path.name} to {category}")
            return True, f"Moved to {category}", category, file_size
            
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Error organizing {file_path}: {e}", exc_info=True)
            
            # Log error to database
            self.database.log_operation(
                filename=file_path.name,
                original_path=original_path,
                destination_path="",
                category="",
                operation_type="organize",
                file_size=file_size,
                file_hash=file_hash,
                success=False,
                error_message=str(e)
            )
            
            # Update error statistics
            self.database.update_statistics(
                category="Errors",
                errors=1
            )
            
            return False, f"Error: {str(e)}", "", file_size
    
    def _get_unique_path(self, path: Path) -> Path:
        """Generate unique file path if file exists"""
        if not path.exists():
            return path
        
        stem = path.stem
        suffix = path.suffix
        parent = path.parent
        counter = 1
        
        while True:
            new_path = parent / f"{stem}_{counter}{suffix}"
            if not new_path.exists():
                return new_path
            counter += 1
    
    def get_stats(self) -> dict:
        """Get organization statistics"""
        return self.stats.copy()
