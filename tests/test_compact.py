"""Tests for pendula.compact module."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from pendula.compact import (
    KEEP_RECENT_TOOL_RESULTS,
    MAX_MESSAGES,
    THRESHOLD_CHARS,
    _is_tool_result_message,
    _message_has_tool_use,
    compact_history,
    estimate_token_count,
    micro_compact,
    reactive_compact,
    run_compression_pipeline,
    snip_compact,
    tool_result_budget,
    write_transcript,
)


def test_THRESHOLD_CHARS_is_positive():
    assert THRESHOLD_CHARS > 0


def test_MAX_MESSAGES_is_positive():
    assert MAX_MESSAGES > 0


def test_KEEP_RECENT_TOOL_RESULTS_is_positive():
    assert KEEP_RECENT_TOOL_RESULTS > 0


# ── Helpers ──


def test_message_has_tool_use():
    assert _message_has_tool_use({"role": "assistant", "tool_calls": ["a"]})
    assert not _message_has_tool_use({"role": "user", "content": "hi"})
    assert not _message_has_tool_use({"role": "assistant", "content": "hi"})


def test_is_tool_result_message():
    assert _is_tool_result_message({"role": "tool", "content": "x"})
    assert not _is_tool_result_message({"role": "user", "content": "x"})


def test_estimate_token_count():
    msgs = [{"role": "user", "content": "hello world"}]
    count = estimate_token_count(msgs)
    assert count > 0


# ── snip_compact ──


def test_snip_compact_keeps_short_list():
    msgs = [{"role": "user", "content": f"msg {i}"} for i in range(10)]
    result = snip_compact(msgs, max_messages=50)
    assert len(result) == 10


def test_snip_compact_trims_long_list():
    msgs = [{"role": "user", "content": f"msg {i}"} for i in range(100)]
    result = snip_compact(msgs, max_messages=50)
    assert len(result) <= 52  # 3 head + 1 placeholder + 47 tail


def test_snip_compact_protects_boundary():
    # Simulate a tool_use followed by tool_result at the boundary
    msgs = [{"role": "user", "content": f"msg {i}"} for i in range(80)]
    msgs.insert(2, {"role": "assistant", "tool_calls": ["tc1"], "content": None})
    msgs.insert(3, {"role": "tool", "content": "result1"})
    result = snip_compact(msgs, max_messages=50)
    assert len(result) <= 52


# ── micro_compact ──


def test_micro_compact_keeps_few_results():
    msgs = [
        {"role": "tool", "content": "a" * 200} for _ in range(2)
    ]
    result = micro_compact(msgs)
    assert result == msgs


def test_micro_compact_replaces_old_results():
    msgs = [
        {"role": "tool", "content": "a" * 200} for _ in range(10)
    ]
    result = micro_compact(msgs)
    # Last KEEP_RECENT_TOOL_RESULTS should be intact
    intact = result[-KEEP_RECENT_TOOL_RESULTS:]
    assert all(len(m.get("content", "")) > 100 for m in intact)
    # Older ones should be replaced
    old = result[:-KEEP_RECENT_TOOL_RESULTS]
    assert any("compacted" in m.get("content", "") for m in old)


# ── tool_result_budget ──


def test_tool_result_budget_keeps_small():
    msgs = [{"role": "user", "content": [{"type": "tool_result", "content": "small", "tool_use_id": "1"}]}]
    result = tool_result_budget(msgs, max_bytes=200_000)
    assert "persisted" not in str(result)


def test_tool_result_budget_persists_large():
    msgs = [{"role": "user", "content": [{"type": "tool_result", "content": "x" * 300_000, "tool_use_id": "1"}]}]
    result = tool_result_budget(msgs, max_bytes=200_000)
    content = str(result[-1].get("content", ""))
    assert "<persisted-output>" in content


# ── compact_history ──


@patch("pendula.config.get_client")
def test_compact_history_replaces_messages(mock_get_client):
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(
            content="Summary of the conversation.",
            model_dump=lambda: {"role": "assistant", "content": "Summary"},
        ))]
    )
    mock_get_client.return_value = mock_client

    msgs = [{"role": "user", "content": "hello"}, {"role": "assistant", "content": "world"}]
    result = compact_history(msgs)
    assert len(result) == 1
    assert "[Compacted]" in result[0]["content"]


# ── reactive_compact ──


@patch("pendula.config.get_client")
def test_reactive_compact_keeps_tail(mock_get_client):
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(
            content="Emergency summary.",
            model_dump=lambda: {"role": "assistant", "content": "Emergency"},
        ))]
    )
    mock_get_client.return_value = mock_client

    msgs = [{"role": "user", "content": f"msg {i}"} for i in range(20)]
    result = reactive_compact(msgs)
    assert len(result) >= 2  # summary + tail


# ── write_transcript ──


def test_write_transcript_creates_file():
    msgs = [{"role": "user", "content": "test"}]
    path = write_transcript(msgs)
    assert path.exists()
    assert ".transcripts" in str(path)
    path.unlink()


# ── run_compression_pipeline ──


def test_pipeline_runs_without_error():
    msgs = [{"role": "user", "content": "hello"}]
    result = run_compression_pipeline(msgs)
    assert len(result) >= 1
