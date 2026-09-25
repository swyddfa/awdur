from __future__ import annotations

import argparse
import bdb
import dataclasses
import inspect
import logging
import pathlib
import sys
import typing

import platformdirs
from docutils.parsers.rst import directives
from docutils.parsers.rst.directives.body import CodeBlock

from awdur.directives import ProjectTreeDirective
from awdur.directives import define_codeblock
from awdur.directives import define_template

from .extract import register_extract
from .render import render

if typing.TYPE_CHECKING:
    from collections.abc import Callable
    from collections.abc import Sequence
    from typing import Any
    from typing import TypeVar

    T = TypeVar("T")


@dataclasses.dataclass
class Context:
    """A place to store general utility values."""

    logger: logging.Logger
    """The logger instance to use."""

    data_dir: pathlib.Path
    """The path at which to store persistent data."""

    @classmethod
    def fromargs(cls, args: dict[str, Any]):
        if (data_dir := args.get("data_dir")) is None:
            data_dir = pathlib.Path(
                platformdirs.user_data_dir(
                    "awdur", appauthor="swyddfa", ensure_exists=True
                )
            )
        elif not data_dir.exists():
            data_dir.mkdir(parents=True)

        return cls(logger=setup_logging(args.get("verbosity", 0)), data_dir=data_dir)


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
    directives.register_directive("awdur:project-tree", ProjectTreeDirective)
    directives.register_directive("awdur:template", template)


def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Literate programming tools built on docutils."
    )
    _ = parser.add_argument("--debug", action="store_true", help="enable debug mode")

    _ = parser.add_argument(
        "-v",
        action="count",
        dest="verbosity",
        default=0,
        help="increase logging verbosity",
    )

    _ = parser.add_argument(
        "--data-dir",
        default=None,
        type=pathlib.Path,
        help="override the directory used to store persistent data",
    )

    subcommands = parser.add_subparsers(title="commands")
    register_extract(subcommands)

    render_cmd = subcommands.add_parser("render")
    render_cmd.set_defaults(run=render)
    _ = render_cmd.add_argument(
        "source", type=pathlib.Path, help="the source file to render"
    )
    _ = render_cmd.add_argument(
        "-o", "--output", type=pathlib.Path, help="the location to write to"
    )

    return parser


LOG_LEVELS = [logging.INFO, logging.DEBUG]
LOG_FORMATS = ["[%(name)s]: %(message)s"]


def setup_logging(verbosity: int) -> logging.Logger:
    """Configure logging for the cli."""
    log_level = LOG_LEVELS[min(verbosity, len(LOG_LEVELS) - 1)]
    log_fmt = LOG_FORMATS[min(verbosity, len(LOG_FORMATS) - 1)]

    logger = logging.getLogger("awdur")
    logger.setLevel(log_level)

    handler = logging.StreamHandler()
    handler.setLevel(log_level)
    handler.setFormatter(logging.Formatter(log_fmt))

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

    arguments["context"] = context = Context.fromargs(arguments)

    register_directives()

    try:
        sys.exit(call(command, arguments))
    except bdb.BdbQuit:
        # Don't debug exiting from the debugger.
        pass
    except Exception as exc:
        context.logger.error("%s", exc)

        if arguments.get("debug", False):
            import pdb

            pdb.post_mortem()
