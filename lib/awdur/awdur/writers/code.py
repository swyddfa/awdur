from __future__ import annotations

import typing

from docutils.writers import Writer

from awdur.transforms import BuildProjectsTransform
from awdur.transforms import ResolveProjectMetadataTransform

if typing.TYPE_CHECKING:
    from docutils.transforms import Transform

    from awdur.project import Project


class SourceCodeWriter(Writer):
    """A writer for writing source code."""

    def get_transforms(self) -> list[type[Transform]]:
        return super().get_transforms() + [
            ResolveProjectMetadataTransform,
            BuildProjectsTransform,
        ]

    def translate(self) -> None:
        # Currently this writer doesn't actually do anything, but instead provides the necessary transforms.
        # See awdur.cli.extract for actually writing code to disk.
        pass
