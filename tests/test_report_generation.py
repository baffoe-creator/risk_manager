"""Tests for report generation."""
import pytest
import json
from datetime import datetime
from src.controllers.app_controller import AppController
from src.models.risk_engine import calculate_discipline_score


class TestReportGeneration:
    """Tests for report generation and calculations."""
    
    def test_report_fields_present(self):
        """Test that all required fields are present in a report."""
        # Create a session summary
        session_data = {
            "start_time": "2024-01-01T09:00:00",
            "end_time": "2024-01-01T16:00:00",
            "final_pnl": 500.50,
            "total_trades": 15,
            "max_position_size": 5.0,
            "rule_violations": [],
            "adherence_score": 100.0,
            "profitability_score": 100.0,
            "discipline_score": 100.0,
            "session_grade": "A",
            "capital_preservation": 100
        }
        
        # Check all required fields exist
        required_fields = [
            "start_time", "end_time", "final_pnl", "total_trades",
            "max_position_size", "rule_violations", "adherence_score",
            "profitability_score", "discipline_score", "session_grade",
            "capital_preservation"
        ]
        
        for field in required_fields:
            assert field in session_data
    
    def test_discipline_score_calculation_perfect(self):
        """Test discipline score calculation for perfect session."""
        settings = {
            "daily_loss_limit": "1000.0",
            "rule_severity_map": json.dumps({
                "daily_loss_limit": "major"
            })
        }
        
        violations = []
        final_pnl = 500.0
        
        result = calculate_discipline_score(violations, settings, final_pnl)
        
        assert result["adherence"] == 100.0
        assert result["profitability"] == 100.0
        assert result["blended"] == 100.0
    
    def test_discipline_score_calculation_good(self):
        """Test discipline score calculation for good session (0 violations, negative P&L)."""
        settings = {
            "daily_loss_limit": "1000.0",
            "rule_severity_map": json.dumps({
                "daily_loss_limit": "major"
            })
        }
        
        violations = []
        final_pnl = -500.0
        
        result = calculate_discipline_score(violations, settings, final_pnl)
        
        assert result["adherence"] == 100.0
        assert result["profitability"] == 50.0
        assert result["blended"] == 85.0
    
    def test_discipline_score_calculation_mediocre(self):
        """Test discipline score calculation for mediocre session (1 minor violation)."""
        settings = {
            "daily_loss_limit": "1000.0",
            "rule_severity_map": json.dumps({
                "max_trades_per_day": "minor"
            })
        }
        
        violations = [
            {"rule": "max_trades_per_day", "severity": "minor"}
        ]
        final_pnl = 500.0
        
        result = calculate_discipline_score(violations, settings, final_pnl)
        
        assert result["adherence"] == 80.0
        assert result["profitability"] == 100.0
        assert result["blended"] == 86.0
    
    def test_discipline_score_calculation_bad(self):
        """Test discipline score calculation for bad session (1 major violation)."""
        settings = {
            "daily_loss_limit": "1000.0",
            "rule_severity_map": json.dumps({
                "daily_loss_limit": "major"
            })
        }
        
        violations = [
            {"rule": "daily_loss_limit", "severity": "major"}
        ]
        final_pnl = 500.0
        
        result = calculate_discipline_score(violations, settings, final_pnl)
        
        assert result["adherence"] == 50.0
        assert result["profitability"] == 100.0
        assert result["blended"] == 65.0
    
    def test_capital_preservation_score(self):
        """Test capital preservation score calculation."""
        # Should be 100 if no loss limit violation
        violations_without_loss = [
            {"rule": "max_trades_per_day", "severity": "minor"}
        ]
        has_loss_limit = any(
            v.get("rule") == "daily_loss_limit" 
            for v in violations_without_loss
        )
        capital_preservation = 0 if has_loss_limit else 100
        assert capital_preservation == 100
        
        # Should be 0 if loss limit violation exists
        violations_with_loss = [
            {"rule": "daily_loss_limit", "severity": "major"}
        ]
        has_loss_limit = any(
            v.get("rule") == "daily_loss_limit" 
            for v in violations_with_loss
        )
        capital_preservation = 0 if has_loss_limit else 100
        assert capital_preservation == 0
    
    def test_session_grade_mapping(self):
        """Test session grade mapping."""
        grade_mapping = [
            (95, "A"),
            (85, "B"),
            (75, "C"),
            (65, "D"),
            (55, "F")
        ]
        
        for score, expected_grade in grade_mapping:
            if score >= 90:
                grade = "A"
            elif score >= 80:
                grade = "B"
            elif score >= 70:
                grade = "C"
            elif score >= 60:
                grade = "D"
            else:
                grade = "F"
            
            assert grade == expected_grade
    
    def test_report_generation_from_session(self, tmp_path):
        """Test full report generation from a session."""
        from src.models.session import Session
        from src.models.data_manager import DataManager
        
        # Create a session
        session = Session()
        session.start()
        
        # Add some data
        session.update_trade_stats(100.0, 2.0)
        session.update_trade_stats(-50.0, 1.5)
        session.update_trade_stats(200.0, 3.0)
        session.record_violation("max_trades_per_day", "minor")
        
        # End session
        summary = session.end()
        
        # Calculate scores
        settings = {
            "daily_loss_limit": "1000.0",
            "rule_severity_map": json.dumps({
                "max_trades_per_day": "minor"
            })
        }
        
        scores = calculate_discipline_score(
            summary.get("rule_violations", []),
            settings,
            summary.get("final_pnl", 0.0)
        )
        
        summary["adherence_score"] = scores["adherence"]
        summary["profitability_score"] = scores["profitability"]
        summary["discipline_score"] = scores["blended"]
        
        # Grade
        blended = scores["blended"]
        if blended >= 90:
            summary["session_grade"] = "A"
        elif blended >= 80:
            summary["session_grade"] = "B"
        elif blended >= 70:
            summary["session_grade"] = "C"
        elif blended >= 60:
            summary["session_grade"] = "D"
        else:
            summary["session_grade"] = "F"
        
        # Capital preservation
        has_loss_limit = any(
            v.get("rule") == "daily_loss_limit" 
            for v in summary.get("rule_violations", [])
        )
        summary["capital_preservation"] = 0 if has_loss_limit else 100
        
        # Verify the report data
        assert summary["total_trades"] == 3
        assert summary["final_pnl"] == 250.0
        assert summary["max_position_size"] == 3.0
        assert len(summary["rule_violations"]) == 1
        assert summary["adherence_score"] == 80.0
        assert summary["profitability_score"] == 100.0
        assert summary["discipline_score"] == 86.0
        assert summary["session_grade"] == "B"
        assert summary["capital_preservation"] == 100
    
    def test_rule_violations_json_roundtrip(self, tmp_path):
        """Test that rule_violations round-trips correctly as JSON."""
        from src.models.data_manager import DataManager
        
        # Create a DataManager with temp path
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = tmp_path / "test.db"
        
        dm = DataManager(db_path)
        
        # Create session with violations
        violations = [
            {"rule": "daily_loss_limit", "severity": "major", "timestamp": "2024-01-01T10:00:00"},
            {"rule": "max_trades_per_day", "severity": "minor", "timestamp": "2024-01-01T10:30:00"}
        ]
        
        session_data = {
            "start_time": "2024-01-01T09:00:00",
            "end_time": "2024-01-01T16:00:00",
            "final_pnl": 500.0,
            "total_trades": 15,
            "max_position_size": 5.0,
            "rule_violations": violations,
            "adherence_score": 80.0,
            "profitability_score": 90.0,
            "discipline_score": 83.0,
            "session_grade": "B"
        }
        
        # Save session
        session_id = dm.save_session(session_data)
        assert session_id is not None
        
        # Retrieve session
        history = dm.get_session_history()
        assert len(history) == 1
        
        retrieved = history[0]
        
        # Check that rule_violations is a list (not a string)
        assert isinstance(retrieved["rule_violations"], list)
        assert len(retrieved["rule_violations"]) == 2
        assert retrieved["rule_violations"][0]["rule"] == "daily_loss_limit"
        assert retrieved["rule_violations"][0]["severity"] == "major"
        assert retrieved["rule_violations"][1]["rule"] == "max_trades_per_day"
        assert retrieved["rule_violations"][1]["severity"] == "minor"