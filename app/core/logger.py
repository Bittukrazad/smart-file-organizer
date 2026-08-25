# ============================================
# FILE: app/core/logger.py (FIXED - writes to %LOCALAPPDATA%)
# ============================================

"""Logging configuration with Unicode support"""
import logging
import os
import sys
from pathlib import Path
from datetime import datetime


def get_log_dir() -> Path:
    """
    Return a writable directory for logs, independent of where the app
    is installed. On Windows this resolves to:
        C:\\Users\\<user>\\AppData\\Local\\FileOrgPro\\SmartFileOrganizerPro\\logs
    which is always writable by the current user, even when the app
    itself is installed under C:\\Program Files (protected, non-writable
    for standard users).

    On macOS/Linux it falls back to a sensible per-user location too,
    in case the app is ever run there.
    """
    app_name = "SmartFileOrganizerPro"
    org_name = "FileOrgPro"

    if sys.platform == "win32":
        base = os.getenv("LOCALAPPDATA")
        if not base:
            # Extremely rare fallback if the env var is missing
            base = str(Path.home() / "AppData" / "Local")
        log_dir = Path(base) / org_name / app_name / "logs"
    elif sys.platform == "darwin":
        log_dir = Path.home() / "Library" / "Logs" / app_name
    else:
        # Linux / other: follow XDG convention
        base = os.getenv("XDG_STATE_HOME", str(Path.home() / ".local" / "state"))
        log_dir = Path(base) / app_name / "logs"

    return log_dir


def setup_logger():
    """Setup application logger with Unicode support for Windows"""

    # Create logs directory in a user-writable location (not the install dir)
    log_dir = get_log_dir()
    log_dir.mkdir(parents=True, exist_ok=True)

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

    logger.info(f"Logger initialized successfully. Log directory: {log_dir}")

    return logger