from __future__ import annotations

import pathlib

from docutils import io
from docutils.core import Publisher


def render(source: pathlib.Path):
    """Render sources to produce a documentation artifact.

    Parameters
    ----------
    source
       The source file to build.
    """
    reader = "standalone"
    parser = "restructuredtext"
    writer = "html5"

    publisher = Publisher(
        reader,
        parser,
        writer,
        settings=None,
        source_class=io.FileInput,
        destination_class=io.FileOutput,
    )
    publisher.process_programmatic_settings(None, {}, None)

    publisher.set_source(source_path=source)
    publisher.set_destination(destination_path=source.with_suffix(".html"))

    _output = publisher.publish(enable_exit_status=False)

    document = publisher.document
    if document.reporter.max_level >= 3:
        return 1
