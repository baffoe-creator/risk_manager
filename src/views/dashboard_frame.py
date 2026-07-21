"""Dashboard UI component."""
import logging
import customtkinter as ctk
from tkinter import messagebox
from src.models.risk_engine import RiskStatus

logger = logging.getLogger(__name__)


class DashboardFrame(ctk.CTkFrame):
    """Main dashboard frame with live data and controls."""
    
    STATUS_COLORS = {
        RiskStatus.GREEN: "#00cc44",
        RiskStatus.YELLOW: "#ffcc00",
        RiskStatus.ORANGE: "#ff8800",
        RiskStatus.RED: "#ff0000",
        RiskStatus.DATA_ERROR: "#808080"
    }
    
    STATUS_LABELS = {
        RiskStatus.GREEN: "GREEN - Normal",
        RiskStatus.YELLOW: "YELLOW - Caution",
        RiskStatus.ORANGE: "ORANGE - Warning",
        RiskStatus.RED: "RED - Critical",
        RiskStatus.DATA_ERROR: "DATA ERROR"
    }
    
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.current_status = RiskStatus.GREEN
        self.current_warnings = []
        
        self._setup_ui()
        self._update_display()
    
    def _setup_ui(self):
        """Setup all UI components."""
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)
        self.grid_rowconfigure(3, weight=0)
        self.grid_rowconfigure(4, weight=0)
        
        self._create_status_panel()
        self._create_data_panel()
        self._create_limits_panel()
        self._create_controls()
        self._create_cooldown_timer()
    
    def _create_status_panel(self):
        """Create the status display panel."""
        self.status_frame = ctk.CTkFrame(self)
        self.status_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        
        self.status_indicator = ctk.CTkLabel(
            self.status_frame,
            text="GREEN - Normal",
            font=("Helvetica", 16, "bold"),
            fg_color="#00cc44",
            corner_radius=8,
            padx=20,
            pady=10
        )
        self.status_indicator.pack(side="left", padx=10, pady=10)
        
        self.warnings_label = ctk.CTkLabel(
            self.status_frame,
            text="No warnings",
            font=("Helvetica", 12),
            anchor="w"
        )
        self.warnings_label.pack(side="left", padx=20, pady=10, fill="x", expand=True)
    
    def _create_data_panel(self):
        """Create the live data display panel."""
        self.data_frame = ctk.CTkFrame(self)
        self.data_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 5))
        
        ctk.CTkLabel(
            self.data_frame,
            text="Live Data",
            font=("Helvetica", 14, "bold")
        ).grid(row=0, column=0, columnspan=2, pady=(10, 5), sticky="w", padx=10)
        
        self.data_fields = {}
        fields = [
            ("P&L", "$0.00"),
            ("Position Size", "0.00"),
            ("Trade Count", "0"),
            ("Trading Time", "0 min"),
            ("Consecutive Losses", "0")
        ]
        
        for i, (label, initial_value) in enumerate(fields):
            frame = ctk.CTkFrame(self.data_frame, fg_color="transparent")
            frame.grid(row=i+1, column=0, columnspan=2, sticky="ew", pady=2, padx=10)
            
            ctk.CTkLabel(
                frame,
                text=f"{label}:",
                font=("Helvetica", 12),
                width=120,
                anchor="w"
            ).pack(side="left", padx=(0, 10))
            
            value_label = ctk.CTkLabel(
                frame,
                text=initial_value,
                font=("Helvetica", 12, "bold"),
                anchor="w"
            )
            value_label.pack(side="left", fill="x", expand=True)
            self.data_fields[label] = value_label
        
        # OCR Status indicator
        self.ocr_status_label = ctk.CTkLabel(
            self.data_frame,
            text="Source: Simulate",
            font=("Helvetica", 10),
            text_color="gray"
        )
        self.ocr_status_label.grid(row=len(fields)+1, column=0, columnspan=2, pady=(5, 5), sticky="w", padx=10)
    
    def _create_limits_panel(self):
        """Create the daily limits display panel."""
        self.limits_frame = ctk.CTkFrame(self)
        self.limits_frame.grid(row=1, column=1, sticky="nsew", padx=(5, 0))
        
        ctk.CTkLabel(
            self.limits_frame,
            text="Daily Limits",
            font=("Helvetica", 14, "bold")
        ).grid(row=0, column=0, columnspan=2, pady=(10, 5), sticky="w", padx=10)
        
        self.limit_fields = {}
        limits = [
            ("Daily Loss Limit", "$1000.00"),
            ("Max Position Size", "10.00"),
            ("Max Trades/Day", "20"),
            ("Trading Cutoff", "16:00"),
            ("Consecutive Loss Limit", "5"),
            ("Cooldown Period", "30 min")
        ]
        
        for i, (label, initial_value) in enumerate(limits):
            frame = ctk.CTkFrame(self.limits_frame, fg_color="transparent")
            frame.grid(row=i+1, column=0, columnspan=2, sticky="ew", pady=2, padx=10)
            
            ctk.CTkLabel(
                frame,
                text=f"{label}:",
                font=("Helvetica", 11),
                width=140,
                anchor="w"
            ).pack(side="left", padx=(0, 10))
            
            value_label = ctk.CTkLabel(
                frame,
                text=initial_value,
                font=("Helvetica", 11, "bold"),
                anchor="w"
            )
            value_label.pack(side="left", fill="x", expand=True)
            self.limit_fields[label] = value_label
    
    def _create_controls(self):
        """Create the control buttons."""
        self.controls_frame = ctk.CTkFrame(self)
        self.controls_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        
        session_frame = ctk.CTkFrame(self.controls_frame, fg_color="transparent")
        session_frame.pack(side="left", padx=10, pady=10)
        
        self.start_btn = ctk.CTkButton(
            session_frame,
            text="Start Session",
            command=self._on_start_session,
            width=120
        )
        self.start_btn.pack(side="left", padx=5)
        
        self.end_btn = ctk.CTkButton(
            session_frame,
            text="End Session",
            command=self._on_end_session,
            state="disabled",
            width=120
        )
        self.end_btn.pack(side="left", padx=5)
        
        data_frame = ctk.CTkFrame(self.controls_frame, fg_color="transparent")
        data_frame.pack(side="right", padx=10, pady=10)
        
        self.simulate_btn = ctk.CTkButton(
            data_frame,
            text="Simulate Data",
            command=self._on_simulate,
            width=120,
            state="disabled"
        )
        self.simulate_btn.pack(side="left", padx=5)
        
        # OCR Toggle
        self.ocr_switch = ctk.CTkSwitch(
            data_frame,
            text="OCR",
            command=self._on_ocr_toggle,
            width=80
        )
        self.ocr_switch.pack(side="left", padx=5)
        
        self.settings_btn = ctk.CTkButton(
            data_frame,
            text="Settings",
            command=self._on_settings,
            width=100
        )
        self.settings_btn.pack(side="left", padx=5)
    
    def _create_cooldown_timer(self):
        """Create the cooldown timer display."""
        self.cooldown_frame = ctk.CTkFrame(self)
        self.cooldown_frame.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        
        self.cooldown_label = ctk.CTkLabel(
            self.cooldown_frame,
            text="⏱️ Cooldown active: 0 seconds remaining",
            font=("Helvetica", 12, "bold"),
            text_color="#ff8800"
        )
        self.cooldown_label.pack(pady=5)
        
        self.cooldown_frame.grid_remove()
    
    def update_dashboard(self, state, status, warnings, settings):
        """Update all dashboard components with new data."""
        self.current_status = status
        self.current_warnings = warnings
        
        self._update_status_panel(status, warnings)
        
        if state:
            self._update_data_fields(state)
        
        if settings:
            self._update_limit_fields(settings)
        
        self._update_cooldown_state()
    
    def _update_status_panel(self, status, warnings):
        """Update the status panel with new status."""
        color = self.STATUS_COLORS.get(status, "#808080")
        label = self.STATUS_LABELS.get(status, "UNKNOWN")
        
        self.status_indicator.configure(
            text=label,
            fg_color=color
        )
        
        if warnings:
            warning_text = "⚠ " + " | ".join(warnings[:3])
            if len(warnings) > 3:
                warning_text += f" (+{len(warnings)-3} more)"
            self.warnings_label.configure(text=warning_text)
        else:
            self.warnings_label.configure(text="✓ No warnings")
    
    def _update_data_fields(self, state):
        """Update the live data fields."""
        self.data_fields["P&L"].configure(text=f"${state.current_pnl:,.2f}")
        self.data_fields["Position Size"].configure(text=f"{state.position_size:.2f}")
        self.data_fields["Trade Count"].configure(text=str(state.num_trades))
        self.data_fields["Trading Time"].configure(text=f"{state.trading_time_minutes} min")
        self.data_fields["Consecutive Losses"].configure(text=str(state.consecutive_losses))
    
    def _update_limit_fields(self, settings):
        """Update the daily limits fields."""
        self.limit_fields["Daily Loss Limit"].configure(text=f"${float(settings.get('daily_loss_limit', 0)):,.2f}")
        self.limit_fields["Max Position Size"].configure(text=f"{float(settings.get('max_contract_size', 0)):.2f}")
        self.limit_fields["Max Trades/Day"].configure(text=settings.get('max_trades_per_day', '0'))
        self.limit_fields["Trading Cutoff"].configure(text=settings.get('trading_cutoff_time', '16:00'))
        self.limit_fields["Consecutive Loss Limit"].configure(text=settings.get('consecutive_loss_limit', '0'))
        self.limit_fields["Cooldown Period"].configure(text=f"{settings.get('cooldown_period_minutes', '0')} min")
    
    def _update_cooldown_state(self):
        """Update cooldown UI state."""
        remaining = self.controller.get_cooldown_remaining()
        
        if remaining > 0:
            self.cooldown_frame.grid()
            self.cooldown_label.configure(text=f"⏱️ Cooldown active: {remaining} seconds remaining")
            self.simulate_btn.configure(state="disabled")
        else:
            self.cooldown_frame.grid_remove()
            if self.controller.session_active:
                self.simulate_btn.configure(state="normal")
    
    def set_session_controls(self, active: bool):
        """Update session control button states."""
        if active:
            self.start_btn.configure(state="disabled")
            self.end_btn.configure(state="normal")
            self.simulate_btn.configure(state="normal")
        else:
            self.start_btn.configure(state="normal")
            self.end_btn.configure(state="disabled")
            self.simulate_btn.configure(state="disabled")
    
    def _on_start_session(self):
        """Handle Start Session button click."""
        if self.controller.start_session():
            self.set_session_controls(True)
            messagebox.showinfo("Session Started", "Trading session has been started.")
    
    def _on_end_session(self):
        """Handle End Session button click."""
        if messagebox.askyesno("End Session", "Are you sure you want to end the session?"):
            summary = self.controller.end_session()
            if summary:
                self.set_session_controls(False)
                self.controller.show_report(summary)
    
    def _on_simulate(self):
        """Handle Simulate Data button click."""
        self.controller.simulate_data()
    
    def _on_settings(self):
        """Handle Settings button click."""
        self.controller.show_settings()
    
    def _on_ocr_toggle(self):
        """Handle OCR toggle."""
        enabled = self.ocr_switch.get() == 1
        if enabled:
            # Check if OCR is available
            if not self.controller.toggle_ocr(True):
                self.ocr_switch.deselect()
                messagebox.showerror("OCR Error", "OCR is not available. Please install pytesseract, opencv-python, and mss.")
                return
            self.ocr_status_label.configure(text="Source: OCR (Active)", text_color="#00cc44")
            self.simulate_btn.configure(state="disabled")
        else:
            self.controller.toggle_ocr(False)
            self.ocr_status_label.configure(text="Source: Simulate", text_color="gray")
            if self.controller.session_active:
                self.simulate_btn.configure(state="normal")
        
        logger.info(f"OCR toggled: {enabled}")
    
    def update_cooldown_ui(self):
        """Update cooldown UI from controller."""
        self._update_cooldown_state()
    
    def _update_display(self):
        """Initial display update."""
        state = self.controller.get_current_state()
        status = self.controller.get_current_status()
        warnings = self.controller.get_current_warnings()
        settings = self.controller.get_current_settings()
        
        if state and settings:
            self.update_dashboard(state, status, warnings, settings)
        
        self._start_cooldown_updates()
    
    def _start_cooldown_updates(self):
        """Start periodic cooldown updates."""
        self.after(1000, self._update_cooldown_loop)
    
    def _update_cooldown_loop(self):
        """Update cooldown every second."""
        self.update_cooldown_ui()
        self.after(1000, self._update_cooldown_loop)