# app/ui/theme.py
"""Modern dark theme styling"""
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPalette, QColor
from PyQt6.QtCore import Qt

def apply_dark_theme(app: QApplication):
    """Apply modern dark theme to application"""
    palette = QPalette()
    
    # Colors
    dark_bg = QColor(30, 30, 30)
    darker_bg = QColor(20, 20, 20)
    light_text = QColor(220, 220, 220)
    accent = QColor(0, 120, 215)
    accent_light = QColor(0, 150, 255)
    
    palette.setColor(QPalette.ColorRole.Window, dark_bg)
    palette.setColor(QPalette.ColorRole.WindowText, light_text)
    palette.setColor(QPalette.ColorRole.Base, darker_bg)
    palette.setColor(QPalette.ColorRole.AlternateBase, dark_bg)
    palette.setColor(QPalette.ColorRole.ToolTipBase, darker_bg)
    palette.setColor(QPalette.ColorRole.ToolTipText, light_text)
    palette.setColor(QPalette.ColorRole.Text, light_text)
    palette.setColor(QPalette.ColorRole.Button, dark_bg)
    palette.setColor(QPalette.ColorRole.ButtonText, light_text)
    palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
    palette.setColor(QPalette.ColorRole.Link, accent)
    palette.setColor(QPalette.ColorRole.Highlight, accent)
    palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.white)
    
    app.setPalette(palette)
    
    # Stylesheet
    app.setStyleSheet("""
        QMainWindow {
            background-color: #1e1e1e;
        }
        QGroupBox {
            border: 1px solid #3a3a3a;
            border-radius: 8px;
            margin-top: 12px;
            padding: 15px;
            font-weight: bold;
            color: #e0e0e0;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px;
        }
        QPushButton {
            background-color: #2d2d2d;
            border: 1px solid #3a3a3a;
            border-radius: 6px;
            padding: 3px 20px;
            color: #e0e0e0;
            font-size: 13px;
            font-weight: 500;
        }
        QPushButton:hover {
            background-color: #3a3a3a;
            border: 1px solid #0078d7;
        }
        QPushButton:pressed {
            background-color: #2a2a2a;
        }
        QPushButton:disabled {
            background-color: #252525;
            color: #666666;
        }
        QPushButton#startButton {
            background-color: #0078d7;
            border: none;
        }
        QPushButton#startButton:hover {
            background-color: #0096ff;
        }
        QPushButton#stopButton {
            background-color: #d73737;
            border: none;
        }
        QPushButton#stopButton:hover {
            background-color: #ff4444;
        }
        QLabel {
            color: #e0e0e0;
        }
        QTextEdit, QListWidget, QTableWidget {
            background-color: #1a1a1a;
            border: 1px solid #3a3a3a;
            border-radius: 6px;
            padding: 8px;
            color: #e0e0e0;
        }
        QLineEdit, QComboBox {
            background-color: #2d2d2d;
            border: 1px solid #3a3a3a;
            border-radius: 6px;
            padding: 8px;
            color: #e0e0e0;
        }
        QLineEdit:focus, QComboBox:focus {
            border: 1px solid #0078d7;
        }
        QCheckBox {
            color: #e0e0e0;
            spacing: 8px;
        }
        QCheckBox::indicator {
            width: 18px;
            height: 18px;
            border-radius: 4px;
            border: 1px solid #3a3a3a;
            background-color: #2d2d2d;
        }
        QCheckBox::indicator:checked {
            background-color: #0078d7;
            border: 1px solid #0078d7;
        }
        QProgressBar {
            border: 1px solid #3a3a3a;
            border-radius: 6px;
            text-align: center;
            background-color: #2d2d2d;
        }
        QProgressBar::chunk {
            background-color: #0078d7;
            border-radius: 5px;
        }
        QTabWidget::pane {
            border: 1px solid #3a3a3a;
            border-radius: 6px;
            background-color: #1e1e1e;
        }
        QTabBar::tab {
            background-color: #2d2d2d;
            border: 1px solid #3a3a3a;
            padding: 10px 20px;
            margin-right: 2px;
            border-top-left-radius: 6px;
            border-top-right-radius: 6px;
        }
        QTabBar::tab:selected {
            background-color: #1e1e1e;
            border-bottom-color: #1e1e1e;
        }
        QTabBar::tab:hover {
            background-color: #3a3a3a;
        }
        QScrollArea {
            border: none;
            background-color: transparent;
        }
        
        QScrollBar:vertical {
            border: none;
            background-color: #2d2d2d;
            width: 12px;
            border-radius: 6px;
            margin: 0px;
        }
        
        QScrollBar::handle:vertical {
            background-color: #4a4a4a;
            border-radius: 6px;
            min-height: 20px;
        }
        
        QScrollBar::handle:vertical:hover {
            background-color: #5a5a5a;
        }
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
        }
        
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
            background: none;
        }
        
    """)
