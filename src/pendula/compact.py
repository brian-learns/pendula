"""Context compression for the Pendula coding agent.

Four-layer pipeline — cheap first, expensive last:

1. **L3: tool_result_budget** — persist large tool results (>200KB) to disk
2. **L1: snip_compact** — trim middle messages when count > 50
3. **L2: micro_compact** — replace old tool results with placeholders
4. **L4: compact_history** — LLM summary when tokens still exceed threshold

Plus ``reactive_compact`` — emergency trim when API returns prompt_too_long.
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path

from .config import WORKDIR

# ═══════════════════════════════════════════════════════════
#  Constants
# ═══════════════════════════════════════════════════════════

THRESHOLD_CHARS = 200_000  # chars → compact_history trigger
MAX_MESSAGES = 50  # max messages before snip_compact triggers
HEAD_KEEP = 3  # messages to keep from the start
KEEP_RECENT_TOOL_RESULTS = 3  # tool_results to keep intact in micro_compact
MAX_TOOL_RESULT_BYTES = 200_000  # persist results larger than this
MAX_CONSECUTIVE_FAILURES = 3  # circuit breaker for compact_history
MAX_REACTIVE_RETRIES = 1  # retry limit for reactive_compact

# ═══════════════════════════════════════════════════════════
#  Helpers
# ═══════════════════════════════════════════════════════════


def _message_has_tool_use(msg: dict) -> bool:
    """Check if a message contains tool_calls (assistant with tool_use)."""
    return msg.get("role") == "assistant" and "tool_calls" in msg and msg["tool_calls"]


def _is_tool_result_message(msg: dict) -> bool:
    """Check if a message is a tool_result (user role with tool_call_id)."""
    return msg.get("role") == "tool"


def estimate_token_count(messages: list[dict]) -> int:
    """Estimate token count from character length (cheap approximation).

    Uses a rough 4:1 character-to-token ratio.
    """
    total = 0
    for msg in messages:
        content = msg.get("content") or ""
        total += len(content)
    return total // 4


def write_transcript(messages: list[dict], suffix: str = "") -> Path:
    """Write the full conversation to a JSONL transcript file.

    Returns the path to the transcript.
    """
    transcript_dir = WORKDIR / ".transcripts"
    transcript_dir.mkdir(parents=True, exist_ok=True)
    stamp = uuid.uuid4().hex[:8]
    path = transcript_dir / f"compact_{stamp}{suffix}.jsonl"
    with path.open("w", encoding="utf-8") as f:
        f.writelines(json.dumps(msg, ensure_ascii=False) + "\n" for msg in messages)
    return path


def persist_large_output(tool_call_id: str, content: str) -> str:
    """Persist large tool result content to disk, return a marker string.

    Returns a ``<persisted-output>`` marker with a 2000-char preview.
    """
    out_dir = WORKDIR / ".task_outputs" / "tool-results"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{tool_call_id}.txt"
    path.write_text(content, encoding="utf-8")
    preview = content[:2000]
    return f"<persisted-output>\n{preview}\n(Full content at {path})"


# ═══════════════════════════════════════════════════════════
#  Layer 3: tool_result_budget
# ═══════════════════════════════════════════════════════════


def tool_result_budget(
    messages: list[dict],
    max_bytes: int = MAX_TOOL_RESULT_BYTES,
) -> list[dict]:
    """Persist large tool results in the last user message to disk.

    Runs first so micro_compact doesn't replace content before it's saved.
    """
    if not messages:
        return messages

    last = messages[-1]
    if last.get("role") != "user":
        return messages

    content = last.get("content", "")
    # Content is a list of blocks in OpenAI format
    if isinstance(content, list):
        blocks = list(content)
    else:
        blocks = [{"type": "text", "text": content}]

    # Find tool_result blocks
    result_blocks = [
        (i, b) for i, b in enumerate(blocks) if b.get("type") == "tool_result"
    ]
    if not result_blocks:
        return messages

    total = sum(len(str(b.get("content", ""))) for _, b in result_blocks)
    if total <= max_bytes:
        return messages

    # Sort by size descending
    ranked = sorted(
        result_blocks, key=lambda p: len(str(p[1].get("content", ""))), reverse=True
    )

    for _, block in ranked:
        if total <= max_bytes:
            break
        content_str = str(block.get("content", ""))
        block["content"] = persist_large_output(
            block.get("tool_use_id", ""), content_str
        )
        total = sum(len(str(b.get("content", ""))) for _, b in result_blocks)

    messages[-1]["content"] = blocks
    return messages


# ═══════════════════════════════════════════════════════════
#  Layer 1: snip_compact
# ═══════════════════════════════════════════════════════════


def snip_compact(
    messages: list[dict],
    max_messages: int = MAX_MESSAGES,
) -> list[dict]:
    """Trim middle messages when count exceeds *max_messages*.

    Keeps HEAD_KEEP messages from the start and tail, with a boundary guard
    to prevent separating a tool_use from its tool_result.
    """
    if len(messages) <= max_messages:
        return messages

    head_end = HEAD_KEEP
    tail_start = len(messages) - (max_messages - HEAD_KEEP)

    # Ensure tool_use at head boundary is not separated from its tool_result
    if _message_has_tool_use(messages[head_end - 1]):
        while head_end < len(messages) and _is_tool_result_message(messages[head_end]):
            head_end += 1

    # Ensure tool_result at tail boundary has its tool_use
    if _is_tool_result_message(messages[tail_start]) and _message_has_tool_use(
        messages[tail_start - 1]
    ):
        tail_start -= 1

    snipped = tail_start - head_end
    placeholder = {
        "role": "user",
        "content": f"[snipped {snipped} messages from conversation middle]",
    }
    return [*messages[:head_end], placeholder, *messages[tail_start:]]


# ═══════════════════════════════════════════════════════════
#  Layer 2: micro_compact
# ═══════════════════════════════════════════════════════════


def micro_compact(messages: list[dict]) -> list[dict]:
    """Replace old tool_result content with placeholders.

    Keeps ``KEEP_RECENT_TOOL_RESULTS`` most recent tool_results intact.
    """
    tool_results = [
        (i, m) for i, m in enumerate(messages) if _is_tool_result_message(m)
    ]
    if len(tool_results) <= KEEP_RECENT_TOOL_RESULTS:
        return messages

    for _, msg in tool_results[:-KEEP_RECENT_TOOL_RESULTS]:
        content = msg.get("content") or ""
        if len(content) > 120:
            msg["content"] = "[Earlier tool result compacted. Re-run if needed.]"

    return messages


# ═══════════════════════════════════════════════════════════
#  Layer 4: compact_history (LLM summary)
# ═══════════════════════════════════════════════════════════


def summarize_history(
    messages: list[dict],
) -> str:
    """Ask the LLM to produce a summary of the conversation.

    Uses the same client and model as the main agent loop.
    """
    from .config import MAX_TOKENS, MODEL, get_client

    client = get_client()
    summary_system = (
        "You are a summarizer. Produce a concise summary of the conversation. "
        "Include: current goals, important findings, modified files, "
        "remaining work, user constraints. Do NOT call tools."
    )
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "system", "content": summary_system}, *messages],
        max_tokens=MAX_TOKENS,
    )
    return response.choices[0].message.content or "(empty summary)"


def compact_history(messages: list[dict]) -> list[dict]:
    """Save transcript, generate LLM summary, replace messages with summary."""
    write_transcript(messages)
    summary = summarize_history(messages)
    return [{"role": "user", "content": f"[Compacted]\n\n{summary}"}]


# ═══════════════════════════════════════════════════════════
#  Reactive compact (emergency)
# ═══════════════════════════════════════════════════════════


def reactive_compact(messages: list[dict]) -> list[dict]:
    """Emergency trim when API returns prompt_too_long.

    More aggressive than compact_history: keeps last 5 messages after the
    summary, with a boundary guard.
    """
    write_transcript(messages, suffix="_reactive")
    summary = summarize_history(messages)

    tail_start = max(0, len(messages) - 5)
    if _is_tool_result_message(messages[tail_start]) and _message_has_tool_use(
        messages[tail_start - 1]
    ):
        tail_start -= 1

    return [
        {"role": "user", "content": f"[Reactive compact]\n\n{summary}"},
        *messages[tail_start:],
    ]


# ═══════════════════════════════════════════════════════════
#  Pipeline runner
# ═══════════════════════════════════════════════════════════


def run_compression_pipeline(messages: list[dict]) -> list[dict]:
    """Run the full compression pipeline (budget → snip → micro).

    Returns compressed messages. Does NOT run compact_history — that is
    triggered separately when the estimated token count exceeds THRESHOLD.
    """
    messages = tool_result_budget(messages)
    messages = snip_compact(messages)
    messages = micro_compact(messages)
    return messages
