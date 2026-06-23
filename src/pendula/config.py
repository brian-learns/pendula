"""Configuration for the Pendula coding agent.

Loads environment variables and creates the shared OpenAI client.
The client is lazy-loaded so tests can mock it without needing a real .env file.
"""

import os
from contextlib import suppress
from pathlib import Path

with suppress(ImportError):
    import readline

    readline.parse_and_bind("set bind-tty-special-chars off")
    readline.parse_and_bind("set input-meta on")
    readline.parse_and_bind("set output-meta on")
    readline.parse_and_bind("set convert-meta off")

import openai
from dotenv import load_dotenv

load_dotenv(override=True)

WORKDIR = Path.cwd()
MODEL = os.environ["DEFAULT_MODEL"]
SYSTEM = (
    f"You are a coding agent at {WORKDIR}. "
    "Use tools to solve tasks. Act, don't explain.\n\n"
    "Before starting any complex task, use todo_write to list the steps. "
    "Update todo statuses as you work. "
    "If you receive a reminder to update todos, do so immediately."
)


def build_system(catalog: str = "") -> str:
    """Return the system prompt with an optional skill *catalog* prepended.

    Parameters
    ----------
    catalog : str
        A string listing available skills, or empty for no skills.
    """
    base = (
        f"You are a coding agent at {WORKDIR}. "
        "Use tools to solve tasks. Act, don't explain.\n\n"
        "Before starting any complex task, use todo_write to list the steps. "
        "Update todo statuses as you work. "
        "If you receive a reminder to update todos, do so immediately."
    )
    if catalog:
        base = (
            f"Skills available:\n{catalog}\n\n"
            "Use load_skill to get full details when needed.\n\n"
            f"{base}"
        )
    return base


# Maximum tokens per completion — can be overridden via env
MAX_TOKENS = int(os.environ.get("MAX_TOKENS", "8000"))

# Lazy-loaded client: constructed on first call to get_client()
_client: openai.OpenAI | None = None


def get_client() -> openai.OpenAI:
    """Return the shared OpenAI client, creating it if needed."""
    global _client
    if _client is None:
        _client = openai.OpenAI()
    return _client
