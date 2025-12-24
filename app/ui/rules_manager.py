# ============================================
# FILE: app/ui/rules_manager.py (NEW)
# Rules management UI
# ============================================

"""Rules management UI"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QPushButton, QLabel, QMessageBox,
    QLineEdit, QSpinBox, QCheckBox, QComboBox,
    QGroupBox, QFormLayout, QTextEdit,
    QWidget
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
import logging

from ..core.rules_engine import Rule, RulesEngine

logger = logging.getLogger("FileOrganizer")


class RuleEditor(QDialog):
    """Dialog for creating/editing rules"""
    
    def __init__(self, rule: Rule = None, rules_engine: RulesEngine = None, parent=None):
        super().__init__(parent)
        self.rule = rule
        self.rules_engine = rules_engine
        self.setWindowTitle("Edit Rule" if rule else "New Rule")
        self.setGeometry(100, 100, 600, 500)
        self.init_ui()
        
        if rule:
            self.load_rule()
    
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)
        
        # Form
        form = QFormLayout()
        
        # Rule name
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g., Screenshots")
        form.addRow("Rule Name:", self.name_input)
        
        # Pattern
        self.pattern_input = QLineEdit()
        self.pattern_input.setPlaceholderText("e.g., *screenshot*.png or invoice_.*\.pdf")
        form.addRow("File Pattern:", self.pattern_input)
        
        # Pattern help
        pattern_help = QLabel("Use * for wildcards or regex patterns")
        pattern_help.setStyleSheet("color: #888888; font-size: 10px;")
        form.addRow("", pattern_help)
        
        # Target folder
        self.target_input = QLineEdit()
        self.target_input.setPlaceholderText("e.g., Screenshots or Finance/Invoices")
        form.addRow("Target Folder:", self.target_input)
        
        # Priority
        self.priority_spin = QSpinBox()
        self.priority_spin.setRange(0, 100)
        self.priority_spin.setValue(5)
        form.addRow("Priority:", self.priority_spin)
        
        # Enabled
        self.enabled_check = QCheckBox("Enabled")
        self.enabled_check.setChecked(True)
        form.addRow("", self.enabled_check)
        
        layout.addLayout(form)
        
        # Conditions group
        conditions_group = QGroupBox("Additional Conditions (Optional)")
        conditions_layout = QVBoxLayout()
        
        # File size
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("File Size:"))
        size_layout.addWidget(QLabel("Min (MB):"))
        self.min_size_spin = QSpinBox()
        self.min_size_spin.setRange(0, 10000)
        self.min_size_spin.setSpecialValueText("No limit")
        size_layout.addWidget(self.min_size_spin)
        size_layout.addWidget(QLabel("Max (MB):"))
        self.max_size_spin = QSpinBox()
        self.max_size_spin.setRange(0, 10000)
        self.max_size_spin.setSpecialValueText("No limit")
        size_layout.addWidget(self.max_size_spin)
        size_layout.addStretch()
        conditions_layout.addLayout(size_layout)
        
        # File age
        age_layout = QHBoxLayout()
        age_layout.addWidget(QLabel("File Age:"))
        age_layout.addWidget(QLabel("Older than (days):"))
        self.older_spin = QSpinBox()
        self.older_spin.setRange(0, 3650)
        self.older_spin.setSpecialValueText("Any")
        age_layout.addWidget(self.older_spin)
        age_layout.addWidget(QLabel("Newer than (days):"))
        self.newer_spin = QSpinBox()
        self.newer_spin.setRange(0, 3650)
        self.newer_spin.setSpecialValueText("Any")
        age_layout.addWidget(self.newer_spin)
        age_layout.addStretch()
        conditions_layout.addLayout(age_layout)
        
        # Contains text
        text_layout = QHBoxLayout()
        text_layout.addWidget(QLabel("Contains Text:"))
        self.contains_input = QLineEdit()
        self.contains_input.setPlaceholderText("Text to search in file content")
        text_layout.addWidget(self.contains_input)
        conditions_layout.addLayout(text_layout)
        
        conditions_group.setLayout(conditions_layout)
        layout.addWidget(conditions_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        save_btn = QPushButton("💾 Save Rule")
        save_btn.clicked.connect(self.save_rule)
        button_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
    
    def load_rule(self):
        """Load rule data into form"""
        self.name_input.setText(self.rule.name)
        self.pattern_input.setText(self.rule.pattern)
        self.target_input.setText(self.rule.target_folder)
        self.priority_spin.setValue(self.rule.priority)
        self.enabled_check.setChecked(self.rule.enabled)
        
        # Load conditions
        if "min_size_mb" in self.rule.conditions:
            self.min_size_spin.setValue(self.rule.conditions["min_size_mb"])
        if "max_size_mb" in self.rule.conditions:
            self.max_size_spin.setValue(self.rule.conditions["max_size_mb"])
        if "older_than_days" in self.rule.conditions:
            self.older_spin.setValue(self.rule.conditions["older_than_days"])
        if "newer_than_days" in self.rule.conditions:
            self.newer_spin.setValue(self.rule.conditions["newer_than_days"])
        if "contains_text" in self.rule.conditions:
            self.contains_input.setText(self.rule.conditions["contains_text"])
    
    def save_rule(self):
        """Save rule"""
        # Validate
        if not self.name_input.text():
            QMessageBox.warning(self, "Validation", "Please enter a rule name")
            return
        if not self.pattern_input.text():
            QMessageBox.warning(self, "Validation", "Please enter a file pattern")
            return
        if not self.target_input.text():
            QMessageBox.warning(self, "Validation", "Please enter a target folder")
            return
        
        # Build conditions
        conditions = {}
        if self.min_size_spin.value() > 0:
            conditions["min_size_mb"] = self.min_size_spin.value()
        if self.max_size_spin.value() > 0:
            conditions["max_size_mb"] = self.max_size_spin.value()
        if self.older_spin.value() > 0:
            conditions["older_than_days"] = self.older_spin.value()
        if self.newer_spin.value() > 0:
            conditions["newer_than_days"] = self.newer_spin.value()
        if self.contains_input.text():
            conditions["contains_text"] = self.contains_input.text()
        
        # Create or update rule
        if self.rule:
            # Update existing
            self.rule.name = self.name_input.text()
            self.rule.pattern = self.pattern_input.text()
            self.rule.target_folder = self.target_input.text()
            self.rule.priority = self.priority_spin.value()
            self.rule.enabled = self.enabled_check.isChecked()
            self.rule.conditions = conditions
        else:
            # Create new
            rule_id = self.rules_engine.get_next_id() if self.rules_engine else 1
            self.rule = Rule(
                rule_id=rule_id,
                name=self.name_input.text(),
                pattern=self.pattern_input.text(),
                target_folder=self.target_input.text(),
                conditions=conditions,
                priority=self.priority_spin.value(),
                enabled=self.enabled_check.isChecked()
            )
        
        self.accept()


class RulesManager(QDialog):
    """Dialog for managing organization rules"""
    
    rules_changed = pyqtSignal()
    
    def __init__(self, rules_engine: RulesEngine, parent=None):
        super().__init__(parent)
        self.rules_engine = rules_engine
        self.setWindowTitle("Smart Rules Manager")
        self.setGeometry(100, 100, 800, 600)
        self.init_ui()
        self.load_rules()
    
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("📏 Smart Organization Rules")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        layout.addWidget(title)
        
        help_text = QLabel(
            "Create custom rules to automatically organize files based on patterns and conditions.\n"
            "Rules are checked in priority order (highest first)."
        )
        help_text.setStyleSheet("color: #888888;")
        help_text.setWordWrap(True)
        layout.addWidget(help_text)
        
        # Rules table
        self.rules_table = QTableWidget()
        self.rules_table.setColumnCount(6)
        self.rules_table.setHorizontalHeaderLabels([
            "Priority", "Name", "Pattern", "Target Folder", "Conditions", "Actions"
        ])
        self.rules_table.horizontalHeader().setStretchLastSection(True)
        self.rules_table.setAlternatingRowColors(True)
        layout.addWidget(self.rules_table)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        add_btn = QPushButton("➕ Add Rule")
        add_btn.clicked.connect(self.add_rule)
        button_layout.addWidget(add_btn)
        
        button_layout.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def load_rules(self):
        """Load rules into table"""
        self.rules_table.setRowCount(len(self.rules_engine.rules))
        
        for row, rule in enumerate(self.rules_engine.rules):
            # Priority
            priority_item = QTableWidgetItem(str(rule.priority))
            priority_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.rules_table.setItem(row, 0, priority_item)
            
            # Name
            name_item = QTableWidgetItem(rule.name)
            if not rule.enabled:
                name_item.setForeground(Qt.GlobalColor.gray)
            self.rules_table.setItem(row, 1, name_item)
            
            # Pattern
            self.rules_table.setItem(row, 2, QTableWidgetItem(rule.pattern))
            
            # Target
            self.rules_table.setItem(row, 3, QTableWidgetItem(rule.target_folder))
            
            # Conditions
            conditions_text = f"{len(rule.conditions)} condition(s)" if rule.conditions else "None"
            self.rules_table.setItem(row, 4, QTableWidgetItem(conditions_text))
            
            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(2, 2, 2, 2)
            
            edit_btn = QPushButton("✏️")
            edit_btn.setMaximumWidth(30)
            edit_btn.clicked.connect(lambda checked, r=rule: self.edit_rule(r))
            actions_layout.addWidget(edit_btn)
            
            toggle_btn = QPushButton("👁️" if rule.enabled else "🚫")
            toggle_btn.setMaximumWidth(30)
            toggle_btn.clicked.connect(lambda checked, r=rule: self.toggle_rule(r))
            actions_layout.addWidget(toggle_btn)
            
            delete_btn = QPushButton("🗑️")
            delete_btn.setMaximumWidth(30)
            delete_btn.clicked.connect(lambda checked, r=rule: self.delete_rule(r))
            actions_layout.addWidget(delete_btn)
            
            self.rules_table.setCellWidget(row, 5, actions_widget)
    
    def add_rule(self):
        """Add new rule"""
        editor = RuleEditor(rules_engine=self.rules_engine, parent=self)
        if editor.exec() == QDialog.DialogCode.Accepted:
            self.rules_engine.add_rule(editor.rule)
            self.load_rules()
            self.rules_changed.emit()
    
    def edit_rule(self, rule: Rule):
        """Edit existing rule"""
        editor = RuleEditor(rule=rule, rules_engine=self.rules_engine, parent=self)
        if editor.exec() == QDialog.DialogCode.Accepted:
            self.rules_engine.update_rule(rule)
            self.load_rules()
            self.rules_changed.emit()
    
    def toggle_rule(self, rule: Rule):
        """Enable/disable rule"""
        self.rules_engine.toggle_rule(rule.id)
        self.load_rules()
        self.rules_changed.emit()
    
    def delete_rule(self, rule: Rule):
        """Delete rule"""
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Delete rule '{rule.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.rules_engine.remove_rule(rule.id)
            self.load_rules()
            self.rules_changed.emit()