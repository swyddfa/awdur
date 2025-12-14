from __future__ import annotations

import pathlib
import subprocess
import sys

import pytest


@pytest.mark.parametrize("workspace", ["hello-world"], indirect=True)
def test_render_hello_world(workspace: pathlib.Path):
    """Ensure we can generate a html file from the example correctly."""

    result = subprocess.run(
        [sys.executable, "-m", "awdur", "render", "hello-world.rst"], cwd=workspace
    )
    assert result.returncode == 0

    output = workspace / "hello-world.html"
    assert output.exists()

    text = output.read_text()
    assert "<!DOCTYPE html>" in text


@pytest.mark.parametrize("workspace", ["multiple-blocks"], indirect=True)
def test_render_multiple_blocks(workspace: pathlib.Path):
    """Ensure we can generate a html file from the example correctly."""

    result = subprocess.run(
        [sys.executable, "-m", "awdur", "render", "multiple-blocks.rst"], cwd=workspace
    )
    assert result.returncode == 0

    output = workspace / "multiple-blocks.html"
    assert output.exists()

    text = output.read_text()
    assert "<!DOCTYPE html>" in text


@pytest.mark.parametrize("workspace", ["multiple-files"], indirect=True)
def test_render_multiple_files(workspace: pathlib.Path):
    """Ensure we can generate a html file from the example correctly."""

    result = subprocess.run(
        [sys.executable, "-m", "awdur", "render", "multiple-files.rst"], cwd=workspace
    )
    assert result.returncode == 0

    output = workspace / "multiple-files.html"
    assert output.exists()

    text = output.read_text()
    assert "<!DOCTYPE html>" in text
