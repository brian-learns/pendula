"""Reusable REPL loop for the Pendula coding agent.

Can be called from ``cli.py``, ``__main__.py``, or test code without
parsing CLI arguments.
"""

from .agent import agent_loop
from .hooks import trigger_hooks


def run_repl() -> None:
    """Read-eval-print loop: user queries → agent_loop → display.

    Exits on ``q``, ``exit``, ``<EOF>``, or ``<Ctrl-C>``.
    The ``UserPromptSubmit`` hook fires before each query reaches the LLM.
    """
    print("s04: Hooks — extension logic on hooks, loop stays clean")
    print("输入问题,回车发送。输入 q 退出。\n")

    history: list[dict[str, str]] = []
    while True:
        try:
            query = input("\033[36ms04 >> \033[0m")
        except (EOFError, KeyboardInterrupt):
            break
        if query.strip().lower() in ("q", "exit", ""):
            break
        trigger_hooks("UserPromptSubmit", query)
        history.append({"role": "user", "content": query})
        agent_loop(history)
        last_msg = history[-1]
        if last_msg["role"] == "assistant" and last_msg["content"]:
            print(last_msg["content"])
        print()
