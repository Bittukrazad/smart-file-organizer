# FILE: app/core/config.py
"""Application configuration"""
from pydantic import BaseModel, Field, validator
from pathlib import Path
from typing import Optional
import json

class AppConfig(BaseModel):
    """Application configuration with validation"""
    watch_folder: Path
    organized_folder: Path
    duplicate_folder: Path
    
    auto_rename: bool = True
    enable_duplicates: bool = True
    cloud_backup: bool = False
    ai_classification: bool = False
    
    max_file_size_mb: int = Field(default=1000, ge=1)
    scan_interval_sec: int = Field(default=5, ge=1)
    
    class Config:
        arbitrary_types_allowed = True
    
    @validator('watch_folder', 'organized_folder', 'duplicate_folder')
    def validate_paths(cls, v):
        if not isinstance(v, Path):
            v = Path(v)
        return v.resolve()
    
    def save(self, path: Path):
        """Save configuration to JSON"""
        with open(path, 'w') as f:
            data = self.dict()
            data['watch_folder'] = str(data['watch_folder'])
            data['organized_folder'] = str(data['organized_folder'])
            data['duplicate_folder'] = str(data['duplicate_folder'])
            json.dump(data, f, indent=4)
    
    @classmethod
    def load(cls, path: Path) -> 'AppConfig':
        """Load configuration from JSON"""
        with open(path) as f:
            return cls.model_validate(json.load(f))