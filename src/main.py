"""Main entry point for Risk Manager application."""
import logging
import sys
from pathlib import Path

# Add src to path if running from project root
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import path helper first to set up paths
from src.path_helper import get_log_file, get_database_path, get_data_path


def setup_logging():
    """Configure logging with RotatingFileHandler."""
    from logging.handlers import RotatingFileHandler
    
    log_file = get_log_file()
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    
    # File handler with rotation
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=3
    )
    file_handler.setLevel(logging.DEBUG)
    
    # Console handler for development
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    return root_logger


def main():
    """Launch the Risk Manager application."""
    logger = setup_logging()
    logger.info("=" * 60)
    logger.info("Risk Manager Application Starting")
    logger.info(f"Data directory: {get_data_path()}")
    logger.info(f"Database path: {get_database_path()}")
    logger.info(f"Log file: {get_log_file()}")
    logger.info("=" * 60)
    
    try:
        # Update DataManager to use persistent database path
        from src.models.data_manager import DataManager
        from src.controllers.app_controller import AppController
        from src.views.main_app import RiskManagerApp
        
        # Override DataManager default path
        DataManager._default_db_path = get_database_path()
        
        app = RiskManagerApp()
        app.controller.set_dashboard(app.dashboard)
        app.mainloop()
    except Exception as e:
        logger.critical(f"Application crashed: {e}", exc_info=True)
        raise
    finally:
        logger.info("Risk Manager application closed")
        logger.info("=" * 60)


if __name__ == "__main__":
    main()