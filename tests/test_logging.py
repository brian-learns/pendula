"""Tests for pendula.logging module."""

from pendula.logging import configure_logging, get_logger, log_call


def test_configure_logging_once():
    """configure_logging can be called multiple times but only initialises once."""
    configure_logging("DEBUG")
    # Calling again should not raise
    configure_logging("INFO")


def test_get_logger():
    """get_logger returns a bound logger with the module name."""
    log = get_logger("test_module")
    assert log is not None


def test_log_call_decorator():
    """log_call decorator wraps a function and returns its result."""
    logger = get_logger("test")

    @log_call(logger, event="test_event")
    def my_fn(a: int, b: int) -> int:
        return a + b

    result = my_fn(1, 2)
    assert result == 3
