"""Structured logging configuration for SONiC build infrastructure tools."""

import logging
import sys

DEFAULT_FORMAT = "%(asctime)s %(levelname)-8s [%(name)s] %(message)s"
DEFAULT_DATEFMT = "%Y-%m-%d %H:%M:%S"


def setup_logging(
    level: int = logging.INFO,
    fmt: str = DEFAULT_FORMAT,
    datefmt: str = DEFAULT_DATEFMT,
) -> None:
    """Configure root logger with human-readable format.

    Call once in each app's main() entry point.
    Library modules use logging.getLogger(__name__) internally
    and do NOT call this function.

    Args:
        level: Logging level (default: INFO).
        fmt: Log format string.
        datefmt: Timestamp format string.
    """
    logging.basicConfig(
        level=level,
        format=fmt,
        datefmt=datefmt,
        stream=sys.stderr,
        force=True,
    )
