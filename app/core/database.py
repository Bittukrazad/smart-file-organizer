# ============================================
# FILE: app/core/database.py
# Complete SQLite Database System
# ============================================

"""Database management for Smart File Organizer Pro"""
import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Tuple
import logging
from contextlib import contextmanager

logger = logging.getLogger("FileOrganizer")


class Database:
    """SQLite database manager for persistent storage"""
    
    def __init__(self, db_path: str = "file_organizer.db"):
        self.db_path = Path(db_path)
        self.connection = None
        self.initialize_database()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}", exc_info=True)
            raise
        finally:
            conn.close()
    
    def initialize_database(self):
        """Create database tables if they don't exist"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # File operations history
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS file_operations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        filename TEXT NOT NULL,
                        original_path TEXT NOT NULL,
                        destination_path TEXT NOT NULL,
                        category TEXT NOT NULL,
                        operation_type TEXT NOT NULL,
                        file_size INTEGER,
                        file_hash TEXT,
                        success INTEGER NOT NULL,
                        error_message TEXT,
                        can_undo INTEGER DEFAULT 1
                    )
                """)
                
                # Duplicate files cache
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS duplicate_hashes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        file_hash TEXT UNIQUE NOT NULL,
                        original_path TEXT NOT NULL,
                        file_size INTEGER,
                        first_seen TEXT NOT NULL,
                        last_seen TEXT NOT NULL,
                        duplicate_count INTEGER DEFAULT 0
                    )
                """)
                
                # Statistics and analytics
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS statistics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        date TEXT NOT NULL,
                        category TEXT NOT NULL,
                        files_processed INTEGER DEFAULT 0,
                        total_size INTEGER DEFAULT 0,
                        duplicates_found INTEGER DEFAULT 0,
                        errors_count INTEGER DEFAULT 0,
                        UNIQUE(date, category)
                    )
                """)
                
                # Configuration history
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS config_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        config_json TEXT NOT NULL,
                        description TEXT
                    )
                """)
                
                # User sessions
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS sessions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        start_time TEXT NOT NULL,
                        end_time TEXT,
                        mode TEXT NOT NULL,
                        watch_folder TEXT NOT NULL,
                        files_processed INTEGER DEFAULT 0,
                        status TEXT DEFAULT 'active'
                    )
                """)
                
                # Create indexes for better performance
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_operations_timestamp 
                    ON file_operations(timestamp)
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_operations_filename 
                    ON file_operations(filename)
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_duplicate_hash 
                    ON duplicate_hashes(file_hash)
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_statistics_date 
                    ON statistics(date)
                """)
                
                logger.info("Database initialized successfully")
                
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}", exc_info=True)
            raise
    
    # ==========================================
    # FILE OPERATIONS
    # ==========================================
    
    def log_operation(self, filename: str, original_path: str, 
                     destination_path: str, category: str,
                     operation_type: str, file_size: int = 0,
                     file_hash: str = None, success: bool = True,
                     error_message: str = None) -> int:
        """Log a file operation to database"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO file_operations 
                    (timestamp, filename, original_path, destination_path, 
                     category, operation_type, file_size, file_hash, 
                     success, error_message)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    datetime.now().isoformat(),
                    filename,
                    original_path,
                    destination_path,
                    category,
                    operation_type,
                    file_size,
                    file_hash,
                    1 if success else 0,
                    error_message
                ))
                
                operation_id = cursor.lastrowid
                logger.debug(f"Logged operation ID: {operation_id}")
                return operation_id
                
        except Exception as e:
            logger.error(f"Failed to log operation: {e}", exc_info=True)
            return -1
    
    def get_operation_history(self, limit: int = 100, 
                             offset: int = 0) -> List[Dict]:
        """Get operation history"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM file_operations 
                    ORDER BY timestamp DESC 
                    LIMIT ? OFFSET ?
                """, (limit, offset))
                
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Failed to get operation history: {e}")
            return []
    
    def get_undoable_operations(self, limit: int = 50) -> List[Dict]:
        """Get operations that can be undone"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM file_operations 
                    WHERE can_undo = 1 AND success = 1
                    ORDER BY timestamp DESC 
                    LIMIT ?
                """, (limit,))
                
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Failed to get undoable operations: {e}")
            return []
    
    def mark_operation_undone(self, operation_id: int):
        """Mark an operation as undone"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE file_operations 
                    SET can_undo = 0 
                    WHERE id = ?
                """, (operation_id,))
                logger.info(f"Marked operation {operation_id} as undone")
                
        except Exception as e:
            logger.error(f"Failed to mark operation as undone: {e}")
    
    def search_operations(self, search_term: str, 
                         limit: int = 100) -> List[Dict]:
        """Search operations by filename"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM file_operations 
                    WHERE filename LIKE ? 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                """, (f"%{search_term}%", limit))
                
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Failed to search operations: {e}")
            return []
    
    # ==========================================
    # DUPLICATE MANAGEMENT
    # ==========================================
    
    def add_duplicate_hash(self, file_hash: str, file_path: str, 
                          file_size: int) -> bool:
        """Add or update duplicate hash entry"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                now = datetime.now().isoformat()
                
                # Check if hash exists
                cursor.execute("""
                    SELECT id, duplicate_count FROM duplicate_hashes 
                    WHERE file_hash = ?
                """, (file_hash,))
                
                existing = cursor.fetchone()
                
                if existing:
                    # Update existing
                    cursor.execute("""
                        UPDATE duplicate_hashes 
                        SET last_seen = ?, duplicate_count = duplicate_count + 1
                        WHERE file_hash = ?
                    """, (now, file_hash))
                    logger.debug(f"Updated duplicate hash: {file_hash}")
                    return True  # Is duplicate
                else:
                    # Insert new
                    cursor.execute("""
                        INSERT INTO duplicate_hashes 
                        (file_hash, original_path, file_size, first_seen, last_seen)
                        VALUES (?, ?, ?, ?, ?)
                    """, (file_hash, file_path, file_size, now, now))
                    logger.debug(f"Added new hash: {file_hash}")
                    return False  # Not duplicate
                    
        except Exception as e:
            logger.error(f"Failed to add duplicate hash: {e}")
            return False
    
    def is_duplicate_hash(self, file_hash: str) -> Tuple[bool, Optional[str]]:
        """Check if hash exists (returns is_dup, original_path)"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT original_path FROM duplicate_hashes 
                    WHERE file_hash = ?
                """, (file_hash,))
                
                row = cursor.fetchone()
                if row:
                    return True, row['original_path']
                return False, None
                
        except Exception as e:
            logger.error(f"Failed to check duplicate hash: {e}")
            return False, None
    
    def get_duplicate_statistics(self) -> Dict:
        """Get duplicate statistics"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_unique,
                        SUM(duplicate_count) as total_duplicates,
                        SUM(file_size * duplicate_count) as wasted_space
                    FROM duplicate_hashes
                """)
                
                row = cursor.fetchone()
                return dict(row) if row else {}
                
        except Exception as e:
            logger.error(f"Failed to get duplicate statistics: {e}")
            return {}
    
    def clear_duplicate_cache(self):
        """Clear duplicate hash cache"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM duplicate_hashes")
                logger.info("Cleared duplicate cache")
                
        except Exception as e:
            logger.error(f"Failed to clear duplicate cache: {e}")
    
    # ==========================================
    # STATISTICS
    # ==========================================
    
    def update_statistics(self, category: str, files_count: int = 0,
                         total_size: int = 0, duplicates: int = 0,
                         errors: int = 0):
        """Update daily statistics"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                date = datetime.now().strftime("%Y-%m-%d")
                
                cursor.execute("""
                    INSERT INTO statistics 
                    (date, category, files_processed, total_size, 
                     duplicates_found, errors_count)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(date, category) DO UPDATE SET
                        files_processed = files_processed + ?,
                        total_size = total_size + ?,
                        duplicates_found = duplicates_found + ?,
                        errors_count = errors_count + ?
                """, (
                    date, category, files_count, total_size, 
                    duplicates, errors,
                    files_count, total_size, duplicates, errors
                ))
                
        except Exception as e:
            logger.error(f"Failed to update statistics: {e}")
    
    def get_statistics(self, days: int = 30) -> List[Dict]:
        """Get statistics for last N days"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM statistics 
                    WHERE date >= date('now', '-' || ? || ' days')
                    ORDER BY date DESC, category
                """, (days,))
                
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return []
    
    def get_category_summary(self) -> List[Dict]:
        """Get summary by category (all time)"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        category,
                        SUM(files_processed) as total_files,
                        SUM(total_size) as total_size,
                        SUM(duplicates_found) as total_duplicates
                    FROM statistics 
                    GROUP BY category
                    ORDER BY total_files DESC
                """)
                
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Failed to get category summary: {e}")
            return []
    
    # ==========================================
    # SESSIONS
    # ==========================================
    
    def start_session(self, mode: str, watch_folder: str) -> int:
        """Start a new session"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO sessions 
                    (start_time, mode, watch_folder)
                    VALUES (?, ?, ?)
                """, (datetime.now().isoformat(), mode, watch_folder))
                
                session_id = cursor.lastrowid
                logger.info(f"Started session ID: {session_id}")
                return session_id
                
        except Exception as e:
            logger.error(f"Failed to start session: {e}")
            return -1
    
    def end_session(self, session_id: int, files_processed: int):
        """End a session"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE sessions 
                    SET end_time = ?, files_processed = ?, status = 'completed'
                    WHERE id = ?
                """, (datetime.now().isoformat(), files_processed, session_id))
                
                logger.info(f"Ended session ID: {session_id}")
                
        except Exception as e:
            logger.error(f"Failed to end session: {e}")
    
    def get_recent_sessions(self, limit: int = 10) -> List[Dict]:
        """Get recent sessions"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM sessions 
                    ORDER BY start_time DESC 
                    LIMIT ?
                """, (limit,))
                
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Failed to get recent sessions: {e}")
            return []
    
    # ==========================================
    # CONFIGURATION
    # ==========================================
    
    def save_config(self, config_dict: Dict, description: str = None):
        """Save configuration snapshot"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO config_history 
                    (timestamp, config_json, description)
                    VALUES (?, ?, ?)
                """, (
                    datetime.now().isoformat(),
                    json.dumps(config_dict),
                    description
                ))
                
                logger.info("Saved configuration snapshot")
                
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
    
    def get_config_history(self, limit: int = 10) -> List[Dict]:
        """Get configuration history"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM config_history 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                """, (limit,))
                
                rows = cursor.fetchall()
                result = []
                for row in rows:
                    row_dict = dict(row)
                    row_dict['config'] = json.loads(row_dict['config_json'])
                    result.append(row_dict)
                return result
                
        except Exception as e:
            logger.error(f"Failed to get config history: {e}")
            return []
    
    # ==========================================
    # MAINTENANCE
    # ==========================================
    
    def vacuum_database(self):
        """Optimize database (VACUUM)"""
        try:
            with self.get_connection() as conn:
                conn.execute("VACUUM")
                logger.info("Database vacuumed successfully")
                
        except Exception as e:
            logger.error(f"Failed to vacuum database: {e}")
    
    def get_database_size(self) -> int:
        """Get database file size in bytes"""
        try:
            return self.db_path.stat().st_size if self.db_path.exists() else 0
        except Exception as e:
            logger.error(f"Failed to get database size: {e}")
            return 0
    
    def export_data(self, output_file: str):
        """Export all data to JSON"""
        try:
            data = {
                'operations': self.get_operation_history(limit=10000),
                'statistics': self.get_statistics(days=365),
                'sessions': self.get_recent_sessions(limit=100),
                'export_time': datetime.now().isoformat()
            }
            
            with open(output_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Exported data to {output_file}")
            
        except Exception as e:
            logger.error(f"Failed to export data: {e}")
    
    def clear_old_data(self, days: int = 90):
        """Clear data older than specified days"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cutoff_date = datetime.now().isoformat()
                
                # Clear old operations
                cursor.execute("""
                    DELETE FROM file_operations 
                    WHERE timestamp < date('now', '-' || ? || ' days')
                """, (days,))
                
                deleted = cursor.rowcount
                logger.info(f"Cleared {deleted} old operations")
                
        except Exception as e:
            logger.error(f"Failed to clear old data: {e}")
            
    def close(self):
        """
        Close database connection and cleanup
        
        Note: This class uses context managers for connections,
        so there's typically no persistent connection to close.
        This method is provided for compatibility and to ensure
        any potential lingering connections are cleaned up.
        """
        try:
            # Check if there's a persistent connection attribute
            if hasattr(self, 'connection') and self.connection:
                self.connection.close()
                self.connection = None
                logger.info("Database connection closed")
            
            # Also close any lingering connections (shouldn't happen with context managers)
            # This is a safety measure
            logger.info("Database cleanup completed")
            
        except Exception as e:
            logger.error(f"Error closing database: {e}", exc_info=True)
    
    def __del__(self):
        """Destructor - ensure cleanup on object deletion"""
        try:
            self.close()
        except:
            pass  # Ignore errors in destructor
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup"""
        self.close()
        return False        

