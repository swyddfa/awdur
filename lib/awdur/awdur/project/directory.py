from __future__ import annotations

import logging
import pathlib
import subprocess
import tempfile
import typing

from .fossil import FossilExporter

if typing.TYPE_CHECKING:
    from typing import Literal

    from . import Project


class DirectoryExporter:
    """Export a project to files in a directory."""

    def __init__(
        self,
        logger: logging.Logger | None = None,
        existing_files: Literal["keep", "force"] | None = None,
    ):
        self.logger = logger or logging.getLogger(__name__)
        self.existing_files = existing_files

    def export(self, project: Project, output: pathlib.Path):
        """Export the project to the given location."""

        # For now, just shove the fossil project into a temp directory, but it probably
        # makes sense to do something smarter at some point.
        with tempfile.TemporaryDirectory() as tmp:
            repo = pathlib.Path(tmp, f"{project.name}.fossil")

            fossil = FossilExporter(logger=self.logger)
            fossil.export(project, repo)

            cmd = ["fossil", "open", str(repo), "--workdir", str(output)]
            match self.existing_files:
                case "keep":
                    cmd.extend(["--keep"])
                case "force":
                    cmd.append("--force")
                case _:
                    pass  # error if existing files

            result = subprocess.run(
                cmd,
                capture_output=True,
            )
            if result.returncode == 0:
                self.logger.info(result.stdout.decode("utf8"))
            else:
                self.logger.error(
                    "Unable to open repository\n%s", result.stderr.decode("utf8")
                )
                raise RuntimeError(
                    f"Fossil process exited with returncode: {result.returncode}"
                )
