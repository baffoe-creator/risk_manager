"""Risk engine for evaluating trading risk."""
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple, List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class RiskStatus(Enum):
    """Risk status levels."""
    GREEN = "GREEN"
    YELLOW = "YELLOW"
    ORANGE = "ORANGE"
    RED = "RED"
    DATA_ERROR = "DATA_ERROR"


@dataclass
class TradeState:
    """Current trading state for risk evaluation."""
    current_pnl: float
    position_size: float
    num_trades: int
    trading_time_minutes: int
    consecutive_losses: int


def evaluate_risk(state: TradeState, settings: dict) -> Tuple[RiskStatus, List[str]]:
    """
    Evaluate risk based on current trade state and settings.
    
    Args:
        state: Current trade state
        settings: Dictionary of risk settings (must contain all required keys)
        
    Returns:
        Tuple of (RiskStatus, list of warning messages)
    """
    logger.debug(f"Evaluating risk with state: {state}, settings: {settings}")
    
    # Validate state - check for None or missing fields
    if state is None:
        logger.error("TradeState is None")
        return (RiskStatus.DATA_ERROR, ["Invalid trade state received"])
    
    # Check each field for None or invalid type
    if not isinstance(state.current_pnl, (int, float)):
        logger.error(f"current_pnl is invalid type: {type(state.current_pnl)}")
        return (RiskStatus.DATA_ERROR, ["Invalid trade state received"])
    
    if not isinstance(state.position_size, (int, float)):
        logger.error(f"position_size is invalid type: {type(state.position_size)}")
        return (RiskStatus.DATA_ERROR, ["Invalid trade state received"])
    
    if not isinstance(state.num_trades, int):
        logger.error(f"num_trades is invalid type: {type(state.num_trades)}")
        return (RiskStatus.DATA_ERROR, ["Invalid trade state received"])
    
    if not isinstance(state.trading_time_minutes, int):
        logger.error(f"trading_time_minutes is invalid type: {type(state.trading_time_minutes)}")
        return (RiskStatus.DATA_ERROR, ["Invalid trade state received"])
    
    if not isinstance(state.consecutive_losses, int):
        logger.error(f"consecutive_losses is invalid type: {type(state.consecutive_losses)}")
        return (RiskStatus.DATA_ERROR, ["Invalid trade state received"])
    
    # Validate settings - ensure all required keys exist
    required_settings = [
        "daily_loss_limit",
        "max_contract_size", 
        "max_trades_per_day",
        "trading_cutoff_time",
        "consecutive_loss_limit",
        "cooldown_period_minutes"
    ]
    
    for key in required_settings:
        if key not in settings:
            logger.error(f"Missing required setting: {key}")
            return (RiskStatus.DATA_ERROR, ["Invalid trade state received"])
        
        # Check if setting can be converted properly
        try:
            if key == "daily_loss_limit":
                float(settings[key])
            elif key == "max_contract_size":
                float(settings[key])
            elif key == "max_trades_per_day":
                int(settings[key])
            elif key == "trading_cutoff_time":
                # Validate time format HH:MM
                time_str = settings[key]
                if not isinstance(time_str, str) or ":" not in time_str:
                    raise ValueError(f"Invalid time format: {time_str}")
                hours, minutes = time_str.split(":")
                int(hours), int(minutes)
            elif key == "consecutive_loss_limit":
                int(settings[key])
            elif key == "cooldown_period_minutes":
                int(settings[key])
        except (ValueError, TypeError) as e:
            logger.error(f"Invalid setting value for {key}: {settings[key]}")
            return (RiskStatus.DATA_ERROR, ["Invalid trade state received"])
    
    # Parse settings to appropriate types
    daily_loss_limit = float(settings["daily_loss_limit"])
    max_contract_size = float(settings["max_contract_size"])
    max_trades_per_day = int(settings["max_trades_per_day"])
    trading_cutoff_time = settings["trading_cutoff_time"]
    consecutive_loss_limit = int(settings["consecutive_loss_limit"])
    cooldown_period_minutes = int(settings["cooldown_period_minutes"])
    
    # Initialize tracking
    highest_severity = RiskStatus.GREEN
    warnings = []
    
    # Helper function to determine severity based on threshold percentage
    def get_severity(percentage: float) -> RiskStatus:
        if percentage >= 100.0:
            return RiskStatus.RED
        elif percentage >= 90.0:
            return RiskStatus.ORANGE
        elif percentage >= 75.0:
            return RiskStatus.YELLOW
        else:
            return RiskStatus.GREEN
    
    # Helper to update highest severity
    def update_severity(severity: RiskStatus, warning_msg: str):
        nonlocal highest_severity
        if severity != RiskStatus.GREEN:
            warnings.append(warning_msg)
        # Use enum comparison (RED > ORANGE > YELLOW > GREEN)
        if severity.value in ["RED", "ORANGE", "YELLOW"]:
            # Convert to comparable values
            severity_order = {"GREEN": 0, "YELLOW": 1, "ORANGE": 2, "RED": 3}
            if severity_order.get(severity.value, 0) > severity_order.get(highest_severity.value, 0):
                highest_severity = severity
    
    # 1. Check daily loss limit
    loss_percentage = abs(state.current_pnl) / daily_loss_limit * 100 if daily_loss_limit > 0 else 0
    if state.current_pnl < 0:
        if loss_percentage >= 100.0:
            severity = RiskStatus.RED
            update_severity(severity, f"Daily loss limit exceeded: ${abs(state.current_pnl):.2f} loss (limit: ${daily_loss_limit:.2f})")
        elif loss_percentage >= 90.0:
            severity = RiskStatus.ORANGE
            update_severity(severity, f"Daily loss limit at {loss_percentage:.1f}%: ${abs(state.current_pnl):.2f} loss (limit: ${daily_loss_limit:.2f})")
        elif loss_percentage >= 75.0:
            severity = RiskStatus.YELLOW
            update_severity(severity, f"Daily loss limit at {loss_percentage:.1f}%: ${abs(state.current_pnl):.2f} loss (limit: ${daily_loss_limit:.2f})")
    
    # 2. Check position size
    pos_percentage = state.position_size / max_contract_size * 100 if max_contract_size > 0 else 0
    if pos_percentage >= 100.0:
        severity = RiskStatus.RED
        update_severity(severity, f"Position size limit exceeded: {state.position_size:.1f} contracts (limit: {max_contract_size:.1f})")
    elif pos_percentage >= 90.0:
        severity = RiskStatus.ORANGE
        update_severity(severity, f"Position size at {pos_percentage:.1f}%: {state.position_size:.1f} contracts (limit: {max_contract_size:.1f})")
    elif pos_percentage >= 75.0:
        severity = RiskStatus.YELLOW
        update_severity(severity, f"Position size at {pos_percentage:.1f}%: {state.position_size:.1f} contracts (limit: {max_contract_size:.1f})")
    
    # 3. Check trade count
    trade_percentage = state.num_trades / max_trades_per_day * 100 if max_trades_per_day > 0 else 0
    if trade_percentage >= 100.0:
        severity = RiskStatus.RED
        update_severity(severity, f"Daily trade count limit exceeded: {state.num_trades} trades (limit: {max_trades_per_day})")
    elif trade_percentage >= 90.0:
        severity = RiskStatus.ORANGE
        update_severity(severity, f"Daily trade count at {trade_percentage:.1f}%: {state.num_trades} trades (limit: {max_trades_per_day})")
    elif trade_percentage >= 75.0:
        severity = RiskStatus.YELLOW
        update_severity(severity, f"Daily trade count at {trade_percentage:.1f}%: {state.num_trades} trades (limit: {max_trades_per_day})")
    
    # 4. Check trading time cutoff
    # Parse cutoff time (assuming format "HH:MM")
    try:
        cutoff_hours, cutoff_minutes = map(int, trading_cutoff_time.split(":"))
        cutoff_minutes_total = cutoff_hours * 60 + cutoff_minutes
        
        # Calculate time remaining percentage
        # Assuming trading day starts at 9:30 AM (570 minutes from midnight)
        day_start = 9 * 60 + 30  # 9:30 AM
        day_end = cutoff_minutes_total
        total_trading_minutes = day_end - day_start
        
        if total_trading_minutes > 0:
            time_elapsed = state.trading_time_minutes
            time_percentage = time_elapsed / total_trading_minutes * 100
            
            if time_percentage >= 100.0:
                severity = RiskStatus.RED
                update_severity(severity, f"Trading time cutoff reached: {state.trading_time_minutes} minutes elapsed (cutoff: {trading_cutoff_time})")
            elif time_percentage >= 90.0:
                severity = RiskStatus.ORANGE
                update_severity(severity, f"Trading time at {time_percentage:.1f}%: {state.trading_time_minutes} minutes elapsed (cutoff: {trading_cutoff_time})")
            elif time_percentage >= 75.0:
                severity = RiskStatus.YELLOW
                update_severity(severity, f"Trading time at {time_percentage:.1f}%: {state.trading_time_minutes} minutes elapsed (cutoff: {trading_cutoff_time})")
    except (ValueError, ZeroDivisionError) as e:
        logger.warning(f"Could not parse trading_cutoff_time: {trading_cutoff_time}, skipping time check")
    
    # 5. Check consecutive losses
    loss_percentage = state.consecutive_losses / consecutive_loss_limit * 100 if consecutive_loss_limit > 0 else 0
    if loss_percentage >= 100.0:
        severity = RiskStatus.RED
        update_severity(severity, f"Consecutive loss limit exceeded: {state.consecutive_losses} losses (limit: {consecutive_loss_limit})")
    elif loss_percentage >= 90.0:
        severity = RiskStatus.ORANGE
        update_severity(severity, f"Consecutive losses at {loss_percentage:.1f}%: {state.consecutive_losses} losses (limit: {consecutive_loss_limit})")
    elif loss_percentage >= 75.0:
        severity = RiskStatus.YELLOW
        update_severity(severity, f"Consecutive losses at {loss_percentage:.1f}%: {state.consecutive_losses} losses (limit: {consecutive_loss_limit})")
    
    # Return results
    logger.debug(f"Risk evaluation complete: {highest_severity.value} with {len(warnings)} warnings")
    return (highest_severity, warnings)


def calculate_discipline_score(violations: List[dict], settings: dict, final_pnl: float) -> Dict[str, float]:
    """
    Calculate discipline score based on violations and P&L.
    
    Args:
        violations: List of violation dictionaries, each containing 'rule' and 'severity'
        settings: Dictionary of risk settings (must contain 'rule_severity_map')
        final_pnl: Final P&L for the session
        
    Returns:
        Dictionary with adherence, profitability, and blended scores
    """
    logger.debug(f"Calculating discipline score with {len(violations) if violations else 0} violations, P&L: {final_pnl}")
    
    # Default rule severity map (used if settings don't provide one or parsing fails)
    default_map = {
        "daily_loss_limit": "major",
        "max_contract_size": "major",
        "max_trades_per_day": "minor",
        "trading_cutoff_time": "minor",
        "consecutive_loss_limit": "major",
        "cooldown_period_minutes": "minor"
    }
    
    # Get rule_severity_map from settings
    rule_severity_map = default_map.copy()
    if "rule_severity_map" in settings:
        try:
            import json
            if isinstance(settings["rule_severity_map"], str):
                parsed = json.loads(settings["rule_severity_map"])
                rule_severity_map.update(parsed)
            elif isinstance(settings["rule_severity_map"], dict):
                rule_severity_map.update(settings["rule_severity_map"])
        except (json.JSONDecodeError, TypeError) as e:
            logger.error(f"Failed to parse rule_severity_map: {e}, using defaults")
    
    # Count violations by severity
    major_count = 0
    minor_count = 0
    
    if violations:
        for violation in violations:
            rule = violation.get("rule", "")
            severity = violation.get("severity", "")
            
            # If severity not explicitly set, look it up in the map
            if not severity and rule in rule_severity_map:
                severity = rule_severity_map[rule]
            
            if severity == "major":
                major_count += 1
            elif severity == "minor":
                minor_count += 1
            else:
                # Default to minor if unknown
                logger.warning(f"Unknown severity '{severity}' for rule '{rule}', defaulting to minor")
                minor_count += 1
    
    # Calculate adherence score
    total_violations = major_count + minor_count
    
    if total_violations == 0:
        adherence = 100.0
    elif total_violations == 1:
        if major_count == 1:
            adherence = 50.0  # Exactly 1 major violation
        else:
            adherence = 80.0  # Exactly 1 minor violation
    else:
        adherence = 0.0  # 2+ violations of any severity
    
    # Calculate profitability score
    daily_loss_limit = float(settings.get("daily_loss_limit", 1000.0))
    
    if final_pnl >= 0:
        profitability = 100.0
    else:
        # Scale linearly from daily_loss_limit (0) to $0 (100)
        # Clamp to ensure it doesn't go below 0
        profitability = max(0.0, (1 - abs(final_pnl) / daily_loss_limit) * 100)
    
    # Calculate blended score
    blended = adherence * 0.7 + profitability * 0.3
    
    result = {
        "adherence": adherence,
        "profitability": profitability,
        "blended": blended
    }
    
    logger.debug(f"Discipline score calculated: adherence={adherence:.1f}, profitability={profitability:.1f}, blended={blended:.1f}")
    return result