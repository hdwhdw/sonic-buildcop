"""Tests for buildcop_common.log — structured logging setup."""
import logging
import re

from buildcop_common.log import setup_logging, DEFAULT_FORMAT, DEFAULT_DATEFMT


def test_setup_logging_configures_root():
    setup_logging()
    root = logging.getLogger()
    assert root.level == logging.INFO
    assert len(root.handlers) >= 1


def test_log_format_has_components(capfd):
    setup_logging()
    logger = logging.getLogger("test.format_check")
    logger.info("hello format test")
    captured = capfd.readouterr()
    # Timestamp: YYYY-MM-DD HH:MM:SS
    assert re.search(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", captured.err)
    # Level name
    assert "INFO" in captured.err
    # Logger name in brackets
    assert "[test.format_check]" in captured.err
    # Message
    assert "hello format test" in captured.err


def test_setup_logging_custom_level():
    setup_logging(level=logging.DEBUG)
    root = logging.getLogger()
    assert root.level == logging.DEBUG


def test_module_logger(capfd):
    setup_logging()
    logger = logging.getLogger("buildcop_common.http")
    logger.warning("test warning message")
    captured = capfd.readouterr()
    assert "WARNING" in captured.err
    assert "[buildcop_common.http]" in captured.err
    assert "test warning message" in captured.err


def test_setup_logging_force(capfd):
    setup_logging(fmt="%(levelname)s - %(message)s")
    logger = logging.getLogger("test.force_check")
    logger.info("first format")
    setup_logging()  # Reset to default format
    logger.info("second format")
    captured = capfd.readouterr()
    # Second call should use default format with brackets
    assert "[test.force_check]" in captured.err
