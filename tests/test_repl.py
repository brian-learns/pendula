"""Tests for pendula.repl module."""

from unittest.mock import MagicMock, patch

import pytest

from pendula.repl import run_repl


@patch("pendula.repl.agent_loop")
@patch("builtins.input")
def test_run_repl_sends_query(mock_input, mock_agent_loop):
    """A non-empty query should be sent to agent_loop."""
    mock_input.side_effect = ["hello", "q"]
    mock_agent_loop.return_value = None

    run_repl()

    # agent_loop should have been called with one user message
    assert mock_agent_loop.call_count == 1
    args = mock_agent_loop.call_args[0][0]
    assert len(args) == 1
    assert args[0]["role"] == "user"
    assert args[0]["content"] == "hello"


@patch("pendula.repl.agent_loop")
@patch("builtins.input")
def test_run_repl_exits_on_q(mock_input, mock_agent_loop):
    """Typing 'q' should exit without calling agent_loop."""
    mock_input.side_effect = ["q"]
    run_repl()
    mock_agent_loop.assert_not_called()


@patch("pendula.repl.agent_loop")
@patch("builtins.input")
def test_run_repl_exits_on_empty_input(mock_input, mock_agent_loop):
    """Empty input should exit."""
    mock_input.side_effect = [""]
    run_repl()
    mock_agent_loop.assert_not_called()


@patch("pendula.repl.agent_loop")
@patch("builtins.input")
def test_run_repl_exits_on_eof(mock_input, mock_agent_loop):
    """EOFError should exit cleanly."""
    mock_input.side_effect = [EOFError]
    run_repl()
    mock_agent_loop.assert_not_called()


@patch("pendula.repl.agent_loop")
@patch("builtins.input")
def test_run_repl_exits_on_keyboard_interrupt(mock_input, mock_agent_loop):
    """KeyboardInterrupt should exit cleanly."""
    mock_input.side_effect = [KeyboardInterrupt]
    run_repl()
    mock_agent_loop.assert_not_called()
