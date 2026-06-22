"""Tests for pendula.hooks module."""

from unittest.mock import MagicMock, patch

import pytest

from pendula.hooks import (
    HOOKS,
    permission_hook,
    register_hook,
    trigger_hooks,
)


def test_register_and_trigger():
    """A registered callback should be called on trigger."""
    called = []

    def my_hook(block):
        called.append(block)
        return None

    register_hook("PreToolUse", my_hook)
    trigger_hooks("PreToolUse", "test_block")
    assert called == ["test_block"]

    # Clean up
    HOOKS["PreToolUse"].remove(my_hook)


def test_trigger_returns_first_block():
    """If a callback returns a string, that string should be returned."""
    def block_hook(_):
        return "blocked"

    register_hook("PreToolUse", block_hook)
    result = trigger_hooks("PreToolUse", "anything")
    assert result == "blocked"

    HOOKS["PreToolUse"].remove(block_hook)


def test_trigger_returns_none_if_no_block():
    """If no callback blocks, trigger_hooks should return None."""
    def allow_hook(_):
        return None

    register_hook("PreToolUse", allow_hook)
    result = trigger_hooks("PreToolUse", "anything")
    assert result is None

    HOOKS["PreToolUse"].remove(allow_hook)


def test_register_unknown_event():
    """Registering for an invalid event should raise ValueError."""
    with pytest.raises(ValueError, match="Unknown hook event"):
        register_hook("NonExistent", lambda _: None)


def test_trigger_unknown_event():
    """Triggering an unknown event should return None without error."""
    result = trigger_hooks("NonExistent")
    assert result is None


def test_register_multiple_callbacks():
    """Multiple callbacks for the same event should all fire."""
    results = []

    def cb1(_):
        results.append("cb1")
        return None

    def cb2(_):
        results.append("cb2")
        return None

    register_hook("UserPromptSubmit", cb1)
    register_hook("UserPromptSubmit", cb2)
    trigger_hooks("UserPromptSubmit", "query")
    assert results == ["cb1", "cb2"]

    HOOKS["UserPromptSubmit"].clear()


def test_permission_hook_allows_safe_bash():
    """A safe bash command should not be blocked by permission_hook."""
    block = MagicMock()
    block.name = "bash"
    block.input = {"command": "echo hello"}

    result = permission_hook(block)
    assert result is None


def test_permission_hook_allows_safe_write():
    """A write inside workspace should not be blocked."""
    block = MagicMock()
    block.name = "write_file"
    block.input = {"path": "test.txt", "content": "data"}

    result = permission_hook(block)
    assert result is None


@patch("builtins.input")
def test_permission_hook_allows_destructive_when_user_approves(mock_input):
    """A destructive command should be allowed if user types 'y'."""
    mock_input.return_value = "y"

    block = MagicMock()
    block.name = "bash"
    block.input = {"command": "rm /tmp/file.txt"}

    result = permission_hook(block)
    assert result is None
