# app/ui/main_window.py
"""Main application window with modern UI and batch/continuous modes"""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QFileDialog, QCheckBox, QGroupBox, QTextEdit, 
    QProgressBar, QTabWidget, QTableWidget, QTableWidgetItem,
    QLineEdit, QSpinBox, QMessageBox, QListWidget,
    QSplitter, QFrame, QRadioButton, QButtonGroup,
    QSystemTrayIcon
)
from PyQt6.QtCore import QThread, pyqtSignal, QTimer, Qt
from PyQt6.QtGui import QFont
from PyQt6.QtGui import QPixmap
from pathlib import Path
import json
import logging
import time
import sys
from datetime import datetime
from typing import Optional

from ..core.config import AppConfig
from ..core.organizer import FileOrganizer
from ..core.watcher import FolderMonitor
from ..core.analytics import FileAnalytics
from .system_tray import SystemTrayManager
from ..core.database import Database
from .history_viewer import HistoryViewer
from ..core.content_analyzer import ContentAnalyzer
from ..core.rules_engine import RulesEngine
from .visual_analytics import VisualAnalytics
from .rules_manager import RulesManager
from app.core.updater import UpdateChecker

logger = logging.getLogger("FileOrganizer")


class OrganizerThread(QThread):
    """Background thread for continuous file organization"""
    file_processed = pyqtSignal(str, bool, str, str, int)
    progress_update = pyqtSignal(int, int)
    
    def __init__(self, organizer: FileOrganizer):
        super().__init__()
        self.organizer = organizer
        self.running = True
    
    def process_file(self, file_path: Path):
        if not self.running:
            return
        success, message, category, size = self.organizer.organize_file(file_path)
        self.file_processed.emit(file_path.name, success, message, category, size)
    
    def stop(self):
        """Stop the thread gracefully"""
        self.running = False
        # Don't call quit() here - let the thread finish naturally
    
    def run(self):
        """Thread main loop - override if needed"""
        # Keep thread alive for processing
        while self.running:
            self.msleep(100)  # Sleep 100ms


class BatchOrganizerThread(QThread):
    """Thread for one-time batch organization with progress"""
    file_processed = pyqtSignal(str, bool, str, str, int)
    progress_update = pyqtSignal(int, int)
    batch_complete = pyqtSignal(int, int, int)
    
    def __init__(self, organizer: FileOrganizer, files: list):
        super().__init__()
        self.organizer = organizer
        self.files = files
        self.running = True
    
    def run(self):
        """Process all files and report completion"""
        total = len(self.files)
        success = 0
        failed = 0
        
        for i, file_path in enumerate(self.files):
            if not self.running:
                break
            
            result, message, category, size = self.organizer.organize_file(file_path)
            self.file_processed.emit(file_path.name, result, message, category, size)
            self.progress_update.emit(i + 1, total)
            
            if result:
                success += 1
            else:
                failed += 1
            
            # Small delay to show progress
            time.sleep(0.05)
        
        # Emit completion signal
        self.batch_complete.emit(total, success, failed)
    
    def stop(self):
        """Stop the thread gracefully"""
        self.running = False


class UpdateCheckThread(QThread):
    """Background thread for checking updates"""
    update_found = pyqtSignal(dict)
    no_update = pyqtSignal()
    check_failed = pyqtSignal(str)
    
    def __init__(self, show_no_update=False):
        super().__init__()
        self.show_no_update = show_no_update
        self._is_running = True
    
    def run(self):
        """Run update check in background"""
        try:
            if not self._is_running:
                return
                
            checker = UpdateChecker()
            
            if not self._is_running:
                return
            
            # Only check if enough time has passed (unless forced)
            if not self.show_no_update and not checker.should_check_for_updates():
                return
            
            if not self._is_running:
                return
                
            if checker.check_for_updates():
                self.update_found.emit(checker.get_update_info())
            else:
                if self.show_no_update:  # Only emit if manual check
                    self.no_update.emit()
                
        except Exception as e:
            logger.error(f"Update check thread error: {e}")
            if self._is_running:
                self.check_failed.emit(str(e))
    
    def stop(self):
        """Stop the thread gracefully"""
        self._is_running = False


class MainWindow(QMainWindow):
    """Modern main application window with batch and continuous modes"""
    
    def __init__(self):
        super().__init__()
        self.config = None
        self.organizer = None
        self.monitor = None
        self.organizer_thread = None
        self.batch_thread = None
        self.update_thread = None  # ADD THIS
        self.analytics = FileAnalytics()
        self.tray_manager = None
        
        # ADD DATABASE
        self.database = Database()
        self.current_session_id = None

        # ADD NEW FEATURES
        self.content_analyzer = ContentAnalyzer()
        self.rules_engine = RulesEngine()
        
        # Setup UI first
        self.init_ui()
        
        # Then setup system tray (needs UI to be ready)
        self.setup_system_tray()
        
        # Load config and setup timers
        self.load_config()
        self.setup_timers()
        
        # Check for updates after 3 seconds
        QTimer.singleShot(3000, self.check_for_updates_background)


    def check_for_updates_background(self):
        """Check for updates in background (automatic on startup)"""
        try:
            # Don't create new thread if one is already running
            if self.update_thread and self.update_thread.isRunning():
                return
            
            self.update_thread = UpdateCheckThread(show_no_update=False)

            self.update_thread.update_found.connect(self.on_update_found)
            self.update_thread.no_update.connect(lambda: None)
            self.update_thread.check_failed.connect(
                lambda err: logger.debug(f"Update check failed: {err}")
            )

            # 🔒 SAFE CLEANUP (CRITICAL FIX)
            self.update_thread.finished.connect(self.update_thread.deleteLater)
            self.update_thread.finished.connect(lambda: setattr(self, "update_thread", None))

            self.update_thread.start()

        except Exception as e:
            logger.error(f"Failed to start update check: {e}")
    
    
    def check_for_updates_manual(self):
        """Check for updates manually (user clicked button) - FIXED"""
        from PyQt6.QtWidgets import QMessageBox, QApplication
        from PyQt6.QtCore import QTimer
        
        # Don't create new thread if one is already running
        if hasattr(self, 'update_thread') and self.update_thread and self.update_thread.isRunning():
            QMessageBox.information(
                self,
                "Please Wait",
                "Update check already in progress..."
            )
            return
        
        # Create checking message dialog
        checking_msg = QMessageBox(self)
        checking_msg.setWindowTitle("Checking for Updates")
        checking_msg.setText("Checking for updates...\n\nPlease wait.")
        checking_msg.setStandardButtons(QMessageBox.StandardButton.NoButton)
        checking_msg.setModal(True)
        checking_msg.show()
        QApplication.processEvents()
        
        # Helper to properly close and cleanup
        def close_checking_dialog():
            """Properly close and cleanup the checking dialog"""
            try:
                if checking_msg:
                    checking_msg.close()
                    checking_msg.hide()
                    checking_msg.deleteLater()
            except:
                pass
            QApplication.processEvents()
        
        try:
            self.update_thread = UpdateCheckThread(show_no_update=True)
            
            def cleanup_and_show_update(info):
                close_checking_dialog()
                # Small delay to ensure dialog is closed
                QTimer.singleShot(50, lambda: self.on_update_found(info))
            
            def cleanup_and_show_no_update():
                close_checking_dialog()
                # Small delay to ensure dialog is closed
                QTimer.singleShot(50, self.on_no_update_available)
            
            def cleanup_and_show_error(error):
                close_checking_dialog()
                # Small delay to ensure dialog is closed
                QTimer.singleShot(50, lambda: QMessageBox.warning(
                    self,
                    "Update Check Failed",
                    f"Could not check for updates:\n\n{error}"
                ))
            
            # Connect signals
            self.update_thread.update_found.connect(cleanup_and_show_update)
            self.update_thread.no_update.connect(cleanup_and_show_no_update)
            self.update_thread.check_failed.connect(cleanup_and_show_error)
            
            # Cleanup on finish
            self.update_thread.finished.connect(close_checking_dialog)
            self.update_thread.finished.connect(self.update_thread.deleteLater)
            self.update_thread.finished.connect(lambda: setattr(self, "update_thread", None))
            
            # Start the check
            self.update_thread.start()
            
        except Exception as e:
            close_checking_dialog()
            logger.error(f"Failed to check for updates: {e}")
            QMessageBox.critical(
                self, 
                "Error", 
                f"Failed to check for updates:\n\n{str(e)}"
            )
 
    
    def on_update_found(self, info):
        """Handle update found notification"""
        from PyQt6.QtWidgets import QMessageBox
        
        # Format release notes (limit length)
        release_notes = info['release_notes']
        if len(release_notes) > 300:
            release_notes = release_notes[:300] + "..."
        
        # Create update dialog
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Update Available")
        msg_box.setIcon(QMessageBox.Icon.Information)
        
        message = f"""
<h3>A new version is available!</h3>

<table>
<tr><td><b>Current Version:</b></td><td>{info['current_version']}</td></tr>
<tr><td><b>Latest Version:</b></td><td>{info['latest_version']}</td></tr>
</table>

<h4>What's New:</h4>
<p>{release_notes}</p>

<p>Would you like to download the update?</p>
        """
        
        msg_box.setText(message)
        msg_box.setTextFormat(Qt.TextFormat.RichText)
        
        # Add buttons
        download_btn = msg_box.addButton("Download Update", QMessageBox.ButtonRole.AcceptRole)
        later_btn = msg_box.addButton("Later", QMessageBox.ButtonRole.RejectRole)
        
        msg_box.exec()
        
        # Handle button click
        if msg_box.clickedButton() == download_btn:
            import webbrowser
            webbrowser.open(info['download_url'])
            
            # Show instructions
            QMessageBox.information(
                self,
                "Download Started",
                "The download page has been opened in your browser.\n\n"
                "After downloading:\n"
                "1. Close this application\n"
                "2. Run the installer\n"
                "3. Your settings will be preserved"
            )
    
    
    def on_no_update_available(self):
        """Handle no update available (manual check only)"""
        from PyQt6.QtWidgets import QMessageBox
        from app.version import APP_VERSION
        
        QMessageBox.information(
            self,
            "No Updates Available",
            f"You are running the latest version!\n\n"
            f"Current Version: {APP_VERSION}"
        )
    
    
    def show_about(self):
        """Show about dialog with version info"""
        from PyQt6.QtWidgets import QMessageBox
        from app.version import APP_VERSION, APP_NAME, APP_AUTHOR, APP_COPYRIGHT
        
        about_text = f"""
<h2>{APP_NAME}</h2>
<p><b>Version:</b> {APP_VERSION}</p>
<p><b>Author:</b> {APP_AUTHOR}</p>
<p>{APP_COPYRIGHT}</p>

<h3>Features:</h3>
<ul>
<li>Automatic file organization</li>
<li>Visual analytics dashboard</li>
<li>Batch and continuous monitoring</li>
<li>History with undo capability</li>
<li>Custom organization rules</li>
<li>Desktop notifications</li>
<li>System tray integration</li>
</ul>

<p><small>Built with PyQt6 and Python</small></p>
        """
        
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(f"About {APP_NAME}")
        msg_box.setText(about_text)
        msg_box.setTextFormat(Qt.TextFormat.RichText)
        msg_box.setIconPixmap(QPixmap("app/resources/icon.png").scaled(64, 64))
        
        # Add update check button
        check_update_btn = msg_box.addButton("Check for Updates", QMessageBox.ButtonRole.ActionRole)
        close_btn = msg_box.addButton("Close", QMessageBox.ButtonRole.RejectRole)
        
        msg_box.exec()
        
        if msg_box.clickedButton() == check_update_btn:
            self.check_for_updates_manual()


    def setup_system_tray(self):
        """Setup system tray integration"""
        # Check if system tray is available
        if not QSystemTrayIcon.isSystemTrayAvailable():
            logger.warning("System tray not available on this system")
            self.tray_manager = None
            return
        
        try:
            from PyQt6.QtWidgets import QApplication
            app = QApplication.instance()
            
            self.tray_manager = SystemTrayManager(app, self)
            
            # Connect tray signals to window actions
            self.tray_manager.show_window.connect(self.show_from_tray)
            self.tray_manager.hide_window.connect(self.hide)
            self.tray_manager.start_monitoring.connect(self.start_monitoring)
            self.tray_manager.stop_monitoring.connect(self.stop_monitoring)
            self.tray_manager.exit_app.connect(self.exit_application)
            self.tray_manager.open_watch_folder.connect(self.open_watch_folder_location)
            self.tray_manager.open_output_folder.connect(self.open_output_folder_location)
            
            logger.info("System tray integration enabled")
            
            # Show initial notification
            if self.tray_manager.tray_icon:
                self.tray_manager.show_notification(
                    "Smart File Organizer Started",
                    "Application is ready. Click tray icon to access controls."
                )
            
        except Exception as e:
            logger.error(f"Could not setup system tray: {e}", exc_info=True)
            self.tray_manager = None

    
    def show_from_tray(self):
        """Show window from system tray"""
        self.show()
        self.raise_()
        self.activateWindow()
        
        if self.tray_manager:
            self.tray_manager.show_action.setText("📦 Hide to Tray")
    
    def open_watch_folder_location(self):
        """Open watch folder in file explorer"""
        if self.folder_input.text():
            self.open_folder_in_explorer(self.folder_input.text())
        else:
            QMessageBox.information(
                self, 
                "No Folder Selected", 
                "Please select a watch folder first."
            )
    
    def open_output_folder_location(self):
        """Open output folder in file explorer"""
        if self.config and self.config.organized_folder:
            self.open_folder_in_explorer(str(self.config.organized_folder))
        elif self.output_input.text():
            self.open_folder_in_explorer(self.output_input.text())
        else:
            QMessageBox.information(
                self, 
                "No Output Folder", 
                "No output folder has been configured yet."
            )
    
    def open_folder_in_explorer(self, folder_path):
        """Open folder in system file explorer"""
        import os
        import subprocess
        from pathlib import Path
        
        folder = Path(folder_path)
        if not folder.exists():
            QMessageBox.warning(
                self,
                "Folder Not Found",
                f"The folder does not exist:\n{folder_path}"
            )
            return
        
        try:
            if sys.platform == "win32":
                os.startfile(str(folder))
            elif sys.platform == "darwin":
                subprocess.run(["open", str(folder)])
            else:
                subprocess.run(["xdg-open", str(folder)])
        except Exception as e:
            logger.error(f"Failed to open folder: {e}")
            QMessageBox.warning(
                self,
                "Error",
                f"Failed to open folder:\n{str(e)}"
            )
    
    def exit_application(self):
        """Exit application completely"""
        self.close()    
    
    def init_ui(self):
        """Initialize modern UI"""
        self.setWindowTitle("Smart File Organizer Pro")
        self.setGeometry(100, 50, 1200, 800)
        self.setMinimumSize(1000, 700)
        
        # Central widget with tabs
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)
        
        # Header
        self.create_header(main_layout)
        
        # Tab widget
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        
        # Create tabs
        self.create_dashboard_tab()
        self.create_settings_tab()
        self.create_analytics_tab()
        self.create_rules_tab()
        self.create_logs_tab()
        
        main_layout.addWidget(self.tabs)
        
        # Status bar
        self.create_status_bar()
    
    def create_header(self, layout):
        """Create modern header section"""
        header = QFrame()
        header.setMaximumHeight(80)
        header_layout = QHBoxLayout(header)
        
        # Title with icon
        title_container = QVBoxLayout()
        title = QLabel("🗂️ Smart File Organizer Pro")
        title.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        title_container.addWidget(title)
        
        subtitle = QLabel("Intelligent automated file management system")
        subtitle.setFont(QFont("Segoe UI", 10))
        subtitle.setStyleSheet("color: #888888;")
        title_container.addWidget(subtitle)
        
        header_layout.addLayout(title_container)
        header_layout.addStretch()
        
        # Quick stats
        self.quick_stats = QLabel("Files: 0 | Active: No")
        self.quick_stats.setFont(QFont("Segoe UI", 11))
        header_layout.addWidget(self.quick_stats)
        
        layout.addWidget(header)
    
    def create_dashboard_tab(self):
        """Create dashboard tab with monitoring controls"""
        dashboard = QWidget()
        layout = QVBoxLayout(dashboard)
        layout.setSpacing(15)
        
        # Main controls in a grid-like structure
        controls_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left: Folder Configuration
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        folder_group = QGroupBox("📁 Folder Configuration")
        folder_layout = QVBoxLayout()
        
        # Watch folder
        watch_layout = QHBoxLayout()
        watch_layout.addWidget(QLabel("Watch Folder:"))
        self.folder_input = QLineEdit()
        self.folder_input.setPlaceholderText("Select a folder to monitor...")
        self.folder_input.setReadOnly(True)
        watch_layout.addWidget(self.folder_input, 1)
        
        browse_btn = QPushButton("Browse")
        browse_btn.setMaximumWidth(100)
        browse_btn.clicked.connect(self.select_folder)
        watch_layout.addWidget(browse_btn)
        folder_layout.addLayout(watch_layout)
        
        # Output folders
        output_layout = QHBoxLayout()
        output_layout.addWidget(QLabel("Output Folder:"))
        self.output_input = QLineEdit()
        self.output_input.setPlaceholderText("Auto: Watch Folder/Organized")
        output_layout.addWidget(self.output_input, 1)
        
        output_browse_btn = QPushButton("Browse")
        output_browse_btn.setMaximumWidth(100)
        output_browse_btn.clicked.connect(self.select_output_folder)
        output_layout.addWidget(output_browse_btn)
        folder_layout.addLayout(output_layout)
        
        folder_group.setLayout(folder_layout)
        left_layout.addWidget(folder_group)
        
        # MODE SELECTION GROUP
        mode_group = QGroupBox("🎯 Operation Mode")
        mode_layout = QVBoxLayout()
        
        # Radio buttons for mode selection
        self.mode_button_group = QButtonGroup()
        
        self.continuous_mode = QRadioButton("⚡ Continuous Monitoring")
        self.continuous_mode.setToolTip("Watch folder 24/7 and organize files as they arrive")
        self.continuous_mode.setChecked(True)
        self.mode_button_group.addButton(self.continuous_mode, 1)
        mode_layout.addWidget(self.continuous_mode)
        
        self.batch_mode = QRadioButton("📦 One-Time Batch Organization")
        self.batch_mode.setToolTip("Organize existing files once and stop automatically")
        self.mode_button_group.addButton(self.batch_mode, 2)
        mode_layout.addWidget(self.batch_mode)
        
        mode_info = QLabel("💡 Tip: Use Continuous for ongoing monitoring, Batch for cleanup tasks")
        mode_info.setStyleSheet("color: #888888; font-size: 10px;")
        mode_layout.addWidget(mode_info)
        
        mode_group.setLayout(mode_layout)
        left_layout.addWidget(mode_group)
        
        # Quick Options
        options_group = QGroupBox("⚙️ Quick Options")
        options_layout = QVBoxLayout()
        
        self.duplicate_check = QCheckBox("🔍 Enable Duplicate Detection")
        self.duplicate_check.setChecked(True)
        self.duplicate_check.setToolTip("Detect and move duplicate files")
        options_layout.addWidget(self.duplicate_check)
        
        self.ai_check = QCheckBox("🤖 Enable AI Classification")
        self.ai_check.setToolTip("Use intelligent name-based classification")
        options_layout.addWidget(self.ai_check)
        
        self.auto_organize_check = QCheckBox("⚡ Auto-organize on file creation")
        self.auto_organize_check.setChecked(True)
        options_layout.addWidget(self.auto_organize_check)
        
        self.notification_check = QCheckBox("🔔 Desktop Notifications")
        options_layout.addWidget(self.notification_check)
        
        options_group.setLayout(options_layout)
        left_layout.addWidget(options_group)
        left_layout.addStretch()
        
        controls_splitter.addWidget(left_panel)
        
        # Right: Status & Controls
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        status_group = QGroupBox("📊 System Status")
        status_layout = QVBoxLayout()
        
        self.status_label = QLabel("🔴 Status: Stopped")
        self.status_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        status_layout.addWidget(self.status_label)
        
        self.stats_label = QLabel("Files Processed: 0\nDuplicates Found: 0\nErrors: 0")
        self.stats_label.setFont(QFont("Segoe UI", 11))
        self.stats_label.setStyleSheet("color: #aaaaaa; line-height: 1.5;")
        status_layout.addWidget(self.stats_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(True)
        status_layout.addWidget(self.progress_bar)
        
        status_group.setLayout(status_layout)
        right_layout.addWidget(status_group)
        
        # Control buttons
        buttons_layout = QVBoxLayout()
        buttons_layout.setSpacing(10)
        
        self.start_btn = QPushButton("▶️  Start")
        self.start_btn.setObjectName("startButton")
        self.start_btn.clicked.connect(self.start_monitoring)
        self.start_btn.setMinimumHeight(50)
        self.start_btn.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        buttons_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("⏹️  Stop")
        self.stop_btn.setObjectName("stopButton")
        self.stop_btn.clicked.connect(self.stop_monitoring)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setMinimumHeight(50)
        self.stop_btn.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        buttons_layout.addWidget(self.stop_btn)
        history_btn = QPushButton("📜 History & Undo")
        history_btn.clicked.connect(self.show_history)
        history_btn.setMinimumHeight(40)
        buttons_layout.addWidget(history_btn)
        
        right_layout.addLayout(buttons_layout)
        right_layout.addStretch()
        
        controls_splitter.addWidget(right_panel)
        controls_splitter.setStretchFactor(0, 1)
        controls_splitter.setStretchFactor(1, 1)
        
        layout.addWidget(controls_splitter)
        
        # Activity Feed
        activity_group = QGroupBox("📝 Real-time Activity Feed")
        activity_layout = QVBoxLayout()
        
        self.activity_list = QListWidget()
        self.activity_list.setAlternatingRowColors(True)
        activity_layout.addWidget(self.activity_list)
        
        clear_btn = QPushButton("Clear Activity")
        clear_btn.setMaximumWidth(150)
        clear_btn.clicked.connect(self.activity_list.clear)
        activity_layout.addWidget(clear_btn, alignment=Qt.AlignmentFlag.AlignRight)
        
        activity_group.setLayout(activity_layout)
        layout.addWidget(activity_group, 1)
        
        self.tabs.addTab(dashboard, "🏠 Dashboard")
    
    def create_settings_tab(self):
        """Create settings tab with proper scrolling"""
        from PyQt6.QtWidgets import QScrollArea
        
        # Main settings widget
        settings = QWidget()
        main_layout = QVBoxLayout(settings)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        # Content widget (what goes inside scroll area)
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # ============================================
        # PERFORMANCE SETTINGS
        # ============================================
        perf_group = QGroupBox("⚡ Performance Settings")
        perf_layout = QVBoxLayout()
        
        # Max file size
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("Max File Size (MB):"))
        self.max_size_spin = QSpinBox()
        self.max_size_spin.setRange(1, 10000)
        self.max_size_spin.setValue(1000)
        self.max_size_spin.setSuffix(" MB")
        self.max_size_spin.setMinimumWidth(150)
        size_layout.addWidget(self.max_size_spin)
        size_layout.addStretch()
        perf_layout.addLayout(size_layout)
        
        # Scan interval
        interval_layout = QHBoxLayout()
        interval_layout.addWidget(QLabel("Scan Interval (seconds):"))
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(1, 60)
        self.interval_spin.setValue(5)
        self.interval_spin.setSuffix(" sec")
        self.interval_spin.setMinimumWidth(150)
        interval_layout.addWidget(self.interval_spin)
        interval_layout.addStretch()
        perf_layout.addLayout(interval_layout)
        
        perf_group.setLayout(perf_layout)
        layout.addWidget(perf_group)
        
        # ============================================
        # FILE TYPE FILTERS
        # ============================================
        filter_group = QGroupBox("🎯 File Type Filters")
        filter_layout = QVBoxLayout()
        
        filter_layout.addWidget(QLabel("Only process these file types (leave empty for all):"))
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("e.g., .pdf, .jpg, .docx")
        filter_layout.addWidget(self.filter_input)
        
        filter_group.setLayout(filter_layout)
        layout.addWidget(filter_group)
        
        # ============================================
        # ADVANCED OPTIONS
        # ============================================
        advanced_group = QGroupBox("🔧 Advanced Options")
        advanced_layout = QVBoxLayout()
        
        self.recursive_check = QCheckBox("Monitor subfolders recursively")
        advanced_layout.addWidget(self.recursive_check)
        
        self.backup_check = QCheckBox("Create backup before moving files")
        advanced_layout.addWidget(self.backup_check)
        
        self.log_detail_check = QCheckBox("Enable detailed logging")
        self.log_detail_check.setChecked(True)
        advanced_layout.addWidget(self.log_detail_check)
        
        advanced_group.setLayout(advanced_layout)
        layout.addWidget(advanced_group)
        
        # ============================================
        # ADVANCED FEATURES
        # ============================================
        advanced_features_group = QGroupBox("🚀 Advanced Features")
        advanced_features_layout = QVBoxLayout()
        
        # Content Analysis
        self.content_analysis_check = QCheckBox("Enable Content Analysis")
        self.content_analysis_check.setChecked(False)
        self.content_analysis_check.setToolTip(
            "Extract text and metadata from files for smarter organization"
        )
        advanced_features_layout.addWidget(self.content_analysis_check)
        
        # Rules Engine
        self.rules_engine_check = QCheckBox("Enable Smart Rules Engine")
        self.rules_engine_check.setChecked(True)
        self.rules_engine_check.setToolTip(
            "Create custom rules based on file name, size, age, and content"
        )
        advanced_features_layout.addWidget(self.rules_engine_check)
        
        # Visual Analytics
        self.visual_analytics_check = QCheckBox("Enable Visual Analytics")
        self.visual_analytics_check.setChecked(True)
        self.visual_analytics_check.setToolTip(
            "Display charts and graphs in the Analytics tab"
        )
        advanced_features_layout.addWidget(self.visual_analytics_check)
        
        # Simple info note (no technical details)
        note_label = QLabel(
            "💡 Advanced features will automatically use available system capabilities"
        )
        note_label.setWordWrap(True)
        note_label.setStyleSheet("color: #888; font-size: 10px; padding: 10px;")
        advanced_features_layout.addWidget(note_label)
        
        advanced_features_group.setLayout(advanced_features_layout)
        layout.addWidget(advanced_features_group)
        
        # ============================================
        # DATABASE MANAGEMENT
        # ============================================
        db_group = QGroupBox("💾 Database Management")
        db_layout = QVBoxLayout()
        
        db_info = QLabel("Store operation history, statistics, and enable undo functionality")
        db_info.setStyleSheet("color: #888888;")
        db_info.setWordWrap(True)
        db_layout.addWidget(db_info)
        
        db_buttons_layout = QHBoxLayout()
        
        view_history_btn = QPushButton("📜 View History")
        view_history_btn.clicked.connect(self.show_history)
        view_history_btn.setMinimumHeight(35)
        db_buttons_layout.addWidget(view_history_btn)
        
        optimize_db_btn = QPushButton("🔧 Optimize Database")
        optimize_db_btn.clicked.connect(self.optimize_database)
        optimize_db_btn.setMinimumHeight(35)
        db_buttons_layout.addWidget(optimize_db_btn)
        
        clear_old_btn = QPushButton("🗑️ Clear Old Data")
        clear_old_btn.clicked.connect(self.clear_old_data)
        clear_old_btn.setMinimumHeight(35)
        db_buttons_layout.addWidget(clear_old_btn)
        
        db_layout.addLayout(db_buttons_layout)
        
        # Database stats
        db_stats = QLabel()
        try:
            db_size = self.database.get_database_size()
            db_size_mb = db_size / (1024 * 1024)
            db_stats.setText(f"Current database size: {db_size_mb:.2f} MB")
        except:
            db_stats.setText("Database size: Unknown")
        db_stats.setStyleSheet("color: #888888; font-size: 10px;")
        db_layout.addWidget(db_stats)
        
        db_group.setLayout(db_layout)
        layout.addWidget(db_group)
        
        # ============================================
        # CONFIGURATION MANAGEMENT
        # ============================================
        config_group = QGroupBox("⚙️ Configuration")
        config_layout = QVBoxLayout()
        
        config_buttons_layout = QHBoxLayout()
        
        save_config_btn = QPushButton("💾 Save Configuration")
        save_config_btn.clicked.connect(self.save_config)
        save_config_btn.setMinimumHeight(35)
        config_buttons_layout.addWidget(save_config_btn)
        
        load_config_btn = QPushButton("📂 Load Configuration")
        load_config_btn.clicked.connect(self.load_config)
        load_config_btn.setMinimumHeight(35)
        config_buttons_layout.addWidget(load_config_btn)
        
        reset_config_btn = QPushButton("🔄 Reset to Defaults")
        reset_config_btn.clicked.connect(self.reset_config)
        reset_config_btn.setMinimumHeight(35)
        config_buttons_layout.addWidget(reset_config_btn)
        
        config_layout.addLayout(config_buttons_layout)
        config_group.setLayout(config_layout)
        layout.addWidget(config_group)
        
        # Updates & Information Section
        updates_group = QGroupBox("🔄 Updates & Information")
        updates_layout = QVBoxLayout()

        # Version display
        try:
            from app.version import APP_VERSION, APP_NAME
            version_label = QLabel(f"<b>{APP_NAME}</b><br>Version {APP_VERSION}")
        except ImportError:
            version_label = QLabel("<b>Smart File Organizer Pro</b><br>Version 1.0.0")

        version_label.setStyleSheet("color: #555; padding: 5px;")
        updates_layout.addWidget(version_label)

        # Info text
        update_info = QLabel(
            "Keep your application up to date with the latest features and bug fixes."
        )
        update_info.setWordWrap(True)
        update_info.setStyleSheet("color: #888; font-size: 10px; padding: 5px;")
        updates_layout.addWidget(update_info)

        # Buttons
        update_buttons_layout = QHBoxLayout()

        check_updates_btn = QPushButton("🔄 Check for Updates")
        check_updates_btn.clicked.connect(self.check_for_updates_manual)
        check_updates_btn.setMinimumHeight(40)
        check_updates_btn.setStyleSheet("""
            QPushButton {
                background-color: #0078d7;
                color: white;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1084e0;
            }
        """)
        update_buttons_layout.addWidget(check_updates_btn)

        about_btn = QPushButton("ℹ️ About")
        about_btn.clicked.connect(self.show_about)
        about_btn.setMinimumHeight(40)
        about_btn.setStyleSheet("""
            QPushButton {
                background-color: #5c5c5c;
                color: white;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #6c6c6c;
            }
        """)
        update_buttons_layout.addWidget(about_btn)

        updates_layout.addLayout(update_buttons_layout)
        updates_group.setLayout(updates_layout)
        layout.addWidget(updates_group)
                
        # ============================================
        # ADD STRETCH AT THE BOTTOM
        # This ensures everything stays at the top
        # ============================================
        layout.addStretch(1)
        
        # Set the content widget to the scroll area
        scroll.setWidget(content_widget)
        
        # Add scroll area to main layout
        main_layout.addWidget(scroll)
        
        # Add settings tab
        self.tabs.addTab(settings, "⚙️ Settings")

    def show_dependency_instructions(self):
        """Show instructions for installing missing dependencies"""
        msg = QMessageBox(self)
        msg.setWindowTitle("Install Dependencies")
        msg.setIcon(QMessageBox.Information)
        
        instructions = """
    <h3>Install Missing Dependencies</h3>
    <p>To enable all advanced features, install the following packages:</p>

    <h4>For Content Analysis (OCR):</h4>
    <pre>pip install pytesseract Pillow PyPDF2 python-docx</pre>
    <p><b>Note:</b> You also need to install Tesseract OCR separately:</p>
    <ul>
    <li><b>Windows:</b> Download from <a href="https://github.com/UB-Mannheim/tesseract/wiki">GitHub</a></li>
    <li><b>Mac:</b> brew install tesseract</li>
    <li><b>Linux:</b> sudo apt-get install tesseract-ocr</li>
    </ul>

    <h4>For Visual Analytics:</h4>
    <pre>pip install matplotlib</pre>

    <h4>Install All at Once:</h4>
    <pre>pip install pytesseract Pillow PyPDF2 python-docx matplotlib</pre>

    <p>After installation, restart the application to enable new features.</p>
        """
        
        msg.setText(instructions)
        msg.setTextFormat(Qt.RichText)
        msg.exec_()    


    # ADD database maintenance methods:
    def optimize_database(self):
        """Optimize database"""
        try:
            reply = QMessageBox.question(
                self,
                "Optimize Database",
                "This will compact the database and free up space.\n\n"
                "This may take a few seconds. Continue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.database.vacuum_database()
                
                # Show new size
                db_size = self.database.get_database_size()
                db_size_mb = db_size / (1024 * 1024)
                
                QMessageBox.information(
                    self,
                    "Success",
                    f"Database optimized successfully!\n\n"
                    f"Current size: {db_size_mb:.2f} MB"
                )
                
                self.log_activity("💾 Database optimized", "info")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to optimize database:\n{str(e)}")

    def clear_old_data(self):
        """Clear old data from database"""
        try:
            from PyQt6.QtWidgets import QInputDialog
            
            days, ok = QInputDialog.getInt(
                self,
                "Clear Old Data",
                "Delete data older than how many days?",
                90, 1, 365
            )
            
            if ok:
                reply = QMessageBox.warning(
                    self,
                    "Confirm Deletion",
                    f"This will permanently delete all data older than {days} days.\n\n"
                    f"This action cannot be undone. Continue?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    self.database.clear_old_data(days)
                    
                    QMessageBox.information(
                        self,
                        "Success",
                        f"Old data cleared successfully!"
                    )
                    
                    self.log_activity(f"🗑️ Cleared data older than {days} days", "info")
                    
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to clear old data:\n{str(e)}")    
    
    # UPDATE create_analytics_tab to use Visual Analytics:
    def create_analytics_tab(self):
        """Create analytics dashboard with visual charts"""
        analytics_widget = QWidget()
        layout = QVBoxLayout(analytics_widget)
        
        # Tab selector for different views
        from PyQt6.QtWidgets import QTabWidget
        analytics_tabs = QTabWidget()
        
        # Visual Analytics Tab (if matplotlib available)
        try:
            from .visual_analytics import VisualAnalytics
            visual_analytics = VisualAnalytics(self.database, self)
            analytics_tabs.addTab(visual_analytics, "📊 Visual Charts")
        except ImportError as e:
            logger.warning(f"Visual analytics not available: {e}")
        
        # Table-based statistics (always available)
        stats_widget = self.create_stats_table_widget()
        analytics_tabs.addTab(stats_widget, "📋 Tables")
        
        layout.addWidget(analytics_tabs)
        self.tabs.addTab(analytics_widget, "📊 Analytics")

    def create_stats_table_widget(self):
        """Create traditional stats table widget"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Stats Overview
        stats_group = QGroupBox("📈 Statistics Overview")
        stats_layout = QVBoxLayout()
        
        self.stats_table = QTableWidget()
        self.stats_table.setColumnCount(2)
        self.stats_table.setHorizontalHeaderLabels(["Metric", "Value"])
        self.stats_table.horizontalHeader().setStretchLastSection(True)
        self.stats_table.setAlternatingRowColors(True)
        stats_layout.addWidget(self.stats_table)
        
        refresh_stats_btn = QPushButton("🔄 Refresh Statistics")
        refresh_stats_btn.clicked.connect(self.update_analytics)
        stats_layout.addWidget(refresh_stats_btn)
        
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)
        
        # Category Breakdown
        category_group = QGroupBox("📊 Files by Category")
        category_layout = QVBoxLayout()
        
        self.category_table = QTableWidget()
        self.category_table.setColumnCount(3)
        self.category_table.setHorizontalHeaderLabels(["Category", "Count", "Size"])
        self.category_table.horizontalHeader().setStretchLastSection(True)
        category_layout.addWidget(self.category_table)
        
        category_group.setLayout(category_layout)
        layout.addWidget(category_group)
        
        return widget    
    
    # UPDATE create_rules_tab to use Smart Rules:
    def create_rules_tab(self):
        """Create smart rules tab"""
        rules = QWidget()
        layout = QVBoxLayout(rules)
        
        # Header
        header = QLabel("📏 Smart Organization Rules")
        header.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        layout.addWidget(header)
        
        # Description
        desc = QLabel(
            "Create custom rules to automatically organize files based on patterns, "
            "size, age, and content. Rules are applied before standard classification."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #888888; margin-bottom: 10px;")
        layout.addWidget(desc)
        
        # Rules summary
        rules_group = QGroupBox("Active Rules")
        rules_layout = QVBoxLayout()
        
        self.rules_summary = QListWidget()
        self.rules_summary.setMaximumHeight(200)
        rules_layout.addWidget(self.rules_summary)
        
        rules_group.setLayout(rules_layout)
        layout.addWidget(rules_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        manage_rules_btn = QPushButton("⚙️ Manage Rules")
        manage_rules_btn.clicked.connect(self.manage_rules)
        manage_rules_btn.setMinimumHeight(40)
        button_layout.addWidget(manage_rules_btn)
        
        test_rules_btn = QPushButton("🧪 Test Rules")
        test_rules_btn.clicked.connect(self.test_rules)
        test_rules_btn.setMinimumHeight(40)
        button_layout.addWidget(test_rules_btn)
        
        layout.addLayout(button_layout)
        
        # Examples
        examples_group = QGroupBox("Rule Examples")
        examples_layout = QVBoxLayout()
        
        examples_text = QTextEdit()
        examples_text.setReadOnly(True)
        examples_text.setMaximumHeight(200)
        examples_text.setText("""
    Example Rules:

    1. Screenshots → Screenshots folder
    Pattern: *screenshot*
    
    2. Large Videos → Videos/Large
    Pattern: *.mp4
    Condition: Size > 100 MB
    
    3. Old Documents → Archive
    Pattern: *.pdf
    Condition: Older than 365 days
    
    4. Invoices → Finance/Invoices
    Pattern: *invoice*
    Condition: Extension: .pdf
    
    5. Photos with GPS → Photos/Locations
    Pattern: *.jpg
    Condition: Has GPS metadata
        """)
        examples_layout.addWidget(examples_text)
        examples_group.setLayout(examples_layout)
        layout.addWidget(examples_group)
        
        layout.addStretch()
        
        # Update rules summary
        self.update_rules_summary()
        
        self.tabs.addTab(rules, "📏 Rules")

    # ADD new methods for rules management:
    def manage_rules(self):
        """Open rules manager dialog"""
        try:
            rules_dialog = RulesManager(self.rules_engine, self)
            rules_dialog.rules_changed.connect(self.update_rules_summary)
            rules_dialog.exec()
        except Exception as e:
            logger.error(f"Failed to open rules manager: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to open rules manager:\n{str(e)}")

    def update_rules_summary(self):
        """Update rules summary display"""
        if hasattr(self, 'rules_summary'):
            self.rules_summary.clear()
            for rule in self.rules_engine.rules:
                status = "✅" if rule.enabled else "⏸️"
                text = f"{status} [{rule.priority}] {rule.name}: {rule.pattern} → {rule.target_folder}"
                self.rules_summary.addItem(text)

    def test_rules(self):
        """Test rules on a sample file"""
        from PyQt6.QtWidgets import QFileDialog
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select File to Test Rules",
            "",
            "All Files (*.*)"
        )
        
        if file_path:
            from pathlib import Path
            test_file = Path(file_path)
            
            # Test rules
            result = self.rules_engine.apply_rules(test_file)
            
            if result:
                QMessageBox.information(
                    self,
                    "Rule Match Found",
                    f"File: {test_file.name}\n\n"
                    f"Would be organized to:\n{result}"
                )
            else:
                QMessageBox.information(
                    self,
                    "No Match",
                    f"File: {test_file.name}\n\n"
                    f"No matching rule found.\n"
                    f"Would use standard classification."
                )
    

    
    def create_logs_tab(self):
        """Create detailed logs tab"""
        logs = QWidget()
        layout = QVBoxLayout(logs)
        
        logs_group = QGroupBox("📜 Detailed Activity Logs")
        logs_layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))
        logs_layout.addWidget(self.log_text)
        
        logs_btn_layout = QHBoxLayout()
        clear_logs_btn = QPushButton("Clear Logs")
        clear_logs_btn.clicked.connect(self.log_text.clear)
        logs_btn_layout.addWidget(clear_logs_btn)
        
        export_logs_btn = QPushButton("💾 Export Logs")
        export_logs_btn.clicked.connect(self.export_logs)
        logs_btn_layout.addWidget(export_logs_btn)
        logs_btn_layout.addStretch()
        
        logs_layout.addLayout(logs_btn_layout)
        logs_group.setLayout(logs_layout)
        layout.addWidget(logs_group)
        
        self.tabs.addTab(logs, "📜 Logs")
    
    def create_status_bar(self):
        """Create modern status bar"""
        statusbar = self.statusBar()
        statusbar.setStyleSheet("QStatusBar { border-top: 1px solid #3a3a3a; padding: 5px; }")
        
        self.status_message = QLabel("Ready")
        statusbar.addWidget(self.status_message)
        
        statusbar.addPermanentWidget(QLabel("Version 1.0.0"))
    
    def setup_timers(self):
        """Setup update timers"""
        self.stats_timer = QTimer()
        self.stats_timer.timeout.connect(self.update_stats)
        self.stats_timer.start(1000)
        
        self.analytics_timer = QTimer()
        self.analytics_timer.timeout.connect(self.update_analytics)
        self.analytics_timer.start(5000)
    
    def select_folder(self):
        """Select folder to watch"""
        folder = QFileDialog.getExistingDirectory(self, "Select Folder to Monitor")
        if folder:
            self.folder_input.setText(folder)
            self.log_activity(f"📁 Selected watch folder: {folder}", "info")
    
    def select_output_folder(self):
        """Select output folder"""
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if folder:
            self.output_input.setText(folder)
            self.log_activity(f"📁 Selected output folder: {folder}", "info")
    
    # UPDATE start_monitoring to create session:
    def start_monitoring(self):
        """Start file monitoring or batch organization based on mode"""
        if not self.folder_input.text():
            QMessageBox.warning(self, "Warning", "Please select a folder to monitor first!")
            return
        
        try:
            watch_folder = Path(self.folder_input.text())
            output_folder = Path(self.output_input.text()) if self.output_input.text() else watch_folder / "Organized"
            
            self.config = AppConfig(
                watch_folder=watch_folder,
                organized_folder=output_folder,
                duplicate_folder=watch_folder / "Duplicates",
                enable_duplicates=self.duplicate_check.isChecked(),
                ai_classification=self.ai_check.isChecked(),
                max_file_size_mb=self.max_size_spin.value(),
                scan_interval_sec=self.interval_spin.value()
            )
            
            # Create folders
            self.config.watch_folder.mkdir(parents=True, exist_ok=True)
            self.config.organized_folder.mkdir(parents=True, exist_ok=True)
            self.config.duplicate_folder.mkdir(parents=True, exist_ok=True)
            
            # Save config to database
            config_dict = {
                "watch_folder": str(self.config.watch_folder),
                "organized_folder": str(self.config.organized_folder),
                "duplicate_folder": str(self.config.duplicate_folder),
                "enable_duplicates": self.config.enable_duplicates,
                "ai_classification": self.config.ai_classification,
                "max_file_size_mb": self.config.max_file_size_mb
            }
            self.database.save_config(config_dict, "Session started")
            
            # Initialize organizer WITH all features
            self.organizer = FileOrganizer(
                self.config, 
                self.database,
                content_analyzer=self.content_analyzer,
                rules_engine=self.rules_engine
            )
            
            # Start session in database
            mode = "batch" if self.batch_mode.isChecked() else "continuous"
            self.current_session_id = self.database.start_session(mode, str(watch_folder))
            
            # Check selected mode
            if self.batch_mode.isChecked():
                self.start_batch_mode()
            else:
                self.start_continuous_mode()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to start:\n{str(e)}")
            logger.error(f"Error starting: {e}", exc_info=True)
    
    def start_continuous_mode(self):
        """Start continuous folder monitoring"""
        self.organizer_thread = OrganizerThread(self.organizer)
        self.organizer_thread.file_processed.connect(self.on_file_processed)
        self.organizer_thread.start()
        
        # Start monitoring
        self.monitor = FolderMonitor(
            self.config.watch_folder,
            self.organizer_thread.process_file
        )
        self.monitor.start()
        
        self.status_label.setText("🟢 Status: Monitoring (Continuous)")
        self.status_message.setText("Watching for new files...")
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.log_activity("✅ Continuous monitoring started", "success")
        self.quick_stats.setText(f"Active: Yes | Mode: Continuous | Watching: {self.config.watch_folder.name}")

        # Update system tray
        if self.tray_manager:
            self.tray_manager.update_monitoring_state(True)
            self.tray_manager.show_notification(
                "Monitoring Started",
                f"Watching: {self.config.watch_folder.name}",
                QSystemTrayIcon.MessageIcon.Information
            )
    
    def start_batch_mode(self):
        """Start one-time batch organization"""
        # Get all files in folder
        files = list(self.config.watch_folder.glob("*"))
        files = [f for f in files if f.is_file() and f.name not in ['Organized', 'Duplicates']]
        
        # Exclude organized and duplicates folders
        files = [f for f in files if not str(f).startswith(str(self.config.organized_folder)) 
                 and not str(f).startswith(str(self.config.duplicate_folder))]
        
        if not files:
            QMessageBox.information(
                self, 
                "No Files Found", 
                "No files found to organize in the selected folder."
            )
            return
        
        reply = QMessageBox.question(
            self, 
            "Confirm Batch Organization",
            f"Found {len(files)} files to organize.\n\n"
            f"The system will:\n"
            f"• Organize all files once\n"
            f"• Show progress in real-time\n"
            f"• Notify you when complete\n"
            f"• Stop automatically\n\n"
            f"Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.No:
            return
        
        # Create batch thread
        self.batch_thread = BatchOrganizerThread(self.organizer, files)
        self.batch_thread.file_processed.connect(self.on_file_processed)
        self.batch_thread.progress_update.connect(self.on_batch_progress)
        self.batch_thread.batch_complete.connect(self.on_batch_complete)
        self.batch_thread.start()
        
        # Update UI
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(len(files))
        self.progress_bar.setValue(0)
        
        self.status_label.setText("🟡 Status: Processing Batch...")
        self.status_message.setText(f"Organizing {len(files)} files...")
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.log_activity(f"📦 Batch organization started ({len(files)} files)", "info")
        self.quick_stats.setText(f"Active: Yes | Mode: Batch | Processing: {len(files)} files")

        # Update system tray
        if self.tray_manager:
            self.tray_manager.update_monitoring_state(True)
            self.tray_manager.show_notification(
                "Batch Started",
                f"Processing {len(files)} files...",
                QSystemTrayIcon.MessageIcon.Information
            )
    
    def on_batch_progress(self, current: int, total: int):
        """Update progress bar during batch operation"""
        self.progress_bar.setValue(current)
        percent = (current / total * 100) if total > 0 else 0
        self.status_message.setText(f"Processing: {current}/{total} files ({percent:.1f}%)...")
    
    def on_batch_complete(self, total: int, success: int, failed: int):
        """Handle batch organization completion"""
        self.progress_bar.setVisible(False)
        
        self.status_label.setText("Status: Batch Complete!")
        self.status_message.setText("Ready")
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        
        self.log_activity(
            f"Batch organization completed! Total: {total} | Success: {success} | Failed: {failed}",
            "success"
        )
        
        # Update system tray
        if self.tray_manager:
            self.tray_manager.update_monitoring_state(False)
            self.tray_manager.show_batch_complete(total, success, failed)
        
        # Show completion dialog
        completion_msg = (
            f"Batch Organization Complete!\n\n"
            f"Summary:\n"
            f"  Total Files: {total}\n"
            f"  Successfully Organized: {success}\n"
            f"  Failed: {failed}\n"
            f"  Success Rate: {(success/total*100):.1f}%\n\n"
            f"All files have been organized and the operation has stopped automatically."
        )
        
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.setWindowTitle("Batch Complete")
        msg_box.setText(completion_msg)
        msg_box.setStandardButtons(
            QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Open
        )
        
        open_button = msg_box.button(QMessageBox.StandardButton.Open)
        open_button.setText("Open Output Folder")
        
        result = msg_box.exec()
        
        if result == QMessageBox.StandardButton.Open:
            self.open_folder_in_explorer(str(self.config.organized_folder))
        
        self.quick_stats.setText("Active: No | Last: Batch completed")

    
    def show_notification(self, title: str, message: str, icon_type: str = "info"):
        """Show desktop notification (cross-platform)"""
        try:
            # Try Windows notifications first
            if sys.platform == "win32":
                try:
                    from win10toast import ToastNotifier
                    toaster = ToastNotifier()
                    toaster.show_toast(
                        title,
                        message,
                        duration=5,
                        threaded=True
                    )
                except ImportError:
                    # Fallback to log
                    self.log_activity(f"📢 {title}: {message}", "info")
            else:
                # Fallback: just log it
                self.log_activity(f"📢 {title}: {message}", "info")
        except Exception as e:
            logger.warning(f"Could not show notification: {e}")
            self.log_activity(f"📢 {title}: {message}", "info")
    
    # UPDATE stop_monitoring to end session:
    def stop_monitoring(self):
        """Stop file monitoring"""
        # Stop monitor
        if self.monitor:
            self.monitor.stop()
            self.monitor = None
        
        # Stop organizer thread
        if self.organizer_thread:
            self.organizer_thread.stop()
            self.organizer_thread.quit()
            self.organizer_thread.wait(2000)  # Wait up to 2 seconds
            if self.organizer_thread.isRunning():
                logger.warning("Organizer thread didn't stop gracefully")
                self.organizer_thread.terminate()
            self.organizer_thread = None
        
        # Stop batch thread
        if self.batch_thread:
            self.batch_thread.stop()
            self.batch_thread.quit()
            self.batch_thread.wait(2000)
            if self.batch_thread.isRunning():
                logger.warning("Batch thread didn't stop gracefully")
                self.batch_thread.terminate()
            self.batch_thread = None
        
        # End session in database
        if self.current_session_id and self.organizer:
            stats = self.organizer.get_stats()
            self.database.end_session(self.current_session_id, stats['processed'])
            self.current_session_id = None
        
        self.status_label.setText("🔴 Status: Stopped")
        self.status_message.setText("Ready")
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_bar.setVisible(False)
        self.log_activity("⏸️ Monitoring stopped", "warning")
        self.quick_stats.setText("Active: No")
        
        # Update system tray
        if self.tray_manager:
            self.tray_manager.update_monitoring_state(False)
            self.tray_manager.show_notification(
                "Monitoring Stopped",
                "File organizer is now idle",
                QSystemTrayIcon.MessageIcon.Information
            )

    # ADD this new method to show history:
    def show_history(self):
        """Show history and undo dialog"""
        try:
            # Check if database exists
            if not hasattr(self, 'database') or self.database is None:
                QMessageBox.warning(
                    self,
                    "Database Not Available",
                    "Database not initialized. Please start monitoring first."
                )
                return
            
            from .history_viewer import HistoryViewer
            history_dialog = HistoryViewer(self.database, self)
            history_dialog.file_restored.connect(self.on_file_restored)
            history_dialog.exec()
        except ImportError:
            QMessageBox.warning(
                self,
                "Feature Not Available",
                "History viewer module not found. Please ensure all files are properly installed."
            )
        except Exception as e:
            logger.error(f"Failed to show history: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to open history:\n{str(e)}")


    def on_file_restored(self, filename: str, message: str):
        """Handle file restored event"""
        self.log_activity(f"↩️ Restored: {filename} - {message}", "info")
        
    
    def on_file_processed(self, filename: str, success: bool, message: str, category: str, size: int = 0):
        """Handle file processing result with file size"""
        icon = "✅" if success else "❌"
        
        # Format size for display
        size_str = self._format_size(size) if size > 0 else ""
        log_msg = f"{icon} {filename} ({size_str}) → {message}" if size_str else f"{icon} {filename} → {message}"
        
        self.log_activity(log_msg, "success" if success else "error")
        
        # Add to analytics WITH FILE SIZE
        if success and category:
            self.analytics.add_file(filename, category, size)
        
        # Show notification based on mode and settings
        if self.continuous_mode.isChecked():
            # In continuous mode, show if notifications enabled
            if self.notification_check.isChecked() and self.tray_manager:
                self.tray_manager.show_file_processed(filename, success, category)

    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format"""
        if size_bytes == 0:
            return "0 B"
        
        units = ['B', 'KB', 'MB', 'GB', 'TB']
        unit_index = 0
        size = float(size_bytes)
        
        while size >= 1024.0 and unit_index < len(units) - 1:
            size /= 1024.0
            unit_index += 1
        
        if unit_index == 0:
            return f"{int(size)} {units[unit_index]}"
        else:
            return f"{size:.2f} {units[unit_index]}"
    
    def update_stats(self):
        """Update statistics display"""
        if self.organizer:
            stats = self.organizer.get_stats()
            self.stats_label.setText(
                f"Files Processed: {stats['processed']}\n"
                f"Duplicates Found: {stats['duplicates']}\n"
                f"Errors: {stats['errors']}"
            )
            
            # Update quick stats
            is_active = (self.monitor and self.monitor.is_running()) or (self.batch_thread and self.batch_thread.isRunning())
            mode = "Continuous" if self.continuous_mode.isChecked() else "Batch"
            self.quick_stats.setText(
                f"Files: {stats['processed']} | Active: {'Yes' if is_active else 'No'} | Mode: {mode}"
            )
    
    def update_analytics(self):
        """Update analytics dashboard"""
        # Check if tables exist (they might not if only visual analytics is shown)
        if not hasattr(self, 'stats_table') or not hasattr(self, 'category_table'):
            logger.debug("Stats tables not available, skipping table update")
            return
        
        if not self.organizer:
            return
        
        try:
            stats = self.organizer.get_stats()
            
            # Update stats table
            self.stats_table.setRowCount(6)
            success_count = stats['processed'] - stats['errors']
            success_rate = (success_count / max(stats['processed'], 1)) * 100
            
            # Get database size
            db_size = self.database.get_database_size()
            db_size_mb = db_size / (1024 * 1024)
            
            metrics = [
                ("Total Files Processed", str(stats['processed'])),
                ("Duplicates Detected", str(stats['duplicates'])),
                ("Errors Encountered", str(stats['errors'])),
                ("Success Rate", f"{success_rate:.1f}%"),
                ("Database Size", f"{db_size_mb:.2f} MB"),
                ("Active Since", datetime.now().strftime("%Y-%m-%d %H:%M"))
            ]
            
            for i, (metric, value) in enumerate(metrics):
                self.stats_table.setItem(i, 0, QTableWidgetItem(metric))
                self.stats_table.setItem(i, 1, QTableWidgetItem(value))
            
            # Update category breakdown from DATABASE
            category_stats = self.database.get_category_summary()
            self.category_table.setRowCount(len(category_stats))
            
            for i, stat in enumerate(category_stats):
                self.category_table.setItem(i, 0, QTableWidgetItem(stat['category']))
                self.category_table.setItem(i, 1, QTableWidgetItem(str(stat['total_files'])))
                
                size_mb = stat['total_size'] / (1024 * 1024) if stat['total_size'] else 0
                self.category_table.setItem(i, 2, QTableWidgetItem(f"{size_mb:.2f} MB"))
        
        except Exception as e:
            logger.error(f"Failed to update analytics: {e}", exc_info=True)
    
    def log_activity(self, message: str, level: str = "info"):
        """Add message to activity feed and logs"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Activity list
        self.activity_list.insertItem(0, f"[{timestamp}] {message}")
        if self.activity_list.count() > 100:
            self.activity_list.takeItem(self.activity_list.count() - 1)
        
        # Detailed log
        self.log_text.append(f"[{timestamp}] {message}")
    
    def add_rule(self):
        """Add custom organization rule"""
        row = self.rules_table.rowCount()
        self.rules_table.insertRow(row)
        self.rules_table.setItem(row, 0, QTableWidgetItem("*.pdf"))
        self.rules_table.setItem(row, 1, QTableWidgetItem("Documents/PDFs"))
        self.rules_table.setItem(row, 2, QTableWidgetItem("Move"))
    
    def remove_rule(self):
        """Remove selected rule"""
        current_row = self.rules_table.currentRow()
        if current_row >= 0:
            self.rules_table.removeRow(current_row)
    
    def save_config(self):
        """Save current configuration"""
        try:
            config_data = {
                "watch_folder": self.folder_input.text(),
                "output_folder": self.output_input.text(),
                "enable_duplicates": self.duplicate_check.isChecked(),
                "ai_classification": self.ai_check.isChecked(),
                "max_file_size_mb": self.max_size_spin.value(),
                "scan_interval_sec": self.interval_spin.value(),
                "mode": "batch" if self.batch_mode.isChecked() else "continuous"
            }
            
            with open("config.json", "w") as f:
                json.dump(config_data, f, indent=4)
            
            QMessageBox.information(self, "Success", "Configuration saved successfully!")
            self.log_activity("💾 Configuration saved", "info")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save configuration:\n{str(e)}")
    
    def load_config(self):
        """Load saved configuration"""
        try:
            config_file = Path("config.json")
            if config_file.exists():
                with open(config_file) as f:
                    data = json.load(f)
                    
                self.folder_input.setText(data.get("watch_folder", ""))
                self.output_input.setText(data.get("output_folder", ""))
                self.duplicate_check.setChecked(data.get("enable_duplicates", True))
                self.ai_check.setChecked(data.get("ai_classification", False))
                self.max_size_spin.setValue(data.get("max_file_size_mb", 1000))
                self.interval_spin.setValue(data.get("scan_interval_sec", 5))
                
                # Load mode
                if data.get("mode") == "batch":
                    self.batch_mode.setChecked(True)
                else:
                    self.continuous_mode.setChecked(True)
                
                self.log_activity("📂 Configuration loaded", "info")
        except Exception as e:
            logger.warning(f"Could not load config: {e}")
    
    def reset_config(self):
        """Reset configuration to defaults"""
        reply = QMessageBox.question(
            self, "Confirm Reset",
            "Reset all settings to default values?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.folder_input.clear()
            self.output_input.clear()
            self.duplicate_check.setChecked(True)
            self.ai_check.setChecked(False)
            self.continuous_mode.setChecked(True)
            self.max_size_spin.setValue(1000)
            self.interval_spin.setValue(5)
            self.log_activity("🔄 Settings reset to defaults", "info")
    
    def export_logs(self):
        """Export logs to file"""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export Logs",
            f"logs_{datetime.now():%Y%m%d_%H%M%S}.txt",
            "Text Files (*.txt)"
        )
        
        if filename:
            try:
                with open(filename, 'w') as f:
                    f.write(self.log_text.toPlainText())
                QMessageBox.information(self, "Success", "Logs exported successfully!")
                self.log_activity("📤 Logs exported successfully", "info")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export logs:\n{str(e)}")
                logger.error(f"Failed to export logs: {e}")
    
    def closeEvent(self, event):
        """Handle window close with proper cleanup"""
        
        # Check if monitoring is active
        is_monitoring = (self.monitor and self.monitor.is_running()) or \
                       (self.batch_thread and self.batch_thread.isRunning())
        
        if is_monitoring:
            reply_box = QMessageBox(self)
            reply_box.setIcon(QMessageBox.Icon.Question)
            reply_box.setWindowTitle("Monitoring Active")
            reply_box.setText("File monitoring is currently active.\n\nWhat would you like to do?")
            
            if self.tray_manager:
                minimize_btn = reply_box.addButton("Minimize to Tray", QMessageBox.ButtonRole.AcceptRole)
                stop_exit_btn = reply_box.addButton("Stop & Exit", QMessageBox.ButtonRole.DestructiveRole)
                cancel_btn = reply_box.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)
                
                reply_box.exec()
                clicked = reply_box.clickedButton()
                
                if clicked == minimize_btn:
                    event.ignore()
                    self.hide()
                    if self.tray_manager:
                        self.tray_manager.show_notification(
                            "Running in Background",
                            "Smart File Organizer is still monitoring files",
                            QSystemTrayIcon.MessageIcon.Information
                        )
                    return
                elif clicked == cancel_btn:
                    event.ignore()
                    return
            else:
                reply = QMessageBox.question(
                    self, 
                    "Monitoring Active",
                    "Stop monitoring and exit?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.No:
                    event.ignore()
                    return
        else:
            # Not monitoring - check tray minimize
            if self.tray_manager:
                reply = QMessageBox.question(
                    self,
                    "Minimize to Tray?",
                    "Would you like to minimize to system tray instead of closing?",
                    QMessageBox.StandardButton.Yes | 
                    QMessageBox.StandardButton.No |
                    QMessageBox.StandardButton.Cancel,
                    QMessageBox.StandardButton.Yes
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    event.ignore()
                    self.hide()
                    self.tray_manager.show_notification(
                        "Minimized to Tray",
                        "Click tray icon to restore window",
                        QSystemTrayIcon.MessageIcon.Information
                    )
                    return
                elif reply == QMessageBox.StandardButton.Cancel:
                    event.ignore()
                    return
        
        # === COMPREHENSIVE CLEANUP ===
        logger.info("Starting application cleanup...")
        
        # 1. Stop all timers
        if hasattr(self, 'stats_timer'):
            self.stats_timer.stop()
        if hasattr(self, 'analytics_timer'):
            self.analytics_timer.stop()
        
        # 2. Stop monitoring
        if self.monitor:
            logger.info("Stopping folder monitor...")
            self.monitor.stop()
            self.monitor = None
        
        # 3. Stop and cleanup organizer thread
        if self.organizer_thread:
            logger.info("Stopping organizer thread...")
            self.organizer_thread.stop()
            self.organizer_thread.quit()
            if not self.organizer_thread.wait(3000):  # Wait 3 seconds
                logger.warning("Organizer thread didn't stop, terminating...")
                self.organizer_thread.terminate()
                self.organizer_thread.wait(1000)
            self.organizer_thread.deleteLater()
            self.organizer_thread = None
        
        # 4. Stop and cleanup batch thread
        if self.batch_thread:
            logger.info("Stopping batch thread...")
            self.batch_thread.stop()
            self.batch_thread.quit()
            if not self.batch_thread.wait(3000):
                logger.warning("Batch thread didn't stop, terminating...")
                self.batch_thread.terminate()
                self.batch_thread.wait(1000)
            self.batch_thread.deleteLater()
            self.batch_thread = None
        
        # 5. Stop and cleanup update thread (SAFE)
        try:
            if self.update_thread is not None and self.update_thread.isRunning():
                logger.info("Stopping update thread...")
                self.update_thread.stop()
                self.update_thread.quit()
                self.update_thread.wait(2000)
        except RuntimeError:
            # QObject already deleted by Qt → safe to ignore
            pass

        self.update_thread = None

        
        # 6. End current session
        if self.current_session_id and self.organizer:
            logger.info("Ending database session...")
            try:
                stats = self.organizer.get_stats()
                self.database.end_session(self.current_session_id, stats['processed'])
            except Exception as e:
                logger.error(f"Failed to end session: {e}")
            self.current_session_id = None
        
        # 7. Cleanup system tray
        if self.tray_manager:
            logger.info("Cleaning up system tray...")
            try:
                self.tray_manager.cleanup()
            except Exception as e:
                logger.error(f"Error cleaning up tray: {e}")
            self.tray_manager = None
        
        # 8. Close database connection
        if hasattr(self, 'database') and self.database:
            logger.info("Closing database...")
            try:
                self.database.close()
            except Exception as e:
                logger.error(f"Error closing database: {e}")
        
        logger.info("Application cleanup complete")
        event.accept()
