"""Tests for the risk engine module."""
import pytest
import json
from src.models.risk_engine import (
    TradeState,
    RiskStatus,
    evaluate_risk,
    calculate_discipline_score
)


class TestEvaluateRisk:
    """Tests for evaluate_risk function."""
    
    @pytest.fixture
    def default_settings(self):
        """Default settings for testing."""
        return {
            "daily_loss_limit": "1000.0",
            "max_contract_size": "10.0",
            "max_trades_per_day": "20",
            "trading_cutoff_time": "16:00",
            "consecutive_loss_limit": "5",
            "cooldown_period_minutes": "30"
        }
    
    def test_no_violations_green(self, default_settings):
        """Test that no violations returns GREEN."""
        state = TradeState(
            current_pnl=500.0,
            position_size=3.0,
            num_trades=5,
            trading_time_minutes=120,
            consecutive_losses=0
        )
        
        status, warnings = evaluate_risk(state, default_settings)
        
        assert status == RiskStatus.GREEN
        assert warnings == []
    
    def test_loss_limit_at_75_percent_yellow(self, default_settings):
        """Test loss at exactly 75% of limit returns YELLOW."""
        state = TradeState(
            current_pnl=-750.0,  # 75% of 1000
            position_size=3.0,
            num_trades=5,
            trading_time_minutes=120,
            consecutive_losses=0
        )
        
        status, warnings = evaluate_risk(state, default_settings)
        
        assert status == RiskStatus.YELLOW
        assert len(warnings) == 1
        assert "75.0%" in warnings[0]
        assert "loss" in warnings[0]
    
    def test_loss_limit_at_90_percent_orange(self, default_settings):
        """Test loss at exactly 90% of limit returns ORANGE."""
        state = TradeState(
            current_pnl=-900.0,  # 90% of 1000
            position_size=3.0,
            num_trades=5,
            trading_time_minutes=120,
            consecutive_losses=0
        )
        
        status, warnings = evaluate_risk(state, default_settings)
        
        assert status == RiskStatus.ORANGE
        assert len(warnings) == 1
        assert "90.0%" in warnings[0]
    
    def test_loss_limit_at_100_percent_red(self, default_settings):
        """Test loss at exactly 100% of limit returns RED."""
        state = TradeState(
            current_pnl=-1000.0,  # 100% of 1000
            position_size=3.0,
            num_trades=5,
            trading_time_minutes=120,
            consecutive_losses=0
        )
        
        status, warnings = evaluate_risk(state, default_settings)
        
        assert status == RiskStatus.RED
        assert len(warnings) == 1
        assert "exceeded" in warnings[0]
    
    def test_position_size_limit_75_percent_yellow(self, default_settings):
        """Test position size at 75% of limit returns YELLOW."""
        state = TradeState(
            current_pnl=500.0,
            position_size=7.5,  # 75% of 10
            num_trades=5,
            trading_time_minutes=120,
            consecutive_losses=0
        )
        
        status, warnings = evaluate_risk(state, default_settings)
        
        assert status == RiskStatus.YELLOW
        assert len(warnings) == 1
        assert "75.0%" in warnings[0]
        assert "position size" in warnings[0].lower()
    
    def test_position_size_limit_90_percent_orange(self, default_settings):
        """Test position size at 90% of limit returns ORANGE."""
        state = TradeState(
            current_pnl=500.0,
            position_size=9.0,  # 90% of 10
            num_trades=5,
            trading_time_minutes=120,
            consecutive_losses=0
        )
        
        status, warnings = evaluate_risk(state, default_settings)
        
        assert status == RiskStatus.ORANGE
        assert len(warnings) == 1
    
    def test_position_size_limit_exceeded_red(self, default_settings):
        """Test position size exceeding limit returns RED."""
        state = TradeState(
            current_pnl=500.0,
            position_size=12.0,  # > 10
            num_trades=5,
            trading_time_minutes=120,
            consecutive_losses=0
        )
        
        status, warnings = evaluate_risk(state, default_settings)
        
        assert status == RiskStatus.RED
        assert len(warnings) == 1
        assert "exceeded" in warnings[0]
    
    def test_trade_count_limit_75_percent_yellow(self, default_settings):
        """Test trade count at 75% of limit returns YELLOW."""
        state = TradeState(
            current_pnl=500.0,
            position_size=3.0,
            num_trades=15,  # 75% of 20
            trading_time_minutes=120,
            consecutive_losses=0
        )
        
        status, warnings = evaluate_risk(state, default_settings)
        
        assert status == RiskStatus.YELLOW
        assert len(warnings) == 1
        assert "75.0%" in warnings[0]
    
    def test_trade_count_limit_exceeded_red(self, default_settings):
        """Test trade count exceeding limit returns RED."""
        state = TradeState(
            current_pnl=500.0,
            position_size=3.0,
            num_trades=25,  # > 20
            trading_time_minutes=120,
            consecutive_losses=0
        )
        
        status, warnings = evaluate_risk(state, default_settings)
        
        assert status == RiskStatus.RED
        assert len(warnings) == 1
        assert "exceeded" in warnings[0]
    
    def test_consecutive_losses_75_percent_yellow(self, default_settings):
        """Test consecutive losses at 75% of limit returns YELLOW."""
        state = TradeState(
            current_pnl=500.0,
            position_size=3.0,
            num_trades=5,
            trading_time_minutes=120,
            consecutive_losses=4  # 80% of 5
        )
        
        status, warnings = evaluate_risk(state, default_settings)
        
        assert status == RiskStatus.YELLOW
        assert len(warnings) == 1
        assert "losses" in warnings[0]
    
    def test_consecutive_losses_exceeded_red(self, default_settings):
        """Test consecutive losses exceeding limit returns RED."""
        state = TradeState(
            current_pnl=500.0,
            position_size=3.0,
            num_trades=5,
            trading_time_minutes=120,
            consecutive_losses=6  # > 5
        )
        
        status, warnings = evaluate_risk(state, default_settings)
        
        assert status == RiskStatus.RED
        assert len(warnings) == 1
        assert "exceeded" in warnings[0]
    
    def test_multiple_rules_highest_severity_wins(self, default_settings):
        """Test that the highest severity among multiple rules wins."""
        state = TradeState(
            current_pnl=-800.0,  # 80% loss - ORANGE
            position_size=9.5,   # 95% position - ORANGE
            num_trades=18,       # 90% trades - ORANGE
            trading_time_minutes=200,  # Below 75% threshold (9:30-16:00 = 390 min, 200/390=51%)
            consecutive_losses=4  # 80% losses - YELLOW
        )
        
        status, warnings = evaluate_risk(state, default_settings)
        
        # Should be ORANGE (highest)
        assert status == RiskStatus.ORANGE
        # Should have warnings for all triggered rules (loss, position, trades, losses)
        assert len(warnings) == 4
    
    def test_missing_state_returns_data_error(self, default_settings):
        """Test that missing TradeState returns DATA_ERROR."""
        status, warnings = evaluate_risk(None, default_settings)
        
        assert status == RiskStatus.DATA_ERROR
        assert len(warnings) == 1
        assert "Invalid trade state" in warnings[0]
    
    def test_invalid_state_fields_data_error(self, default_settings):
        """Test that invalid fields in TradeState return DATA_ERROR."""
        # Test with invalid current_pnl
        state = TradeState(
            current_pnl="invalid",  # Should be float
            position_size=3.0,
            num_trades=5,
            trading_time_minutes=120,
            consecutive_losses=0
        )
        
        status, warnings = evaluate_risk(state, default_settings)
        assert status == RiskStatus.DATA_ERROR
        assert len(warnings) == 1
        assert "Invalid trade state" in warnings[0]
        
        # Test with invalid num_trades
        state = TradeState(
            current_pnl=500.0,
            position_size=3.0,
            num_trades=5.5,  # Should be int
            trading_time_minutes=120,
            consecutive_losses=0
        )
        
        status, warnings = evaluate_risk(state, default_settings)
        assert status == RiskStatus.DATA_ERROR
    
    def test_missing_settings_data_error(self, default_settings):
        """Test that missing settings return DATA_ERROR."""
        # Remove a required setting
        incomplete_settings = default_settings.copy()
        del incomplete_settings["daily_loss_limit"]
        
        state = TradeState(
            current_pnl=500.0,
            position_size=3.0,
            num_trades=5,
            trading_time_minutes=120,
            consecutive_losses=0
        )
        
        status, warnings = evaluate_risk(state, incomplete_settings)
        
        assert status == RiskStatus.DATA_ERROR
        assert len(warnings) == 1
    
    def test_invalid_settings_data_error(self, default_settings):
        """Test that invalid settings values return DATA_ERROR."""
        # Invalid daily_loss_limit (not a number)
        invalid_settings = default_settings.copy()
        invalid_settings["daily_loss_limit"] = "not_a_number"
        
        state = TradeState(
            current_pnl=500.0,
            position_size=3.0,
            num_trades=5,
            trading_time_minutes=120,
            consecutive_losses=0
        )
        
        status, warnings = evaluate_risk(state, invalid_settings)
        
        assert status == RiskStatus.DATA_ERROR
        assert len(warnings) == 1


class TestCalculateDisciplineScore:
    """Tests for calculate_discipline_score function."""
    
    @pytest.fixture
    def default_settings(self):
        """Default settings for testing."""
        return {
            "daily_loss_limit": "1000.0",
            "rule_severity_map": json.dumps({
                "daily_loss_limit": "major",
                "max_contract_size": "major",
                "max_trades_per_day": "minor",
                "trading_cutoff_time": "minor",
                "consecutive_loss_limit": "major",
                "cooldown_period_minutes": "minor"
            })
        }
    
    def test_perfect_score(self, default_settings):
        """Test perfect score: 0 violations, P&L >= 0."""
        violations = []
        final_pnl = 500.0
        
        result = calculate_discipline_score(violations, default_settings, final_pnl)
        
        assert result["adherence"] == 100.0
        assert result["profitability"] == 100.0
        assert result["blended"] == 100.0
    
    def test_good_score_zero_violations_negative_pnl(self, default_settings):
        """Test good score: 0 violations, negative P&L within limit."""
        violations = []
        final_pnl = -500.0
        
        result = calculate_discipline_score(violations, default_settings, final_pnl)
        
        assert result["adherence"] == 100.0
        # Profitability should be 50% ($500 loss on $1000 limit)
        assert result["profitability"] == 50.0
        # Blended should be 100*0.7 + 50*0.3 = 85
        assert result["blended"] == 85.0
    
    def test_mediocre_score_one_minor_violation(self, default_settings):
        """Test mediocre score: 1 minor violation."""
        violations = [
            {"rule": "max_trades_per_day", "severity": "minor"}
        ]
        final_pnl = 500.0
        
        result = calculate_discipline_score(violations, default_settings, final_pnl)
        
        assert result["adherence"] == 80.0
        assert result["profitability"] == 100.0
        # Blended should be 80*0.7 + 100*0.3 = 86
        assert result["blended"] == 86.0
    
    def test_bad_score_one_major_violation(self, default_settings):
        """Test bad score: 1 major violation, even with positive P&L."""
        violations = [
            {"rule": "daily_loss_limit", "severity": "major"}
        ]
        final_pnl = 500.0
        
        result = calculate_discipline_score(violations, default_settings, final_pnl)
        
        assert result["adherence"] == 50.0
        assert result["profitability"] == 100.0
        # Blended should be 50*0.7 + 100*0.3 = 65
        assert result["blended"] == 65.0
    
    def test_two_violations_zero_adherence(self, default_settings):
        """Test 2+ violations results in 0 adherence."""
        violations = [
            {"rule": "max_trades_per_day", "severity": "minor"},
            {"rule": "trading_cutoff_time", "severity": "minor"}
        ]
        final_pnl = 500.0
        
        result = calculate_discipline_score(violations, default_settings, final_pnl)
        
        assert result["adherence"] == 0.0
        assert result["profitability"] == 100.0
        # Blended should be 0*0.7 + 100*0.3 = 30
        assert result["blended"] == 30.0
    
    def test_violations_with_implicit_severity(self, default_settings):
        """Test violations that don't specify severity but match rule_severity_map."""
        violations = [
            {"rule": "daily_loss_limit"}  # No severity specified
        ]
        final_pnl = 500.0
        
        result = calculate_discipline_score(violations, default_settings, final_pnl)
        
        # Should use rule_severity_map to determine it's major
        assert result["adherence"] == 50.0
        assert result["blended"] == 65.0
    
    def test_profitability_at_loss_limit_zero(self, default_settings):
        """Test profitability = 0 when P&L exactly at loss limit."""
        violations = []
        final_pnl = -1000.0  # Exactly at limit
        
        result = calculate_discipline_score(violations, default_settings, final_pnl)
        
        assert result["adherence"] == 100.0
        assert result["profitability"] == 0.0
        assert result["blended"] == 70.0  # 100*0.7 + 0*0.3
    
    def test_profitability_at_breakeven_and_above(self, default_settings):
        """Test profitability = 100 for breakeven and above."""
        # Test breakeven
        violations = []
        final_pnl = 0.0
        
        result = calculate_discipline_score(violations, default_settings, final_pnl)
        assert result["profitability"] == 100.0
        
        # Test above breakeven
        final_pnl = 2000.0
        
        result = calculate_discipline_score(violations, default_settings, final_pnl)
        assert result["profitability"] == 100.0
    
    def test_profitability_scale_between_limit_and_zero(self, default_settings):
        """Test profitability scales linearly between loss limit and zero."""
        violations = []
        
        # Test at 25% of limit
        final_pnl = -250.0
        result = calculate_discipline_score(violations, default_settings, final_pnl)
        assert result["profitability"] == 75.0
        
        # Test at 50% of limit
        final_pnl = -500.0
        result = calculate_discipline_score(violations, default_settings, final_pnl)
        assert result["profitability"] == 50.0
        
        # Test at 75% of limit
        final_pnl = -750.0
        result = calculate_discipline_score(violations, default_settings, final_pnl)
        assert result["profitability"] == 25.0
    
    def test_missing_rule_severity_map_fallback(self):
        """Test that missing rule_severity_map uses default fallback."""
        settings = {
            "daily_loss_limit": "1000.0"
            # No rule_severity_map
        }
        
        violations = [
            {"rule": "daily_loss_limit"}
        ]
        final_pnl = 500.0
        
        result = calculate_discipline_score(violations, settings, final_pnl)
        
        # Should use default mapping where daily_loss_limit is major
        assert result["adherence"] == 50.0
        assert result["blended"] == 65.0  # 50*0.7 + 100*0.3
    
    def test_empty_violations_list(self, default_settings):
        """Test with empty violations list."""
        violations = []
        final_pnl = 300.0
        
        result = calculate_discipline_score(violations, default_settings, final_pnl)
        
        assert result["adherence"] == 100.0
        assert result["profitability"] == 100.0
        assert result["blended"] == 100.0
    
    def test_none_violations(self, default_settings):
        """Test with None violations."""
        final_pnl = 300.0
        
        result = calculate_discipline_score(None, default_settings, final_pnl)
        
        assert result["adherence"] == 100.0
        assert result["profitability"] == 100.0
        assert result["blended"] == 100.0