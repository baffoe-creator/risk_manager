"""Report view UI component."""
import logging
import customtkinter as ctk
from datetime import datetime

logger = logging.getLogger(__name__)


class ReportView(ctk.CTkToplevel):
    """Report view showing session summary."""
    
    def __init__(self, parent, session_data):
        super().__init__(parent)
        
        self.session_data = session_data
        self.title("Session Report")
        self.geometry("700x650")
        self.resizable(True, True)
        
        self.transient(parent)
        self.grab_set()
        
        self._setup_ui()
        self._display_report()
        
        logger.info("Report view created")
    
    def _setup_ui(self):
        """Setup the UI components."""
        self.container = ctk.CTkFrame(self)
        self.container.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.title_label = ctk.CTkLabel(
            self.container,
            text=" Session Report",
            font=("Helvetica", 20, "bold")
        )
        self.title_label.pack(pady=(0, 10))
        
        ctk.CTkFrame(self.container, height=2, fg_color="gray").pack(fill="x", pady=5)
        
        self.content_frame = ctk.CTkScrollableFrame(self.container)
        self.content_frame.pack(fill="both", expand=True, pady=10)
        
        self.close_btn = ctk.CTkButton(
            self.container,
            text="Close Report",
            command=self.destroy,
            width=150,
            fg_color="#2196F3",
            hover_color="#1976D2"
        )
        self.close_btn.pack(pady=(15, 0))
    
    def _display_report(self):
        """Display the session data in the report."""
        if not self.session_data:
            ctk.CTkLabel(
                self.content_frame,
                text="No session data available",
                font=("Helvetica", 14),
                text_color="gray"
            ).pack(pady=40)
            return
        
        self._add_section_header("Session Information")
        
        start_time = self.session_data.get("start_time", "N/A")
        end_time = self.session_data.get("end_time", "N/A")
        
        if start_time and start_time != "N/A" and start_time is not None:
            try:
                dt = datetime.fromisoformat(start_time)
                start_time = dt.strftime("%Y-%m-%d %H:%M:%S")
            except:
                pass
        else:
            start_time = "N/A"
        
        if end_time and end_time != "N/A" and end_time is not None:
            try:
                dt = datetime.fromisoformat(end_time)
                end_time = dt.strftime("%Y-%m-%d %H:%M:%S")
            except:
                pass
        else:
            end_time = "N/A"
        
        final_pnl = self.session_data.get("final_pnl", 0.0)
        if final_pnl is None:
            final_pnl = 0.0
        
        max_position = self.session_data.get("max_position_size", 0.0)
        if max_position is None:
            max_position = 0.0
        
        info_items = [
            ("Start Time", start_time),
            ("End Time", end_time),
            ("Duration", self._calculate_duration()),
            ("Total Trades", str(self.session_data.get("total_trades", 0) or 0)),
            ("Final P&L", f"${final_pnl:,.2f}"),
            ("Max Position Size", f"{max_position:.2f}"),
            ("Session Grade", self._format_grade())
        ]
        
        for label, value in info_items:
            self._add_info_row(label, value)
        
        self._add_separator()
        
        self._add_section_header("Performance Scores")
        
        adherence = self.session_data.get("adherence_score")
        if adherence is None:
            adherence = 0.0
        
        profitability = self.session_data.get("profitability_score")
        if profitability is None:
            profitability = 0.0
        
        discipline = self.session_data.get("discipline_score")
        if discipline is None:
            discipline = 0.0
        
        capital = self.session_data.get("capital_preservation")
        if capital is None:
            capital = 0
        
        scores = [
            ("Adherence Score", f"{adherence:.1f}%", self._get_score_color(adherence)),
            ("Profitability Score", f"{profitability:.1f}%", self._get_score_color(profitability)),
            ("Discipline Score (Blended)", f"{discipline:.1f}%", self._get_score_color(discipline)),
            ("Capital Preservation", f"{capital}%", self._get_score_color(capital))
        ]
        
        for label, value, color in scores:
            self._add_score_row(label, value, color)
        
        self._add_separator()
        
        self._add_section_header("Rule Violations")
        
        violations = self.session_data.get("rule_violations", [])
        if violations:
            for v in violations:
                rule = v.get('rule', 'Unknown')
                severity = v.get('severity', 'unknown')
                timestamp = v.get('timestamp', '')
                
                try:
                    if timestamp:
                        dt = datetime.fromisoformat(timestamp)
                        timestamp = dt.strftime("%H:%M:%S")
                except:
                    pass
                
                color = "#ff4444" if severity == "major" else "#ffaa00"
                self._add_violation_row(rule, severity, timestamp, color)
        else:
            ctk.CTkLabel(
                self.content_frame,
                text=" No violations recorded",
                font=("Helvetica", 13),
                text_color="#00cc44"
            ).pack(anchor="w", pady=8, padx=10)
        
        self._add_separator()
        
        self._add_section_header("Recommendations")
        
        recommendations = self._generate_recommendations()
        for rec in recommendations:
            self._add_recommendation_row(rec)
    
    def _calculate_duration(self) -> str:
        """Calculate session duration."""
        start = self.session_data.get("start_time")
        end = self.session_data.get("end_time")
        
        if not start or not end or start == "N/A" or end == "N/A":
            return "N/A"
        
        try:
            start_dt = datetime.fromisoformat(start)
            end_dt = datetime.fromisoformat(end)
            duration = end_dt - start_dt
            
            hours = duration.seconds // 3600
            minutes = (duration.seconds % 3600) // 60
            seconds = duration.seconds % 60
            
            if duration.days > 0:
                return f"{duration.days}d {hours:02d}h {minutes:02d}m"
            elif hours > 0:
                return f"{hours}h {minutes:02d}m"
            else:
                return f"{minutes}m {seconds:02d}s"
        except:
            return "N/A"
    
    def _format_grade(self) -> str:
        """Format the session grade with color."""
        grade = self.session_data.get("session_grade")
        if grade is None or grade == "N/A":
            return "N/A"
        
        grade_map = {
            "A": " A - Excellent",
            "B": " B - Good",
            "C": " C - Average",
            "D": " D - Below Average",
            "F": " F - Needs Improvement"
        }
        return grade_map.get(grade, grade)
    
    def _get_score_color(self, score: float) -> str:
        """Get color for a score."""
        if score >= 80:
            return "#00cc44"
        elif score >= 60:
            return "#ffaa00"
        elif score >= 40:
            return "#ff8800"
        else:
            return "#ff4444"
    
    def _add_section_header(self, text: str):
        """Add a section header."""
        header = ctk.CTkLabel(
            self.content_frame,
            text=text,
            font=("Helvetica", 16, "bold"),
            anchor="w"
        )
        header.pack(anchor="w", pady=(10, 5), padx=5)
    
    def _add_separator(self):
        """Add a separator line."""
        ctk.CTkFrame(self.content_frame, height=2, fg_color="gray").pack(
            fill="x", pady=10, padx=5
        )
    
    def _add_info_row(self, label: str, value: str):
        """Add an information row."""
        frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        frame.pack(fill="x", pady=3, padx=10)
        
        ctk.CTkLabel(
            frame,
            text=f"{label}:",
            font=("Helvetica", 13),
            width=180,
            anchor="w"
        ).pack(side="left")
        
        if label == "Final P&L":
            final_pnl = self.session_data.get("final_pnl", 0.0)
            if final_pnl is None:
                final_pnl = 0.0
            color = "#00cc44" if final_pnl >= 0 else "#ff4444"
            ctk.CTkLabel(
                frame,
                text=value,
                font=("Helvetica", 13, "bold"),
                text_color=color,
                anchor="w"
            ).pack(side="left", padx=5)
        else:
            ctk.CTkLabel(
                frame,
                text=value,
                font=("Helvetica", 13, "bold"),
                anchor="w"
            ).pack(side="left", padx=5)
    
    def _add_score_row(self, label: str, value: str, color: str):
        """Add a score row."""
        frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        frame.pack(fill="x", pady=3, padx=10)
        
        ctk.CTkLabel(
            frame,
            text=f"{label}:",
            font=("Helvetica", 13),
            width=220,
            anchor="w"
        ).pack(side="left")
        
        ctk.CTkLabel(
            frame,
            text=value,
            font=("Helvetica", 14, "bold"),
            text_color=color,
            anchor="w"
        ).pack(side="left", padx=5)
    
    def _add_violation_row(self, rule: str, severity: str, timestamp: str, color: str):
        """Add a violation row."""
        frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        frame.pack(fill="x", pady=3, padx=10)
        
        ctk.CTkLabel(
            frame,
            text=f"• {rule.replace('_', ' ').title()}",
            font=("Helvetica", 12),
            width=220,
            anchor="w"
        ).pack(side="left")
        
        badge = ctk.CTkLabel(
            frame,
            text=f"[{severity.upper()}]",
            font=("Helvetica", 11, "bold"),
            text_color=color,
            anchor="w"
        )
        badge.pack(side="left", padx=5)
        
        if timestamp:
            ctk.CTkLabel(
                frame,
                text=f"at {timestamp}",
                font=("Helvetica", 10),
                text_color="gray",
                anchor="w"
            ).pack(side="left", padx=5)
    
    def _add_recommendation_row(self, text: str):
        """Add a recommendation row."""
        frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        frame.pack(fill="x", pady=3, padx=10)
        
        ctk.CTkLabel(
            frame,
            text=f" {text}",
            font=("Helvetica", 12),
            anchor="w",
            wraplength=600,
            justify="left"
        ).pack(anchor="w", padx=5)
    
    def _generate_recommendations(self) -> list:
        """Generate recommendations based on session data."""
        recs = []
        
        if not self.session_data:
            return ["No data available for recommendations."]
        
        violations = self.session_data.get("rule_violations", [])
        if violations is None:
            violations = []
        
        final_pnl = self.session_data.get("final_pnl", 0.0)
        if final_pnl is None:
            final_pnl = 0.0
        
        adherence = self.session_data.get("adherence_score", 0.0)
        if adherence is None:
            adherence = 0.0
        
        discipline = self.session_data.get("discipline_score", 0.0)
        if discipline is None:
            discipline = 0.0
        
        if discipline >= 90:
            recs.append("Excellent discipline! You're following your risk rules exceptionally well. Keep up the good work!")
        elif discipline >= 75:
            recs.append("Good discipline overall. Focus on the specific areas where violations occurred to improve further.")
        elif discipline >= 60:
            recs.append("Moderate discipline. Review your risk rules carefully and consider tightening your controls.")
        else:
            recs.append("Significant discipline issues detected. Take time to review your trading plan and risk management strategy.")
        
        if adherence < 50:
            recs.append("Low adherence score indicates multiple rule violations. Consider a cooling-off period to reset your trading mindset.")
        elif adherence < 80:
            recs.append("Review the violations listed above. Even minor violations can compound over time.")
        
        if final_pnl < 0:
            recs.append(f"Negative P&L of ${abs(final_pnl):.2f}. Review your entries/exits and consider reducing position size.")
            if adherence < 80:
                recs.append("Your negative P&L combined with rule violations suggests emotional trading. Take a break and reassess.")
        elif final_pnl > 500:
            recs.append(f"Strong positive P&L of ${final_pnl:.2f}. Maintain your discipline and avoid overconfidence.")
        
        for v in violations:
            rule = v.get("rule", "")
            severity = v.get("severity", "")
            
            if rule == "daily_loss_limit":
                recs.append("Daily loss limit exceeded. This is a critical violation. Review your stop-loss placement and consider lowering position sizes.")
            elif rule == "max_contract_size":
                recs.append("Position size exceeded the maximum allowed. Size down your trades to better manage risk.")
            elif rule == "max_trades_per_day":
                recs.append("Trade count limit reached. Focus on quality over quantity. Overtrading often leads to poor decisions.")
            elif rule == "consecutive_loss_limit":
                recs.append("Consecutive losses detected. Take a mandatory break and review your strategy before returning.")
            elif rule == "trading_cutoff_time":
                recs.append("Trading beyond cutoff time. Stick to scheduled trading hours to avoid fatigue-related mistakes.")
            elif rule == "cooldown_period_minutes":
                recs.append("Cooldown period triggered. This is a good time to step away and clear your head.")
        
        capital_preservation = self.session_data.get("capital_preservation", 0)
        if capital_preservation is None:
            capital_preservation = 0
        
        if capital_preservation == 0:
            recs.append("Capital preservation score is 0 because the loss limit was hit. This is a critical risk management failure.")
        elif capital_preservation < 100:
            recs.append("Capital preservation could be improved. Consider tighter stop-losses or smaller position sizes.")
        
        duration = self._calculate_duration()
        if duration != "N/A" and "h" in duration:
            try:
                hours_str = duration.split("h")[0].strip()
                if hours_str:
                    hours = int(hours_str)
                    if hours > 4:
                        recs.append(f"Long trading session ({duration}). Consider taking more breaks to maintain sharp decision-making.")
            except:
                pass
        
        if len(recs) <= 1:
            recs.append("Solid session overall. Continue following your trading plan and risk rules.")
        
        return recs[:8]