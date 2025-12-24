# ============================================
# FILE: app/ui/history_viewer.py (NEW)
# History viewer dialog
# ============================================

"""History and undo functionality viewer"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QPushButton, QLabel, QMessageBox,
    QLineEdit, QTabWidget, QWidget, QTextEdit
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from pathlib import Path
import shutil
import logging

logger = logging.getLogger("FileOrganizer")


class HistoryViewer(QDialog):
    """Dialog for viewing operation history and undo"""
    
    file_restored = pyqtSignal(str, str)  # filename, message
    
    def __init__(self, database, parent=None):
        super().__init__(parent)
        self.database = database
        self.init_ui()
        self.load_history()
    
    def init_ui(self):
        """Initialize UI"""
        self.setWindowTitle("Operation History & Undo")
        self.setGeometry(100, 100, 1000, 600)
        
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("📜 File Organization History")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Tabs
        tabs = QTabWidget()
        
        # History tab
        history_tab = self.create_history_tab()
        tabs.addTab(history_tab, "Recent Operations")
        
        # Statistics tab
        stats_tab = self.create_statistics_tab()
        tabs.addTab(stats_tab, "Statistics")
        
        # Sessions tab
        sessions_tab = self.create_sessions_tab()
        tabs.addTab(sessions_tab, "Sessions")
        
        layout.addWidget(tabs)
        
        # Bottom buttons
        button_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.load_history)
        button_layout.addWidget(refresh_btn)
        
        export_btn = QPushButton("📤 Export Data")
        export_btn.clicked.connect(self.export_data)
        button_layout.addWidget(export_btn)
        
        button_layout.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def create_history_tab(self):
        """Create history tab with undo functionality"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Search bar
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter filename to search...")
        self.search_input.textChanged.connect(self.search_history)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)
        
        # History table
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(7)
        self.history_table.setHorizontalHeaderLabels([
            "Time", "Filename", "From", "To", "Category", "Size", "Actions"
        ])
        self.history_table.horizontalHeader().setStretchLastSection(True)
        self.history_table.setAlternatingRowColors(True)
        layout.addWidget(self.history_table)
        
        # Info label
        self.info_label = QLabel("Select an operation to undo")
        self.info_label.setStyleSheet("color: #888888;")
        layout.addWidget(self.info_label)
        
        return widget
    
    def create_statistics_tab(self):
        """Create statistics tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Stats table
        self.stats_table = QTableWidget()
        self.stats_table.setColumnCount(5)
        self.stats_table.setHorizontalHeaderLabels([
            "Category", "Files", "Total Size", "Duplicates", "Errors"
        ])
        self.stats_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.stats_table)
        
        # Load statistics
        self.load_statistics()
        
        return widget
    
    def create_sessions_tab(self):
        """Create sessions tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Sessions table
        self.sessions_table = QTableWidget()
        self.sessions_table.setColumnCount(5)
        self.sessions_table.setHorizontalHeaderLabels([
            "Start Time", "End Time", "Mode", "Watch Folder", "Files Processed"
        ])
        self.sessions_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.sessions_table)
        
        # Load sessions
        self.load_sessions()
        
        return widget
    
    def load_history(self, search_term: str = None):
        """Load operation history"""
        try:
            if search_term:
                operations = self.database.search_operations(search_term)
            else:
                operations = self.database.get_undoable_operations()
            
            self.history_table.setRowCount(len(operations))
            
            for row, op in enumerate(operations):
                # Time
                time_str = op['timestamp'].split('T')[1][:8] if 'T' in op['timestamp'] else op['timestamp']
                self.history_table.setItem(row, 0, QTableWidgetItem(time_str))
                
                # Filename
                self.history_table.setItem(row, 1, QTableWidgetItem(op['filename']))
                
                # From
                from_path = Path(op['original_path']).parent.name
                self.history_table.setItem(row, 2, QTableWidgetItem(from_path))
                
                # To
                to_path = Path(op['destination_path']).parent.name
                self.history_table.setItem(row, 3, QTableWidgetItem(to_path))
                
                # Category
                self.history_table.setItem(row, 4, QTableWidgetItem(op['category']))
                
                # Size
                size_mb = op['file_size'] / (1024 * 1024) if op['file_size'] else 0
                self.history_table.setItem(row, 5, QTableWidgetItem(f"{size_mb:.2f} MB"))
                
                # Undo button
                if op['can_undo'] == 1:
                    undo_btn = QPushButton("↩️ Undo")
                    undo_btn.clicked.connect(lambda checked, op_id=op['id']: self.undo_operation(op_id))
                    self.history_table.setCellWidget(row, 6, undo_btn)
            
            self.info_label.setText(f"Showing {len(operations)} operations")
            
        except Exception as e:
            logger.error(f"Failed to load history: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to load history:\n{str(e)}")
    
    def search_history(self, text: str):
        """Search history"""
        if text:
            self.load_history(search_term=text)
        else:
            self.load_history()
    
    def undo_operation(self, operation_id: int):
        """Undo a file operation"""
        try:
            # Get operation details
            operations = self.database.get_operation_history(limit=1000)
            operation = next((op for op in operations if op['id'] == operation_id), None)
            
            if not operation:
                QMessageBox.warning(self, "Error", "Operation not found")
                return
            
            # Confirm undo
            reply = QMessageBox.question(
                self,
                "Confirm Undo",
                f"Undo this operation?\n\n"
                f"File: {operation['filename']}\n"
                f"Will move from: {operation['destination_path']}\n"
                f"Back to: {operation['original_path']}",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.No:
                return
            
            # Perform undo
            source = Path(operation['destination_path'])
            dest = Path(operation['original_path'])
            
            if not source.exists():
                QMessageBox.warning(
                    self,
                    "File Not Found",
                    f"Cannot undo: File not found at:\n{source}"
                )
                return
            
            # Ensure destination directory exists
            dest.parent.mkdir(parents=True, exist_ok=True)
            
            # Move file back
            shutil.move(str(source), str(dest))
            
            # Mark as undone in database
            self.database.mark_operation_undone(operation_id)
            
            # Log the undo operation
            self.database.log_operation(
                filename=operation['filename'],
                original_path=str(source),
                destination_path=str(dest),
                category="Undo",
                operation_type="undo",
                file_size=operation['file_size'],
                success=True
            )
            
            QMessageBox.information(
                self,
                "Success",
                f"File restored:\n{operation['filename']}"
            )
            
            self.file_restored.emit(operation['filename'], "Restored successfully")
            self.load_history()
            
        except Exception as e:
            logger.error(f"Failed to undo operation: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to undo:\n{str(e)}")
    
    def load_statistics(self):
        """Load statistics"""
        try:
            stats = self.database.get_category_summary()
            
            self.stats_table.setRowCount(len(stats))
            
            for row, stat in enumerate(stats):
                self.stats_table.setItem(row, 0, QTableWidgetItem(stat['category']))
                self.stats_table.setItem(row, 1, QTableWidgetItem(str(stat['total_files'])))
                
                size_mb = stat['total_size'] / (1024 * 1024) if stat['total_size'] else 0
                self.stats_table.setItem(row, 2, QTableWidgetItem(f"{size_mb:.2f} MB"))
                
                self.stats_table.setItem(row, 3, QTableWidgetItem(str(stat.get('total_duplicates', 0))))
                self.stats_table.setItem(row, 4, QTableWidgetItem("0"))  # Errors by category not tracked yet
            
        except Exception as e:
            logger.error(f"Failed to load statistics: {e}")
    
    def load_sessions(self):
        """Load sessions"""
        try:
            sessions = self.database.get_recent_sessions(limit=50)
            
            self.sessions_table.setRowCount(len(sessions))
            
            for row, session in enumerate(sessions):
                self.sessions_table.setItem(row, 0, QTableWidgetItem(session['start_time']))
                self.sessions_table.setItem(row, 1, QTableWidgetItem(session.get('end_time', 'Running...')))
                self.sessions_table.setItem(row, 2, QTableWidgetItem(session['mode']))
                self.sessions_table.setItem(row, 3, QTableWidgetItem(session['watch_folder']))
                self.sessions_table.setItem(row, 4, QTableWidgetItem(str(session['files_processed'])))
            
        except Exception as e:
            logger.error(f"Failed to load sessions: {e}")
    
    def export_data(self):
        """Export database data"""
        from PyQt6.QtWidgets import QFileDialog
        from datetime import datetime
        
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export Data",
            f"file_organizer_data_{datetime.now():%Y%m%d_%H%M%S}.json",
            "JSON Files (*.json)"
        )
        
        if filename:
            try:
                self.database.export_data(filename)
                QMessageBox.information(self, "Success", f"Data exported to:\n{filename}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export:\n{str(e)}")


