"""Tests covering the construction of fossil manifests representing awdur's internal
project state.

Note: test_db.py should cover the correct construction of a fossil manifest. These tests
are more about the correct representation of an awdur project so will just assume that
uuids and checksums are correct.
"""

from __future__ import annotations

import datetime as dt
import logging
import typing

import pytest

from awdur.project import RepoManager

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
    """Ensure we can construct a simple 'hello, world' manifest record correctly."""
    HELLO_WORLD = testdata("hello-world.rst").read_text()

    builder = manager.start_update(comment="first manifest", date=NOW)
    src, status = builder.add_src(HELLO_WORLD, "hello-world.rst")

    # Check the src was added as we expect.
    assert status == "created", "Source should be newly created"
    assert src.filename == "src/hello-world.rst"
    assert builder.get_artifact(src.blob).text == HELLO_WORLD

    code = 'print("Hello, World!")\n'
    fragment, status = builder.add_fragment(code, src.filename, "hello.py", "default")

    # Check that the fragment as added as we expect
    assert status == "created", "Fragment should be newly created"
    assert (
        fragment.filename
        == "project/default/file/hello.py/content/1/src-hello-world.rst:1"
    )
    assert builder.get_artifact(fragment.blob).text == code

    # Note: test_db.py should cover the correct construction of the manifest.
    # These tests are more about the correct representation of an awdur project's state
    # so we will just assume that uuids and checksums are correct.
    blob = manager.commit_update()
    assert blob.text == "\n".join(
        [
            r"C first\smanifest",
            "D 1970-01-01T00:00:00.000",
            f"F {fragment.filename} {fragment.blob} w",
            f"F {src.filename} {src.blob} w",
            f"R {builder.manifest.rchecksum}",
            "T *branch * trunk",
            "T *source * awdur",
            "T *sym-trunk *",
            "T +projects * default",
            "U username",
            f"Z {builder.manifest.zchecksum}",
            "",
        ]
    )

    # The db should contain the expected number of artifacts.
    assert manager.stats.artifacts == 3  # 2 unique blobs + 1 manifest
    assert manager.stats.other == 2
    assert manager.stats.manifests == 1


def test_abort_update(testdata: Callable[..., pathlib.Path], manager: RepoManager):
    """Ensure we can abort an update, with no changes to the db."""
    HELLO_WORLD = testdata("hello-world.rst").read_text()

    builder = manager.start_update(comment="first manifest", date=NOW)
    src, status = builder.add_src(HELLO_WORLD, "hello-world.rst")

    # Check the src was added as we expect.
    assert status == "created", "Source should be newly created"
    assert src.filename == "src/hello-world.rst"
    assert builder.get_artifact(src.blob).text == HELLO_WORLD

    code = 'print("Hello, World!")\n'
    fragment, status = builder.add_fragment(code, src.filename, "hello.py", "default")

    # Check that the fragment as added as we expect
    assert status == "created", "Fragment should be newly created"
    assert (
        fragment.filename
        == "project/default/file/hello.py/content/1/src-hello-world.rst:1"
    )
    assert builder.get_artifact(fragment.blob).text == code

    # Note: test_db.py should cover the correct construction of the manifest.
    # These tests are more about the correct representation of an awdur project's state
    # so we will just assume that uuids and checksums are correct.
    manager.abort_update()

    # The db should not contain anything we added above.
    assert manager.stats.artifacts == 0  # 2 unique blobs + 1 manifest
    assert manager.stats.other == 0
    assert manager.stats.manifests == 0


def test_no_op_update(testdata: Callable[..., pathlib.Path], manager: RepoManager):
    """Ensure we can detect when nothing has changed and not make an update."""
    HELLO_WORLD = testdata("hello-world.rst").read_text()

    builder = manager.start_update(comment="first manifest", date=NOW)
    src, status = builder.add_src(HELLO_WORLD, "hello-world.rst")

    # Check the src was added as we expect.
    assert status == "created", "Source should be newly created"
    assert src.filename == "src/hello-world.rst"
    assert builder.get_artifact(src.blob).text == HELLO_WORLD

    code = 'print("Hello, World!")\n'
    fragment, status = builder.add_fragment(code, src.filename, "hello.py", "default")

    # Check that the fragment as added as we expect
    assert status == "created", "Fragment should be newly created"
    assert (
        fragment.filename
        == "project/default/file/hello.py/content/1/src-hello-world.rst:1"
    )
    assert builder.get_artifact(fragment.blob).text == code

    # Note: test_db.py should cover the correct construction of the manifest.
    # These tests are more about the correct representation of an awdur project's state
    # so we will just assume that uuids and checksums are correct.
    blob = manager.commit_update()
    assert blob.text == "\n".join(
        [
            r"C first\smanifest",
            "D 1970-01-01T00:00:00.000",
            f"F {fragment.filename} {fragment.blob} w",
            f"F {src.filename} {src.blob} w",
            f"R {builder.manifest.rchecksum}",
            "T *branch * trunk",
            "T *source * awdur",
            "T *sym-trunk *",
            "T +projects * default",
            "U username",
            f"Z {builder.manifest.zchecksum}",
            "",
        ]
    )

    # The db should contain the expected number of artifacts.
    assert manager.stats.artifacts == 3  # 2 unique blobs + 1 manifest
    assert manager.stats.other == 2
    assert manager.stats.manifests == 1

    # Create an update
    manifest = manager.start_update(
        comment="next update", date=NOW + dt.timedelta(days=1)
    )

    # Add an identical source
    src, updated = manifest.add_src(HELLO_WORLD, filename="hello-world.rst")
    assert updated == "unchanged", "Source should be considered identical"

    result = manager.commit_update()
    assert result is None, "Update should be a no-op"

    # The db should contain the expected number of artifacts.
    assert manager.stats.artifacts == 3  # 2 unique blobs + 1 manifest
    assert manager.stats.other == 2
    assert manager.stats.manifests == 1


def test_simple_update(testdata: Callable[..., pathlib.Path], manager: RepoManager):
    """Ensure we can make updates."""
    HELLO_WORLD = testdata("hello-world.rst").read_text()

    builder = manager.start_update(comment="first manifest", date=NOW)
    src, status = builder.add_src(HELLO_WORLD, "hello-world.rst")

    # Check the src was added as we expect.
    assert status == "created", "Source should be newly created"
    assert src.filename == "src/hello-world.rst"
    assert builder.get_artifact(src.blob).text == HELLO_WORLD

    code = 'print("Hello, World!")\n'
    fragment, status = builder.add_fragment(code, src.filename, "hello.py", "default")

    # Check that the fragment as added as we expect
    assert status == "created", "Fragment should be newly created"
    assert (
        fragment.filename
        == "project/default/file/hello.py/content/1/src-hello-world.rst:1"
    )
    assert builder.get_artifact(fragment.blob).text == code

    # Note: test_db.py should cover the correct construction of the manifest.
    # These tests are more about the correct representation of an awdur project's state
    # so we will just assume that uuids and checksums are correct.
    root = manager.commit_update()
    assert root.text == "\n".join(
        [
            r"C first\smanifest",
            "D 1970-01-01T00:00:00.000",
            f"F {fragment.filename} {fragment.blob} w",
            f"F {src.filename} {src.blob} w",
            f"R {builder.manifest.rchecksum}",
            "T *branch * trunk",
            "T *source * awdur",
            "T *sym-trunk *",
            "T +projects * default",
            "U username",
            f"Z {builder.manifest.zchecksum}",
            "",
        ]
    )

    # The db should contain the expected number of artifacts.
    assert manager.stats.artifacts == 3  # 2 unique blobs + 1 manifest
    assert manager.stats.other == 2
    assert manager.stats.manifests == 1

    # Create an update
    builder = manager.start_update(
        comment="next update", date=NOW + dt.timedelta(days=1)
    )

    GOODBYE_WORLD = testdata("goodbye-world.rst").read_text()

    # Add an updated source
    src, updated = builder.add_src(GOODBYE_WORLD, filename="hello-world.rst")
    assert src.filename == "src/hello-world.rst"
    assert updated == "updated", "Source should be considered an update"
    assert builder.get_artifact(src.blob).text == GOODBYE_WORLD

    code = 'print("Goodbye, World!")\n'
    fragment, status = builder.add_fragment(code, src.filename, "hello.py", "default")

    # Check that the fragment as added as we expect
    assert status == "updated", "Fragment should be updated"
    assert (
        fragment.filename
        == "project/default/file/hello.py/content/1/src-hello-world.rst:1"
    )
    assert builder.get_artifact(fragment.blob).text == code

    blob = manager.commit_update()
    assert blob.text == "\n".join(
        [
            r"C next\supdate",
            "D 1970-01-02T00:00:00.000",
            f"F {fragment.filename} {fragment.blob} w",
            f"F {src.filename} {src.blob} w",
            f"P {root.uuid}",
            f"R {builder.manifest.rchecksum}",
            "T +projects * default",
            "U username",
            f"Z {builder.manifest.zchecksum}",
            "",
        ]
    )

    # The db should contain the expected number of artifacts.
    assert manager.stats.artifacts == 6  # 4 unique blobs + 2 manifests
    assert manager.stats.other == 4
    assert manager.stats.manifests == 2


def test_update_multiple_fragments(
    testdata: Callable[..., pathlib.Path], manager: RepoManager
):
    """Ensure we can make updates where a source contributes multiple fragments."""
    FIZZBUZZ_BUG = testdata("fizzbuzz-bug.rst").read_text()

    builder = manager.start_update(comment="first manifest", date=NOW)
    src, status = builder.add_src(FIZZBUZZ_BUG, "fizzbuzz.rst")

    # Check the src was added as we expect.
    assert status == "created", "Source should be newly created"
    assert src.filename == "src/fizzbuzz.rst"
    assert builder.get_artifact(src.blob).text == FIZZBUZZ_BUG

    code = """\
    for i in range(1, 26):
        if i % 3 != 0:
            print("fizz")
        else:
            print(i)
    """
    fragment, status = builder.add_fragment(
        code, src.filename, "fizzbuzz.py", "default"
    )

    # Check that the fragment as added as we expect
    assert status == "created", "Fragment should be newly created"
    assert (
        fragment.filename
        == "project/default/file/fizzbuzz.py/content/1/src-fizzbuzz.rst:1"
    )
    assert builder.get_artifact(fragment.blob).text == code

    code = """\

    for i in range(1, 26):
        if i % 3 == 0 and i % 5 == 0:
            print('fizzbuzz')
        elif i % 3 == 0:
            print('fizz')
        elif i % 5 == 0:
            print('buzz')
        else:
            print(i)
    """
    fragment2, status = builder.add_fragment(
        code, src.filename, "fizzbuzz.py", "default"
    )

    # Check that the fragment as added as we expect
    assert status == "created", "Fragment should be newly created"
    assert (
        fragment2.filename
        == "project/default/file/fizzbuzz.py/content/1/src-fizzbuzz.rst:2"
    )
    assert builder.get_artifact(fragment2.blob).text == code

    # Note: test_db.py should cover the correct construction of the manifest.
    # These tests are more about the correct representation of an awdur project's state
    # so we will just assume that uuids and checksums are correct.
    root = manager.commit_update()
    assert root.text == "\n".join(
        [
            r"C first\smanifest",
            "D 1970-01-01T00:00:00.000",
            f"F {fragment.filename} {fragment.blob} w",
            f"F {fragment2.filename} {fragment2.blob} w",
            f"F {src.filename} {src.blob} w",
            f"R {builder.manifest.rchecksum}",
            "T *branch * trunk",
            "T *source * awdur",
            "T *sym-trunk *",
            "T +projects * default",
            "U username",
            f"Z {builder.manifest.zchecksum}",
            "",
        ]
    )

    # The db should contain the expected number of artifacts.
    assert manager.stats.artifacts == 4  # 3 unique blobs + 1 manifest
    assert manager.stats.other == 3
    assert manager.stats.manifests == 1

    # Create an update
    builder = manager.start_update(
        comment="next update", date=NOW + dt.timedelta(days=1)
    )

    FIZZBUZZ_FIX = testdata("goodbye-world.rst").read_text()

    # Add an updated source
    src, updated = builder.add_src(FIZZBUZZ_FIX, filename="fizzbuzz.rst")
    assert src.filename == "src/fizzbuzz.rst"
    assert updated == "updated", "Source should be considered an update"
    assert builder.get_artifact(src.blob).text == FIZZBUZZ_FIX

    code = """\
    for i in range(1, 26):
        print(i)
    """
    fragment, status = builder.add_fragment(
        code, src.filename, "fizzbuzz.py", "default"
    )

    # Check that the fragment as added as we expect
    assert status == "updated", "Fragment should be considered updated"
    assert (
        fragment.filename
        == "project/default/file/fizzbuzz.py/content/1/src-fizzbuzz.rst:1"
    )
    assert builder.get_artifact(fragment.blob).text == code

    code = """\
    for i in range(1, 26):
        if i % 3 != 0:
            print("fizz")
        else:
            print(i)
    """
    fragment2, status = builder.add_fragment(
        code, src.filename, "fizzbuzz.py", "default"
    )

    # Check that the fragment as added as we expect
    assert status == "updated", "Fragment should be considered updated"
    assert (
        fragment2.filename
        == "project/default/file/fizzbuzz.py/content/1/src-fizzbuzz.rst:2"
    )
    assert builder.get_artifact(fragment2.blob).text == code

    code = """\

    for i in range(1, 26):
        if i % 3 == 0 and i % 5 == 0:
            print('fizzbuzz')
        elif i % 3 == 0:
            print('fizz')
        elif i % 5 == 0:
            print('buzz')
        else:
            print(i)
    """
    fragment3, status = builder.add_fragment(
        code, src.filename, "fizzbuzz.py", "default"
    )

    # Check that the fragment as added as we expect
    assert status == "created", "Fragment should be considered newly created"
    assert (
        fragment3.filename
        == "project/default/file/fizzbuzz.py/content/1/src-fizzbuzz.rst:3"
    )
    assert builder.get_artifact(fragment3.blob).text == code

    blob = manager.commit_update()
    assert blob.text == "\n".join(
        [
            r"C next\supdate",
            "D 1970-01-02T00:00:00.000",
            f"F {fragment.filename} {fragment.blob} w",
            f"F {fragment2.filename} {fragment2.blob} w",
            f"F {fragment3.filename} {fragment3.blob} w",
            f"F {src.filename} {src.blob} w",
            f"P {root.uuid}",
            f"R {builder.manifest.rchecksum}",
            "T +projects * default",
            "U username",
            f"Z {builder.manifest.zchecksum}",
            "",
        ]
    )

    # The db should contain the expected number of artifacts.
    assert manager.stats.artifacts == 7  # 5 unique blobs + 2 manifests
    assert manager.stats.other == 5
    assert manager.stats.manifests == 2


def test_update_remove_fragments(
    testdata: Callable[..., pathlib.Path], manager: RepoManager
):
    """Ensure we can make updates where a source contributes fewer fragments than
    previous."""
    FIZZBUZZ_BUG = testdata("fizzbuzz-bug.rst").read_text()

    builder = manager.start_update(comment="first manifest", date=NOW)
    src, status = builder.add_src(FIZZBUZZ_BUG, "fizzbuzz.rst")

    # Check the src was added as we expect.
    assert status == "created", "Source should be newly created"
    assert src.filename == "src/fizzbuzz.rst"
    assert builder.get_artifact(src.blob).text == FIZZBUZZ_BUG

    code = """\
    for i in range(1, 26):
        if i % 3 != 0:
            print("fizz")
        else:
            print(i)
    """
    fragment, status = builder.add_fragment(
        code, src.filename, "fizzbuzz.py", "default"
    )

    # Check that the fragment as added as we expect
    assert status == "created", "Fragment should be newly created"
    assert (
        fragment.filename
        == "project/default/file/fizzbuzz.py/content/1/src-fizzbuzz.rst:1"
    )
    assert builder.get_artifact(fragment.blob).text == code

    code = """\

    for i in range(1, 26):
        if i % 3 == 0 and i % 5 == 0:
            print('fizzbuzz')
        elif i % 3 == 0:
            print('fizz')
        elif i % 5 == 0:
            print('buzz')
        else:
            print(i)
    """
    fragment2, status = builder.add_fragment(
        code, src.filename, "fizzbuzz.py", "default"
    )

    # Check that the fragment as added as we expect
    assert status == "created", "Fragment should be newly created"
    assert (
        fragment2.filename
        == "project/default/file/fizzbuzz.py/content/1/src-fizzbuzz.rst:2"
    )
    assert builder.get_artifact(fragment2.blob).text == code

    # Note: test_db.py should cover the correct construction of the manifest.
    # These tests are more about the correct representation of an awdur project's state
    # so we will just assume that uuids and checksums are correct.
    root = manager.commit_update()
    assert root.text == "\n".join(
        [
            r"C first\smanifest",
            "D 1970-01-01T00:00:00.000",
            f"F {fragment.filename} {fragment.blob} w",
            f"F {fragment2.filename} {fragment2.blob} w",
            f"F {src.filename} {src.blob} w",
            f"R {builder.manifest.rchecksum}",
            "T *branch * trunk",
            "T *source * awdur",
            "T *sym-trunk *",
            "T +projects * default",
            "U username",
            f"Z {builder.manifest.zchecksum}",
            "",
        ]
    )

    # The db should contain the expected number of artifacts.
    assert manager.stats.artifacts == 4  # 3 unique blobs + 1 manifest
    assert manager.stats.other == 3
    assert manager.stats.manifests == 1

    # Create an update
    builder = manager.start_update(
        comment="next update", date=NOW + dt.timedelta(days=1)
    )

    FIZZBUZZ_FIX = testdata("fizzbuzz-fixed.rst").read_text()

    # Add an updated source
    src, updated = builder.add_src(FIZZBUZZ_FIX, filename="fizzbuzz.rst")
    assert src.filename == "src/fizzbuzz.rst"
    assert updated == "updated", "Source should be considered an update"
    assert builder.get_artifact(src.blob).text == FIZZBUZZ_FIX

    code = """\

    for i in range(1, 26):
        if i % 3 == 0 and i % 5 == 0:
            print('fizzbuzz')
        elif i % 3 == 0:
            print('fizz')
        elif i % 5 == 0:
            print('buzz')
        else:
            print(i)
    """
    fragment, status = builder.add_fragment(
        code, src.filename, "fizzbuzz.py", "default"
    )

    # Check that the fragment as added as we expect
    assert status == "updated", "Fragment should be considered newly created"
    assert (
        fragment.filename
        == "project/default/file/fizzbuzz.py/content/1/src-fizzbuzz.rst:1"
    )
    assert builder.get_artifact(fragment.blob).text == code

    blob = manager.commit_update()
    assert blob.text == "\n".join(
        [
            r"C next\supdate",
            "D 1970-01-02T00:00:00.000",
            f"F {fragment.filename} {fragment.blob} w",
            f"F {src.filename} {src.blob} w",
            f"P {root.uuid}",
            f"R {builder.manifest.rchecksum}",
            "T +projects * default",
            "U username",
            f"Z {builder.manifest.zchecksum}",
            "",
        ]
    )

    # The db should contain the expected number of artifacts.
    assert manager.stats.artifacts == 6  # 4 unique blobs + 2 manifests
    assert manager.stats.other == 4
    assert manager.stats.manifests == 2


def test_update_remove_source(
    testdata: Callable[..., pathlib.Path], manager: RepoManager
):
    """Ensure we can make updates where a source is removed."""
    HELLO_WORLD = testdata("hello-world.rst").read_text()
    GOODBYE_WORLD = testdata("goodbye-world.rst").read_text()
    FIZZBUZZ_BUG = testdata("fizzbuzz-bug.rst").read_text()

    builder = manager.start_update(comment="first manifest", date=NOW)
    hello_src, status = builder.add_src(HELLO_WORLD, "hello-world.rst")

    # Check the src was added as we expect.
    assert status == "created", "Source should be newly created"
    assert hello_src.filename == "src/hello-world.rst"
    assert builder.get_artifact(hello_src.blob).text == HELLO_WORLD

    code = 'print("Hello, World!")\n'
    fragment, status = builder.add_fragment(
        code, hello_src.filename, "everything.py", "default"
    )

    # Check that the fragment as added as we expect
    assert status == "created", "Fragment should be newly created"
    assert (
        fragment.filename
        == "project/default/file/everything.py/content/1/src-hello-world.rst:1"
    )
    assert builder.get_artifact(fragment.blob).text == code

    bye_src, updated = builder.add_src(GOODBYE_WORLD, filename="goodbye-world.rst")
    assert bye_src.filename == "src/goodbye-world.rst"
    assert updated == "created", "Source should be considered newly created"
    assert builder.get_artifact(bye_src.blob).text == GOODBYE_WORLD

    code = 'print("Goodbye, World!")\n'
    fragment2, status = builder.add_fragment(
        code, bye_src.filename, "everything.py", "default"
    )

    # Check that the fragment as added as we expect
    assert status == "created", "Fragment should be considered newly created"
    assert (
        fragment2.filename
        == "project/default/file/everything.py/content/1/src-goodbye-world.rst:1"
    )
    assert builder.get_artifact(fragment2.blob).text == code

    fizzbug_src, status = builder.add_src(FIZZBUZZ_BUG, "fizzbuzz.rst")

    # Check the src was added as we expect.
    assert status == "created", "Source should be newly created"
    assert fizzbug_src.filename == "src/fizzbuzz.rst"
    assert builder.get_artifact(fizzbug_src.blob).text == FIZZBUZZ_BUG

    code = """\
    for i in range(1, 26):
        if i % 3 != 0:
            print("fizz")
        else:
            print(i)
    """
    fragment3, status = builder.add_fragment(
        code, fizzbug_src.filename, "everything.py", "default"
    )

    # Check that the fragment as added as we expect
    assert status == "created", "Fragment should be newly created"
    assert (
        fragment3.filename
        == "project/default/file/everything.py/content/1/src-fizzbuzz.rst:1"
    )
    assert builder.get_artifact(fragment3.blob).text == code

    code = """\

    for i in range(1, 26):
        if i % 3 == 0 and i % 5 == 0:
            print('fizzbuzz')
        elif i % 3 == 0:
            print('fizz')
        elif i % 5 == 0:
            print('buzz')
        else:
            print(i)
    """
    fragment4, status = builder.add_fragment(
        code, fizzbug_src.filename, "everything.py", "default"
    )

    # Check that the fragment as added as we expect
    assert status == "created", "Fragment should be newly created"
    assert (
        fragment4.filename
        == "project/default/file/everything.py/content/1/src-fizzbuzz.rst:2"
    )
    assert builder.get_artifact(fragment4.blob).text == code

    # Note: test_db.py should cover the correct construction of the manifest.
    # These tests are more about the correct representation of an awdur project's state
    # so we will just assume that uuids and checksums are correct.
    root = manager.commit_update()
    assert root.text == "\n".join(
        [
            r"C first\smanifest",
            "D 1970-01-01T00:00:00.000",
            f"F {fragment3.filename} {fragment3.blob} w",
            f"F {fragment4.filename} {fragment4.blob} w",
            f"F {fragment2.filename} {fragment2.blob} w",
            f"F {fragment.filename} {fragment.blob} w",
            f"F {fizzbug_src.filename} {fizzbug_src.blob} w",
            f"F {bye_src.filename} {bye_src.blob} w",
            f"F {hello_src.filename} {hello_src.blob} w",
            f"R {builder.manifest.rchecksum}",
            "T *branch * trunk",
            "T *source * awdur",
            "T *sym-trunk *",
            "T +projects * default",
            "U username",
            f"Z {builder.manifest.zchecksum}",
            "",
        ]
    )

    # The db should contain the expected number of artifacts.
    assert manager.stats.artifacts == 8  # 7 unique blobs + 1 manifest
    assert manager.stats.other == 7
    assert manager.stats.manifests == 1

    # Create an update
    builder = manager.start_update(
        comment="next update", date=NOW + dt.timedelta(days=1)
    )

    # 'Update' hello-world with no change
    hello_src, status = builder.add_src(HELLO_WORLD, "hello-world.rst")

    # Check the src was added as we expect.
    assert status == "unchanged", "Source should be unchanged"
    assert hello_src.filename == "src/hello-world.rst"

    # Skip goodbye-world to delete it.
    FIZZBUZZ_FIX = testdata("fizzbuzz-fixed.rst").read_text()

    # Add an updated source
    fizzfix_src, updated = builder.add_src(FIZZBUZZ_FIX, filename="fizzbuzz.rst")
    assert fizzfix_src.filename == "src/fizzbuzz.rst"
    assert updated == "updated", "Source should be considered an update"
    assert builder.get_artifact(fizzfix_src.blob).text == FIZZBUZZ_FIX

    code = """\

    for i in range(1, 26):
        if i % 3 == 0 and i % 5 == 0:
            print('fizzbuzz')
        elif i % 3 == 0:
            print('fizz')
        elif i % 5 == 0:
            print('buzz')
        else:
            print(i)
    """
    fragment5, status = builder.add_fragment(
        code, fizzfix_src.filename, "everything.py", "default"
    )

    # Check that the fragment as added as we expect
    assert status == "updated", "Fragment should be considered newly created"
    assert (
        fragment5.filename
        == "project/default/file/everything.py/content/1/src-fizzbuzz.rst:1"
    )
    assert builder.get_artifact(fragment5.blob).text == code

    blob = manager.commit_update()
    assert blob.text == "\n".join(
        [
            r"C next\supdate",
            "D 1970-01-02T00:00:00.000",
            f"F {fragment3.filename} {fragment5.blob} w",
            f"F {fragment.filename} {fragment.blob} w",
            f"F {fizzfix_src.filename} {fizzfix_src.blob} w",
            f"F {hello_src.filename} {hello_src.blob} w",
            f"P {root.uuid}",
            f"R {builder.manifest.rchecksum}",
            "T +projects * default",
            "U username",
            f"Z {builder.manifest.zchecksum}",
            "",
        ]
    )

    # The db should contain the expected number of artifacts.
    assert manager.stats.artifacts == 10  # 8 unique blobs + 2 manifests
    assert manager.stats.other == 8
    assert manager.stats.manifests == 2
