from __future__ import annotations

import pathlib

from docutils import io
from docutils.core import Publisher
from docutils.parsers import get_parser_class
from docutils.readers import get_reader_class
from docutils.writers import get_writer_class


def render(source: pathlib.Path):
    """Render sources to produce a documentation artifact.

    Parameters
    ----------
    source
       The source file to build.
    """
    reader = get_reader_class("standalone")
    parser = get_parser_class("restructuredtext")
    writer = get_writer_class("html5")

    publisher = Publisher(
        reader(),
        parser(),
        writer(),
        settings=None,
        source_class=io.FileInput,
        destination_class=io.FileOutput,
    )
    publisher.process_programmatic_settings(None, {}, None)

    publisher.set_source(source_path=str(source))
    publisher.set_destination(destination_path=str(source.with_suffix(".html")))

    _output = publisher.publish(enable_exit_status=False)

    document = publisher.document
    if document.reporter.max_level >= 3:
        return 1
