# pendula

A lightweight Python coding agent that uses OpenAI function-calling (tool use) to execute shell commands, read/write/edit files, and glob within a workspace directory.

Based on [Learn Claude Code -- Harness Engineering for Real Agents](https://github.com/shareAI-lab/learn-claude-code) thanks [shareAI-lab](https://huggingface.co/shareAI)

Just basically me learning to vibe code with [ds4-agent](https://github.com/antirez/ds4/) \*.  

\* I've got my own [`SearchXNG` branch](https://github.com/brian-learns/ds4/tree/SearXNG)

## Main code
[`src/pendula`](src/pendula) has the agent files.


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

## Refactoring note
I should have made a commit to demonstrait the initial state.  I started with `uv init --package pendula` and I took a version of `s02_tool_use.py` and put in it `src/pendula` and had `__main__.py` basically just import `s02_tool_use`.  I forget the exact way I got in hooked into main but I got it working in the fresh uv init.  Then I asked the ai in google search for an aggressive `make test` that does a lot of static analysis.  It had a lot of errors.  I asked ds4-agent to fix all the errors in `make test`.  It realized on it's own that there were no real tests and created a bunch, and then worked till they all passed.  Once they passed, I asked it to refactor from one long `s02_tool_use.py` into multiple files.  After that, I didn the initial commit.  Next time I should commit *before* adding the tests and the refactor.

I know some people like one long file for this type of stuff, but I understand things better with more short files, and ds4-agent seems better at editing shorter files.
