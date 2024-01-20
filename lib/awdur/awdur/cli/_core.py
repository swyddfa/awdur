from __future__ import annotations

import argparse
import inspect
import logging
import typing

if typing.TYPE_CHECKING:
    from typing import Any
    from typing import Callable
    from typing import Dict
    from typing import Optional
    from typing import Sequence


_COMMANDS: Dict[str, Callable] = {}
logger = logging.getLogger("awdur")


def command(fn: Optional[Callable] = None):
    """Register a cli command."""

    def register(f):
        _COMMANDS[f.__name__] = f

    if fn is not None:
        register(fn)
        return fn

    return register


def call(fn: Callable, args: Dict[str, Any]):
    """Invoke the given function, taking relevant inputs from ``args``."""

    arguments = inspect.signature(fn).parameters.keys()
    kwargs = {}

    for name in arguments:
        if name not in args:
            raise RuntimeError(f"Missing required argument: {name!r}")

        kwargs[name] = args[name]

    return fn(**kwargs)


def get_parser(commands: Dict[str, Callable]) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Literate programming tools built on docutils."
    )

    subcommands = parser.add_subparsers(title="commands")

    for name, command in commands.items():
        doc = inspect.getdoc(command)
        # TODO: Extract short 'help' text from `doc`
        cmd = subcommands.add_parser(name, description=doc)
        cmd.set_defaults(run=command)

        for arg_name, type_ in typing.get_type_hints(command).items():
            # TODO: Extract parameter help from `doc`
            cmd.add_argument(arg_name, type=type_)

    return parser


def setup_logging():
    """Configure logging for the cli."""
    logging.basicConfig(format="%(levelname)s: %(message)s")


def main(argv: Optional[Sequence[str]] = None):
    cli = get_parser(_COMMANDS)
    args = cli.parse_args(argv)

    if not hasattr(args, "run"):
        cli.print_help()
        return 0

    arguments = vars(args)
    command = arguments.pop("run")

    try:
        call(setup_logging, arguments)
        call(command, arguments)
    except Exception as exc:
        logger.error("%s", exc)
