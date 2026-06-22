"""Tests for pendula.config module."""

import os
from pathlib import Path

from pendula import config


def test_workdir_is_cwd():
    """WORKDIR should be the current working directory."""
    assert config.WORKDIR == Path.cwd()


def test_model_from_env():
    """MODEL should come from the DEFAULT_MODEL environment variable."""
    assert config.MODEL == os.environ["DEFAULT_MODEL"]


def test_system_prompt():
    """SYSTEM should mention the workspace path."""
    assert str(config.WORKDIR) in config.SYSTEM


def test_client_is_openai():
    """client should be an openai.OpenAI instance."""
    from openai import OpenAI
    assert isinstance(config.client, OpenAI)
