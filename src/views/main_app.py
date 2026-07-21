"""Main application window."""
import logging
import customtkinter as ctk
from src.views.dashboard_frame import DashboardFrame
from src.controllers.app_controller import AppController

logger = logging.getLogger(__name__)


class RiskManagerApp(ctk.CTk):
    """Main Risk Manager application window."""
    
    def __init__(self):
        super().__init__()
        
        self.title("Risk Manager")
        self.geometry("900x700")
        self.minsize(800, 600)
        
        # Set dark theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Create controller
        self.controller = AppController(self)
        
        # Setup UI
        self._setup_ui()
        
        logger.info("Main application window created")
    
    def _setup_ui(self):
        """Setup the UI components."""
        # Main container with padding
        self.main_container = ctk.CTkFrame(self)
        self.main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Title
        self.title_label = ctk.CTkLabel(
            self.main_container,
            text="Risk Manager - Trading Co-pilot",
            font=("Helvetica", 20, "bold")
        )
        self.title_label.pack(pady=(0, 10))
        
        # Dashboard frame
        self.dashboard = DashboardFrame(self.main_container, self.controller)
        self.dashboard.pack(fill="both", expand=True)
        
        # Status bar at bottom
        self.status_bar = ctk.CTkLabel(
            self.main_container,
            text="Ready",
            font=("Helvetica", 10),
            anchor="w"
        )
        self.status_bar.pack(fill="x", pady=(10, 0))
        
        logger.info("UI setup complete")
    
    def update_status(self, message: str):
        """Update the status bar message."""
        self.status_bar.configure(text=message)