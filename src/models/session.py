"""Session state management."""
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any

logger = logging.getLogger(__name__)


class Session:
    """Trading session state tracking."""
    
    def __init__(self):
        """Initialize a new session."""
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.active: bool = False
        self.trade_count: int = 0
        self.max_position_size: float = 0.0
        self.sum_pnl: float = 0.0
        self.violations: List[Dict[str, Any]] = []
        self.cooldown_active: bool = False
        self.cooldown_ends_at: Optional[datetime] = None
    
    def start(self):
        """Start a new session."""
        self.start_time = datetime.now()
        self.active = True
        self.trade_count = 0
        self.max_position_size = 0.0
        self.sum_pnl = 0.0
        self.violations = []
        self.cooldown_active = False
        self.cooldown_ends_at = None
        logger.info(f"Session started at {self.start_time}")
    
    def end(self) -> dict:
        """End the session and return summary data."""
        self.end_time = datetime.now()
        self.active = False
        logger.info(f"Session ended at {self.end_time}")
        return self.get_summary()
    
    def record_violation(self, rule: str, severity: str):
        """Record a rule violation."""
        violation = {
            "rule": rule,
            "severity": severity,
            "timestamp": datetime.now().isoformat()
        }
        self.violations.append(violation)
        logger.debug(f"Recorded violation: {violation}")
    
    def start_cooldown(self, minutes: int):
        """Start a cooldown period."""
        self.cooldown_active = True
        self.cooldown_ends_at = datetime.now() + timedelta(minutes=minutes)
        logger.info(f"Cooldown started for {minutes} minutes, ends at {self.cooldown_ends_at}")
    
    def is_cooldown_expired(self) -> bool:
        """Check if cooldown has expired."""
        if not self.cooldown_active or self.cooldown_ends_at is None:
            return True
        
        if datetime.now() >= self.cooldown_ends_at:
            self.cooldown_active = False
            logger.debug("Cooldown expired")
            return True
        
        return False
    
    def update_trade_state(self, pnl: float, position_size: float, trade_count: int):
        """Update trade statistics."""
        if not self.active:
            logger.warning("Attempted to update inactive session")
            return
        
        self.sum_pnl += pnl
        self.trade_count = trade_count
        self.max_position_size = max(self.max_position_size, position_size)
    
    def get_summary(self) -> dict:
        """Get session summary for saving."""
        if not self.start_time:
            logger.warning("Session summary requested but session never started")
            return {}
        
        return {
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "final_pnl": self.sum_pnl,
            "total_trades": self.trade_count,
            "max_position_size": self.max_position_size,
            "rule_violations": self.violations,
            "adherence_score": None,  # Will be filled by risk engine
            "profitability_score": None,
            "discipline_score": None,
            "session_grade": None
        }