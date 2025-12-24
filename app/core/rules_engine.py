# ============================================
# FILE: app/core/rules_engine.py (NEW)
# Smart rules engine for custom organization
# ============================================

"""Smart rules engine for custom file organization"""
import re
import logging
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import json

logger = logging.getLogger("FileOrganizer")


class Rule:
    """Represents a single organization rule"""
    
    def __init__(self, rule_id: int, name: str, pattern: str, 
                 target_folder: str, conditions: Dict, 
                 priority: int = 0, enabled: bool = True):
        self.id = rule_id
        self.name = name
        self.pattern = pattern  # Filename pattern (glob or regex)
        self.target_folder = target_folder
        self.conditions = conditions  # Additional conditions
        self.priority = priority  # Higher priority = checked first
        self.enabled = enabled
    
    def matches(self, file_path: Path, metadata: Dict = None) -> bool:
        """Check if file matches this rule"""
        if not self.enabled:
            return False
        
        try:
            # Check filename pattern
            if not self._match_pattern(file_path):
                return False
            
            # Check additional conditions
            if not self._check_conditions(file_path, metadata):
                return False
            
            return True
        
        except Exception as e:
            logger.error(f"Rule matching failed: {e}")
            return False
    
    def _match_pattern(self, file_path: Path) -> bool:
        """Check if filename matches pattern"""
        filename = file_path.name
        
        # Check if pattern is regex (contains special chars)
        if any(c in self.pattern for c in ['[', ']', '(', ')', '^', '$', '+']):
            # Regex pattern
            return bool(re.match(self.pattern, filename, re.IGNORECASE))
        else:
            # Glob pattern
            return file_path.match(self.pattern)
    
    def _check_conditions(self, file_path: Path, metadata: Dict = None) -> bool:
        """Check additional conditions"""
        if not self.conditions:
            return True
        
        metadata = metadata or {}
        
        # File size condition
        if "min_size_mb" in self.conditions:
            size_mb = file_path.stat().st_size / (1024 * 1024)
            if size_mb < self.conditions["min_size_mb"]:
                return False
        
        if "max_size_mb" in self.conditions:
            size_mb = file_path.stat().st_size / (1024 * 1024)
            if size_mb > self.conditions["max_size_mb"]:
                return False
        
        # File age condition
        if "older_than_days" in self.conditions:
            file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
            age_days = (datetime.now() - file_time).days
            if age_days < self.conditions["older_than_days"]:
                return False
        
        if "newer_than_days" in self.conditions:
            file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
            age_days = (datetime.now() - file_time).days
            if age_days > self.conditions["newer_than_days"]:
                return False
        
        # Extension condition
        if "extensions" in self.conditions:
            if file_path.suffix.lower() not in self.conditions["extensions"]:
                return False
        
        # Content-based conditions
        if "contains_text" in self.conditions:
            text = metadata.get("content_text", "")
            if self.conditions["contains_text"].lower() not in text.lower():
                return False
        
        # Metadata conditions
        if "has_gps" in self.conditions:
            if metadata.get("metadata", {}).get("has_gps") != self.conditions["has_gps"]:
                return False
        
        return True
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "pattern": self.pattern,
            "target_folder": self.target_folder,
            "conditions": self.conditions,
            "priority": self.priority,
            "enabled": self.enabled
        }
    
    @staticmethod
    def from_dict(data: Dict) -> 'Rule':
        """Create from dictionary"""
        return Rule(
            rule_id=data["id"],
            name=data["name"],
            pattern=data["pattern"],
            target_folder=data["target_folder"],
            conditions=data.get("conditions", {}),
            priority=data.get("priority", 0),
            enabled=data.get("enabled", True)
        )


class RulesEngine:
    """Manage and apply custom organization rules"""
    
    def __init__(self, rules_file: str = "organization_rules.json"):
        self.rules_file = Path(rules_file)
        self.rules: List[Rule] = []
        self.load_rules()
    
    def load_rules(self):
        """Load rules from file"""
        try:
            if self.rules_file.exists():
                with open(self.rules_file, 'r') as f:
                    data = json.load(f)
                    self.rules = [Rule.from_dict(r) for r in data]
                    # Sort by priority (highest first)
                    self.rules.sort(key=lambda r: r.priority, reverse=True)
                    logger.info(f"Loaded {len(self.rules)} rules")
            else:
                self._create_default_rules()
        except Exception as e:
            logger.error(f"Failed to load rules: {e}")
            self.rules = []
    
    def save_rules(self):
        """Save rules to file"""
        try:
            data = [r.to_dict() for r in self.rules]
            with open(self.rules_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Saved {len(self.rules)} rules")
        except Exception as e:
            logger.error(f"Failed to save rules: {e}")
    
    def _create_default_rules(self):
        """Create default rules"""
        self.rules = [
            Rule(1, "Screenshots", "*screenshot*", "Screenshots", {}, priority=10),
            Rule(2, "Downloads", "*download*", "Downloads", {}, priority=9),
            Rule(3, "Invoices", "*invoice*", "Finance/Invoices", 
                 {"extensions": [".pdf"]}, priority=8),
            Rule(4, "Large Videos", "*.mp4", "Videos/Large",
                 {"min_size_mb": 100}, priority=7),
            Rule(5, "Old Documents", "*.pdf", "Archive/Old",
                 {"older_than_days": 365}, priority=6),
            Rule(6, "Photos with GPS", "*.jpg", "Photos/Locations",
                 {"has_gps": True}, priority=5)
        ]
        self.save_rules()
    
    def apply_rules(self, file_path: Path, metadata: Dict = None) -> Optional[str]:
        """
        Apply rules to file and return target folder
        Returns None if no rule matches
        """
        for rule in self.rules:
            if rule.matches(file_path, metadata):
                logger.info(f"Rule '{rule.name}' matched for {file_path.name}")
                return rule.target_folder
        
        return None
    
    def add_rule(self, rule: Rule):
        """Add a new rule"""
        self.rules.append(rule)
        self.rules.sort(key=lambda r: r.priority, reverse=True)
        self.save_rules()
    
    def remove_rule(self, rule_id: int):
        """Remove a rule"""
        self.rules = [r for r in self.rules if r.id != rule_id]
        self.save_rules()
    
    def update_rule(self, rule: Rule):
        """Update existing rule"""
        for i, r in enumerate(self.rules):
            if r.id == rule.id:
                self.rules[i] = rule
                break
        self.rules.sort(key=lambda r: r.priority, reverse=True)
        self.save_rules()
    
    def toggle_rule(self, rule_id: int):
        """Enable/disable a rule"""
        for rule in self.rules:
            if rule.id == rule_id:
                rule.enabled = not rule.enabled
                break
        self.save_rules()
    
    def get_next_id(self) -> int:
        """Get next available rule ID"""
        if not self.rules:
            return 1
        return max(r.id for r in self.rules) + 1