from __future__ import annotations

import logging
import pathlib
import subprocess
import typing

if typing.TYPE_CHECKING:
    from typing import Literal
    from typing import Protocol

    from . import ProjectManager

    class ProjectExporter(Protocol):
        """Interface for exporters."""

        def __init__(self, logger: logging.Logger | None = None): ...

        def export(
            self, project: str, manager: ProjectManager, output: pathlib.Path
        ): ...


class DirectoryExporter:
    """Export a project to files in a directory."""

    def __init__(
        self,
        logger: logging.Logger | None = None,
        existing_files: Literal["keep", "force"] | None = None,
    ):
        self.logger = (logger or logging.getLogger(__name__)).getChild(
            self.__class__.__name__
        )
        self.existing_files = existing_files

    def export(self, project: str, manager: ProjectManager, output: pathlib.Path):
        """Export the project to the given location."""

        uuid = manager.get_project_version(project)
        cmd = ["fossil", "open", str(manager.dbpath), uuid, "--workdir", str(output)]
        match self.existing_files:
            case "keep":
                cmd.extend(["--keep"])
            case "force":
                cmd.append("--force")
            case _:
                pass  # error if existing files

        _ = subprocess.run(cmd)
