"""Tests for pendula.tools module."""

from pathlib import Path
from unittest.mock import patch

import pytest

from pendula.models import (
    BashArgs,
    EditFileArgs,
    GlobArgs,
    ReadFileArgs,
    WriteFileArgs,
)
from pendula.tools import (
    CURRENT_TODOS,
    TOOLS,
    TOOL_HANDLERS,
    reset_todos,
    run_bash,
    run_edit,
    run_glob,
    run_read,
    run_todo_write,
    run_write,
    safe_path,
)


class TestSafePath:
    def test_allows_relative_path(self):
        p = safe_path("some/file.txt")
        assert p == (Path.cwd() / "some/file.txt").resolve()

    def test_allows_absolute_inside_workspace(self):
        p = safe_path(str(Path.cwd()))
        assert p == Path.cwd().resolve()

    def test_rejects_path_escape(self):
        with pytest.raises(ValueError, match="escapes workspace"):
            safe_path("/etc/passwd")

    def test_rejects_dotdot_escape(self):
        with pytest.raises(ValueError, match="escapes workspace"):
            safe_path("../../etc/passwd")


class TestRunBash:
    def test_echo(self):
        result = run_bash("echo hello world")
        assert result == "hello world"

    def test_raw_bash_does_not_block(self):
        """run_bash no longer blocks inline — permission hook handles that."""
        result = run_bash("echo hello from raw")
        assert result == "hello from raw"

    @patch("pendula.tools.subprocess.run")
    def test_timeout(self, mock_run):
        import subprocess
        mock_run.side_effect = subprocess.TimeoutExpired("sleep", 120)
        result = run_bash("echo hello")
        assert "Timeout" in result


class TestRunWrite:
    def test_write_and_read_back(self, tmp_path):
        test_dir = Path.cwd() / "tmp_test_write"
        test_dir.mkdir(exist_ok=True)
        try:
            rel_path = str(Path(test_dir.name) / "test.txt")
            result = run_write(rel_path, "hello world")
            assert "Wrote" in result
            assert (test_dir / "test.txt").read_text() == "hello world"
        finally:
            import shutil
            shutil.rmtree(test_dir, ignore_errors=True)


class TestRunRead:
    def test_read_existing_file(self, tmp_path):
        test_dir = Path.cwd() / "tmp_test_read"
        test_dir.mkdir(exist_ok=True)
        try:
            (test_dir / "foo.txt").write_text("line1\nline2\nline3")
            rel_path = str(Path(test_dir.name) / "foo.txt")
            result = run_read(rel_path)
            assert result == "line1\nline2\nline3"
        finally:
            import shutil
            shutil.rmtree(test_dir, ignore_errors=True)

    def test_read_with_limit(self, tmp_path):
        test_dir = Path.cwd() / "tmp_test_read_limit"
        test_dir.mkdir(exist_ok=True)
        try:
            (test_dir / "foo.txt").write_text("a\nb\nc\nd\ne")
            rel_path = str(Path(test_dir.name) / "foo.txt")
            result = run_read(rel_path, limit=2)
            assert "(3 more lines)" in result
        finally:
            import shutil
            shutil.rmtree(test_dir, ignore_errors=True)

    def test_read_nonexistent(self):
        result = run_read("does_not_exist_12345.txt")
        assert "Error" in result


class TestRunEdit:
    def test_edit_success(self, tmp_path):
        test_dir = Path.cwd() / "tmp_test_edit"
        test_dir.mkdir(exist_ok=True)
        try:
            (test_dir / "foo.txt").write_text("hello world foo")
            rel_path = str(Path(test_dir.name) / "foo.txt")
            result = run_edit(rel_path, "foo", "bar")
            assert "Edited" in result
            assert (test_dir / "foo.txt").read_text() == "hello world bar"
        finally:
            import shutil
            shutil.rmtree(test_dir, ignore_errors=True)

    def test_edit_text_not_found(self, tmp_path):
        test_dir = Path.cwd() / "tmp_test_edit_notfound"
        test_dir.mkdir(exist_ok=True)
        try:
            (test_dir / "foo.txt").write_text("hello")
            rel_path = str(Path(test_dir.name) / "foo.txt")
            result = run_edit(rel_path, "zzz", "yyy")
            assert "not found" in result
        finally:
            import shutil
            shutil.rmtree(test_dir, ignore_errors=True)


class TestRunGlob:
    def test_glob_python_files(self):
        result = run_glob("src/pendula/*.py")
        lines = result.splitlines()
        expected = {"agent.py", "config.py", "tools.py", "cli.py", "__init__.py", "__main__.py", "pendula.py"}
        found = {Path(l).name for l in lines}
        assert found.intersection(expected), f"Expected at least one of {expected}, got {found}"

    def test_glob_no_matches(self):
        result = run_glob("--no-such-file--")
        assert "(no matches)" in result


class TestRunTodoWrite:
    def test_stores_todos_and_prints_progress(self, capsys):
        todos = [
            {"content": "Step 1", "status": "pending"},
            {"content": "Step 2", "status": "in_progress"},
        ]
        result = run_todo_write(todos)
        assert "Updated 2 tasks" in result
        assert CURRENT_TODOS == todos

        captured = capsys.readouterr()
        assert "## Current Tasks" in captured.out
        assert "Step 1" in captured.out
        assert "Step 2" in captured.out

    def test_reset_todos_clears_list(self):
        reset_todos()
        assert CURRENT_TODOS == []


class TestPydanticModels:
    def test_bash_args(self):
        a = BashArgs(command="echo hi")
        assert a.command == "echo hi"

    def test_read_file_args(self):
        a = ReadFileArgs(path="foo.txt", limit=10)
        assert a.path == "foo.txt"
        assert a.limit == 10

    def test_read_file_args_default_limit(self):
        a = ReadFileArgs(path="foo.txt")
        assert a.limit is None

    def test_write_file_args(self):
        a = WriteFileArgs(path="bar.txt", content="data")
        assert a.path == "bar.txt"
        assert a.content == "data"

    def test_edit_file_args(self):
        a = EditFileArgs(path="f.txt", old_text="old", new_text="new")
        assert a.path == "f.txt"
        assert a.old_text == "old"
        assert a.new_text == "new"

    def test_glob_args(self):
        a = GlobArgs(pattern="*.py")
        assert a.pattern == "*.py"


class TestToolDefinitions:
    def test_TOOLS_has_eight(self):
        assert len(TOOLS) == 8

    def test_TOOL_HANDLERS_has_eight(self):
        assert len(TOOL_HANDLERS) == 8

    def test_TOOL_HANDLERS_keys(self):
        expected = {"bash", "read_file", "write_file", "edit_file", "glob", "todo_write", "task", "load_skill"}
        assert set(TOOL_HANDLERS) == expected

    def test_handler_entries_are_pairs(self):
        for name, (model, handler) in TOOL_HANDLERS.items():
            assert hasattr(model, "model_validate_json"), f"{name} model missing validate_json"
            assert callable(handler), f"{name} handler not callable"
