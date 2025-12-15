from __future__ import annotations

import os
import pathlib
import subprocess
import sys

import pytest

try:
    import sphinx

    SPHINX_AVAILABLE = True
except ImportError:
    SPHINX_AVAILABLE = False


@pytest.mark.parametrize("workspace", ["hello-world"], indirect=True)
@pytest.mark.skipif(not SPHINX_AVAILABLE, reason="test requires sphinx")
def test_hello_world_render(workspace: pathlib.Path):
    """Ensure that we can render docs from our hello-world example."""

    # fmt: off
    cmd = [
        sys.executable, "-m", "sphinx",
        ".", "out",
        "-C",
        "-b", "singlehtml",
        "-D", "root_doc=hello-world",
        "-D", "extensions=awdur.sphinxext",
    ]
    # fmt: on

    result = subprocess.run(cmd, cwd=workspace)
    assert result.returncode == 0

    output = workspace / "out/hello-world.html"
    assert output.exists()

    content = output.read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in content


@pytest.mark.parametrize("workspace", ["hello-world"], indirect=True)
@pytest.mark.skipif(not SPHINX_AVAILABLE, reason="test requires sphinx")
def test_hello_world_extract(workspace: pathlib.Path):
    """Ensure that we can extract code from our hello-world example."""

    # fmt: off
    cmd = [
        sys.executable, "-m", "sphinx",
        ".", "out",
        "-b", "awdur",
        "-C",
        "-D", "root_doc=hello-world",
        "-D", "extensions=awdur.sphinxext",
    ]
    # fmt: on

    result = subprocess.run(cmd, cwd=workspace)
    assert result.returncode == 0

    output = workspace / "out/hello-world.py"
    assert output.exists()

    content = output.read_text()
    assert content == 'print("Hello, World!")\n'


@pytest.mark.parametrize("workspace", ["multiple-blocks"], indirect=True)
@pytest.mark.skipif(not SPHINX_AVAILABLE, reason="test requires sphinx")
def test_multiple_blocks_render(workspace: pathlib.Path):
    """Ensure that we can render docs from our multiple-blocks example."""

    # fmt: off
    cmd = [
        sys.executable, "-m", "sphinx",
        ".", "out",
        "-b", "singlehtml",
        "-C",
        "-D", "root_doc=multiple-blocks",
        "-D", "extensions=awdur.sphinxext",
    ]
    # fmt: on

    result = subprocess.run(cmd, cwd=workspace)
    assert result.returncode == 0

    output = workspace / "out/multiple-blocks.html"
    assert output.exists()

    content = output.read_text()
    assert "<!DOCTYPE html>" in content


@pytest.mark.parametrize("workspace", ["multiple-blocks"], indirect=True)
@pytest.mark.skipif(not SPHINX_AVAILABLE, reason="test requires sphinx")
def test_multiple_blocks_extract(workspace: pathlib.Path):
    """Ensure that we can extract code from our multiple-blocks example."""

    # fmt: off
    cmd = [
        sys.executable, "-m", "sphinx",
        ".", "out",
        "-b", "awdur",
        "-C",
        "-D", "root_doc=multiple-blocks",
        "-D", "extensions=awdur.sphinxext",
    ]
    # fmt: on

    result = subprocess.run(cmd, cwd=workspace)
    assert result.returncode == 0

    output = workspace / "out/multiple-blocks.py"
    assert output.exists()

    result = subprocess.run([sys.executable, f"{output}"], capture_output=True)
    assert result.returncode == 0

    # fmt: off
    stdout = result.stdout.decode("utf-8")
    assert stdout.strip() == (
        f"A triangle with sides a=3, b=4, c=5 has{os.linesep}"
        f"- Perimeter, P=12{os.linesep}"
        "- Area, A=6.0"
    )
    # fmt: on


@pytest.mark.parametrize("workspace", ["multiple-files"], indirect=True)
@pytest.mark.skipif(not SPHINX_AVAILABLE, reason="test requires sphinx")
def test_multiple_files_render(workspace: pathlib.Path):
    """Ensure that we can render docs from our multiple-files example."""

    # fmt: off
    cmd = [
        sys.executable, "-m", "sphinx",
        ".", "out",
        "-b", "singlehtml",
        "-C",
        "-D", "root_doc=multiple-files",
        "-D", "extensions=awdur.sphinxext",
    ]
    # fmt: on

    result = subprocess.run(cmd, cwd=workspace)
    assert result.returncode == 0

    output = workspace / "out/multiple-files.html"
    assert output.exists()

    content = output.read_text()
    assert "<!DOCTYPE html>" in content


@pytest.mark.parametrize("workspace", ["multiple-files"], indirect=True)
@pytest.mark.skipif(not SPHINX_AVAILABLE, reason="test requires sphinx")
def test_multiple_files_extract(workspace: pathlib.Path):
    """Ensure that we can extract code from our multiple-files example."""

    # fmt: off
    cmd = [
        sys.executable, "-m", "sphinx",
        ".", "out",
        "-b", "awdur",
        "-C",
        "-D", "root_doc=multiple-files",
        "-D", "extensions=awdur.sphinxext",
    ]
    # fmt: on

    result = subprocess.run(cmd, cwd=workspace)
    assert result.returncode == 0

    # check fib.py
    output = workspace / "out/fib.py"
    assert output.exists()

    result = subprocess.run([sys.executable, f"{output}"], capture_output=True)
    assert result.returncode == 0

    stdout = result.stdout.decode("utf-8")
    assert stdout.strip() == (
        "The first 10 Fibonacci numbers are: 1, 1, 2, 3, 5, 8, 13, 21, 34, 55"
    )

    # check square.py
    output = workspace / "out/square.py"
    assert output.exists()

    result = subprocess.run([sys.executable, f"{output}"], capture_output=True)
    assert result.returncode == 0

    stdout = result.stdout.decode("utf-8")
    assert stdout.strip() == (
        "The first 10 square numbers are: 1, 4, 9, 16, 25, 36, 49, 64, 81, 100"
    )
