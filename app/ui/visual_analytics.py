"""
Ultra Professional Visual Analytics Dashboard - PyQt6 Compatible
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QComboBox, QLabel, QPushButton, QFrame, QGridLayout,
    QScrollArea, QTextEdit, QSizePolicy, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont
import logging

logger = logging.getLogger("FileOrganizer")


class StatCard(QFrame):
    """Professional stat card widget"""
    def __init__(self, icon, title, value, color, parent=None):
        super().__init__(parent)
        self.color = color
        self.setup_ui(icon, title, value)
    
    def setup_ui(self, icon, title, value):
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet(f"""
            StatCard {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2d2d2d, stop:1 #1e1e1e);
                border-left: 4px solid {self.color};
                border-radius: 8px;
                padding: 15px;
            }}
            StatCard:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #353535, stop:1 #262626);
            }}
        """)
        self.setMinimumHeight(110)
        self.setMaximumHeight(130)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(15, 12, 15, 12)
        
        # Top row - icon and value
        top_layout = QHBoxLayout()
        top_layout.setSpacing(10)
        
        icon_label = QLabel(icon)
        icon_label.setFont(QFont("Segoe UI Emoji", 28))
        icon_label.setStyleSheet("background: transparent;")
        top_layout.addWidget(icon_label)
        
        top_layout.addStretch()
        
        self.value_label = QLabel(value)
        value_font = QFont("Segoe UI", 24, QFont.Weight.Bold)
        self.value_label.setFont(value_font)
        self.value_label.setStyleSheet(f"color: {self.color}; background: transparent;")
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        top_layout.addWidget(self.value_label)
        
        layout.addLayout(top_layout)
        
        # Bottom - title
        title_label = QLabel(title)
        title_label.setFont(QFont("Segoe UI", 11))
        title_label.setStyleSheet("color: #999999; background: transparent;")
        layout.addWidget(title_label)
    
    def update_value(self, value):
        """Update card value"""
        self.value_label.setText(value)


class VisualAnalytics(QWidget):
    """Ultra Professional Visual Analytics Dashboard"""
    
    def __init__(self, database, parent=None):
        super().__init__(parent)
        self.database = database
        self.matplotlib_available = False
        self.stat_cards = []
        self.init_ui()
    
    def init_ui(self):
        """Initialize professional UI"""
        # Main layout with scroll
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea {
                background-color: #1e1e1e;
                border: none;
            }
            QScrollBar:vertical {
                background: #2d2d2d;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: #555555;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #666666;
            }
        """)
        
        # Container widget
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setSpacing(20)
        container_layout.setContentsMargins(20, 20, 20, 20)
        
        # Header section
        header = self.create_header()
        container_layout.addWidget(header)
        
        # Control panel
        controls = self.create_control_panel()
        container_layout.addWidget(controls)
        
        # KPI Cards
        cards = self.create_kpi_cards()
        container_layout.addWidget(cards)
        
        # Charts section
        charts = self.create_charts_section()
        container_layout.addWidget(charts, 1)
        
        scroll.setWidget(container)
        main_layout.addWidget(scroll)
        
        # Load initial data
        self.update_charts()
        
        # Auto-refresh timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_charts)
        self.timer.start(30000)  # 30 seconds
    
    def create_header(self):
        """Create modern gradient header"""
        header = QFrame()
        header.setFrameShape(QFrame.Shape.StyledPanel)
        header.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #0078d7, stop:0.5 #0086e8, stop:1 #00a2e8);
                border-radius: 12px;
            }
        """)
        header.setMinimumHeight(120)
        header.setMaximumHeight(140)
        
        layout = QVBoxLayout(header)
        layout.setSpacing(10)
        layout.setContentsMargins(30, 20, 30, 20)
        
        # Title with icon and live indicator row
        title_row = QHBoxLayout()
        title_row.setSpacing(15)
        
        # Icon
        icon_label = QLabel("📊")
        icon_label.setFont(QFont("Segoe UI Emoji", 32))
        icon_label.setStyleSheet("background: transparent; color: white;")
        title_row.addWidget(icon_label)
        
        # Title and subtitle container
        title_container = QVBoxLayout()
        title_container.setSpacing(5)
        
        # Title
        title = QLabel("Visual Analytics Dashboard")
        title_font = QFont("Segoe UI", 24, QFont.Weight.Bold)
        title.setFont(title_font)
        title.setStyleSheet("color: white; background: transparent;")
        title_container.addWidget(title)
        
        # Subtitle
        subtitle = QLabel("Real-time insights and performance metrics")
        subtitle.setFont(QFont("Segoe UI", 12))
        subtitle.setStyleSheet("color: rgba(255, 255, 255, 0.9); background: transparent;")
        title_container.addWidget(subtitle)
        
        title_row.addLayout(title_container)
        
        title_row.addStretch()
        
        # Live indicator
        live_indicator = QLabel("● LIVE")
        live_indicator.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        live_indicator.setStyleSheet("""
            QLabel {
                color: #00ff00;
                background: rgba(0, 0, 0, 0.25);
                padding: 8px 16px;
                border-radius: 15px;
                border: 2px solid rgba(0, 255, 0, 0.3);
            }
        """)
        live_indicator.setMinimumHeight(35)
        live_indicator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_row.addWidget(live_indicator)
        
        layout.addLayout(title_row)
        
        return header
    
    def create_control_panel(self):
        """Create enhanced control panel"""
        panel = QFrame()
        panel.setFrameShape(QFrame.Shape.StyledPanel)
        panel.setStyleSheet("""
            QFrame {
                background-color: #2d2d2d;
                border: 1px solid #3d3d3d;
                border-radius: 10px;
                padding: 15px;
            }
        """)
        
        layout = QHBoxLayout(panel)
        layout.setSpacing(15)
        
        # Time range section
        range_container = QFrame()
        range_container.setStyleSheet("background: transparent; border: none;")
        range_layout = QHBoxLayout(range_container)
        range_layout.setContentsMargins(0, 0, 0, 0)
        range_layout.setSpacing(10)
        
        time_icon = QLabel("📅")
        time_icon.setFont(QFont("Segoe UI Emoji", 16))
        range_layout.addWidget(time_icon)
        
        time_label = QLabel("Time Range:")
        time_font = QFont("Segoe UI", 11, QFont.Weight.Bold)
        time_label.setFont(time_font)
        time_label.setStyleSheet("color: white;")
        range_layout.addWidget(time_label)
        
        self.time_range = QComboBox()
        self.time_range.addItems([
            "Last 24 Hours",
            "Last 7 Days",
            "Last 30 Days", 
            "Last 90 Days",
            "Last Year",
            "All Time"
        ])
        self.time_range.setCurrentIndex(2)
        self.time_range.currentIndexChanged.connect(self.update_charts)
        self.time_range.setMinimumWidth(160)
        self.time_range.setStyleSheet("""
            QComboBox {
                background-color: #1e1e1e;
                color: white;
                border: 2px solid #555555;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 11px;
                font-weight: bold;
            }
            QComboBox:hover {
                border-color: #0078d7;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid white;
                margin-right: 8px;
            }
            QComboBox QAbstractItemView {
                background-color: #2d2d2d;
                color: white;
                selection-background-color: #0078d7;
                border: 1px solid #555555;
            }
        """)
        range_layout.addWidget(self.time_range)
        
        layout.addWidget(range_container)
        layout.addStretch()
        
        # Summary label
        self.summary_label = QLabel("Loading...")
        self.summary_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.summary_label.setStyleSheet("color: #aaaaaa;")
        layout.addWidget(self.summary_label)
        
        layout.addStretch()
        
        # Action buttons
        export_btn = QPushButton("📤 Export")
        export_btn.setMinimumHeight(38)
        export_btn.setStyleSheet("""
            QPushButton {
                background-color: #7fba00;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 20px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #6da000;
            }
            QPushButton:pressed {
                background-color: #5a8a00;
            }
        """)
        export_btn.clicked.connect(self.export_data)
        layout.addWidget(export_btn)
        
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setMinimumHeight(38)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #0078d7;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 20px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #006cc1;
            }
            QPushButton:pressed {
                background-color: #005a9e;
            }
        """)
        refresh_btn.clicked.connect(self.update_charts)
        layout.addWidget(refresh_btn)
        
        return panel
    
    def create_kpi_cards(self):
        """Create KPI dashboard cards"""
        container = QWidget()
        layout = QGridLayout(container)
        layout.setSpacing(15)
        layout.setContentsMargins(0, 0, 0, 0)
        
        cards_data = [
            ("📁", "Total Files", "0", "#0078d7"),
            ("💾", "Total Storage", "0 MB", "#7fba00"),
            ("📊", "Categories", "0", "#ffb900"),
            ("⚡", "Processing Speed", "0/day", "#f25022"),
        ]
        
        for i, (icon, title, value, color) in enumerate(cards_data):
            card = StatCard(icon, title, value, color)
            self.stat_cards.append(card)
            layout.addWidget(card, 0, i)
        
        return container
    
    def create_charts_section(self):
        """Create charts section with tabs"""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(15)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Try matplotlib
        try:
            from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
            from matplotlib.figure import Figure
            import matplotlib.pyplot as plt
            
            plt.style.use('dark_background')
            
            # Pie Chart
            pie_group = self.create_chart_container("📊 Files by Category")
            pie_layout = QVBoxLayout()
            
            self.category_figure = Figure(figsize=(10, 5), facecolor='#1e1e1e')
            self.category_canvas = FigureCanvasQTAgg(self.category_figure)
            self.category_canvas.setMinimumHeight(350)
            self.category_canvas.setStyleSheet("background-color: #1e1e1e;")
            pie_layout.addWidget(self.category_canvas)
            
            pie_group.setLayout(pie_layout)
            layout.addWidget(pie_group)
            
            # Storage Bar Chart
            storage_group = self.create_chart_container("💾 Storage Usage by Category")
            storage_layout = QVBoxLayout()
            
            self.storage_figure = Figure(figsize=(10, 5), facecolor='#1e1e1e')
            self.storage_canvas = FigureCanvasQTAgg(self.storage_figure)
            self.storage_canvas.setMinimumHeight(350)
            self.storage_canvas.setStyleSheet("background-color: #1e1e1e;")
            storage_layout.addWidget(self.storage_canvas)
            
            storage_group.setLayout(storage_layout)
            layout.addWidget(storage_group)
            
            # Timeline Chart
            timeline_group = self.create_chart_container("📈 Files Organized Over Time")
            timeline_layout = QVBoxLayout()
            
            self.timeline_figure = Figure(figsize=(10, 5), facecolor='#1e1e1e')
            self.timeline_canvas = FigureCanvasQTAgg(self.timeline_figure)
            self.timeline_canvas.setMinimumHeight(350)
            self.timeline_canvas.setStyleSheet("background-color: #1e1e1e;")
            timeline_layout.addWidget(self.timeline_canvas)
            
            timeline_group.setLayout(timeline_layout)
            layout.addWidget(timeline_group)
            
            self.matplotlib_available = True
            
        except ImportError:
            self.matplotlib_available = False
            fallback = self.create_fallback_display()
            layout.addWidget(fallback)
        
        return container
    
    def create_chart_container(self, title):
        """Create styled container for charts"""
        group = QGroupBox(title)
        group.setStyleSheet("""
            QGroupBox {
                background-color: #2d2d2d;
                border: 1px solid #3d3d3d;
                border-radius: 10px;
                padding: 20px;
                margin-top: 15px;
                font-weight: bold;
                font-size: 13px;
                color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 20px;
                padding: 0 10px;
                background-color: #2d2d2d;
            }
        """)
        return group
    
    def create_fallback_display(self):
        """Create fallback when matplotlib not available"""
        group = self.create_chart_container("📊 Statistics Overview")
        layout = QVBoxLayout()
        
        info = QLabel(
            "💡 <b>Install matplotlib for visual charts:</b><br><br>"
            "<code style='background-color: #1e1e1e; padding: 8px; border-radius: 4px;'>"
            "pip install matplotlib</code><br><br>"
            "Showing text-based statistics below:"
        )
        info.setTextFormat(Qt.TextFormat.RichText)
        info.setWordWrap(True)
        info.setStyleSheet("""
            QLabel {
                color: #cccccc;
                background-color: rgba(0, 120, 215, 0.1);
                padding: 20px;
                border-radius: 8px;
                border-left: 4px solid #0078d7;
            }
        """)
        layout.addWidget(info)
        
        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        self.stats_text.setFont(QFont("Consolas", 10))
        self.stats_text.setMinimumHeight(400)
        self.stats_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #cccccc;
                border: 1px solid #3d3d3d;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        layout.addWidget(self.stats_text)
        
        group.setLayout(layout)
        return group
    
    def update_charts(self):
        """Update all visualizations"""
        try:
            range_days = {
                "Last 24 Hours": 1,
                "Last 7 Days": 7,
                "Last 30 Days": 30,
                "Last 90 Days": 90,
                "Last Year": 365,
                "All Time": 10000
            }
            days = range_days.get(self.time_range.currentText(), 30)
            
            stats = self.database.get_statistics(days=days)
            category_summary = self.database.get_category_summary()
            
            # Update KPI cards
            self.update_kpi_cards(category_summary)
            
            # Update charts
            if self.matplotlib_available:
                self._render_matplotlib_charts(stats, category_summary)
            else:
                self._render_text_stats(stats, category_summary)
        
        except Exception as e:
            logger.error(f"Chart update failed: {e}", exc_info=True)
    
    def update_kpi_cards(self, category_summary):
        """Update KPI cards with latest data"""
        total_files = sum(c.get('total_files', 0) for c in category_summary) if category_summary else 0
        total_size = sum(c.get('total_size', 0) for c in category_summary) if category_summary else 0
        total_categories = len(category_summary) if category_summary else 0
        avg_speed = total_files / 30 if total_files > 0 else 0
        
        self.summary_label.setText(
            f"📊 {total_files:,} files  •  💾 {total_size/(1024*1024):.1f} MB  •  📁 {total_categories} categories"
        )
        
        if len(self.stat_cards) >= 4:
            self.stat_cards[0].update_value(f"{total_files:,}")
            self.stat_cards[1].update_value(f"{total_size/(1024*1024):.1f} MB")
            self.stat_cards[2].update_value(str(total_categories))
            self.stat_cards[3].update_value(f"{avg_speed:.1f}/day")
    
    def _render_matplotlib_charts(self, stats, category_summary):
        """Render beautiful matplotlib charts"""
        try:
            colors = ['#0078d7', '#00a2e8', '#7fba00', '#ffb900', 
                     '#f25022', '#c239b3', '#e74856', '#00bcf2']
            
            # PIE CHART
            self.category_figure.clear()
            ax1 = self.category_figure.add_subplot(111, facecolor='#1e1e1e')
            
            if category_summary and sum(c.get('total_files', 0) for c in category_summary) > 0:
                categories = [s['category'] for s in category_summary]
                counts = [s['total_files'] for s in category_summary]
                
                wedges, texts, autotexts = ax1.pie(
                    counts, labels=categories, autopct='%1.1f%%',
                    colors=colors[:len(categories)], startangle=90,
                    textprops={'color': 'white', 'fontsize': 12, 'fontweight': 'bold'},
                    wedgeprops={'edgecolor': '#1e1e1e', 'linewidth': 2}
                )
                
                for autotext in autotexts:
                    autotext.set_color('white')
                    autotext.set_fontweight('bold')
                
                ax1.axis('equal')
            else:
                ax1.text(0.5, 0.5, '📁\n\nNo files organized yet\nStart monitoring to see data', 
                        ha='center', va='center', fontsize=14, color='#888888')
                ax1.axis('off')
            
            self.category_figure.patch.set_facecolor('#1e1e1e')
            self.category_figure.tight_layout(pad=2)
            self.category_canvas.draw()
            
            # STORAGE BAR CHART
            self.storage_figure.clear()
            ax2 = self.storage_figure.add_subplot(111, facecolor='#1e1e1e')
            
            if category_summary and sum(c.get('total_size', 0) for c in category_summary) > 0:
                categories = [s['category'] for s in category_summary]
                sizes_mb = [s['total_size'] / (1024 * 1024) for s in category_summary]
                
                sorted_data = sorted(zip(categories, sizes_mb), key=lambda x: x[1], reverse=True)
                categories, sizes_mb = zip(*sorted_data)
                
                bars = ax2.barh(categories, sizes_mb, color=colors[:len(categories)],
                               edgecolor='#1e1e1e', linewidth=2, height=0.6)
                
                ax2.set_xlabel('Storage (MB)', fontsize=12, color='white', fontweight='bold')
                ax2.grid(True, axis='x', alpha=0.2, linestyle='--', color='#555555')
                ax2.tick_params(colors='white', labelsize=11)
                
                for bar, size in zip(bars, sizes_mb):
                    width = bar.get_width()
                    ax2.text(width + max(sizes_mb)*0.01, bar.get_y() + bar.get_height()/2,
                            f'{size:.1f} MB', ha='left', va='center',
                            fontsize=10, color='white', fontweight='bold')
                
                for spine in ax2.spines.values():
                    spine.set_color('#555555')
            else:
                ax2.text(0.5, 0.5, '💾\n\nNo storage data yet\nOrganize files to track usage', 
                        ha='center', va='center', transform=ax2.transAxes,
                        fontsize=14, color='#888888')
                ax2.axis('off')
            
            self.storage_figure.patch.set_facecolor('#1e1e1e')
            self.storage_figure.tight_layout(pad=2)
            self.storage_canvas.draw()
            
            # TIMELINE CHART
            self.timeline_figure.clear()
            ax3 = self.timeline_figure.add_subplot(111, facecolor='#1e1e1e')
            
            if stats and len(stats) > 0:
                from collections import defaultdict
                daily_counts = defaultdict(int)
                
                for stat in stats:
                    daily_counts[stat.get('date', '')] += stat.get('files_processed', 0)
                
                dates = sorted(daily_counts.keys())
                counts = [daily_counts[d] for d in dates]
                
                if dates and sum(counts) > 0:
                    ax3.plot(dates, counts, marker='o', linewidth=3,
                            color='#0078d7', markersize=7, markerfacecolor='#00a2e8',
                            markeredgecolor='white', markeredgewidth=2)
                    ax3.fill_between(range(len(dates)), counts, alpha=0.3, color='#0078d7')
                    
                    ax3.set_xlabel('Date', fontsize=12, color='white', fontweight='bold')
                    ax3.set_ylabel('Files Organized', fontsize=12, color='white', fontweight='bold')
                    ax3.grid(True, alpha=0.2, linestyle='--', color='#555555')
                    ax3.tick_params(colors='white', labelsize=11)
                    
                    step = max(1, len(dates) // 10)
                    ax3.set_xticks(range(0, len(dates), step))
                    ax3.set_xticklabels([dates[i] for i in range(0, len(dates), step)],
                                       rotation=45, ha='right')
                    
                    for spine in ax3.spines.values():
                        spine.set_color('#555555')
                else:
                    ax3.text(0.5, 0.5, '📈\n\nNo activity yet\nStart organizing to track progress', 
                            ha='center', va='center', transform=ax3.transAxes,
                            fontsize=14, color='#888888')
                    ax3.axis('off')
            else:
                ax3.text(0.5, 0.5, '📈\n\nNo activity yet\nStart organizing to track progress', 
                        ha='center', va='center', transform=ax3.transAxes,
                        fontsize=14, color='#888888')
                ax3.axis('off')
            
            self.timeline_figure.patch.set_facecolor('#1e1e1e')
            self.timeline_figure.tight_layout(pad=2)
            self.timeline_canvas.draw()
        
        except Exception as e:
            logger.error(f"Matplotlib rendering failed: {e}", exc_info=True)
    
    def _render_text_stats(self, stats, category_summary):
        """Render text-based stats"""
        output = []
        output.append("╔" + "═" * 78 + "╗")
        output.append("║" + " " * 25 + "📊 STATISTICS SUMMARY" + " " * 32 + "║")
        output.append("╚" + "═" * 78 + "╝")
        output.append("")
        
        output.append("┌─ FILES BY CATEGORY " + "─" * 58 + "┐")
        if category_summary:
            max_files = max((c.get('total_files', 0) for c in category_summary), default=0)
            for cat in category_summary:
                files = cat.get('total_files', 0)
                size_mb = cat.get('total_size', 0) / (1024 * 1024)
                bar_len = int((files / max_files) * 40) if max_files > 0 else 0
                bar = "█" * bar_len + "░" * (40 - bar_len)
                output.append(f"│  {cat['category']:<20} │{bar}│ {files:>6} files  {size_mb:>8.1f} MB")
        else:
            output.append("│  No data available")
        output.append("└" + "─" * 78 + "┘")
        
        self.stats_text.setText("\n".join(output))
    
    def export_data(self):
        """Export analytics data"""
        try:
            import json
            from datetime import datetime
            
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Export Analytics",
                f"analytics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                "JSON Files (*.json)"
            )
            
            if file_path:
                data = {
                    "export_date": datetime.now().isoformat(),
                    "time_range": self.time_range.currentText(),
                    "summary": self.database.get_category_summary(),
                    "statistics": self.database.get_statistics(days=365)
                }
                
                with open(file_path, 'w') as f:
                    json.dump(data, f, indent=2)
                
                QMessageBox.information(self, "Success", f"Data exported to:\n{file_path}")
        except Exception as e:
            logger.error(f"Export failed: {e}", exc_info=True)