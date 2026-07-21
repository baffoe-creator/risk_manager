"""Settings dialog UI component."""
import logging
import json
import customtkinter as ctk
from tkinter import messagebox

logger = logging.getLogger(__name__)


class SettingsDialog(ctk.CTkToplevel):
    """Settings dialog for editing risk parameters."""
    
    def __init__(self, parent, controller):
        super().__init__(parent)
        
        self.controller = controller
        self.title("Risk Settings")
        self.geometry("550x650")
        self.resizable(False, False)
        
        # Make it modal
        self.transient(parent)
        self.grab_set()
        
        self._setup_ui()
        self._load_settings()
        
        logger.info("Settings dialog created")
    
    def _setup_ui(self):
        """Setup the UI components."""
        # Main container with padding
        self.container = ctk.CTkFrame(self)
        self.container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        ctk.CTkLabel(
            self.container,
            text="Risk Settings",
            font=("Helvetica", 18, "bold")
        ).pack(pady=(0, 10))
        
        # Separator
        ctk.CTkFrame(self.container, height=2, fg_color="gray").pack(fill="x", pady=5)
        
        # Settings content (scrollable)
        self.content_frame = ctk.CTkScrollableFrame(self.container)
        self.content_frame.pack(fill="both", expand=True, pady=10)
        
        # Settings entries
        self.entries = {}
        settings_fields = [
            ("daily_loss_limit", "Daily Loss Limit ($)", "float"),
            ("max_contract_size", "Max Contract Size", "float"),
            ("max_trades_per_day", "Max Trades Per Day", "int"),
            ("trading_cutoff_time", "Trading Cutoff Time (HH:MM)", "str"),
            ("consecutive_loss_limit", "Consecutive Loss Limit", "int"),
            ("cooldown_period_minutes", "Cooldown Period (minutes)", "int")
        ]
        
        for i, (key, label, data_type) in enumerate(settings_fields):
            frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
            frame.pack(fill="x", pady=5)
            
            ctk.CTkLabel(
                frame,
                text=label,
                font=("Helvetica", 12),
                width=200,
                anchor="w"
            ).pack(side="left", padx=5)
            
            entry = ctk.CTkEntry(frame, width=150)
            entry.pack(side="right", padx=5)
            self.entries[key] = entry
        
        # Separator
        ctk.CTkFrame(self.content_frame, height=2, fg_color="gray").pack(fill="x", pady=15)
        
        # Rule severity mapping section
        ctk.CTkLabel(
            self.content_frame,
            text="Rule Severity Mapping",
            font=("Helvetica", 14, "bold")
        ).pack(anchor="w", pady=(5, 10))
        
        ctk.CTkLabel(
            self.content_frame,
            text="Major violations have a greater impact on discipline scores.",
            font=("Helvetica", 10),
            text_color="gray"
        ).pack(anchor="w", pady=(0, 10))
        
        # Severity dropdowns
        self.severity_vars = {}
        rule_names = [
            "daily_loss_limit",
            "max_contract_size", 
            "max_trades_per_day",
            "trading_cutoff_time",
            "consecutive_loss_limit",
            "cooldown_period_minutes"
        ]
        
        for rule in rule_names:
            frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
            frame.pack(fill="x", pady=3)
            
            # Rule name with nice formatting
            display_name = rule.replace("_", " ").title()
            ctk.CTkLabel(
                frame,
                text=display_name,
                font=("Helvetica", 11),
                width=200,
                anchor="w"
            ).pack(side="left", padx=5)
            
            severity_var = ctk.StringVar(value="minor")
            dropdown = ctk.CTkOptionMenu(
                frame,
                values=["major", "minor"],
                variable=severity_var,
                width=150
            )
            dropdown.pack(side="right", padx=5)
            self.severity_vars[rule] = severity_var
        
        # Buttons at bottom
        button_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        button_frame.pack(fill="x", pady=(15, 0))
        
        ctk.CTkButton(
            button_frame,
            text="Save",
            command=self._save_settings,
            width=120,
            fg_color="#2196F3",
            hover_color="#1976D2"
        ).pack(side="right", padx=5)
        
        ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=self.destroy,
            width=120,
            fg_color="#666",
            hover_color="#555"
        ).pack(side="right", padx=5)
        
        ctk.CTkButton(
            button_frame,
            text="Reset to Defaults",
            command=self._reset_defaults,
            width=120,
            fg_color="#FF9800",
            hover_color="#F57C00"
        ).pack(side="left", padx=5)
    
    def _load_settings(self):
        """Load current settings into the UI."""
        settings = self.controller.get_current_settings()
        
        # Load basic settings
        for key, entry in self.entries.items():
            value = settings.get(key, "")
            entry.delete(0, ctk.END)
            entry.insert(0, str(value))
        
        # Load severity mappings
        severity_map = settings.get("rule_severity_map", {})
        if isinstance(severity_map, str):
            try:
                severity_map = json.loads(severity_map)
            except:
                severity_map = {}
        
        for rule, var in self.severity_vars.items():
            var.set(severity_map.get(rule, "minor"))
    
    def _save_settings(self):
        """Save settings from UI to database and refresh dashboard."""
        try:
            # Validate inputs first
            if not self._validate_settings():
                return
            
            # Save basic settings
            for key, entry in self.entries.items():
                value = entry.get().strip()
                if value:
                    # Convert to appropriate type for validation
                    if key == "daily_loss_limit" or key == "max_contract_size":
                        try:
                            float(value)
                        except ValueError:
                            messagebox.showerror("Error", f"Invalid number for {key.replace('_', ' ').title()}")
                            return
                    elif key in ["max_trades_per_day", "consecutive_loss_limit", "cooldown_period_minutes"]:
                        try:
                            int(value)
                        except ValueError:
                            messagebox.showerror("Error", f"Invalid integer for {key.replace('_', ' ').title()}")
                            return
                    elif key == "trading_cutoff_time":
                        if ":" not in value or len(value.split(":")) != 2:
                            messagebox.showerror("Error", "Trading cutoff time must be in HH:MM format")
                            return
                        try:
                            hours, minutes = value.split(":")
                            int(hours), int(minutes)
                            if not (0 <= int(hours) <= 23 and 0 <= int(minutes) <= 59):
                                raise ValueError
                        except:
                            messagebox.showerror("Error", "Trading cutoff time must be valid HH:MM format")
                            return
                    
                    # Save the setting
                    self.controller.update_setting(key, value)
            
            # Save severity mapping
            severity_map = {}
            for rule, var in self.severity_vars.items():
                severity_map[rule] = var.get()
            
            self.controller.update_setting("rule_severity_map", json.dumps(severity_map))
            
            # Close dialog
            self.destroy()
            logger.info("Settings saved successfully")
            
            # Show success message
            messagebox.showinfo("Success", "Settings saved and dashboard updated!")
            
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")
            messagebox.showerror("Error", f"Failed to save settings: {e}")
    
    def _validate_settings(self) -> bool:
        """Validate all settings before saving."""
        try:
            # Check daily loss limit
            loss_limit = float(self.entries["daily_loss_limit"].get().strip())
            if loss_limit <= 0:
                messagebox.showerror("Error", "Daily loss limit must be greater than 0")
                return False
            
            # Check max contract size
            max_size = float(self.entries["max_contract_size"].get().strip())
            if max_size <= 0:
                messagebox.showerror("Error", "Max contract size must be greater than 0")
                return False
            
            # Check max trades per day
            max_trades = int(self.entries["max_trades_per_day"].get().strip())
            if max_trades <= 0:
                messagebox.showerror("Error", "Max trades per day must be greater than 0")
                return False
            
            # Check consecutive loss limit
            loss_limit = int(self.entries["consecutive_loss_limit"].get().strip())
            if loss_limit <= 0:
                messagebox.showerror("Error", "Consecutive loss limit must be greater than 0")
                return False
            
            # Check cooldown period
            cooldown = int(self.entries["cooldown_period_minutes"].get().strip())
            if cooldown <= 0:
                messagebox.showerror("Error", "Cooldown period must be greater than 0")
                return False
            
            return True
            
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid number format: {e}")
            return False
    
    def _reset_defaults(self):
        """Reset all settings to default values."""
        if not messagebox.askyesno("Confirm Reset", "Reset all settings to default values?"):
            return
        
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
        
        # Update UI
        for key, entry in self.entries.items():
            entry.delete(0, ctk.END)
            entry.insert(0, defaults[key])
        
        # Update severity dropdowns
        severity_map = json.loads(defaults["rule_severity_map"])
        for rule, var in self.severity_vars.items():
            var.set(severity_map.get(rule, "minor"))
        
        # Save defaults
        for key, value in defaults.items():
            if key != "rule_severity_map":
                self.controller.update_setting(key, value)
        
        self.controller.update_setting("rule_severity_map", defaults["rule_severity_map"])
        
        messagebox.showinfo("Reset Complete", "Settings have been reset to defaults.")
        self.destroy()