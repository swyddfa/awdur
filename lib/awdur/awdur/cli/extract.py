from __future__ import annotations

import pathlib

from docutils import io
from docutils.core import Publisher
from docutils.parsers import get_parser_class
from docutils.readers import get_reader_class

from awdur.project import Project
from awdur.writers import SourceCodeWriter


def extract(source: pathlib.Path, *, output: pathlib.Path | None = None):
    """Extract source code from documentation sources.

    Parameters
    ----------
    source
       The source file to extract code from

    output
       The location to write to
    """
    reader_cls = get_reader_class("standalone")
    parser_cls = get_parser_class("restructuredtext")
    writer = SourceCodeWriter()

    publisher = Publisher(
        reader=reader_cls(),
        parser=parser_cls(),
        writer=writer,
        settings=None,
        source_class=io.FileInput,
    )

    project = Project(default_name=source.stem)
    publisher.process_programmatic_settings(
        settings_spec=None,
        settings_overrides={"awdur_project": project},
        config_section=None,
    )

    publisher.set_source(source_path=str(source))

    _output = publisher.publish(enable_exit_status=False)
    document = publisher.document
    if document.reporter.max_level >= 3:
        return 1

    if output is None:
        output = source.with_suffix("")
        if output == source:
            raise ValueError("Please provide a destination")

    project.export(output)
