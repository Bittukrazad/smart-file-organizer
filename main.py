
# FILE: main.py

"""
Smart File Organizer Pro - Modern Automated File Management System
Version: 2.1.0
"""
import sys
import os
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

# IMPORTANT: Set Windows taskbar icon (must be before QApplication)
if sys.platform == 'win32':
    try:
        import ctypes
        from pathlib import Path
        
        # Tell Windows this is a separate app (not Python)
        myappid = 'smart file organizer pro'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        
        # CRITICAL: Register icon for notifications
        # This makes notifications show your custom icon
        icon_path = Path(__file__).parent / "app" / "resources" / "icon.png"
        if icon_path.exists():
            # Convert path to absolute Windows path
            abs_icon_path = str(icon_path.resolve())
            print(f"Registering notification icon: {abs_icon_path}")
            
    except Exception as e:
        print(f"Could not set AppUserModelID: {e}")

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.ui.main_window import MainWindow
from app.core.logger import setup_logger


def set_application_icon(app):
    """Set application icon for all windows"""
    # Try multiple icon paths
    icon_paths = [
        Path(__file__).parent / "app" / "resources" / "icon.png",
        Path(__file__).parent / "resources" / "icon.png",
        Path("app/resources/icon.png"),
        Path("resources/icon.png"),
        Path("icon.png"),
    ]
    
    for icon_path in icon_paths:
        if icon_path.exists():
            try:
                icon = QIcon(str(icon_path))
                if not icon.isNull():
                    app.setWindowIcon(icon)
                    print(f"✅ Application icon set: {icon_path}")
                    return True
            except Exception as e:
                print(f"⚠️ Failed to load icon from {icon_path}: {e}")
    
    print("⚠️ No icon file found, using default")
    return False


def main():
    """Main application entry point"""
    # Setup logging
    setup_logger()
    
    # Enable high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("Smart File Organizer Pro")
    app.setOrganizationName("FileOrgPro")
    app.setApplicationDisplayName("Smart File Organizer Pro")
    app.setStyle("Fusion")
    
    # Set application icon (CRITICAL for taskbar)
    icon_set = set_application_icon(app)
    
    if not icon_set:
        print("WARNING: Could not set application icon - taskbar may show Python icon")
    
    # Apply modern dark theme
    from app.ui.theme import apply_dark_theme
    apply_dark_theme(app)
    
    # Create and show main window
    window = MainWindow()
    
    # IMPORTANT: Set window icon again (ensures taskbar icon on Windows)
    if icon_set:
        icon_paths = [
            Path(__file__).parent / "app" / "resources" / "icon.png",
            Path(__file__).parent / "resources" / "icon.png",
        ]
        for icon_path in icon_paths:
            if icon_path.exists():
                window.setWindowIcon(QIcon(str(icon_path)))
                print(f"Window icon set: {icon_path}")
                break
    
    window.show()
    
    # Start event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()