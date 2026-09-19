"""Database types common to fossil and awdur."""

from __future__ import annotations

import hashlib
import operator
import os
import pathlib
import struct
import typing
import zlib

if typing.TYPE_CHECKING:
    import logging
    import sqlite3
    from datetime import datetime


ASCII_SPACE = chr(0x20)
ASCII_NL = chr(0x0A)
ASCII_BSLASH = chr(0x5C)

ESC_SPACE = chr(0x5C) + chr(0x73)
ESC_NL = chr(0x5C) + chr(0x6E)
ESC_BSLASH = 2 * ASCII_BSLASH


@typing.final
class Blob:
    """Represents a record from the ``blob`` table."""

    def __init__(
        self, rid: int | None, rcvid: int, size: int, uuid: str, content: bytes
    ):
        self.rid = rid
        self.rcvid = rcvid
        self.size = size
        self.uuid = uuid
        self.content = content
        self._text: str | None = None

    def __repr__(self):
        return f"Blob<{self.uuid}; {self.size} bytes>"

    @classmethod
    def fromdb(cls, rid: int, rcvid: int, size: int, uuid: str, content: bytes):
        return cls(rid, rcvid, size, uuid, content)

    def insert(self, db: sqlite3.Connection | sqlite3.Cursor):
        """Insert this record into the given db."""
        cursor = db.execute(
            "INSERT INTO blob(rcvid, size, uuid, content) VALUES (?,?,?,?) RETURNING *",
            (self.rcvid, self.size, self.uuid, self.content),
        )
        blob = Blob.fromdb(*cursor.fetchone())
        return blob

    @classmethod
    def create(cls, content: str, rcvid: int):
        """Create a new blob record."""
        bcontent = content.encode()
        uuid = hashlib.sha3_256(bcontent).hexdigest()

        data = zlib.compress(bcontent)
        size = len(bcontent)
        header = struct.pack(">I", size)

        blob = cls(None, rcvid, size, uuid, header + data)
        blob._text = content

        return blob

    @property
    def text(self) -> str:
        """Return the uncompressed text held in a blob."""
        if self._text is not None:
            return self._text

        self._text = zlib.decompress(self.content[4:]).decode("utf8")
        return self._text


@typing.final
class Manifest:
    """Responsible for building the manifest entry for a check-in."""

    def __init__(
        self,
        comment: str,
        date: datetime,
        user: str,
        previous: list[Blob] | None = None,
    ):
        self.comment = comment
        self.date = date
        self.files: list[tuple[str, Blob]] = []
        self.previous = previous or []
        self.repo_checksum = hashlib.md5()
        self.tags: list[tuple[str, str]] = []
        self.user = user

    def add_file(self, filename: pathlib.Path, blob: Blob):
        self.files.append((escape_filename(filename), blob))

    def add_tag(self, name: str, value: str = ""):
        self.tags.append((name, value))

    def build(self) -> str:
        """Close the manifest by appending the ``Z`` checksum card and return it."""
        cards: list[str] = [
            f"C {escape_text(self.comment)}",
            f"D {format_date(self.date)}",
        ]

        for filename, blob in sorted(self.files, key=operator.itemgetter(0)):
            cards.append(f"F {filename} {blob.uuid}")

            # Also update the repository checksum.
            file = f"{filename}{ASCII_SPACE}{len(blob.text)}{ASCII_NL}{blob.text}"
            self.repo_checksum.update(file.encode())

        if self.previous:
            cards.append(f"P {' '.join(b.uuid for b in self.previous)}")

        cards.append(f"R {self.repo_checksum.hexdigest()}")

        for name, value in self.tags:
            # '*' refers to 'self' i.e. this manifest, see file format spec for details.
            cards.append(f"T *{name} * {value}".strip())

        cards.append(f"U {self.user}")

        record = "\n".join(cards) + "\n"
        checksum = hashlib.md5(record.encode()).hexdigest()
        record += f"Z {checksum}\n"
        return record


def escape_filename(filepath: os.PathLike[str]) -> str:
    """Validate and escape the given filepath for inclusion in a fossil record.

    .. pull-quote::

       The pathname of the file in the check-in is relative to the root of the project
       file hierarchy. No ".." or "." directories are allowed within the filename.

       Space characters are escaped as in a C card comment. Backslash and newlines are
       not allowed within filenames.

       The directory separator character is a forward slash (ASCII 0x2f).

       -- `F card <https://fossil-scm.org/home/doc/trunk/www/fileformat.wiki#manifest>`__
    """
    filename = os.fspath(filepath)
    if "./" in filename or "../" in filename:
        raise ValueError(
            f"Invalid path: {filename!r} path must be relative to project root"
        )

    if ASCII_NL in filename or ASCII_BSLASH in filename:
        raise ValueError(
            f"Invalid path: {filename!r}, newlines and backslashes are not permitted"
        )

    return filename.replace(ASCII_SPACE, ESC_SPACE)


def escape_text(text: str) -> str:
    """Escape text for inclusion in a fossil record.

    .. pull-quote::

       The following escape sequences are applied to the text:
       - A space (ASCII 0x20) is represented as "\\s" (ASCII 0x5C, 0x73).
       - A newline (ASCII 0x0a) is "\\n" (ASCII 0x5C, x6E).
       - A backslash (ASCII 0x5C) is represented as two backslashes "\\\\".

       -- `C card <https://fossil-scm.org/home/doc/trunk/www/fileformat.wiki#manifest>`__
    """
    return (
        text.replace(ASCII_BSLASH, ESC_BSLASH)
        .replace(ASCII_SPACE, ESC_SPACE)
        .replace(ASCII_NL, ESC_NL)
    )


def format_date(dt: datetime) -> str:
    """Format a datetime for inclusion in a fossil record.

    .. pull-quote::

       The sole argument to the D card is a date-time stamp in the ISO8601 format.

       The date and time should be in coordinated universal time (UTC).
       The format one of:

       - YYYY-MM-DDTHH:MM:SS
       - YYYY-MM-DDTHH:MM:SS.SSS
    """
    return dt.isoformat("T", "milliseconds").replace("+00:00", "")
