"""Tests for pendula.agent module."""

from unittest.mock import MagicMock, patch

import pytest

from pendula.agent import agent_loop


def _make_choice(message):
    """Create a fake choice object with a message."""
    return MagicMock(message=message)


def _make_message(content, tool_calls=None):
    """Create a fake message with optional tool_calls."""
    msg = MagicMock()
    msg.content = content
    msg.tool_calls = tool_calls

    def model_dump():
        d = {"role": "assistant", "content": content}
        if tool_calls:
            d["tool_calls"] = [
                {"type": "function", "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                for tc in tool_calls
            ]
        return d

    msg.model_dump = model_dump
    return msg


def _make_tool_call(name, arguments, call_id="call_1"):
    """Create a real ChatCompletionMessageFunctionToolCall via model_construct."""
    from openai.types.chat import ChatCompletionMessageFunctionToolCall

    func = MagicMock()
    func.name = name
    func.arguments = arguments
    return ChatCompletionMessageFunctionToolCall.construct(
        id=call_id,
        function=func,
        type="function",
    )


@patch("pendula.agent.get_client")
def test_agent_loop_returns_on_no_tool_calls(mock_get_client):
    """When the model returns a message without tool_calls, the loop should exit."""
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = MagicMock(
        choices=[_make_choice(_make_message(content="Hello!", tool_calls=None))]
    )
    mock_get_client.return_value = mock_client

    messages = [{"role": "user", "content": "say hi"}]
    agent_loop(messages)

    assert len(messages) == 2
    assert messages[-1]["role"] == "assistant"


@patch("pendula.agent.get_client")
def test_agent_loop_calls_tool_and_appends_result(mock_get_client):
    """When the model calls a tool, the loop dispatches and appends a tool result."""
    tool_call = _make_tool_call(
        name="bash",
        arguments='{"command":"echo hello"}',
    )
    first_msg = _make_message(content=None, tool_calls=[tool_call])
    second_msg = _make_message(content="done!", tool_calls=None)

    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = [
        MagicMock(choices=[_make_choice(first_msg)]),
        MagicMock(choices=[_make_choice(second_msg)]),
    ]
    mock_get_client.return_value = mock_client

    messages = [{"role": "user", "content": "run echo hello"}]
    agent_loop(messages)

    assert len(messages) >= 4
    tool_results = [m for m in messages if m.get("role") == "tool"]
    assert len(tool_results) == 1
    assert "hello" in tool_results[0]["content"]


@patch("pendula.agent.get_client")
def test_agent_loop_unknown_tool(mock_get_client):
    """When the model calls an unknown tool, the loop returns an error message."""
    tool_call = _make_tool_call(
        name="nonexistent_tool",
        arguments='{}',
    )
    first_msg = _make_message(content=None, tool_calls=[tool_call])
    second_msg = _make_message(content="done", tool_calls=None)

    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = [
        MagicMock(choices=[_make_choice(first_msg)]),
        MagicMock(choices=[_make_choice(second_msg)]),
    ]
    mock_get_client.return_value = mock_client

    messages = [{"role": "user", "content": "use unknown tool"}]
    agent_loop(messages)

    tool_results = [m for m in messages if m.get("role") == "tool"]
    assert len(tool_results) == 1
    assert "Unknown" in tool_results[0]["content"]


@patch("pendula.agent.get_client")
def test_agent_loop_nag_reminder_after_three_rounds(mock_get_client):
    """After 3 consecutive rounds without todo_write, a reminder should be injected."""
    bash_call = _make_tool_call(
        name="bash",
        arguments='{"command":"echo round"}',
    )
    bash_msg = _make_message(content=None, tool_calls=[bash_call])
    done_msg = _make_message(content="done", tool_calls=None)

    # Simulate 3 rounds of bash calls, then a final round with no tool calls
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = [
        MagicMock(choices=[_make_choice(bash_msg)]),  # round 1: bash
        MagicMock(choices=[_make_choice(bash_msg)]),  # round 2: bash
        MagicMock(choices=[_make_choice(bash_msg)]),  # round 3: bash (triggers reminder)
        MagicMock(choices=[_make_choice(done_msg)]),  # round 4: exit
    ]
    mock_get_client.return_value = mock_client

    messages = [{"role": "user", "content": "do something"}]
    agent_loop(messages)

    # After 3 tool rounds, a user reminder should exist in messages
    reminder_msgs = [m for m in messages if "reminder" in (m.get("content") or "")]
    assert len(reminder_msgs) >= 1
