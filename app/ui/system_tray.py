# ============================================
# FILE: app/ui/system_tray.py (FINAL VERSION)
# ============================================

"""System tray integration for Smart File Organizer"""
from PyQt6.QtWidgets import QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QAction, QPixmap, QPainter, QColor, QPen, QBrush, QLinearGradient, QPolygon
from PyQt6.QtCore import QObject, pyqtSignal, Qt, QPoint, QRect
import logging
from pathlib import Path

logger = logging.getLogger("FileOrganizer")


class SystemTrayManager(QObject):
    """Manages system tray icon and notifications"""
    
    # Signals
    show_window = pyqtSignal()
    hide_window = pyqtSignal()
    start_monitoring = pyqtSignal()
    stop_monitoring = pyqtSignal()
    exit_app = pyqtSignal()
    open_watch_folder = pyqtSignal()
    open_output_folder = pyqtSignal()
    
    def __init__(self, app, main_window):
        super().__init__()
        self.app = app
        self.main_window = main_window
        self.tray_icon = None
        self.is_monitoring = False
        
        self.setup_tray()
    
    def setup_tray(self):
        """Setup system tray icon and menu"""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            logger.warning("System tray not available on this system")
            return
        
        try:
            # Set icon FIRST before creating QSystemTrayIcon
            icon = self.create_icon()
            
            if icon.isNull():
                logger.error("❌ Failed to create icon - icon is null")
                return
            
            # IMPORTANT: Create tray icon WITH the icon in constructor
            self.tray_icon = QSystemTrayIcon(icon, self.main_window)
            
            # Set tooltip
            self.tray_icon.setToolTip("Smart File Organizer Pro")
            
            # Create context menu BEFORE showing
            self.create_menu()
            
            # Connect signals
            self.tray_icon.activated.connect(self.on_tray_activated)
            
            # Show tray icon - THIS IS CRITICAL
            self.tray_icon.setVisible(True)
            self.tray_icon.show()
            
            # Verify it's visible
            if self.tray_icon.isVisible():
                logger.info("System tray icon displayed successfully")
            else:
                logger.warning("System tray icon created but not visible")
            
        except Exception as e:
            logger.error(f"Failed to setup system tray: {e}", exc_info=True)
            self.tray_icon = None
    
    def create_icon(self):
        """Create or load system tray icon"""
        # Try to load from resources
        project_root = Path(__file__).resolve().parents[2]
        icon_path = project_root / "app" / "resources" / "icon.png"

        logger.info(f"Looking for tray icon at: {icon_path}")

        if icon_path.exists():
            # Load the icon with explicit size for system tray
            pixmap = QPixmap(str(icon_path))
            
            if not pixmap.isNull():
                # Scale to appropriate size for system tray (16x16 or 32x32 for Windows)
                scaled_pixmap = pixmap.scaled(32, 32, Qt.AspectRatioMode.KeepAspectRatio, 
                                              Qt.TransformationMode.SmoothTransformation)
                icon = QIcon(scaled_pixmap)
                
                # Add multiple sizes for better display
                icon.addPixmap(pixmap.scaled(16, 16, Qt.AspectRatioMode.KeepAspectRatio, 
                                            Qt.TransformationMode.SmoothTransformation))
                icon.addPixmap(pixmap.scaled(24, 24, Qt.AspectRatioMode.KeepAspectRatio, 
                                            Qt.TransformationMode.SmoothTransformation))
                icon.addPixmap(pixmap.scaled(32, 32, Qt.AspectRatioMode.KeepAspectRatio, 
                                            Qt.TransformationMode.SmoothTransformation))
                icon.addPixmap(pixmap.scaled(48, 48, Qt.AspectRatioMode.KeepAspectRatio, 
                                            Qt.TransformationMode.SmoothTransformation))
                
                logger.info(f"Successfully loaded custom icon from: {icon_path}")
                return icon
            else:
                logger.warning(f"Failed to load pixmap from {icon_path}")
        else:
            logger.info(f"Icon file not found at {icon_path}, generating default icon")
        
        # Generate professional icon as fallback
        return self.generate_default_icon()

    def generate_default_icon(self):
        """Generate a professional custom system tray icon"""
        try:
            # Create multiple sizes for better compatibility
            sizes = [16, 24, 32, 48]
            icon = QIcon()
            
            for size in sizes:
                pixmap = QPixmap(size, size)
                pixmap.fill(Qt.GlobalColor.transparent)
                
                painter = QPainter(pixmap)
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                
                scale = size / 64.0
                
                # Create gradient for folder
                gradient = QLinearGradient(0, 0, 0, size)
                gradient.setColorAt(0, QColor("#0078d7"))  # Microsoft blue
                gradient.setColorAt(1, QColor("#005a9e"))  # Darker blue
                
                # Draw main folder body
                painter.setBrush(QBrush(gradient))
                painter.setPen(QPen(QColor("#003d6b"), max(1, int(2 * scale))))
                
                # Folder body (main rectangle)
                folder_body = QRect(
                    int(6 * scale), int(18 * scale), 
                    int(52 * scale), int(38 * scale)
                )
                painter.drawRoundedRect(folder_body, int(4 * scale), int(4 * scale))
                
                # Folder tab (top flap)
                painter.setBrush(QColor("#0078d7"))
                tab_points = [
                    QPoint(int(6 * scale), int(18 * scale)),
                    QPoint(int(6 * scale), int(12 * scale)),
                    QPoint(int(28 * scale), int(12 * scale)),
                    QPoint(int(32 * scale), int(18 * scale)),
                ]
                painter.drawPolygon(QPolygon(tab_points))
                
                # Draw checkmark (organizing symbol) - only for larger sizes
                if size >= 24:
                    painter.setPen(QPen(QColor("#ffffff"), max(2, int(3 * scale)), 
                                       Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
                    painter.drawLine(
                        QPoint(int(20 * scale), int(35 * scale)), 
                        QPoint(int(28 * scale), int(43 * scale))
                    )
                    painter.drawLine(
                        QPoint(int(28 * scale), int(43 * scale)), 
                        QPoint(int(44 * scale), int(27 * scale))
                    )
                
                # Add sparkle effects (only for larger sizes)
                if size >= 32:
                    painter.setPen(QPen(QColor("#ffb900"), max(1, int(2 * scale))))
                    painter.drawPoint(QPoint(int(48 * scale), int(22 * scale)))
                    painter.drawPoint(QPoint(int(52 * scale), int(26 * scale)))
                    painter.drawPoint(QPoint(int(50 * scale), int(30 * scale)))
                
                painter.end()
                
                # Add this size to the icon
                icon.addPixmap(pixmap)
            
            logger.info("Generated professional custom tray icon with multiple sizes")
            return icon
            
        except Exception as e:
            logger.error(f"Failed to generate custom icon: {e}", exc_info=True)
            # Last resort: very simple icon
            return self.generate_simple_fallback_icon()
    
    def generate_simple_fallback_icon(self):
        """Generate ultra-simple fallback icon"""
        try:
            size = 64
            pixmap = QPixmap(size, size)
            pixmap.fill(Qt.GlobalColor.transparent)
            
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # Draw simple blue circle
            painter.setBrush(QColor(0, 120, 215))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(2, 2, size-4, size-4)
            
            # Draw white "SF" text
            painter.setPen(QColor(255, 255, 255))
            from PyQt6.QtGui import QFont
            font = QFont("Arial", 20, QFont.Weight.Bold)
            painter.setFont(font)
            painter.drawText(QRect(0, 0, size, size), Qt.AlignmentFlag.AlignCenter, "SF")
            
            painter.end()
            
            logger.info("Created simple fallback icon")
            return QIcon(pixmap)
            
        except Exception as e:
            logger.error(f"Failed to generate simple icon: {e}")
            return QIcon()
    
    def create_menu(self):
        """Create system tray context menu"""
        menu = QMenu()
        
        # Header
        header = QAction("Smart File Organizer Pro", menu)
        header.setEnabled(False)
        font = header.font()
        font.setBold(True)
        header.setFont(font)
        menu.addAction(header)
        menu.addSeparator()
        
        # Show/Hide Window
        self.show_action = QAction("Show Window", menu)
        self.show_action.triggered.connect(self.toggle_window)
        menu.addAction(self.show_action)
        
        menu.addSeparator()
        
        # Start/Stop Monitoring
        self.monitor_action = QAction("Start Monitoring", menu)
        self.monitor_action.triggered.connect(self.toggle_monitoring)
        menu.addAction(self.monitor_action)
        
        menu.addSeparator()
        
        # Quick Actions submenu
        quick_menu = menu.addMenu("Quick Actions")
        
        open_watch = QAction("Open Watch Folder", quick_menu)
        open_watch.triggered.connect(self.open_watch_folder.emit)
        quick_menu.addAction(open_watch)
        
        open_output = QAction("Open Output Folder", quick_menu)
        open_output.triggered.connect(self.open_output_folder.emit)
        quick_menu.addAction(open_output)
        
        quick_menu.addSeparator()
        
        view_stats = QAction("View Statistics", quick_menu)
        view_stats.triggered.connect(lambda: self.show_window_and_tab(2))
        quick_menu.addAction(view_stats)
        
        view_logs = QAction("View Logs", quick_menu)
        view_logs.triggered.connect(lambda: self.show_window_and_tab(4))
        quick_menu.addAction(view_logs)
        
        menu.addSeparator()
        
        # Settings
        settings = QAction("Settings", menu)
        settings.triggered.connect(lambda: self.show_window_and_tab(1))
        menu.addAction(settings)
        
        menu.addSeparator()
        
        # Exit
        exit_action = QAction("Exit", menu)
        exit_action.triggered.connect(self.exit_app.emit)
        menu.addAction(exit_action)
        
        self.tray_icon.setContextMenu(menu)
    
    def on_tray_activated(self, reason):
        """Handle tray icon activation (clicks)"""
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            # Single click - toggle window
            self.toggle_window()
        elif reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            # Double click - show window
            self.show_window.emit()
    
    def toggle_window(self):
        """Toggle main window visibility"""
        if self.main_window.isVisible():
            self.main_window.hide()
            self.show_action.setText("Show Window")
            self.show_notification(
                "Minimized to Tray",
                "Smart File Organizer is running in the background"
            )
        else:
            self.show_window.emit()
            self.show_action.setText("Hide to Tray")
    
    def show_window_and_tab(self, tab_index):
        """Show window and switch to specific tab"""
        self.show_window.emit()
        if hasattr(self.main_window, 'tabs'):
            self.main_window.tabs.setCurrentIndex(tab_index)
    
    def toggle_monitoring(self):
        """Toggle monitoring state"""
        if self.is_monitoring:
            self.stop_monitoring.emit()
        else:
            self.start_monitoring.emit()
    
    def update_monitoring_state(self, is_active):
        """Update monitoring state and menu text"""
        self.is_monitoring = is_active
        
        if is_active:
            self.monitor_action.setText("Stop Monitoring")
            self.tray_icon.setToolTip("Smart File Organizer Pro (Active)")
        else:
            self.monitor_action.setText("Start Monitoring")
            self.tray_icon.setToolTip("Smart File Organizer Pro (Stopped)")
    
    def show_notification(self, title, message, icon=None):
        """Show system tray notification"""
        if not self.tray_icon or not self.tray_icon.isVisible():
            logger.debug("Tray icon not visible, skipping notification")
            return
        
        try:
            if icon is None:
                icon = QSystemTrayIcon.MessageIcon.Information
            
            # Use the tray icon itself for notification icon
            # This ensures the notification shows your custom icon
            self.tray_icon.showMessage(
                title,
                message,
                self.tray_icon.icon(),  # Use the actual tray icon
                5000  # 5 seconds
            )
        except Exception as e:
            logger.warning(f"Failed to show notification: {e}")
    
    def show_file_processed(self, filename, success, category):
        """Show notification when file is processed"""
        if success:
            self.show_notification(
                "File Organized",
                f"{filename} -> {category}",
                QSystemTrayIcon.MessageIcon.Information
            )
        else:
            self.show_notification(
                "Error",
                f"Failed to organize: {filename}",
                QSystemTrayIcon.MessageIcon.Warning
            )
    
    def show_batch_complete(self, total, success, failed):
        """Show notification when batch is complete"""
        success_rate = (success / total * 100) if total > 0 else 0
        self.show_notification(
            "Batch Complete",
            f"Organized {success}/{total} files ({success_rate:.1f}% success)",
            QSystemTrayIcon.MessageIcon.Information
        )
    
    def cleanup(self):
        """Cleanup system tray resources"""
        if self.tray_icon:
            self.tray_icon.hide()
            self.tray_icon = None
            logger.info("System tray cleaned up")