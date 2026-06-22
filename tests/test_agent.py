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


@patch("pendula.agent.client")
def test_agent_loop_returns_on_no_tool_calls(mock_client):
    """When the model returns a message without tool_calls, the loop should exit."""
    mock_client.chat.completions.create.return_value = MagicMock(
        choices=[_make_choice(_make_message(content="Hello!", tool_calls=None))]
    )

    messages = [{"role": "user", "content": "say hi"}]
    agent_loop(messages)

    # Should have appended the assistant response
    assert len(messages) == 2
    assert messages[-1]["role"] == "assistant"


@patch("pendula.agent.client")
def test_agent_loop_calls_tool_and_appends_result(mock_client):
    """When the model calls a tool, the loop dispatches and appends a tool result."""
    # First response: model calls bash
    tool_call = _make_tool_call(
        name="bash",
        arguments='{"command":"echo hello"}',
    )
    first_msg = _make_message(content=None, tool_calls=[tool_call])

    # Second response: model returns final text
    second_msg = _make_message(content="done!", tool_calls=None)

    mock_client.chat.completions.create.side_effect = [
        MagicMock(choices=[_make_choice(first_msg)]),
        MagicMock(choices=[_make_choice(second_msg)]),
    ]

    messages = [{"role": "user", "content": "run echo hello"}]
    agent_loop(messages)

    # Should have: user msg, assistant msg with tool_calls, tool result, final assistant msg
    assert len(messages) >= 4
    # One of the messages should be a tool result
    tool_results = [m for m in messages if m.get("role") == "tool"]
    assert len(tool_results) == 1
    assert "hello" in tool_results[0]["content"]


@patch("pendula.agent.client")
def test_agent_loop_unknown_tool(mock_client):
    """When the model calls an unknown tool, the loop returns an error message."""
    tool_call = _make_tool_call(
        name="nonexistent_tool",
        arguments='{}',
    )
    first_msg = _make_message(content=None, tool_calls=[tool_call])
    second_msg = _make_message(content="done", tool_calls=None)

    mock_client.chat.completions.create.side_effect = [
        MagicMock(choices=[_make_choice(first_msg)]),
        MagicMock(choices=[_make_choice(second_msg)]),
    ]

    messages = [{"role": "user", "content": "use unknown tool"}]
    agent_loop(messages)

    tool_results = [m for m in messages if m.get("role") == "tool"]
    assert len(tool_results) == 1
    assert "Unknown" in tool_results[0]["content"]
