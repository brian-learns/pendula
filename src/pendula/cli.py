"""CLI entry point for Pendula — parses args then delegates to ``run_repl()``."""

import argparse

from .logging import configure_logging
from .repl import run_repl


def main() -> None:
    """Parse CLI args, configure logging, then start the REPL."""
    parser = argparse.ArgumentParser(description="Pendula coding agent REPL")
    parser.add_argument(
        "--loglevel",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Set the tracing/logging level (default: INFO).",
    )
    args = parser.parse_args()
    configure_logging(level=args.loglevel)
    run_repl()
