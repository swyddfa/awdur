from __future__ import annotations

import hashlib
import json
import logging
import pathlib
import typing

import platformdirs
from docutils import io
from docutils import nodes
from docutils.core import Publisher
from docutils.parsers import get_parser_class
from docutils.readers import get_reader_class

from awdur.project import DirectoryExporter
from awdur.project import FossilExporter
from awdur.project import ProjectManager
from awdur.writers import SourceCodeWriter

if typing.TYPE_CHECKING:
    import argparse
    from typing import Literal


EXPORTERS = {
    "directory": DirectoryExporter,
    "fossil": FossilExporter,
}


class RstParser(get_parser_class("restructuredtext")):
    """Our version of the restructuredtext parser to use."""

    @typing.override
    def setup_parse(self, inputstring: str, document: nodes.document) -> None:
        # Pass the raw source to the document
        document.rawsource = inputstring
        return super().setup_parse(inputstring, document)


def extract(
    source: pathlib.Path,
    *,
    logger: logging.Logger | None = None,
    output: pathlib.Path | None = None,
    format: Literal["directory", "fossil"] = "directory",
    project_name: str = "default",
):
    """Extract source code from documentation sources.

    Parameters
    ----------
    source
       The source file to extract code from

    logger
       The logging instance to use.

    output
       The location to write to

    format
       The format to export the project to.

    project_name
       The project name to extract
    """
    reader_cls = get_reader_class("standalone")
    parser_cls = RstParser
    writer = SourceCodeWriter()

    publisher = Publisher(
        reader=reader_cls(),
        parser=parser_cls(),
        writer=writer,
        settings=None,
        source_class=io.FileInput,
    )

    manager = ProjectManager(
        get_cache_dir(source), default_name=source.stem, logger=logger
    )
    publisher.process_programmatic_settings(
        settings_spec=None,
        settings_overrides={"awdur_project_manager": manager},
        config_section=None,
    )

    publisher.set_source(source_path=str(source))

    _output = publisher.publish(enable_exit_status=False)
    document = publisher.document
    if document.reporter.max_level >= 3:
        return 1

    if project_name not in manager:
        raise ValueError(f"Project {project_name!r} is not defined")

    if output is None:
        # Use the project name if it's not the default one
        if project_name != "default":
            output = source.with_name(project_name)
        else:
            output = source.with_suffix("")

        if output == source:
            raise ValueError("Please provide a destination")

    project = manager[project_name]
    exporter = EXPORTERS[format](logger=logger)
    exporter.export(project, output)


def register_extract(subcommands: argparse._SubParsersAction):
    extract_cmd = subcommands.add_parser("extract")
    extract_cmd.set_defaults(run=extract)
    _ = extract_cmd.add_argument(
        "source", type=pathlib.Path, help="the source file to extract code from"
    )
    _ = extract_cmd.add_argument(
        "-p",
        "--project",
        dest="project_name",
        default="default",
        help="the code project to extract",
    )
    _ = extract_cmd.add_argument(
        "-f",
        "--format",
        choices=("directory", "fossil"),
        default="directory",
        help="the format to export the project in",
    )
    _ = extract_cmd.add_argument(
        "-o", "--output", type=pathlib.Path, help="the location to write to"
    )


def get_cache_dir(source: pathlib.Path):
    """Return the cache dir corresponding with this path."""

    cache = platformdirs.user_data_dir("awdur", appauthor="swyddfa", ensure_exists=True)
    index_json = pathlib.Path(cache, "index.json")

    if not index_json.exists():
        index = {}
    else:
        index = json.loads(index_json.read_bytes())

    uri = source.resolve().as_uri()
    if uri in index:
        return pathlib.Path(index[uri])

    hash = hashlib.md5(uri.encode())
    cache_dir = pathlib.Path(cache, hash.hexdigest())
    cache_dir.mkdir(parents=True)

    index[uri] = str(cache_dir)
    _ = index_json.write_text(json.dumps(index, indent=2))

    return cache_dir
