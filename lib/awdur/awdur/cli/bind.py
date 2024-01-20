from __future__ import annotations

import pathlib
import sys

from docutils.core import publish_file

from ._core import command


@command
def bind(source: pathlib.Path):
    """Produce documentation

    Parameters
    ----------
    source
       The source file to build.
    """
    publish_file(
        source_path=str(source),
        destination_path="out.html",  # sys.stdout,
        writer_name="html5",
    )
