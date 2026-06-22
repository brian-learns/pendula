"""Tests for pendula.subagent module."""

from unittest.mock import MagicMock, patch

import pytest

from pendula.subagent import SUB_MAX_ROUNDS, SUB_SYSTEM, spawn_subagent


def test_SUB_SYSTEM_mentions_no_delegate():
    """The sub-agent prompt should forbid delegation."""
    assert "do not delegate" in SUB_SYSTEM or "no task" in SUB_SYSTEM


def test_SUB_MAX_ROUNDS_is_positive():
    """The safety limit should be a positive integer."""
    assert isinstance(SUB_MAX_ROUNDS, int)
    assert SUB_MAX_ROUNDS > 0


@patch("pendula.subagent.get_client")
def test_spawn_subagent_returns_conclusion(mock_get_client):
    """When the sub-agent finishes without tool calls, it should return its conclusion."""
    mock_client = MagicMock()
    # Single response: no tool calls, just a conclusion
    mock_client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(
            content="Task completed! Found 3 Python files.",
            tool_calls=None,
            model_dump=lambda: {"role": "assistant", "content": "Task completed! Found 3 Python files."},
        ))]
    )
    mock_get_client.return_value = mock_client

    result = spawn_subagent("Find Python files")
    assert "Task completed" in result


@patch("pendula.subagent.get_client")
def test_spawn_subagent_returns_error_on_limit(mock_get_client):
    """When the sub-agent exceeds SUB_MAX_ROUNDS, it should return an error."""
    mock_client = MagicMock()
    # Every response has tool calls — sub-agent never stops
    tool_call = MagicMock()
    tool_call.function.name = "bash"
    tool_call.function.arguments = '{"command":"echo loop"}'
    tool_call.id = "call_1"
    tc_type = MagicMock()
    # Mock ChatCompletionMessageFunctionToolCall.construct
    from openai.types.chat import ChatCompletionMessageFunctionToolCall

    tc = ChatCompletionMessageFunctionToolCall.construct(
        id="call_1",
        function=MagicMock(name="bash", arguments='{"command":"echo loop"}'),
        type="function",
    )

    mock_client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(
            content=None,
            tool_calls=[tc],
            model_dump=lambda: {
                "role": "assistant",
                "content": None,
                "tool_calls": [{
                    "type": "function",
                    "function": {"name": "bash", "arguments": '{"command":"echo loop"}'},
                }],
            },
        ))]
    )
    mock_get_client.return_value = mock_client

    result = spawn_subagent("loop forever")
    assert "Error" in result or "limit" in result
