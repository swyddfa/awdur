from __future__ import annotations

import pathlib

from docutils.core import publish_file

from ._core import command


@command
def render(source: pathlib.Path):
    """Render sources to produce a documentation artifact.

    Parameters
    ----------
    source
       The source file to build.
    """
    publish_file(
        source_path=str(source),
        destination_path=str(source.with_suffix(".html")),
        writer_name="html5",
    )
