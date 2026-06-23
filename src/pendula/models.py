"""Pydantic argument models for OpenAI function-calling tools.

These models define the typed input schemas that the LLM uses
to call tool handlers.  They are also usable standalone for
validation outside the agent loop.
"""

from pydantic import BaseModel, Field


class BashArgs(BaseModel):
    """Input model for the ``bash`` tool."""

    command: str = Field(..., description="The shell command to run.")


class ReadFileArgs(BaseModel):
    """Input model for the ``read_file`` tool."""

    path: str = Field(..., description="The path to the file to read.")
    limit: int | None = Field(default=None, description="Maximum number of lines to return.")


class WriteFileArgs(BaseModel):
    """Input model for the ``write_file`` tool."""

    path: str = Field(..., description="The path to write to.")
    content: str = Field(..., description="The content to write.")


class EditFileArgs(BaseModel):
    """Input model for the ``edit_file`` tool."""

    path: str = Field(..., description="The path to the file to edit.")
    old_text: str = Field(..., description="The exact text to find and replace.")
    new_text: str = Field(..., description="The replacement text.")


class GlobArgs(BaseModel):
    """Input model for the ``glob`` tool."""

    pattern: str = Field(..., description="The glob pattern to search for.")


class TodoItem(BaseModel):
    """A single item in a TODO list."""

    content: str = Field(..., description="Task description.")
    status: str = Field(..., description="Status: pending, in_progress, or completed.")


class TodoWriteArgs(BaseModel):
    """Input model for the ``todo_write`` tool."""

    todos: list[TodoItem] = Field(..., description="List of tasks with statuses.")


class TaskArgs(BaseModel):
    """Input model for the ``task`` tool."""

    description: str = Field(..., description="The subtask description for the sub-agent.")


class LoadSkillArgs(BaseModel):
    """Input model for the ``load_skill`` tool."""

    name: str = Field(..., description="The skill name to load.")


class CompactArgs(BaseModel):
    """Input model for the ``compact`` tool."""

    note: str = Field(
        default="",
        description="Optional note about why compaction was requested.",
    )
