from __future__ import annotations

import datetime as dt
import typing

import pytest

from awdur.project.db import Manifest
from awdur.project.db import Tag
from awdur.project.db import apply_delta
from awdur.project.db import b64_decode

UTC = dt.timezone.utc


if typing.TYPE_CHECKING:
    import pathlib
    from typing import Callable


@pytest.mark.parametrize(
    "val, signed, expected",
    [
        (b"0", False, 0),
        (b"0", True, 0),
        (b"1Xb", True, 6246),
        (b"1Xb", False, 6246),
        (b"2zMM3E", True, -1101438770),
        (b"2zMM3E", False, 3193528526),
    ],
)
def test_b64_decode(val: bytes, signed: bool, expected: int):
    """Ensure we can decode fossil's base 64 encoding scheme correctly."""
    assert b64_decode(val, signed) == expected


@pytest.mark.parametrize(
    "before,after,delta",
    [
        ("simple_before.txt", "simple_after.txt", "simple_delta.txt"),
        ("longer_before.txt", "longer_after.txt", "longer_delta.txt"),
        ("manager_before.py", "manager_after.py", "manager_delta.py"),
    ],
)
def test_apply_delta(
    testdata: Callable[..., pathlib.Path], before: str, after: str, delta: str
):
    """Ensure that we can intepret fossil's delta artifacts correctly."""
    baseline = testdata(before).read_bytes()
    expected = testdata(after).read_bytes()
    dt = testdata(delta).read_bytes()

    actual = apply_delta(baseline, dt)
    assert actual == expected


@pytest.mark.parametrize(
    "manifest,expected",
    [
        (
            Manifest(
                comment="initial empty check-in",
                date=dt.datetime(
                    year=2026,
                    month=9,
                    day=6,
                    hour=19,
                    minute=47,
                    second=21,
                    microsecond=579000,
                    tzinfo=UTC,
                ),
                tags=[
                    Tag("*", "branch", "*", "trunk"),
                    Tag("*", "sym-trunk", "*"),
                ],
                user="alex",
            ),
            [
                r"C initial\sempty\scheck-in",
                "D 2026-09-06T19:47:21.579",
                "R d41d8cd98f00b204e9800998ecf8427e",
                "T *branch * trunk",
                "T *sym-trunk *",
                "U alex",
                "Z 3d011dae7f184723382e589ffeb06b75",
            ],
        ),
    ],
)
def test_manifest_build(manifest: Manifest, expected: list[str]):
    """Ensure that we can build manifests correctly."""
    actual = manifest.build().splitlines()
    assert actual == expected


@pytest.mark.parametrize(
    "lines,expected",
    [
        (
            [
                r"C initial\sempty\scheck-in",
                "D 2026-09-06T19:47:21.579",
                "R d41d8cd98f00b204e9800998ecf8427e",
                "T *branch * trunk",
                "T *sym-trunk *",
                "U alex",
                "Z 3d011dae7f184723382e589ffeb06b75",
            ],
            Manifest(
                comment="initial empty check-in",
                date=dt.datetime(
                    year=2026,
                    month=9,
                    day=6,
                    hour=19,
                    minute=47,
                    second=21,
                    microsecond=579000,
                    tzinfo=UTC,
                ),
                rchecksum="d41d8cd98f00b204e9800998ecf8427e",
                tags=[
                    Tag("*", "branch", "*", "trunk"),
                    Tag("*", "sym-trunk", "*"),
                ],
                user="alex",
                zchecksum="3d011dae7f184723382e589ffeb06b75",
            ),
        ),
    ],
)
def test_manifest_fromtext(lines: list[str], expected: Manifest):
    """Ensure that we can parse manifests correctly."""
    actual = Manifest.fromtext("\n".join(lines) + "\n")
    assert actual == expected


@pytest.mark.parametrize(
    "manifest,expected",
    [
        (Manifest(), "a check-in comment is required"),
        (Manifest(comment="comment"), "a check-in date is required"),
        (
            Manifest(comment="comment", date=dt.datetime.now(tz=UTC)),
            "a check-in must be associated with a user",
        ),
    ],
)
def test_manifest_validation(manifest: Manifest, expected: str):
    """Ensure that we can identify invalid manifests."""

    with pytest.raises(ValueError, match=expected):
        _ = manifest.build()
