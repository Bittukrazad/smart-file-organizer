# ============================================
# FILE: app/resources/generate_icon.py (IMPROVED)
# ============================================

"""Generate application icon for system tray"""
from PyQt6.QtGui import QPixmap, QPainter, QColor, QPen, QLinearGradient
from PyQt6.QtCore import Qt
from pathlib import Path


def generate_app_icon(size=256, output_path="icon.png"):
    """Generate a professional-looking app icon"""
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    
    # Draw background circle with gradient
    gradient = QLinearGradient(0, 0, size, size)
    gradient.setColorAt(0, QColor(0, 120, 215))
    gradient.setColorAt(1, QColor(0, 180, 255))
    
    painter.setBrush(gradient)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawEllipse(0, 0, size, size)
    
    # Draw folder icon
    folder_color = QColor(255, 255, 255, 230)
    painter.setBrush(folder_color)
    
    folder_width = size * 0.6
    folder_height = size * 0.45
    folder_x = (size - folder_width) / 2
    folder_y = size * 0.35
    
    painter.drawRect(int(folder_x), int(folder_y), int(folder_width), int(folder_height))
    
    # Folder tab
    tab_width = folder_width * 0.4
    tab_height = size * 0.08
    painter.drawRect(int(folder_x), int(folder_y - tab_height), int(tab_width), int(tab_height))
    
    # Draw organizing lines
    pen = QPen(QColor(0, 120, 215))
    pen.setWidth(int(size * 0.04))
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    painter.setPen(pen)
    
    center_x = size / 2
    center_y = folder_y + folder_height / 2
    line_length = folder_width * 0.3
    
    for i in range(3):
        y = center_y - line_length/4 + i * line_length/4
        painter.drawLine(
            int(center_x - line_length/2), int(y),
            int(center_x + line_length/2), int(y)
        )
    
    painter.end()
    
    # Save icon
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    pixmap.save(str(output))
    
    print(f"Icon generated: {output}")
    
    # Save smaller sizes
    for small_size in [16, 32, 48, 64, 128]:
        small_pixmap = pixmap.scaled(
            small_size, small_size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        small_output = output.parent / f"icon_{small_size}.png"
        small_pixmap.save(str(small_output))
        print(f"Icon generated: {small_output}")


if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    generate_app_icon(256, "resources/icon.png")
    print("\nAll icons generated successfully!")
    sys.exit(0)