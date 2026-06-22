# as_needed.md — Running Decision Log

Questions answered, decisions made, and why. Append-only.
Helps avoid re-asking the same things across sessions.

---

## 2026-06

- **Logging framework:** Use `structlog`. Tracing → stderr, normal logs → stdout.
  `--loglevel LEVEL` flag (DEBUG/INFO/WARNING/ERROR).
- **tools.py refactor:** Split models into `models.py`. Use `@tool` decorator to
  eliminate boilerplate. (Option B + Option C together.)
- **models.py:** Separate file — Pydantic models can be reused outside tools.
- **max_tokens:** Default 8000, configurable via `MAX_TOKENS` env var, stored in
  `config.py`.
- **OpenAI client:** Lazy-loaded via `get_client()` instead of eager import.
- **Tests:** `conftest.py` with `monkeypatch` for env isolation.
- **CLI REPL:** Deferred — `cli_issue.md` documents the problem.
- **s02.py:** Removed entirely (not just emptied).
- **Branch strategy:** One branch per lesson going forward (s03–s20).
- **AI context files:** `.ai/` directory with `prompts/`, `reports/`, `manuals/`, `other_files.txt`, `as_needed.md`.
