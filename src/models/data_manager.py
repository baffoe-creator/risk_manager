"""Data management layer for SQLite persistence."""
import json
import logging
import sqlite3
from pathlib import Path
from typing import Optional, Dict, List, Any

logger = logging.getLogger(__name__)


class DataManager:
    """Handles all database operations for the Risk Manager."""
    
    def __init__(self, db_path: Optional[Path] = None):
        """Initialize database connection and create tables if needed."""
        if db_path is None:
            db_path = Path(__file__).parent.parent.parent / "database" / "trader_rules.db"
        
        self.db_path = db_path
        self.db_path.parent.mkdir(exist_ok=True)
        
        self._init_db()
    
    def _init_db(self):
        """Create tables if they don't exist."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create settings table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS settings (
                        id INTEGER PRIMARY KEY,
                        key TEXT UNIQUE,
                        value TEXT
                    )
                """)
                
                # Create sessions table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS sessions (
                        id INTEGER PRIMARY KEY,
                        start_time DATETIME,
                        end_time DATETIME,
                        final_pnl REAL,
                        total_trades INTEGER,
                        max_position_size REAL,
                        rule_violations TEXT,
                        adherence_score REAL,
                        profitability_score REAL,
                        discipline_score REAL,
                        session_grade TEXT
                    )
                """)
                
                conn.commit()
                logger.info("Database initialized successfully")
                
        except sqlite3.Error as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    def get_setting(self, key: str) -> Optional[str]:
        """Get a setting value by key."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
                result = cursor.fetchone()
                return result[0] if result else None
                
        except sqlite3.Error as e:
            logger.error(f"Failed to get setting '{key}': {e}")
            return None
    
    def save_setting(self, key: str, value: str) -> bool:
        """Save a setting value."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                    (key, value)
                )
                conn.commit()
                logger.debug(f"Saved setting '{key}' = '{value}'")
                return True
                
        except sqlite3.Error as e:
            logger.error(f"Failed to save setting '{key}': {e}")
            return False
    
    def get_all_settings(self) -> Dict[str, str]:
        """Get all settings as a dictionary."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT key, value FROM settings")
                return {row[0]: row[1] for row in cursor.fetchall()}
                
        except sqlite3.Error as e:
            logger.error(f"Failed to get all settings: {e}")
            return {}
    
    def save_session(self, session_data: dict) -> Optional[int]:
        """Save a session and return its ID."""
        try:
            # Convert rule_violations to JSON if it's a list
            if "rule_violations" in session_data and isinstance(session_data["rule_violations"], list):
                session_data["rule_violations"] = json.dumps(session_data["rule_violations"])
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                columns = list(session_data.keys())
                placeholders = ", ".join(["?"] * len(columns))
                columns_str = ", ".join(columns)
                
                query = f"INSERT INTO sessions ({columns_str}) VALUES ({placeholders})"
                cursor.execute(query, list(session_data.values()))
                
                session_id = cursor.lastrowid
                conn.commit()
                
                logger.info(f"Saved session with ID: {session_id}")
                return session_id
                
        except (sqlite3.Error, json.JSONEncodeError) as e:
            logger.error(f"Failed to save session: {e}")
            return None
    
    def get_session_history(self) -> List[Dict[str, Any]]:
        """Get all sessions as a list of dictionaries."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("SELECT * FROM sessions ORDER BY start_time DESC")
                rows = cursor.fetchall()
                
                sessions = []
                for row in rows:
                    session_dict = dict(row)
                    # Decode rule_violations from JSON if present
                    if "rule_violations" in session_dict and session_dict["rule_violations"]:
                        try:
                            session_dict["rule_violations"] = json.loads(session_dict["rule_violations"])
                        except json.JSONDecodeError:
                            logger.warning(f"Failed to decode rule_violations for session {session_dict.get('id')}")
                            session_dict["rule_violations"] = []
                    sessions.append(session_dict)
                
                return sessions
                
        except sqlite3.Error as e:
            logger.error(f"Failed to get session history: {e}")
            return []
    
    def seed_default_settings(self):
        """Seed default settings on first run."""
        defaults = {
            "daily_loss_limit": "1000.0",
            "max_contract_size": "10.0",
            "max_trades_per_day": "20",
            "trading_cutoff_time": "16:00",
            "consecutive_loss_limit": "5",
            "cooldown_period_minutes": "30",
            "rule_severity_map": json.dumps({
                "daily_loss_limit": "major",
                "max_contract_size": "major",
                "max_trades_per_day": "minor",
                "trading_cutoff_time": "minor",
                "consecutive_loss_limit": "major",
                "cooldown_period_minutes": "minor"
            })
        }
        
        for key, value in defaults.items():
            if self.get_setting(key) is None:
                self.save_setting(key, value)
                logger.info(f"Seeded default setting: {key} = {value}")