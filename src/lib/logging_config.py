"""
Logging configuration for Claude Code Vision.

Provides centralized logging setup with file rotation and configurable levels.
"""

import logging
import logging.handlers
from pathlib import Path
from typing import Optional


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    max_size_mb: int = 10,
    backup_count: int = 3,
) -> logging.Logger:
    """
    Setup logging configuration for Claude Code Vision.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR)
        log_file: Path to log file. If None, uses default location
        max_size_mb: Maximum log file size in MB before rotation
        backup_count: Number of rotated log files to keep

    Returns:
        Configured logger instance

    Example:
        >>> logger = setup_logging(level="DEBUG")
        >>> logger.info("Application started")
    """
    # Create logger
    logger = logging.getLogger("claude_code_vision")
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Clear any existing handlers
    logger.handlers.clear()

    # Create formatters
    detailed_formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_formatter = logging.Formatter(
        fmt="%(levelname)s: %(message)s",
    )

    # Console handler (always enabled)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)  # Console shows INFO and above
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler (if log file specified)
    if log_file:
        log_path = Path(log_file).expanduser()
        log_path.parent.mkdir(parents=True, exist_ok=True)

        max_bytes = max_size_mb * 1024 * 1024
        file_handler = logging.handlers.RotatingFileHandler(
            filename=log_path,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.DEBUG)  # File logs everything
        file_handler.setFormatter(detailed_formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get logger instance for a specific module.

    Args:
        name: Logger name (typically __name__ from calling module)

    Returns:
        Logger instance

    Example:
        >>> from src.lib.logging_config import get_logger
        >>> logger = get_logger(__name__)
        >>> logger.debug("Debug message")
    """
    if name:
        return logging.getLogger(f"claude_code_vision.{name}")
    return logging.getLogger("claude_code_vision")


# Default logger instance
default_logger = logging.getLogger("claude_code_vision")
