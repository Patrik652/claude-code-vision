"""Unit tests for logging configuration helpers."""

import logging
import logging.handlers

from src.lib.logging_config import get_logger, setup_logging


def test_setup_logging_console_only_defaults_to_info_for_invalid_level() -> None:
    logger = setup_logging(level="not-a-level")

    assert logger.level == logging.INFO
    assert len(logger.handlers) == 1
    assert isinstance(logger.handlers[0], logging.StreamHandler)


def test_setup_logging_creates_rotating_file_handler(tmp_path) -> None:
    log_file = tmp_path / "logs" / "vision.log"

    logger = setup_logging(level="debug", log_file=str(log_file), max_size_mb=2, backup_count=5)

    file_handlers = [h for h in logger.handlers if isinstance(h, logging.handlers.RotatingFileHandler)]
    assert len(file_handlers) == 1
    file_handler = file_handlers[0]
    assert file_handler.maxBytes == 2 * 1024 * 1024
    assert file_handler.backupCount == 5
    assert log_file.parent.exists()


def test_setup_logging_clears_existing_handlers() -> None:
    base_logger = logging.getLogger("claude_code_vision")
    base_logger.handlers = [logging.NullHandler()]

    logger = setup_logging(level="INFO")

    assert not any(isinstance(h, logging.NullHandler) for h in logger.handlers)


def test_get_logger_returns_prefixed_name_when_module_given() -> None:
    logger = get_logger("src.some_module")
    assert logger.name == "claude_code_vision.src.some_module"


def test_get_logger_returns_base_logger_when_name_omitted() -> None:
    logger = get_logger()
    assert logger.name == "claude_code_vision"
