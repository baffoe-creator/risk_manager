"""Path helper for bundled application."""
import os
import sys
from pathlib import Path


def get_app_path() -> Path:
    """Get the application base path."""
    if getattr(sys, 'frozen', False):
        # Running as bundled executable
        return Path(sys.executable).parent
    else:
        # Running from source
        return Path(__file__).parent.parent


def get_data_path() -> Path:
    """Get the data directory path."""
    app_path = get_app_path()
    
    # On Windows, use AppData
    if sys.platform == 'win32':
        app_data = os.environ.get('APPDATA', '')
        if app_data:
            data_path = Path(app_data) / 'RiskManager'
        else:
            data_path = app_path / 'data'
    else:
        # Linux/Mac - use ~/.config
        home = Path.home()
        data_path = home / '.config' / 'riskmanager'
    
    data_path.mkdir(parents=True, exist_ok=True)
    return data_path


def get_database_path() -> Path:
    """Get the database file path."""
    return get_data_path() / 'trader_rules.db'


def get_log_path() -> Path:
    """Get the logs directory path."""
    log_path = get_data_path() / 'logs'
    log_path.mkdir(parents=True, exist_ok=True)
    return log_path


def get_log_file() -> Path:
    """Get the log file path."""
    return get_log_path() / 'app.log'