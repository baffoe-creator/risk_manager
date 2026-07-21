"""Main application window."""
import logging
import customtkinter as ctk

logger = logging.getLogger(__name__)


class RiskManagerApp(ctk.CTk):
    """Main Risk Manager application window."""
    
    def __init__(self):
        super().__init__()
        
        self.title("Risk Manager")
        self.geometry("800x600")
        
        # Set dark theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Placeholder for main content
        self.label = ctk.CTkLabel(
            self,
            text="Risk Manager - Coming Soon",
            font=("Helvetica", 24)
        )
        self.label.pack(expand=True, fill="both")
        
        logger.info("Main application window created")