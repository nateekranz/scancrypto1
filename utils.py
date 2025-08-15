# ====================================
# FILE: utils.py
# DESCRIPTION: Reusable utility functions
# ====================================

import logging
from datetime import datetime, timezone
import config

def setup_logging():
    """Configures the logging for the entire application."""
    logging.basicConfig(
        level=config.LOG_LEVEL,
        format=config.LOG_FORMAT,
        handlers=[
            logging.FileHandler(config.LOG_FILE),
            logging.StreamHandler()
        ]
    )

def get_current_day_warning() -> str:
    """Provides a simple news warning based on the day of the week."""
    current_day = datetime.now(timezone.utc).strftime('%A')
    if current_day in ['Wednesday', 'Friday']:
        return f"Potential high-impact news today ({current_day})"
    return "No major scheduled news expected"