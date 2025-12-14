from __future__ import annotations

import pathlib
import subprocess
import sys

import pytest


@pytest.mark.parametrize("workspace", ["hello-world"], indirect=True)
def test_extract_hello_world(workspace: pathlib.Path):
    """Ensure we can extract code from the example correctly."""

    result = subprocess.run(
        [sys.executable, "-m", "awdur", "extract", "hello-world.rst"], cwd=workspace
    )
    assert result.returncode == 0

    output = workspace / "hello-world.py"
    assert output.exists()

    assert 'print("Hello, World!")\n' == output.read_text()


@pytest.mark.parametrize("workspace", ["multiple-blocks"], indirect=True)
def test_extract_multiple_blocks(workspace: pathlib.Path):
    """Ensure we can extract code from the example correctly."""

    result = subprocess.run(
        [sys.executable, "-m", "awdur", "extract", "multiple-blocks.rst"], cwd=workspace
    )
    assert result.returncode == 0

    output = workspace / "multiple-blocks.py"
    assert output.exists()

    result = subprocess.run([sys.executable, f"{output}"], capture_output=True)
    assert result.returncode == 0

    # fmt: off
    assert  result.stdout.decode("utf-8") == (
        "A triangle with sides a=3, b=4, c=5 has\n"
        "- Perimeter, P=12\n"
        "- Area, A=6.0\n"
    )
    # fmt: on


@pytest.mark.parametrize("workspace", ["multiple-files"], indirect=True)
def test_extract_multiple_files(workspace: pathlib.Path):
    """Ensure we can extract code from the example correctly."""

    result = subprocess.run(
        [sys.executable, "-m", "awdur", "extract", "multiple-files.rst"], cwd=workspace
    )
    assert result.returncode == 0

    # check fib.py
    output = workspace / "multiple-files/fib.py"
    assert output.exists()

    result = subprocess.run([sys.executable, f"{output}"], capture_output=True)
    assert result.returncode == 0

    assert result.stdout.decode("utf-8") == (
        "The first 10 Fibonacci numbers are: 1, 1, 2, 3, 5, 8, 13, 21, 34, 55\n"
    )

    # check square.py
    output = workspace / "multiple-files/square.py"
    assert output.exists()

    result = subprocess.run([sys.executable, f"{output}"], capture_output=True)
    assert result.returncode == 0

    assert result.stdout.decode("utf-8") == (
        "The first 10 square numbers are: 1, 4, 9, 16, 25, 36, 49, 64, 81, 100\n"
    )
