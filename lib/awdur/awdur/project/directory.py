from __future__ import annotations

import pathlib
import subprocess
import tempfile
import typing

from .fossil import FossilExporter

if typing.TYPE_CHECKING:
    from . import Project


class DirectoryExporter:
    """Export a project to files in a directory."""

    def export(self, project: Project, output: pathlib.Path):
        """Export the project to the given location."""

        # For now, just shove the fossil project into a temp directory, but it probably
        # makes sense to do something smarter at some point.
        with tempfile.TemporaryDirectory() as tmp:
            repo = pathlib.Path(tmp, f"{project.name}.fossil")

            fossil = FossilExporter()
            fossil.export(project, repo)

            ret = subprocess.run(
                ["fossil", "open", str(repo), "--workdir", str(output)]
            )
