"""Tests for the Session class."""
import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import patch
from src.models.session import Session


class TestSession:
    """Tests for Session class."""
    
    def test_session_start(self):
        """Test starting a new session."""
        session = Session()
        
        # Session should be inactive initially
        assert session.active is False
        assert session.start_time is None
        
        # Start the session
        session.start()
        
        assert session.active is True
        assert session.start_time is not None
        assert session.end_time is None
        assert session.trade_count == 0
        assert session.max_position_size == 0.0
        assert session.sum_pnl == 0.0
        assert session.violations == []
        assert session.cooldown_active is False
        assert session.cooldown_ends_at is None
    
    def test_session_end(self):
        """Test ending a session."""
        session = Session()
        session.start()
        
        # Add a small delay to ensure timestamps differ
        time.sleep(0.01)  # 10ms delay
        
        # Add some data
        session.trade_count = 5
        session.sum_pnl = 500.0
        session.max_position_size = 3.0
        session.record_violation("daily_loss_limit", "major")
        
        # End the session
        summary = session.end()
        
        assert session.active is False
        assert session.end_time is not None
        # end_time should be >= start_time (with microsecond precision)
        assert session.end_time >= session.start_time
        # Ensure there's at least some time difference
        assert (session.end_time - session.start_time).total_seconds() >= 0
        
        # Check summary
        assert summary["start_time"] == session.start_time.isoformat()
        assert summary["end_time"] == session.end_time.isoformat()
        assert summary["final_pnl"] == 500.0
        assert summary["total_trades"] == 5
        assert summary["max_position_size"] == 3.0
        assert len(summary["rule_violations"]) == 1
        assert summary["rule_violations"][0]["rule"] == "daily_loss_limit"
        assert summary["rule_violations"][0]["severity"] == "major"
    
    def test_session_end_inactive(self):
        """Test ending an inactive session."""
        session = Session()
        
        # Don't start the session
        summary = session.end()
        
        assert summary == {}
        assert session.active is False
        assert session.end_time is None
    
    def test_record_violation(self):
        """Test recording violations."""
        session = Session()
        session.start()
        
        # Record a violation
        session.record_violation("max_contract_size", "major")
        
        assert len(session.violations) == 1
        assert session.violations[0]["rule"] == "max_contract_size"
        assert session.violations[0]["severity"] == "major"
        assert "timestamp" in session.violations[0]
        
        # Record another violation
        session.record_violation("max_trades_per_day", "minor")
        
        assert len(session.violations) == 2
        assert session.violations[1]["rule"] == "max_trades_per_day"
        assert session.violations[1]["severity"] == "minor"
    
    def test_start_cooldown(self):
        """Test starting a cooldown period."""
        session = Session()
        session.start()
        
        # Start cooldown
        session.start_cooldown(30)
        
        assert session.cooldown_active is True
        assert session.cooldown_ends_at is not None
        
        # Check cooldown end time is approximately 30 minutes in the future
        expected_end = datetime.now() + timedelta(minutes=30)
        diff = abs((session.cooldown_ends_at - expected_end).total_seconds())
        assert diff < 1.0  # Within 1 second
    
    def test_cooldown_expired(self):
        """Test checking if cooldown has expired."""
        session = Session()
        session.start()
        
        # Start cooldown
        session.start_cooldown(30)
        assert session.cooldown_active is True
        
        # Should not be expired immediately
        assert session.is_cooldown_expired() is False
        
        # Manually set cooldown_ends_at to the past
        session.cooldown_ends_at = datetime.now() - timedelta(minutes=5)
        
        # Should be expired now
        assert session.is_cooldown_expired() is True
        assert session.cooldown_active is False
    
    def test_cooldown_no_active(self):
        """Test is_cooldown_expired when no cooldown is active."""
        session = Session()
        session.start()
        
        # No cooldown active
        assert session.cooldown_active is False
        assert session.is_cooldown_expired() is True
        
        # Cooldown with no end time
        session.cooldown_active = True
        session.cooldown_ends_at = None
        assert session.is_cooldown_expired() is True
    
    def test_update_trade_stats(self):
        """Test updating trade statistics."""
        session = Session()
        session.start()
        
        # Update with first trade
        session.update_trade_stats(100.0, 2.0)
        assert session.sum_pnl == 100.0
        assert session.trade_count == 1
        assert session.max_position_size == 2.0
        
        # Update with second trade (larger position)
        session.update_trade_stats(-50.0, 5.0)
        assert session.sum_pnl == 50.0
        assert session.trade_count == 2
        assert session.max_position_size == 5.0
        
        # Update with third trade (smaller position)
        session.update_trade_stats(75.0, 3.0)
        assert session.sum_pnl == 125.0
        assert session.trade_count == 3
        assert session.max_position_size == 5.0  # Should stay at max
    
    def test_update_trade_stats_inactive(self):
        """Test updating stats on an inactive session."""
        session = Session()
        # Don't start the session
        
        session.update_trade_stats(100.0, 2.0)
        assert session.sum_pnl == 0.0
        assert session.trade_count == 0
        assert session.max_position_size == 0.0
    
    def test_get_summary(self):
        """Test getting session summary."""
        session = Session()
        session.start()
        
        # Add some data
        session.update_trade_stats(150.0, 3.0)
        session.update_trade_stats(-50.0, 2.0)
        session.record_violation("daily_loss_limit", "major")
        
        summary = session.get_summary()
        
        assert summary["start_time"] == session.start_time.isoformat()
        assert summary["end_time"] is None
        assert summary["final_pnl"] == 100.0
        assert summary["total_trades"] == 2
        assert summary["max_position_size"] == 3.0
        assert len(summary["rule_violations"]) == 1
        assert summary["adherence_score"] is None
        assert summary["profitability_score"] is None
        assert summary["discipline_score"] is None
        assert summary["session_grade"] is None
    
    def test_get_summary_before_start(self):
        """Test getting summary before session starts."""
        session = Session()
        summary = session.get_summary()
        assert summary == {}
    
    def test_lifecycle_full(self):
        """Test full session lifecycle."""
        session = Session()
        
        # Start
        session.start()
        assert session.active is True
        
        # Add trades
        session.update_trade_stats(100.0, 2.0)
        session.update_trade_stats(-30.0, 1.5)
        session.update_trade_stats(200.0, 3.0)
        
        # Record violations
        session.record_violation("max_trades_per_day", "minor")
        session.record_violation("trading_cutoff_time", "minor")
        
        # Start cooldown
        session.start_cooldown(15)
        assert session.cooldown_active is True
        
        # End session
        summary = session.end()
        
        assert session.active is False
        assert session.end_time is not None
        
        # Verify summary
        assert summary["final_pnl"] == 270.0  # 100 - 30 + 200
        assert summary["total_trades"] == 3
        assert summary["max_position_size"] == 3.0
        assert len(summary["rule_violations"]) == 2
        assert summary["rule_violations"][0]["rule"] == "max_trades_per_day"
        assert summary["rule_violations"][1]["rule"] == "trading_cutoff_time"
    
    def test_get_cooldown_remaining(self):
        """Test getting remaining cooldown time."""
        session = Session()
        session.start()
        
        # No cooldown
        assert session.get_cooldown_remaining() == 0
        
        # Start cooldown
        session.start_cooldown(30)
        remaining = session.get_cooldown_remaining()
        assert remaining > 0
        assert remaining <= 1800  # 30 minutes in seconds
        
        # Advance time by mocking
        with patch('src.models.session.datetime') as mock_datetime:
            # Set current time to cooldown end time
            mock_datetime.now.return_value = session.cooldown_ends_at
            assert session.get_cooldown_remaining() == 0
            assert session.cooldown_active is False
    
    def test_start_clears_previous_session(self):
        """Test that starting a session clears previous session data."""
        session = Session()
        
        # First session
        session.start()
        session.update_trade_stats(100.0, 2.0)
        session.record_violation("daily_loss_limit", "major")
        session.end()
        
        # Start new session
        session.start()
        
        assert session.trade_count == 0
        assert session.sum_pnl == 0.0
        assert session.max_position_size == 0.0
        assert session.violations == []
        assert session.cooldown_active is False
        assert session.cooldown_ends_at is None
        assert session.active is True
        assert session.end_time is None