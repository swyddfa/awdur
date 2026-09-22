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
    def find(cls, db: sqlite3.Connection, rid: int):
        """Find a blob given its rid"""
        cursor = db.execute("SELECT * FROM BLOB WHERE rid = ?", (rid,))
        if (row := cursor.fetchone()) is None:
            return None

        return cls.fromdb(*row)

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

    previous: list[str] = dataclasses.field(default_factory=list, kw_only=True)
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

    uuid: str | None = dataclasses.field(default=None)
    """The uuid of the this manifest's blob, if known"""

    def __repr__(self) -> str:
        comment = "NO COMMENT"
        if self.comment:
            comment = self.comment.splitlines()[0]

        date = "NO DATE"
        if self.date:
            date = format_date(self.date)

        return f"Manifest<{date}: {comment}; {len(self.files)} files>"

    @classmethod
    def fromblob(cls, blob: Blob):
        """Construct a manifest instance from a blob"""
        manifest = cls.fromtext(blob.text)
        manifest.uuid = blob.uuid
        return manifest

    def toblob(self, rcvid: int):
        """Make a blob from this manifest."""
        blob = Blob.create(self.build(), rcvid)
        self.uuid = blob.uuid
        return blob

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

                case "F":
                    filename, uuid, *rest = value.split(" ")
                    # TODO: Handle permissions, old_filename
                    manifest.files[filename] = Manifest.File(filename, Blob(uuid=uuid))

                case "P":
                    manifest.previous = [p for p in value.split(" ") if p]

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
        filename: os.PathLike[str],
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

    def make_delta(self):
        """Made a delta manifest based on this one"""
        raise NotImplementedError("TODO: Delta manifests")

    def make_update(
        self,
        *,
        comment: str | None = None,
        date: dt.datetime | None = None,
        mimetype: str | None = None,
        tags: list[tuple[str, str]] | None = None,
        user: str | None = None,
    ):
        """Create a new full manifest based on this one."""

        if self.uuid is None:
            raise RuntimeError(
                "Cannot make update, blob associated with this manifest is not known."
            )

        return Manifest(
            baseline=None,  # full manifests cannot have a baseline
            comment=comment,
            date=date,
            files=self.files,  # full manifests should specify every file
            mimetype=mimetype,
            previous=[self.uuid],
            rchecksum=None,  # checksum should be recalculated
            tags=tags or [],
            user=user,
            zchecksum=None,  # checksum should be recalculated
        )

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

        for _, file in sorted(self.files.items(), key=operator.itemgetter(0)):
            cards.append(str(file))

        if self.previous:
            cards.append(f"P {' '.join(self.previous)}")

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


@typing.final
@dataclasses.dataclass
class Rcvfrom:
    """Represents a row from the ``rcvfrom`` table.

    For lack of a better term I think this counts as a "transaction". Meaning an event
    that caused the db to be updated. If you clone a repo all blobs appear to be linked
    to rcvid=1. But as you make commits, each manifest (and related blobs) are linked
    to separate rcvid's.

    No, I don't fully understand this yet.
    """

    rcvid: int
    """The id"""

    uid: int
    """The user id."""

    mtime: dt.datetime | None = dataclasses.field(default=None, kw_only=True)
    """The time of the "transaction"."""

    nonce: str | None = dataclasses.field(default=None, kw_only=True)

    ipaddr: str | None = dataclasses.field(default=None, kw_only=True)
    """If the "transaction" came from a remote server, this records the server's ip."""

    @classmethod
    def fromdb(
        cls, rcvid: int, uid: int, mtime: str, nonce: str | None, ipaddr: str | None
    ):
        """Create an instance from a database row."""
        return cls(
            rcvid,
            uid,
            mtime=dt.datetime.fromisoformat(mtime),
            nonce=nonce,
            ipaddr=ipaddr,
        )

    @classmethod
    def create(cls, uid: int, mtime: dt.datetime | None = None):
        """Create a new record."""
        return cls(-1, uid, mtime=mtime)

    def insert(self, db: sqlite3.Connection):
        """Insert into the database."""
        cursor = db.execute(
            "INSERT INTO rcvfrom(uid,mtime,nonce,ipaddr) VALUES (?,?,?,?) "
            "RETURNING rcvid,uid,strftime('%FT%TZ', mtime, 'unixepoch'),nonce,ipaddr",
            (self.uid, self.mtime.timestamp(), self.nonce, self.ipaddr),
        )
        return Rcvfrom.fromdb(*cursor.fetchone())


@typing.final
@dataclasses.dataclass
class User:
    """Represents a row from the ``user`` table."""

    login: str
    """The user's login name."""

    uid: int | None = dataclasses.field(default=None, kw_only=True)

    pw: str | None = dataclasses.field(default=None, kw_only=True)

    cap: str | None = dataclasses.field(default=None, kw_only=True)

    cookie: str | None = dataclasses.field(default=None, kw_only=True)

    ipaddr: str | None = dataclasses.field(default=None, kw_only=True)

    cexpire: str | None = dataclasses.field(default=None, kw_only=True)

    info: str | None = dataclasses.field(default=None, kw_only=True)

    mtime: dt.datetime | None = dataclasses.field(default=None, kw_only=True)

    photo: bytes | None = dataclasses.field(default=None, kw_only=True)

    jx: str = dataclasses.field(default="", kw_only=True)

    @classmethod
    def fromdb(
        cls,
        uid: int,
        login: str,
        pw: str | None,
        cap: str | None,
        cookie: str | None,
        ipaddr: str | None,
        cexpire: str | None,
        info: str | None,
        mtime: str,
        photo: bytes | None,
        jx: str,
    ):
        return cls(
            login,
            uid=uid,
            pw=pw,
            cap=cap,
            cookie=cookie,
            ipaddr=ipaddr,
            cexpire=cexpire,
            info=info,
            mtime=dt.datetime.fromisoformat(mtime),
            photo=photo,
            jx=jx,
        )

    @classmethod
    def find(cls, db: sqlite3.Connection, login: str) -> User | None:
        """Lookup user record by login name."""
        cursor = db.execute(
            "SELECT uid,login,pw,cap,cookie,ipaddr,cexpire,info,"
            "strftime('%FT%TZ', mtime, 'unixepoch'),photo,jx from user WHERE login = ?",
            (login,),
        )
        if (row := cursor.fetchone()) is None:
            return None

        return cls.fromdb(*row)

    def insert(self, db: sqlite3.Connection | sqlite3.Cursor):
        cursor = db.execute(
            "INSERT INTO user(login,pw,cap,info,mtime) VALUES (?,?,?,?,?) "
            "RETURNING uid,login,pw,cap,cookie,ipaddr,cexpire,info,"
            "strftime('%FT%TZ', mtime, 'unixepoch'),photo,jx",
            (
                self.login,
                self.pw,
                self.cap,
                self.info,
                int(self.mtime.timestamp()) if self.mtime else None,
            ),
        )
        return User.fromdb(*cursor.fetchone())


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
