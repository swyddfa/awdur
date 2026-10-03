from __future__ import annotations

import hashlib
import json
import pathlib
import typing

from docutils import io
from docutils import nodes
from docutils.core import Publisher
from docutils.parsers import get_parser_class
from docutils.readers import get_reader_class

from awdur.project import DirectoryExporter
from awdur.project import ProjectManager
from awdur.writers import SourceCodeWriter

if typing.TYPE_CHECKING:
    import argparse
    from typing import Literal

    from awdur.project.export import ProjectExporter

    from ._core import Context

EXPORTERS: dict[str, type[ProjectExporter]] = {
    "directory": DirectoryExporter,
}


class RstParser(get_parser_class("restructuredtext")):
    """Our version of the restructuredtext parser to use."""

    def setup_parse(self, inputstring: str, document: nodes.document) -> None:
        # Pass the raw source to the document
        document.rawsource = inputstring
        return super().setup_parse(inputstring, document)


def extract(
    context: Context,
    source: pathlib.Path,
    *,
    output: pathlib.Path | None = None,
    format: Literal["directory"] = "directory",
    project_name: str = "default",
):
    """Extract source code from documentation sources.

    Parameters
    ----------
    context
       The context object

    source
       The source file to extract code from

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
        data_dir=get_project_dir(context.data_dir, source),
        logger=context.logger,
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

    if output is None:
        # Use the project name if it's not the default one
        if project_name != "default":
            output = source.with_name(project_name)
        else:
            output = source.with_suffix("")

        if output == source:
            raise ValueError("Please provide a destination")

    exporter = EXPORTERS[format]
    manager.export(project_name, exporter(logger=context.logger), output)


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
        choices=("directory"),
        default="directory",
        help="the format to export the project in",
    )
    _ = extract_cmd.add_argument(
        "-o", "--output", type=pathlib.Path, help="the location to write to"
    )


def get_project_dir(data_dir: pathlib.Path, source: pathlib.Path):
    """Return the project data dir corresponding with this path."""

    index_json = pathlib.Path(data_dir, "index.json")

    if not index_json.exists():
        index = {}
    else:
        index = json.loads(index_json.read_bytes())

    uri = source.resolve().as_uri()
    if uri in index:
        return pathlib.Path(index[uri])

    hash = hashlib.md5(uri.encode())
    cache_dir = pathlib.Path(data_dir, hash.hexdigest())
    cache_dir.mkdir(parents=True)

    index[uri] = str(cache_dir)
    _ = index_json.write_text(json.dumps(index, indent=2))

    return cache_dir
