# CLI Refactor — Open Issue

## Problem

`cli.py` duplicates the REPL loop logic that originally lived in `s02.py`'s `__name__ == "__main__"` block.  
Now that `s02.py` is gone, the REPL is stranded in `cli.py` with no shared abstraction.

## Current code

```python
# cli.py  — 37 lines, REPL + argument parsing mixed together

def main() -> None:
    """REPL entry point: parse CLI args, configure logging, run agent loop."""
    parser = argparse.ArgumentParser(...)
    ...
    history: list[dict[str, str]] = []
    while True:
        try:
            query = input(...)
        except (EOFError, KeyboardInterrupt):
            break
        if query.strip().lower() in ("q", "exit", ""):
            break
        history.append({"role": "user", "content": query})
        agent_loop(history)
        last_msg = history[-1]
        if last_msg["role"] == "assistant" and last_msg["content"]:
            print(last_msg["content"])
        print()
```

## Proposed direction

Extract the REPL loop into a reusable function so that:

1. **`cli.py`** calls it from `main()` after parsing args.
2. **`__main__.py`** can call it directly (currently `__main__.py` just calls `cli.main()`).
3. **Tests** can exercise the REPL loop without parsing CLI args.

### Sketch

```python
# shared location: repl.py or inside cli.py as a separate function

def run_repl() -> None:
    """Read-eval-print loop: user queries → agent_loop → display."""
    history: list[dict[str, str]] = []
    while True:
        try:
            query = input("\033[36ms02 >> \033[0m")
        except (EOFError, KeyboardInterrupt):
            break
        if query.strip().lower() in ("q", "exit", ""):
            break
        history.append({"role": "user", "content": query})
        agent_loop(history)
        last_msg = history[-1]
        if last_msg["role"] == "assistant" and last_msg["content"]:
            print(last_msg["content"])
        print()
```

## Trade-offs

| Approach | Pros | Cons |
|----------|------|------|
| Keep REPL in `cli.py` | Simple, works today | Hard to test, can't reuse from other entry points |
| Extract to `repl.py` | Testable, reusable | Another module; `__main__.py` import changes |
| Extract inline in `cli.py` | No new files, minimal diff | Still coupled to argparse |

## Status

**✅ Resolved** — `run_repl()` extracted to `src/pendula/repl.py`.

Changes made:
1. Created `src/pendula/repl.py` with `run_repl()` — the REPL loop as a standalone function
2. `cli.py` now parses args then calls `run_repl()`
3. `__main__.py` stays unchanged (calls `cli.main()` → `run_repl()`)
4. Added `tests/test_repl.py` with 6 tests exercising the loop
