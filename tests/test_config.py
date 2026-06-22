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


def test_max_tokens_default():
    """MAX_TOKENS should default to 8000."""
    assert config.MAX_TOKENS == 8000


def test_get_client():
    """get_client() should return an openai.OpenAI instance."""
    from openai import OpenAI
    assert isinstance(config.get_client(), OpenAI)


def test_get_client_is_singleton():
    """Repeated calls to get_client() should return the same object."""
    c1 = config.get_client()
    c2 = config.get_client()
    assert c1 is c2
