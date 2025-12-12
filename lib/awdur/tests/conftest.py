from __future__ import annotations

import pathlib
import shutil

import pytest

EXAMPLES_DIR = pathlib.Path(__file__).parent / "../../../examples"


@pytest.fixture(scope="function")
def workspace(request, tmp_path: pathlib.Path):
    """A fixture that automates setup and teardown of a workspace based on one of the
    example projects."""

    example = (EXAMPLES_DIR / request.param).resolve()
    assert example.exists() and example.is_dir()

    yield shutil.copytree(example, tmp_path, dirs_exist_ok=True)
