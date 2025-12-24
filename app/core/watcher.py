# FILE: app/core/watcher.py
"""File system watcher"""
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import logging
from typing import Callable
import time

logger = logging.getLogger("FileOrganizer")

class FileWatcher(FileSystemEventHandler):
    """Watch folder for file changes"""
    
    def __init__(self, callback: Callable[[Path], None]):
        self.callback = callback
    
    def on_created(self, event):
        if not event.is_directory:
            time.sleep(0.5)
            try:
                self.callback(Path(event.src_path))
            except Exception as e:
                logger.error(f"Error processing {event.src_path}: {e}")
    
    def on_moved(self, event):
        if not event.is_directory:
            time.sleep(0.5)
            try:
                self.callback(Path(event.dest_path))
            except Exception as e:
                logger.error(f"Error processing {event.dest_path}: {e}")


class FolderMonitor:
    """Monitor folder and trigger organization"""
    
    def __init__(self, watch_path: Path, callback: Callable[[Path], None]):
        self.watch_path = watch_path
        self.callback = callback
        self.observer = Observer()
        self._running = False
    
    def start(self):
        """Start monitoring"""
        if self._running:
            return
        
        handler = FileWatcher(self.callback)
        self.observer.schedule(handler, str(self.watch_path), recursive=False)
        self.observer.start()
        self._running = True
        logger.info(f"Started monitoring {self.watch_path}")
    
    def stop(self):
        """Stop monitoring"""
        if not self._running:
            return
        
        self.observer.stop()
        self.observer.join()
        self._running = False
        logger.info("Stopped monitoring")
    
    def is_running(self) -> bool:
        return self._running