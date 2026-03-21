import logging
import os
import sys

import structlog
from dotenv import load_dotenv
from structlog.dev import ConsoleRenderer

load_dotenv()

__all__ = ["get_logger"]


def _configure_structlog(log_as_json: bool) -> None:
    processors: list = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt=None if log_as_json else "%y%m%d %H:%M.%S"),
        structlog.processors.JSONRenderer(separators=(",", ":"))
        if log_as_json
        else ConsoleRenderer(),
    ]

    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def _setup_logging() -> None:
    log_as_json = os.environ.get("LOG_AS_JSON", "false").lower() not in (
        "0",
        "false",
        "no",
    )

    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    _configure_structlog(log_as_json)


LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()


def get_logger(name: str):
    if not structlog.is_configured():
        _setup_logging()

    log = structlog.get_logger(name)
    log.setLevel(LOG_LEVEL)
    return log
