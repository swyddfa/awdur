from __future__ import annotations

import datetime as dt

import pytest

from awdur.project.db import Manifest

UTC = dt.timezone.utc


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
                # Need to figure out how tags actually work...
                tags=[("branch", "trunk"), ("sym-trunk", "")],
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
                # Need to figure out how tags actually work...
                tags=[("branch", "trunk"), ("sym-trunk", "")],
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
