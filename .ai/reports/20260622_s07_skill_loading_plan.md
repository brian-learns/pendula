# s07 Skill Loading — Implementation Plan

## Goal
Give the Agent a `load_skill` tool that loads skill content on demand. A skill catalog is injected into the SYSTEM prompt at startup (~100 tokens/skill), and full SKILL.md content is loaded only when the Agent calls the tool (~2000 tokens/skill).

---

## Files to change

| File | Change | Reason |
|------|--------|--------|
| `src/pendula/skills.py` | New module: scan skills/, SKILL_REGISTRY, list_skills(), load_skill() | Skill loading logic |
| `src/pendula/config.py` | Add `build_system(catalog)` function, keep `SYSTEM` as base | System prompt needs catalog |
| `src/pendula/tools.py` | Register `load_skill` tool, import `load_skill` from skills | Tool handler registration |
| `src/pendula/agent.py` | Change `from .config import SYSTEM` → `from .skills import SYSTEM` | Agent uses enriched SYSTEM |
| `tests/test_skills.py` | New test file | Coverage |
| `tests/test_tools.py` | Update tool count (8) and keys | Existing tests |
| `HACKERS.md` | Add `skills.py` to module table | Documentation |
| `SPEC.md` | Mark s07 as ✅, update dependency/module tables | Spec accuracy |

---

## Design decisions & tradeoffs

### 1. Where does SYSTEM live after s07?
The enriched SYSTEM (with skill catalog) is built by `skills.py` at import time. `agent.py` changes its import from `config.py` to `skills.py`.

**Why not keep SYSTEM in config.py?** `config.py` is a leaf module — it can't import from `skills.py` without creating a circular dependency. Moving the enriched SYSTEM to `skills.py` avoids this.

### 2. skills/ directory location
The README shows `skills/` at project root. We'll use `WORKDIR / "skills"`. If the directory doesn't exist, scanning is a no-op.

### 3. SKILL_REGISTRY prevents path traversal
`load_skill` looks up by registry key, not file path. This eliminates path traversal risk — the Agent can't load arbitrary files via the skill tool.

### 4. SKILL.md format
Minimal YAML frontmatter with `name` and `description`. If frontmatter is missing, the skill name defaults to directory name and description to the first line of content.

### 5. No circular imports
Dependency flow: `config.py` (leaf) → `skills.py` (imports build_system from config) → `tools.py` (imports load_skill from skills). Clean DAG.

---

## Dependency flow (updated)

```
config.py  (leaf)
    ↓
models.py  (depends on pydantic only)
    ↓
tools.py   (depends on .config, .models, .logging)
    ↓
hooks.py   (depends on .config)
    ↓
skills.py  (depends on .config)
    ↓
subagent.py (depends on .config, .hooks, .tools via deferred import)
    ↓
agent.py   (depends on .config, .hooks, .tools, .logging, .skills)
    ↓
repl.py    (depends on .agent, .hooks)
    ↓
cli.py     (depends on .repl, .logging)
```

---

## Implementation order

1. Add `build_system(catalog)` to `config.py`, keep base `SYSTEM`
2. Create `skills.py` — scan skills/, SKILL_REGISTRY, list_skills(), load_skill()
3. Register `load_skill` tool in `tools.py`
4. Update `agent.py` import: `from .skills import SYSTEM`
5. Add tests (`test_skills.py`, update `test_tools.py`)
6. Update docs (`HACKERS.md`, `SPEC.md`)
7. `make test` — all pass
8. Commit, user tests

---

## Questions for the user

None — plan is self-contained.
