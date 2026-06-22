"""Logging framework for Pendula.

Uses ``structlog`` for structured output.
Tracing/debug goes to stderr; normal operational logs go to stdout.
"""

from __future__ import annotations

import logging
import sys

import structlog

_initialized = False


def configure_logging(level: str = "INFO") -> None:
    """One-shot setup of structured logging.

    Parameters
    ----------
    level : str
        One of ``DEBUG``, ``INFO``, ``WARNING``, ``ERROR``.
    """
    global _initialized
    if _initialized:
        return
    _initialized = True

    level_int = getattr(logging, level.upper(), logging.INFO)

    # Stdlib logging: tracing → stderr, normal logs → stdout
    logging.root.setLevel(level_int)
    logging.root.addHandler(logging.StreamHandler(sys.stdout))  # normal logs
    logging.root.addHandler(logging.StreamHandler(sys.stderr))  # tracing

    # Structlog: pretty-print to stderr, JSON to stdout
    structlog.configure(
        wrapper_class=structlog.make_filtering_bound_logger(level_int),
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer(),
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(module: str) -> structlog.stdlib.BoundLogger:
    """Return a bound logger for *module*."""
    return structlog.get_logger(module)


def log_call(logger: structlog.stdlib.BoundLogger, event: str = "tool_call"):
    """Decorator: log entry + duration on every call to a tool handler."""

    def decorate(fn):
        """Return wrapped function with entry/exit logging."""
        import functools

        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            """Log call entry, execute, log result or error."""
            logger.debug(event, args=str(args), kwargs=str(kwargs))
            try:
                result = fn(*args, **kwargs)
                logger.info(event, result=str(result)[:200])
                return result
            except Exception as exc:
                logger.warning(event, error=str(exc))
                raise

        return wrapper

    return decorate
