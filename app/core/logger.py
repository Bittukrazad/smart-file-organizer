# ============================================
# FILE: app/core/logger.py (FIXED)
# ============================================

"""Logging configuration with Unicode support"""
import logging
import sys
from pathlib import Path
from datetime import datetime


def setup_logger():
    """Setup application logger with Unicode support for Windows"""
    
    # Create logs directory
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Log file name with timestamp
    log_file = log_dir / f"file_organizer_{datetime.now():%Y%m%d}.log"
    
    # Create logger
    logger = logging.getLogger("FileOrganizer")
    logger.setLevel(logging.DEBUG)
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # File handler (UTF-8 encoding for emojis)
    file_handler = logging.FileHandler(
        log_file, 
        mode='a', 
        encoding='utf-8'  # UTF-8 for file
    )
    file_handler.setLevel(logging.DEBUG)
    
    # Console handler with proper encoding
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    # Try to set UTF-8 encoding for Windows console
    try:
        if sys.platform == 'win32':
            # Force UTF-8 output on Windows
            sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass  # If reconfigure fails, continue with default
    
    # Formatter WITHOUT emojis for better compatibility
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    logger.info("Logger initialized successfully")
    
    return logger