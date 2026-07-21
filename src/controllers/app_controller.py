"""Application controller wiring UI and models."""
import logging
import random
from typing import Optional, Tuple, List, Dict, Any
from datetime import datetime
from src.models.data_manager import DataManager
from src.models.session import Session
from src.models.risk_engine import TradeState, RiskStatus, evaluate_risk, calculate_discipline_score

try:
    from src.views.report_view import ReportView
except ImportError:
    ReportView = None

try:
    from src.ocr.ocr_thread import OCRCaptureThread
    OCR_AVAILABLE = True
except ImportError:
    OCRCaptureThread = None
    OCR_AVAILABLE = False

logger = logging.getLogger(__name__)


class AppController:
    """Controller managing application state and UI coordination."""
    
    def __init__(self, app):
        self.app = app
        self.data_manager = DataManager()
        self.session = Session()
        self.current_state: Optional[TradeState] = None
        self.current_status: RiskStatus = RiskStatus.GREEN
        self.current_warnings: List[str] = []
        self.current_settings: Dict[str, str] = {}
        self.dashboard = None
        
        # OCR
        self.ocr_thread: Optional[OCRCaptureThread] = None
        self.ocr_enabled = False
        self.ocr_poll_id = None
        self.data_source = "simulate"  # "simulate" or "ocr"
        
        self._load_settings()
    
    def set_dashboard(self, dashboard):
        """Set the dashboard reference."""
        self.dashboard = dashboard
    
    def _load_settings(self):
        """Load settings from database."""
        self.current_settings = self.data_manager.get_all_settings()
        logger.debug(f"Loaded {len(self.current_settings)} settings")
    
    def get_current_settings(self) -> Dict[str, str]:
        """Get current settings."""
        return self.current_settings
    
    def get_current_state(self) -> Optional[TradeState]:
        """Get current trade state."""
        return self.current_state
    
    def get_current_status(self) -> RiskStatus:
        """Get current risk status."""
        return self.current_status
    
    def get_current_warnings(self) -> List[str]:
        """Get current warnings."""
        return self.current_warnings
    
    def get_cooldown_remaining(self) -> int:
        """Get remaining cooldown time in seconds."""
        return self.session.get_cooldown_remaining()
    
    @property
    def session_active(self) -> bool:
        """Check if session is active."""
        return self.session.active
    
    def start_session(self) -> bool:
        """Start a new trading session."""
        try:
            self.session.start()
            
            self.current_state = TradeState(
                current_pnl=0.0,
                position_size=0.0,
                num_trades=0,
                trading_time_minutes=0,
                consecutive_losses=0
            )
            
            self._evaluate_and_update()
            
            # Start OCR if enabled
            if self.ocr_enabled:
                self._start_ocr()
            
            logger.info(f"Session started: {self.session.start_time}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start session: {e}")
            return False
    
    def end_session(self) -> Optional[Dict[str, Any]]:
        """End the current session and return summary."""
        try:
            if not self.session.active:
                logger.warning("Cannot end inactive session")
                return None
            
            # Stop OCR
            if self.ocr_enabled:
                self._stop_ocr()
            
            if self.current_state:
                self.session.sum_pnl = self.current_state.current_pnl
                self.session.trade_count = self.current_state.num_trades
                self.session.max_position_size = max(
                    self.session.max_position_size,
                    self.current_state.position_size
                )
            
            summary = self.session.get_summary()
            
            if self.current_settings and summary:
                scores = calculate_discipline_score(
                    summary.get("rule_violations", []),
                    self.current_settings,
                    summary.get("final_pnl", 0.0)
                )
                
                summary["adherence_score"] = scores["adherence"]
                summary["profitability_score"] = scores["profitability"]
                summary["discipline_score"] = scores["blended"]
                
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
                
                has_loss_limit_violation = any(
                    v.get("rule") == "daily_loss_limit" 
                    for v in summary.get("rule_violations", [])
                )
                summary["capital_preservation"] = 0 if has_loss_limit_violation else 100
            
            final_summary = self.session.end()
            
            if final_summary:
                session_id = self.data_manager.save_session(final_summary)
                if session_id:
                    logger.info(f"Session saved with ID: {session_id}")
                else:
                    logger.warning("Session data not saved to database")
            
            self.current_state = None
            self.current_status = RiskStatus.GREEN
            self.current_warnings = []
            
            if self.dashboard:
                self.dashboard.update_dashboard(None, self.current_status, [], self.current_settings)
                self.dashboard.set_session_controls(False)
            
            return final_summary
            
        except Exception as e:
            logger.error(f"Failed to end session: {e}")
            return None
    
    def simulate_data(self):
        """Generate simulated trade data and update dashboard."""
        if self.data_source == "ocr":
            logger.warning("Cannot simulate data when OCR is enabled")
            return
        
        try:
            if not self.session.active:
                logger.warning("Cannot simulate data: session not active")
                return
            
            if not self.session.is_cooldown_expired():
                logger.warning("Cannot simulate data: cooldown active")
                return
            
            if self.current_state is None:
                self.current_state = TradeState(
                    current_pnl=0.0,
                    position_size=0.0,
                    num_trades=0,
                    trading_time_minutes=0,
                    consecutive_losses=0
                )
            
            pnl_change = random.uniform(-200, 300)
            position_change = random.uniform(0, 2)
            
            new_pnl = self.current_state.current_pnl + pnl_change
            new_position = min(max(self.current_state.position_size + position_change, 0), 15)
            new_trades = self.current_state.num_trades + random.randint(0, 2)
            new_time = self.current_state.trading_time_minutes + random.randint(5, 30)
            
            if pnl_change < 0:
                new_losses = self.current_state.consecutive_losses + 1
            else:
                new_losses = 0
            
            self.current_state = TradeState(
                current_pnl=round(new_pnl, 2),
                position_size=round(new_position, 2),
                num_trades=new_trades,
                trading_time_minutes=new_time,
                consecutive_losses=new_losses
            )
            
            self.session.update_trade_stats(pnl_change, new_position)
            
            self._evaluate_and_update()
            
            if self.current_warnings:
                for warning in self.current_warnings:
                    rule = self._extract_rule_from_warning(warning)
                    severity = self._get_severity_for_rule(rule)
                    if rule:
                        self.session.record_violation(rule, severity)
            
            if self.current_status == RiskStatus.RED:
                cooldown_minutes = int(self.current_settings.get("cooldown_period_minutes", 30))
                self.session.start_cooldown(cooldown_minutes)
                logger.info(f"Cooldown started for {cooldown_minutes} minutes")
            
            logger.debug(f"Simulated data: {self.current_state}")
            
        except Exception as e:
            logger.error(f"Failed to simulate data: {e}")
    
    def _evaluate_and_update(self):
        """Evaluate risk with current state and update dashboard."""
        if self.current_state is None:
            return
        
        try:
            self.current_status, self.current_warnings = evaluate_risk(
                self.current_state,
                self.current_settings
            )
            
            if self.dashboard:
                self.dashboard.update_dashboard(
                    self.current_state,
                    self.current_status,
                    self.current_warnings,
                    self.current_settings
                )
                
        except Exception as e:
            logger.error(f"Failed to evaluate risk: {e}")
            self.current_status = RiskStatus.DATA_ERROR
            self.current_warnings = ["Risk evaluation failed"]
    
    def _extract_rule_from_warning(self, warning: str) -> str:
        """Extract rule name from warning message."""
        warning_lower = warning.lower()
        if "loss limit" in warning_lower:
            return "daily_loss_limit"
        elif "position size" in warning_lower:
            return "max_contract_size"
        elif "trade count" in warning_lower:
            return "max_trades_per_day"
        elif "trading time" in warning_lower or "cutoff" in warning_lower:
            return "trading_cutoff_time"
        elif "consecutive losses" in warning_lower:
            return "consecutive_loss_limit"
        elif "cooldown" in warning_lower:
            return "cooldown_period_minutes"
        return ""
    
    def _get_severity_for_rule(self, rule: str) -> str:
        """Get severity for a rule from settings."""
        if not rule:
            return "minor"
        
        severity_map = self.current_settings.get("rule_severity_map", {})
        if isinstance(severity_map, str):
            import json
            try:
                severity_map = json.loads(severity_map)
            except:
                severity_map = {}
        
        return severity_map.get(rule, "minor")
    
    def show_report(self, summary: Dict[str, Any]):
        """Show the report view."""
        try:
            if ReportView is None:
                logger.error("ReportView not available")
                return
            
            report = ReportView(self.app, summary)
            report.grab_set()
        except Exception as e:
            logger.error(f"Failed to show report: {e}")
    
    def show_settings(self):
        """Show the settings dialog."""
        try:
            from src.views.settings_dialog import SettingsDialog
            dialog = SettingsDialog(self.app, self)
            dialog.grab_set()
        except Exception as e:
            logger.error(f"Failed to show settings: {e}")
    
    def update_setting(self, key: str, value: str):
        """Update a setting and refresh dashboard."""
        try:
            if self.data_manager.save_setting(key, value):
                self._load_settings()
                
                if self.current_state:
                    self._evaluate_and_update()
                
                logger.info(f"Setting updated: {key} = {value}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to update setting {key}: {e}")
            return False
    
    # OCR Methods
    
    def toggle_ocr(self, enabled: bool):
        """Enable or disable OCR data source."""
        if not OCR_AVAILABLE:
            logger.warning("OCR not available - missing dependencies")
            return False
        
        self.ocr_enabled = enabled
        self.data_source = "ocr" if enabled else "simulate"
        
        if enabled:
            self._start_ocr()
        else:
            self._stop_ocr()
        
        logger.info(f"OCR {'enabled' if enabled else 'disabled'}")
        return True
    
    def _start_ocr(self):
        """Start OCR capture thread."""
        if not OCR_AVAILABLE:
            logger.error("OCR not available")
            return
        
        if self.ocr_thread and self.ocr_thread.is_alive():
            logger.warning("OCR thread already running")
            return
        
        try:
            # Configure regions (these would come from user settings)
            regions = {
                "pnl": (100, 200, 150, 40),
                "position_size": (100, 300, 150, 40),
                "trade_count": (100, 400, 150, 40),
                "trading_time": (100, 500, 150, 40),
                "consecutive_losses": (100, 600, 150, 40)
            }
            
            self.ocr_thread = OCRCaptureThread(capture_interval=0.5)
            self.ocr_thread.configure_regions(regions)
            self.ocr_thread.start()
            
            # Start polling
            self._poll_ocr_results()
            
            logger.info("OCR capture thread started")
            
        except Exception as e:
            logger.error(f"Failed to start OCR: {e}")
    
    def _stop_ocr(self):
        """Stop OCR capture thread."""
        if self.ocr_thread:
            self.ocr_thread.stop()
            self.ocr_thread = None
            logger.info("OCR capture thread stopped")
        
        if self.ocr_poll_id:
            if self.dashboard:
                self.dashboard.after_cancel(self.ocr_poll_id)
            self.ocr_poll_id = None
    
    def _poll_ocr_results(self):
        """Poll OCR results from the queue."""
        if not self.ocr_thread or not self.ocr_thread.is_alive():
            return
        
        try:
            # Get result without blocking
            result = self.ocr_thread.get_result(block=False)
            
            if result:
                if result["success"]:
                    # Update state with OCR data
                    state = result["state"]
                    if state and self.session.active:
                        # Update current state
                        self.current_state = state
                        
                        # Update session stats
                        self.session.trade_count = state.num_trades
                        self.session.sum_pnl = state.current_pnl
                        self.session.max_position_size = max(
                            self.session.max_position_size,
                            state.position_size
                        )
                        
                        # Evaluate risk
                        self._evaluate_and_update()
                        
                        # Record violations
                        if self.current_warnings:
                            for warning in self.current_warnings:
                                rule = self._extract_rule_from_warning(warning)
                                severity = self._get_severity_for_rule(rule)
                                if rule:
                                    self.session.record_violation(rule, severity)
                        
                        # Check cooldown
                        if self.current_status == RiskStatus.RED:
                            cooldown_minutes = int(self.current_settings.get("cooldown_period_minutes", 30))
                            self.session.start_cooldown(cooldown_minutes)
                            logger.info(f"Cooldown started for {cooldown_minutes} minutes")
                        
                        logger.debug("OCR data processed successfully")
                else:
                    # OCR failure - set DATA_ERROR
                    logger.warning(f"OCR failed: {result.get('error', 'Unknown error')}")
                    self.current_status = RiskStatus.DATA_ERROR
                    self.current_warnings = ["OCR data capture failed"]
                    
                    if self.dashboard and self.current_state:
                        self.dashboard.update_dashboard(
                            self.current_state,
                            self.current_status,
                            self.current_warnings,
                            self.current_settings
                        )
            
        except Exception as e:
            logger.error(f"Failed to poll OCR results: {e}")
        
        # Schedule next poll
        if self.dashboard and self.ocr_enabled:
            self.ocr_poll_id = self.dashboard.after(500, self._poll_ocr_results)
    
    def get_ocr_status(self) -> bool:
        """Get OCR status."""
        return self.ocr_enabled and self.ocr_thread is not None and self.ocr_thread.is_alive()