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
        existing_files: Literal["keep", "force", "overwrite"] | None = None,
    ):
        self.logger = logger or logging.getLogger(__name__)
        self.existing_files = existing_files

    def export(self, project: str, manager: ProjectManager, output: pathlib.Path):
        """Export the project to the given location."""

        if (rid := manager.get_project_version(project)) is None:
            self.logger.debug(
                "Project %r is not defined or has not been rendered", project
            )
            return

        if (blob := manager.get_blob(rid=rid)) is None:
            self.logger.debug(
                "Project %r is not defined or has not been rendered", project
            )
            return

        # Check for existing checkouts.
        if (fslckout := output / ".fslckout").exists():
            # For now, we just delete the existing checkout and move on. At some point
            # however, it will be nice to see if we can do something more interesting!
            fslckout.unlink()

        cmd: list[str] = [
            "fossil",
            "open",
            str(manager.dbpath),
            blob.uuid,
            "--workdir",
            str(output),
        ]
        input_ = None

        match self.existing_files:
            case "keep":
                cmd.append("--keep")
            case "force":
                cmd.append("--force")
            case "overwrite":
                cmd.append("--force")

                # Even with the --force flag, fossil takes the conservative option and
                # if existing files differ with the incoming changes it will ask if we
                # want to overwrite the file or not.
                #
                # So that the user doesn't have to mash 'y' over and over again, this
                # mode sends 'a\n' as input to select the always overwrite option.
                input_ = b"a\n"

            case _:
                pass  # error if existing files

        self.logger.info("Running: %s", " ".join(cmd))
        _ = subprocess.run(cmd, input=input_)
