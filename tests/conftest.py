"""Pytest fixtures for Pendula tests.

Ensures ``DEFAULT_MODEL`` is set so config modules load without error.
"""

import os

import pytest


@pytest.fixture(autouse=True)
def _ensure_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set ``DEFAULT_MODEL`` if not already present in the environment.

    Runs before every test so ``config.py`` module-level code can
    always read this variable.
    """
    if "DEFAULT_MODEL" not in os.environ:
        monkeypatch.setenv("DEFAULT_MODEL", "test-model")
