"""Tests for the DataManager class."""
import json
import sqlite3
import pytest
from pathlib import Path
import tempfile
import logging
import time
from src.models.data_manager import DataManager


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    # Use a unique filename to avoid conflicts
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = Path(f.name)
    
    # Create DataManager with temp path
    dm = DataManager(db_path)
    
    # Clear any auto-seeded settings for clean tests
    with sqlite3.connect(db_path) as conn:
        conn.execute("DELETE FROM settings")
        conn.commit()
    
    yield dm, db_path
    
    # Cleanup - ensure all connections are closed
    # Force garbage collection and wait a moment
    import gc
    gc.collect()
    time.sleep(0.1)
    
    try:
        db_path.unlink(missing_ok=True)
    except PermissionError:
        # If still locked, try one more time after a longer wait
        time.sleep(0.5)
        try:
            db_path.unlink(missing_ok=True)
        except PermissionError:
            # Log but don't fail the test
            print(f"Warning: Could not delete temp file {db_path}")


def test_settings_roundtrip(temp_db):
    """Test saving and retrieving settings."""
    dm, _ = temp_db
    
    # Save a setting
    result = dm.save_setting("test_key", "test_value")
    assert result is True
    
    # Retrieve it
    value = dm.get_setting("test_key")
    assert value == "test_value"
    
    # Update it
    result = dm.save_setting("test_key", "new_value")
    assert result is True
    
    # Verify update
    value = dm.get_setting("test_key")
    assert value == "new_value"


def test_missing_key_returns_none(temp_db):
    """Test that missing keys return None."""
    dm, _ = temp_db
    
    value = dm.get_setting("nonexistent_key")
    assert value is None


def test_get_all_settings(temp_db):
    """Test getting all settings."""
    dm, _ = temp_db
    
    # Save multiple settings
    dm.save_setting("key1", "value1")
    dm.save_setting("key2", "value2")
    dm.save_setting("key3", "value3")
    
    all_settings = dm.get_all_settings()
    
    assert all_settings["key1"] == "value1"
    assert all_settings["key2"] == "value2"
    assert all_settings["key3"] == "value3"
    assert len(all_settings) == 3


def test_session_save_retrieve_roundtrip(temp_db):
    """Test saving and retrieving sessions with proper JSON handling."""
    dm, _ = temp_db
    
    # Create a session with violations as a list
    violations = [
        {"rule": "daily_loss_limit", "severity": "major", "timestamp": "2024-01-01T10:00:00"},
        {"rule": "max_trades_per_day", "severity": "minor", "timestamp": "2024-01-01T10:30:00"}
    ]
    
    session_data = {
        "start_time": "2024-01-01T09:00:00",
        "end_time": "2024-01-01T16:00:00",
        "final_pnl": 500.50,
        "total_trades": 15,
        "max_position_size": 5.0,
        "rule_violations": violations,
        "adherence_score": 80.0,
        "profitability_score": 90.0,
        "discipline_score": 83.0,
        "session_grade": "B"
    }
    
    # Save the session
    session_id = dm.save_session(session_data)
    assert session_id is not None
    assert session_id > 0
    
    # Retrieve session history
    history = dm.get_session_history()
    assert len(history) == 1
    
    retrieved = history[0]
    
    # Check that rule_violations comes back as a list, not a string
    assert isinstance(retrieved["rule_violations"], list)
    assert len(retrieved["rule_violations"]) == 2
    assert retrieved["rule_violations"][0]["rule"] == "daily_loss_limit"
    assert retrieved["rule_violations"][0]["severity"] == "major"
    assert retrieved["rule_violations"][1]["rule"] == "max_trades_per_day"
    assert retrieved["rule_violations"][1]["severity"] == "minor"
    
    # Check other fields
    assert retrieved["final_pnl"] == 500.50
    assert retrieved["total_trades"] == 15
    assert retrieved["max_position_size"] == 5.0
    assert retrieved["adherence_score"] == 80.0
    assert retrieved["profitability_score"] == 90.0
    assert retrieved["discipline_score"] == 83.0
    assert retrieved["session_grade"] == "B"


def test_session_with_empty_violations(temp_db):
    """Test saving a session with empty violations."""
    dm, _ = temp_db
    
    session_data = {
        "start_time": "2024-01-01T09:00:00",
        "end_time": "2024-01-01T16:00:00",
        "final_pnl": 1000.0,
        "total_trades": 10,
        "max_position_size": 3.0,
        "rule_violations": [],
        "adherence_score": 100.0,
        "profitability_score": 100.0,
        "discipline_score": 100.0,
        "session_grade": "A"
    }
    
    session_id = dm.save_session(session_data)
    assert session_id is not None
    
    history = dm.get_session_history()
    assert len(history) == 1
    
    retrieved = history[0]
    assert isinstance(retrieved["rule_violations"], list)
    assert len(retrieved["rule_violations"]) == 0


def test_session_with_none_violations(temp_db):
    """Test saving a session with None violations (should handle gracefully)."""
    dm, _ = temp_db
    
    session_data = {
        "start_time": "2024-01-01T09:00:00",
        "end_time": "2024-01-01T16:00:00",
        "final_pnl": 1000.0,
        "total_trades": 10,
        "max_position_size": 3.0,
        "rule_violations": None,
        "adherence_score": 100.0,
        "profitability_score": 100.0,
        "discipline_score": 100.0,
        "session_grade": "A"
    }
    
    session_id = dm.save_session(session_data)
    assert session_id is not None
    
    history = dm.get_session_history()
    assert len(history) == 1
    
    retrieved = history[0]
    # Should convert None to empty list
    assert isinstance(retrieved["rule_violations"], list)
    assert len(retrieved["rule_violations"]) == 0


def test_malformed_db_write_caught(temp_db, caplog):
    """Test that malformed DB writes are caught and logged."""
    dm, _ = temp_db
    
    # Create session with invalid data type that will cause error
    class Unserializable:
        pass
    
    session_data = {
        "start_time": "2024-01-01T09:00:00",
        "end_time": "2024-01-01T16:00:00",
        "final_pnl": 500.0,
        "total_trades": 10,
        "max_position_size": 5.0,
        "rule_violations": Unserializable(),  # This will cause an error
        "adherence_score": 80.0,
        "profitability_score": 90.0,
        "discipline_score": 83.0,
        "session_grade": "B"
    }
    
    # Should not crash, but return None
    session_id = dm.save_session(session_data)
    assert session_id is None
    
    # Check that error was logged
    assert "Failed to save session" in caplog.text


def test_default_settings_seeded():
    """Test that default settings are seeded on first run."""
    # Create a fresh DataManager with a new database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        fresh_db_path = Path(f.name)
    
    try:
        # This should seed defaults
        dm = DataManager(fresh_db_path)
        
        # Check that all default settings exist
        all_settings = dm.get_all_settings()
        
        expected_keys = [
            "daily_loss_limit",
            "max_contract_size",
            "max_trades_per_day",
            "trading_cutoff_time",
            "consecutive_loss_limit",
            "cooldown_period_minutes",
            "rule_severity_map"
        ]
        
        for key in expected_keys:
            assert key in all_settings, f"Default setting '{key}' not seeded"
            assert all_settings[key] is not None
        
        # Verify rule_severity_map is valid JSON
        rule_severity = json.loads(all_settings["rule_severity_map"])
        assert isinstance(rule_severity, dict)
        assert "daily_loss_limit" in rule_severity
        assert rule_severity["daily_loss_limit"] == "major"
        assert "max_trades_per_day" in rule_severity
        assert rule_severity["max_trades_per_day"] == "minor"
        
    finally:
        # Cleanup - ensure connection is closed
        import gc
        gc.collect()
        time.sleep(0.1)
        try:
            fresh_db_path.unlink(missing_ok=True)
        except PermissionError:
            time.sleep(0.5)
            try:
                fresh_db_path.unlink(missing_ok=True)
            except PermissionError:
                print(f"Warning: Could not delete temp file {fresh_db_path}")


def test_get_session_history_empty(temp_db):
    """Test getting session history when no sessions exist."""
    dm, _ = temp_db
    
    history = dm.get_session_history()
    assert history == []