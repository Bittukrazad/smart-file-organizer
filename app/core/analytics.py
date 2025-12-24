# FILE: app/core/analytics.py

"""File analytics and statistics"""
from collections import defaultdict
from pathlib import Path

class FileAnalytics:
    """Track file organization analytics"""
    
    def __init__(self):
        self.category_data = defaultdict(lambda: {"count": 0, "total_size": 0})
        self.file_registry = []  # Track all processed files
    
    def add_file(self, filename: str, category: str, size: int = 0):
        """
        Add file to analytics with size calculation
        
        Args:
            filename: Name of the file
            category: Category assigned to the file
            size: File size in bytes (if 0, will be calculated from file_path)
        """
        self.category_data[category]["count"] += 1
        self.category_data[category]["total_size"] += size
        
        # Track file entry
        self.file_registry.append({
            "filename": filename,
            "category": category,
            "size": size
        })
    
    def get_category_stats(self) -> dict:
        """Get statistics by category with proper size formatting"""
        result = {}
        for category, data in self.category_data.items():
            size_bytes = data["total_size"]
            size_str = self._format_size(size_bytes)
            
            result[category] = {
                "count": data["count"],
                "size": size_str
            }
        return result
    
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
        
        if unit_index == 0:  # Bytes
            return f"{int(size)} {units[unit_index]}"
        else:
            return f"{size:.2f} {units[unit_index]}"
    
    def get_total_size(self) -> str:
        """Get total size of all files"""
        total = sum(data["total_size"] for data in self.category_data.values())
        return self._format_size(total)
    
    def get_total_files(self) -> int:
        """Get total number of files processed"""
        return sum(data["count"] for data in self.category_data.values())
    
    def clear(self):
        """Clear all analytics data"""
        self.category_data.clear()
        self.file_registry.clear()
