"""
Utility functions
"""

import logging


def setup_logging(level: str = "INFO"):
    """Configure logging

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def enable_debug():
    """Enable debug logging for NetPulse SDK (one-liner shortcut)"""
    setup_logging("DEBUG")
