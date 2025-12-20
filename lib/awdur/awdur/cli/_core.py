from __future__ import annotations

import argparse
import bdb
import inspect
import logging
import pathlib
import sys
import typing

from docutils.parsers.rst import directives
from docutils.parsers.rst.directives.body import CodeBlock

from awdur.directives import define_codeblock
from awdur.directives import define_template

from .extract import extract
from .render import render

if typing.TYPE_CHECKING:
    from collections.abc import Callable
    from collections.abc import Sequence
    from typing import Any
    from typing import TypeVar

    T = TypeVar("T")


def call(fn: Callable[..., T], args: dict[str, Any]) -> T:
    """Invoke the given function, taking relevant inputs from ``args``."""

    arguments = inspect.signature(fn).parameters.keys()
    kwargs = {}

    for name in arguments:
        if name not in args:
            raise RuntimeError(f"Missing required argument: {name!r}")

        kwargs[name] = args[name]

    return fn(**kwargs)


def register_directives():
    """Register our custom directives."""

    codeblock = define_codeblock(CodeBlock)
    template = define_template(CodeBlock)

    directives.register_directive("code", codeblock)
    directives.register_directive("awdur:template", template)


def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Literate programming tools built on docutils."
    )
    _ = parser.add_argument("--debug", action="store_true", help="enable debug mode")

    subcommands = parser.add_subparsers(title="commands")

    extract_cmd = subcommands.add_parser("extract")
    extract_cmd.set_defaults(run=extract)
    _ = extract_cmd.add_argument(
        "source", type=pathlib.Path, help="the source file to extract code from"
    )
    _ = extract_cmd.add_argument(
        "-o", "--output", type=pathlib.Path, help="the location to write to"
    )

    render_cmd = subcommands.add_parser("render")
    render_cmd.set_defaults(run=render)
    _ = render_cmd.add_argument(
        "source", type=pathlib.Path, help="the source file to render"
    )

    return parser


def setup_logging():
    """Configure logging for the cli."""
    logger = logging.getLogger("awdur")
    logger.setLevel(logging.DEBUG)

    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))

    logger.addHandler(handler)
    return logger


def main(argv: Sequence[str] | None = None):
    cli = get_parser()
    args = cli.parse_args(argv)

    if not hasattr(args, "run"):
        cli.print_help()
        return 0

    arguments = vars(args)
    command: Callable[..., Any] = arguments.pop("run")

    arguments["logger"] = logger = call(setup_logging, arguments)

    register_directives()

    try:
        sys.exit(call(command, arguments))
    except bdb.BdbQuit:
        # Don't debug exiting from the debugger.
        pass
    except Exception as exc:
        logger.error("%s", exc)

        if arguments.get("debug", False):
            import pdb

            pdb.post_mortem()
