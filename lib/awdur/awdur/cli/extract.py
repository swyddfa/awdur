from __future__ import annotations

import pathlib

from docutils.core import publish_parts

from awdur.project import Project
from awdur.writers import SourceCodeWriter

# Document parts that are not source code files.
EXCLUDED_PARTS = {"encoding", "whole", "errors", "version"}


def extract(source: pathlib.Path, *, output: pathlib.Path | None = None):
    """Extract source code from documentation sources.

    Parameters
    ----------
    source
       The source file to extract code from

    output
       The location to write to
    """

    project = Project(default_name=source.stem)
    _ = publish_parts(
        source=source.read_text(),
        source_path=str(source),
        writer=SourceCodeWriter(project),
    )

    if output is None:
        output = source.with_suffix("")
        if output == source:
            raise ValueError("Please provide a destination")

    project.export(output)
