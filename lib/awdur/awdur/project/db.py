"""Database types common to fossil and awdur."""

from __future__ import annotations

import dataclasses
import datetime as dt
import hashlib
import operator
import os
import pathlib
import struct
import typing
import zlib

if typing.TYPE_CHECKING:
    import sqlite3
    from typing import Literal

    FilePermissions = Literal["w", "x", "l"]

ASCII_SPACE = chr(0x20)
ASCII_NL = chr(0x0A)
ASCII_BSLASH = chr(0x5C)

ESC_SPACE = chr(0x5C) + chr(0x73)
ESC_NL = chr(0x5C) + chr(0x6E)
ESC_BSLASH = 2 * ASCII_BSLASH

UTC = dt.timezone.utc


@typing.final
@dataclasses.dataclass
class Blob:
    """Represents a record from the ``blob`` table."""

    rid: int | None = dataclasses.field(default=None)
    """The blob's row id"""

    rcvid: int | None = dataclasses.field(default=None)
    """The rcvid."""

    size: int | None = dataclasses.field(default=None)
    """The size of the uncompressed blob"""

    uuid: str | None = dataclasses.field(default=None)
    """The blob's hash"""

    content: bytes | None = dataclasses.field(default=None)
    """The content itself."""

    _text: str | None = dataclasses.field(default=None, init=False)
    """Internal cache of the uncompressed text of the blob, if known"""

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

        if self.content is None:
            return ""

        self._text = zlib.decompress(self.content[4:]).decode("utf8")
        return self._text


@typing.final
@dataclasses.dataclass
class Manifest:
    """Represents a manifest entry corresponding with a check-in."""

    @typing.final
    @dataclasses.dataclass
    class File:
        """Represents an F card in a manifest."""

        filename: str
        """The filepath of the file, relative to the repo root."""

        blob: Blob
        """The blob holding the file's contents"""

        permissions: FilePermissions | None = dataclasses.field(
            default=None, kw_only=True
        )
        """The permissions to assign the file."""

        old_filename: str | None = dataclasses.field(default=None, kw_only=True)
        """If the file was renamed, this is the previous name."""

        def __str__(self):
            parts = ["F", self.filename, self.blob.uuid]

            if self.permissions:
                parts.append(self.permissions)

            if self.old_filename:
                parts.append(self.old_filename)

            return " ".join(parts)

    baseline: Blob | None = dataclasses.field(default=None, kw_only=True)
    """The baseline manifest, only used for delta manifests."""

    comment: str | None = dataclasses.field(default=None, kw_only=True)
    """The check-in comment."""

    date: dt.datetime | None = dataclasses.field(default=None, kw_only=True)
    """The check-in date."""

    files: dict[str, File] = dataclasses.field(default_factory=dict, kw_only=True)
    """The files included in the check-in"""

    mimetype: str | None = dataclasses.field(default=None, kw_only=True)
    """Mime type of the check-in comment"""

    previous: list[Blob] = dataclasses.field(default_factory=list, kw_only=True)
    """The previous manifest(s) this one supercedes."""

    rchecksum: str | None = dataclasses.field(default=None, kw_only=True)
    """Checksum of all files included in check-in"""

    # Note: likely to change as i figure out how these work.
    tags: list[tuple[str, str]] | None = dataclasses.field(
        default_factory=list, kw_only=True
    )
    """Tags."""

    user: str | None = dataclasses.field(default=None, kw_only=True)
    """The user who made the check-in"""

    zchecksum: str | None = dataclasses.field(default=None)
    """Checksum of the manifest record itself."""

    @classmethod
    def fromblob(cls, blob: Blob):
        """Construct a manifest instance from a blob"""
        return cls.fromtext(blob.text)

    @classmethod
    def fromtext(cls, text: str):
        """Construct a manifest instance from text"""
        manifest = cls()

        for line in text.splitlines():
            ctype, value = line[:2], line[2:]
            match ctype.strip():
                case "C":
                    manifest.comment = unescape_text(value)

                case "D":
                    if not value.endswith("Z"):
                        value += "Z"
                    manifest.date = dt.datetime.fromisoformat(value)

                case "R":
                    manifest.rchecksum = value

                case "T":
                    # TODO: Figure out how tags actually work!
                    parts = [
                        p for v in value.replace("*", "").split(" ") if (p := v.strip())
                    ]
                    if len(parts) == 2:
                        name, val = parts
                    else:
                        name = parts[0]
                        val = ""

                    manifest.add_tag(name, val)

                case "U":
                    manifest.user = value

                case "Z":
                    manifest.zchecksum = value

                case _:
                    raise ValueError(
                        f"Invalid manifest: unknown card type {ctype.strip()!r}"
                    )

        return manifest

    def add_file(
        self,
        filename: pathlib.Path,
        blob: Blob,
        permissions: FilePermissions | None = None,
        old_filename: pathlib.Path | None = None,
    ):
        """Add a file to the manifest"""
        fname = escape_filename(filename)
        old_fname = None

        if old_filename:
            old_fname = escape_filename(old_filename)

        self.files[fname] = Manifest.File(
            fname, blob, permissions=permissions, old_filename=old_fname
        )

    def add_tag(self, name: str, value: str = ""):
        self.tags.append((name, value))

    def validate(self):
        """Check to see if we have a valid manifest."""

        if self.comment is None or self.comment == "":
            raise ValueError("Invalid manifest: a check-in comment is required")

        if self.date is None:
            raise ValueError("Invalid manifest: a check-in date is required")

        if self.user is None:
            raise ValueError(
                "Invalid manifest: a check-in must be associated with a user"
            )

        # Calculate the repo checksum
        rchecksum = hashlib.md5()
        for _, file in sorted(self.files.items(), key=operator.itemgetter(0)):
            item = f"{file.filename}{ASCII_SPACE}{len(file.blob.text)}{ASCII_NL}{file.blob.text}"
            rchecksum.update(item.encode())

        # If not set, assume we are computing it fresh for a build()
        if self.rchecksum is None or self.rchecksum == "":
            self.rchecksum = rchecksum.hexdigest()

        # Otherwise, check it.
        elif self.rchecksum != rchecksum.hexdigest():
            raise ValueError("Invalid manifest: R card inconsitent with repo contents")

    def build(self) -> str:
        """Close the manifest by appending the ``Z`` checksum card and return it."""
        self.validate()

        cards: list[str] = [
            f"C {escape_text(self.comment)}",
            f"D {format_date(self.date)}",
        ]

        if self.previous:
            cards.append(f"P {' '.join(b.uuid for b in self.previous)}")

        # The rchecksum is optional
        if self.rchecksum is not None:
            cards.append(f"R {self.rchecksum}")

        for name, value in self.tags:
            # '*' refers to 'self' i.e. this manifest, see file format spec for details.
            cards.append(f"T *{name} * {value}".strip())

        cards.append(f"U {self.user}")

        record = "\n".join(cards) + "\n"
        self.zchecksum = hashlib.md5(record.encode()).hexdigest()
        record += f"Z {self.zchecksum}\n"
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


def unescape_text(text: str) -> str:
    """Unescape text from a fossil record.

    .. pull-quote::

       The following escape sequences are applied to the text:
       - A space (ASCII 0x20) is represented as "\\s" (ASCII 0x5C, 0x73).
       - A newline (ASCII 0x0a) is "\\n" (ASCII 0x5C, x6E).
       - A backslash (ASCII 0x5C) is represented as two backslashes "\\\\".

       -- `C card <https://fossil-scm.org/home/doc/trunk/www/fileformat.wiki#manifest>`__
    """
    return (
        text.replace(ESC_BSLASH, ASCII_BSLASH)
        .replace(ESC_SPACE, ASCII_SPACE)
        .replace(ESC_NL, ASCII_NL)
    )


def format_date(dt: dt.datetime) -> str:
    """Format a datetime for inclusion in a fossil record.

    .. pull-quote::

       The sole argument to the D card is a date-time stamp in the ISO8601 format.

       The date and time should be in coordinated universal time (UTC).
       The format one of:

       - YYYY-MM-DDTHH:MM:SS
       - YYYY-MM-DDTHH:MM:SS.SSS
    """
    return dt.isoformat("T", "milliseconds").replace("+00:00", "")
