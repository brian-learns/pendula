"""Configuration for the Pendula coding agent.

Loads environment variables and creates the shared OpenAI client.
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
    "Use tools to solve tasks. Act, don't explain."
)

client = openai.OpenAI()
