# pendula

A lightweight Python coding agent that uses OpenAI function-calling (tool use) to execute shell commands, read/write/edit files, and glob within a workspace directory.

## Quick start

```bash
# Install dependencies
uv sync

# Copy and edit the environment file
cp env.example .env
# Set DEFAULT_MODEL to your OpenAI-compatible model

# Run the REPL
uv run pendula
```

## Commands

| `make` target | What it does |
|---|---|
| `make check` | Static analysis: ruff, bandit, vulture, refurb |
| `make test`  | `check` + pytest |
| `make clean` | Wipe cache files |

## License

MIT — see LICENSE.
