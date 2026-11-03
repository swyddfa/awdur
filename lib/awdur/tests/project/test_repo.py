"""Tests covering broader repo management, such as the "rendering" of projects into
fossil manifests.
"""

from __future__ import annotations

import datetime as dt
import logging
import typing

import pytest

from awdur.project import RepoManager
from awdur.project.db import Artifact
from awdur.project.db import Manifest
from awdur.project.db import Tag

if typing.TYPE_CHECKING:
    import pathlib
    from typing import Callable

NOW = dt.datetime.fromtimestamp(0).astimezone(dt.timezone.utc)


@pytest.fixture()
def manager(tmp_path: pathlib.Path) -> RepoManager:
    return RepoManager(
        data_dir=tmp_path, username="username", logger=logging.getLogger("awdur")
    )


def test_hello_world(testdata: Callable[..., pathlib.Path], manager: RepoManager):
    """Given an awdur manifest representing a "Hello, World!" project, ensure we can
    render it into standard manifest for just that project."""
    HELLO_WORLD = testdata("hello-world.rst").read_text()

    builder = manager.start_update(comment="first manifest", date=NOW)
    src, _ = builder.add_src(HELLO_WORLD, "hello-world.rst")

    code = 'print("Hello, World!")\n'
    _ = builder.add_fragment(code, src.filename, "hello.py", "default")

    # Note: test_manifest.py should ensure that this has the structure we expect.
    blob = manager.commit_update()

    # Render the project.
    manager.render_project("default", blob)
    assert manager.stats.manifests == 2  # 1 awdur manifest + 1 project manifest.

    r1 = manager.get_project_version("default", revision="1")
    manifest = Manifest.fromblob(r1)

    with manager.dbcon() as db:
        hello_py = manifest.files["hello.py"]
        content = Artifact.find(db, uuid=hello_py.blob)
        assert content.text == code


def test_no_op_update(testdata: Callable[..., pathlib.Path], manager: RepoManager):
    """When no meaningful changes to a project have been made, ensure we don't
    duplicate the content in the repo."""
    HELLO_WORLD = testdata("hello-world.rst").read_text()

    builder = manager.start_update(comment="first manifest", date=NOW)
    src, _ = builder.add_src(HELLO_WORLD, "hello-world.rst")

    code = 'print("Hello, World!")\n'
    _ = builder.add_fragment(code, src.filename, "hello.py", "default")

    # Note: test_manifest.py should ensure that this has the structure we expect.
    blob = manager.commit_update()
    assert manager.stats.manifests == 1  # 1 awdur manifest

    # Render the project.
    manager.render_project("default", blob)
    assert manager.stats.manifests == 2  # 1 awdur manifest + 1 project manifest.

    r1 = manager.get_project_version("default", revision="1")
    manifest = Manifest.fromblob(r1)

    with manager.dbcon() as db:
        hello_py = manifest.files["hello.py"]
        content = Artifact.find(db, uuid=hello_py.blob)
        assert content.text == code

    source: Tag | None = None
    for t in manifest.tags:
        if t.name == "source":
            source = t

    assert source.value == blob.uuid

    # Make an update
    builder = manager.start_update(
        comment="next update", date=NOW + dt.timedelta(days=1)
    )

    src, _ = builder.add_src(
        HELLO_WORLD + "\nIn the future, we will make this program executable.",
        "hello-world.rst",
    )

    code = 'print("Hello, World!")\n'
    _ = builder.add_fragment(code, src.filename, "hello.py", "default")
    blob = manager.commit_update()
    assert manager.stats.manifests == 3  # 2 awdur manifests + 1 project manifest.

    # Render the project.
    manager.render_project("default", blob)
    assert manager.stats.manifests == 3  # no change.
    assert r1.uuid == manager.get_project_version("default", revision="1").uuid


def test_multiple_revisions(
    testdata: Callable[..., pathlib.Path], manager: RepoManager
):
    """Given an awdur manifest representing a project with multiple revisions, ensure we
    can render it into a series of standard manifests."""
    MULTIPLE_REVISIONS = testdata("multiple-revisions.rst").read_text()

    builder = manager.start_update(comment="first manifest", date=NOW)
    src, _ = builder.add_src(MULTIPLE_REVISIONS, "multiple-revisions.rst")

    code = 'print("Hello, World!")\n'
    _ = builder.add_fragment(code, src.filename, "hello.py", "default")

    fullcode = f"#!/usr/bin/env python\n{code}"
    _ = builder.add_fragment(
        fullcode, src.filename, "hello.py", "default", revision="2"
    )

    # Note: test_manifest.py should ensure that this has the structure we expect.
    blob = manager.commit_update()

    # Render the project.
    manager.render_project("default", blob)
    assert manager.stats.manifests == 3  # 1 awdur manifest + 2 project manifests.

    r1 = manager.get_project_version("default", revision="1")
    manifest_r1 = Manifest.fromblob(r1)

    with manager.dbcon() as db:
        hello_py = manifest_r1.files["hello.py"]
        content = Artifact.find(db, uuid=hello_py.blob)
        assert content.text == code

    source: Tag | None = None
    for t in manifest_r1.tags:
        if t.name == "source":
            source = t

    assert source.value == blob.uuid

    r2 = manager.get_project_version("default", revision="2")
    manifest_r2 = Manifest.fromblob(r2)

    # Manifest should link to the previous revision
    assert manifest_r2.previous == r1.uuid

    with manager.dbcon() as db:
        hello_py = manifest_r2.files["hello.py"]
        content = Artifact.find(db, uuid=hello_py.blob)
        assert content.text == fullcode

    source: Tag | None = None
    for t in manifest_r2.tags:
        if t.name == "source":
            source = t

    assert source.value == blob.uuid
