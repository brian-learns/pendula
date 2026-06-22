# pendula

A lightweight Python coding agent that uses OpenAI function-calling (tool use) to execute shell commands, read/write/edit files, and glob within a workspace directory.

Based on [Learn Claude Code -- Harness Engineering for Real Agents](https://github.com/shareAI-lab/learn-claude-code) thanks [shareAI-lab](https://huggingface.co/shareAI)

I'm on step `s02` right now, I'm going to do a tag or branch for each chapter.

Just basically me learning to vibe code with [ds4-agent](https://github.com/antirez/ds4/) \*.  

\* I've got my own [`SearchXNG` branch](https://github.com/brian-learns/ds4/tree/SearXNG)


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

## Python

I'm also learning about `uv init --package` and modern python best practices.
