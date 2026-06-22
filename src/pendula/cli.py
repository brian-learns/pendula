"""CLI entry point for Pendula — REPL loop with configurable log level."""

import argparse

from .agent import agent_loop
from .logging import configure_logging


def main() -> None:
    """REPL entry point: parse CLI args, configure logging, run agent loop."""
    parser = argparse.ArgumentParser(description="Pendula coding agent REPL")
    parser.add_argument(
        "--loglevel",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Set the tracing/logging level (default: INFO).",
    )
    args = parser.parse_args()
    configure_logging(level=args.loglevel)

    print("s02: Tool Use — typed dispatch via Pydantic models")
    print("输入问题,回车发送。输入 q 退出。\n")

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
