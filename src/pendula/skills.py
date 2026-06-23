"""Skill loading system for the Pendula coding agent.

Two-level design:
1. **Catalog** — injected into SYSTEM at startup (~100 tokens/skill)
2. **Content** — loaded on demand via ``load_skill`` tool (~2000 tokens/skill)

Skills live in ``skills/`` at the project root, one subdirectory per skill,
each containing a ``SKILL.md`` file with optional YAML frontmatter.
"""

from __future__ import annotations

from .config import WORKDIR, build_system

# ═══════════════════════════════════════════════════════════
#  Registry & scanning
# ═══════════════════════════════════════════════════════════

SKILLS_DIR = WORKDIR / "skills"

SKILL_REGISTRY: dict[str, dict] = {}


def _parse_frontmatter(raw: str) -> tuple[dict, str]:
    """Parse minimal YAML frontmatter (name / description) from *raw*.

    Returns (metadata, body) where metadata is a dict with at most
    ``name`` and ``description`` keys.
    """
    lines = raw.splitlines()
    meta: dict[str, str] = {}
    body_lines: list[str] = []

    if not lines or not lines[0].startswith("---"):
        return meta, raw

    idx = 1
    while idx < len(lines) and not lines[idx].startswith("---"):
        line = lines[idx]
        if ":" in line:
            key, _, val = line.partition(":")
            meta[key.strip()] = val.strip()
        idx += 1

    body_lines = lines[idx + 1 :] if idx < len(lines) else []
    return meta, "\n".join(body_lines).strip()


def _scan_skills() -> None:
    """Scan ``skills/`` directory and populate ``SKILL_REGISTRY``."""
    if not SKILLS_DIR.is_dir():
        return
    for d in sorted(SKILLS_DIR.iterdir()):
        if not d.is_dir():
            continue
        manifest = d / "SKILL.md"
        if not manifest.exists():
            continue
        raw = manifest.read_text(encoding="utf-8")
        meta, body = _parse_frontmatter(raw)
        name = meta.get("name", d.name)
        desc = meta.get("description", body.split("\n")[0].lstrip("#").strip())
        SKILL_REGISTRY[name] = {"name": name, "description": desc, "content": raw}


_scan_skills()


def list_skills() -> str:
    """Generate a catalog string from the current registry."""
    if not SKILL_REGISTRY:
        return "(no skills loaded)"
    return "\n".join(
        f"- **{s['name']}**: {s['description']}" for s in SKILL_REGISTRY.values()
    )


# Build the enriched system prompt with the skill catalog
SYSTEM = build_system(list_skills())


# ═══════════════════════════════════════════════════════════
#  Tool handler
# ═══════════════════════════════════════════════════════════


def load_skill(name: str) -> str:
    """Return the full content of a skill by *name*.

    Looks up by registry key, not file path, preventing path traversal.
    """
    skill = SKILL_REGISTRY.get(name)
    if skill is None:
        return f"Skill not found: {name}"
    return skill["content"]
