"""Tests for pendula.skills module."""

from pathlib import Path

import pytest

from pendula.skills import (
    SKILL_REGISTRY,
    SYSTEM,
    _parse_frontmatter,
    list_skills,
    load_skill,
)


class TestParseFrontmatter:
    def test_no_frontmatter_returns_raw_body(self):
        meta, body = _parse_frontmatter("# hello\\nworld")
        assert meta == {}
        assert body == "# hello\\nworld"

    def test_with_frontmatter(self):
        raw = "---\nname: test\ndescription: A test skill\n---\n# Full content"
        meta, body = _parse_frontmatter(raw)
        assert meta["name"] == "test"
        assert meta["description"] == "A test skill"
        assert body == "# Full content"

    def test_frontmatter_without_name_uses_default(self):
        raw = "---\ndescription: desc only\n---\n# content"
        meta, body = _parse_frontmatter(raw)
        assert "name" not in meta
        assert meta["description"] == "desc only"


class TestListSkills:
    def test_returns_no_skills_when_registry_empty(self):
        result = list_skills()
        assert "(no skills loaded)" in result

    def test_returns_catalog_when_skills_loaded(self):
        SKILL_REGISTRY["test"] = {
            "name": "test",
            "description": "A test skill",
            "content": "# Test",
        }
        result = list_skills()
        assert "test" in result
        assert "A test skill" in result


class TestLoadSkill:
    def test_returns_content_for_known_skill(self):
        SKILL_REGISTRY["test"] = {
            "name": "test",
            "description": "A test skill",
            "content": "# Full content\\ninstructions",
        }
        result = load_skill("test")
        assert "# Full content" in result
        assert "instructions" in result

    def test_returns_error_for_unknown_skill(self):
        result = load_skill("nonexistent")
        assert "not found" in result


def test_SYSTEM_includes_skills_reference():
    """The enriched system prompt should mention load_skill."""
    assert "load_skill" in SYSTEM
