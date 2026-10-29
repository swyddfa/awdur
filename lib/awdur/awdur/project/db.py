"""Database types common to fossil and awdur."""

from __future__ import annotations

import dataclasses
import datetime as dt
import enum
import hashlib
import itertools
import logging
import operator
import os
import pathlib
import struct
import typing
import zlib
from re import escape

if typing.TYPE_CHECKING:
    import sqlite3
    from collections.abc import Generator
    from typing import Literal

    FilePermissions = Literal["w", "x", "l"]
    FileStatus = Literal["created", "updated", "unchanged"]
    TagType = Literal["+", "*", "-"]


class ASCII(enum.IntEnum):
    """Names for 'interesting' ascii character values used in fossil's data formats."""

    NEWLINE = 0x0A
    SPACE = 0x20
    COMMA = 0x2C
    COLON = 0x3A
    SEMICOLON = 0x3B
    AT = 0x40
    BACKSLASH = 0x5C

    N = 0x6E
    S = 0x73

    @staticmethod
    def escape(v: ASCII) -> str:
        """Escape the given ascii character"""
        match v:
            case ASCII.SPACE:
                v = ASCII.S
            case ASCII.NEWLINE:
                v = ASCII.N
            case ASCII.BACKSLASH:
                v = v
            case _:
                raise ValueError(f"Unable to escape character: {v!r}")

        return chr(ASCII.BACKSLASH) + chr(v)


UTC = dt.timezone.utc


@typing.final
@dataclasses.dataclass
class Artifact:
    """Represents an item from the ``artifact`` view."""

    rid: int | None = dataclasses.field(default=None)
    """The artifact's row id"""

    rcvid: int | None = dataclasses.field(default=None)
    """The rcvid."""

    size: int | None = dataclasses.field(default=None)
    """The size of the uncompressed artifact"""

    atype: int | None = dataclasses.field(default=None)
    """The type of artifact (currently always 1)"""

    srcid: int | None = dataclasses.field(default=None)
    """If this is a delta artifact, this stores the base blob's rid."""

    uuid: str | None = dataclasses.field(default=None)
    """The artifact's hash"""

    content: bytes | None = dataclasses.field(default=None)
    """The content itself."""

    _text: str | None = dataclasses.field(default=None, init=False)
    """Internal cache of the uncompressed text of the blob, if known"""

    def __repr__(self):
        return f"Artifact<{self.uuid}; {self.size} bytes>"

    @classmethod
    def find(
        cls, db: sqlite3.Connection, *, rid: int | None = None, uuid: str | None = None
    ):
        """Find an artifact given its rid or uuid, if artifact is a delta, the delta
        will be automatically applied."""

        if rid is not None:
            query = "SELECT * FROM artifact WHERE rid = ?"
            params = (rid,)

        elif uuid is not None:
            query = "SELECT * FROM artifact WHERE hash = ?"
            params = (uuid,)

        else:
            raise ValueError("Either rid or uuid must be provided")

        cursor = db.execute(query, params)
        if (row := cursor.fetchone()) is None:
            return None

        artifact = cls.fromdb(*row)

        # Is this a delta blob?
        if (srcid := artifact.srcid) is not None:
            if (baseline := Blob.find(db, rid=srcid)) is None:
                raise ValueError(
                    f"Unable to resolve artifact, baseline blob rid={artifact.srcid} not found"
                )

            base_blob = zlib.decompress(baseline.content[4:])
            delta_blob = zlib.decompress(artifact.content[4:])
            artifact.content = apply_delta(base_blob, delta_blob)

        else:
            artifact.content = zlib.decompress(artifact.content[4:])

        return artifact

    @classmethod
    def fromdb(
        cls,
        rid: int,
        rcvid: int,
        size: int,
        atype: int,
        srcid: int | None,
        uuid: str,
        content: bytes,
    ):
        return cls(rid, rcvid, size, atype, srcid, uuid, content)

    @property
    def text(self) -> str:
        """Return the uncompressed text held in a blob."""
        if self._text is not None:
            return self._text

        if self.content is None:
            return ""

        self._text = self.content.decode("utf8")
        return self._text


@typing.final
@dataclasses.dataclass(repr=False)
class Blob:
    """Represents a record from the ``blob`` table."""

    rid: int = dataclasses.field(default=-1)
    """The blob's row id"""

    rcvid: int = dataclasses.field(default=-1)
    """The rcvid."""

    size: int = dataclasses.field(default=0)
    """The size of the uncompressed blob"""

    uuid: str = dataclasses.field(default="")
    """The blob's hash"""

    content: bytes = dataclasses.field(default=b"")
    """The content itself."""

    _text: str = dataclasses.field(default="", init=False)
    """Internal cache of the uncompressed text of the blob, if known"""

    def __repr__(self):
        return f"Blob<{self.uuid}; {self.size} bytes>"

    @classmethod
    def find(
        cls, db: sqlite3.Connection, *, rid: int | None = None, uuid: str | None = None
    ):
        """Find a blob given its rid or uuid"""

        if rid is not None:
            query = "SELECT * FROM blob WHERE rid = ?"
            params = (rid,)

        elif uuid is not None:
            query = "SELECT * FROM blob WHERE uuid = ?"
            params = (uuid,)

        else:
            raise ValueError("Either rid or uuid must be provided")

        cursor = db.execute(query, params)
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

        blob = cls(-1, rcvid, size, uuid, header + data)
        blob._text = content

        return blob

    @property
    def text(self) -> str:
        """Return the uncompressed text held in a blob."""
        if self._text != "":
            return self._text

        if self.content == b"":
            return ""

        self._text = zlib.decompress(self.content[4:]).decode("utf8")
        return self._text


@typing.final
@dataclasses.dataclass
class Config:
    """Represents a record in the ``config`` table."""

    name: str
    value: str
    mtime: dt.datetime = dataclasses.field(
        default_factory=lambda: dt.datetime.now(tz=UTC), repr=False
    )

    @classmethod
    def fromdb(cls, name: str, value: str, mtime: int):
        return cls(name, value, dt.datetime.fromtimestamp(mtime))

    def insert(self, db: sqlite3.Connection):
        cursor = db.execute(
            "INSERT INTO config(name,value,mtime) VALUES (?,?,?) RETURNING *",
            (self.name, self.value, int(self.mtime.timestamp())),
        )
        return Config.fromdb(*cursor.fetchone())


@typing.final
class Event:
    """Represents a record the ``event`` table."""

    def __init__(
        self, type: str, mtime: dt.datetime, objid: int, uid: str, comment: str
    ):
        self.type = type
        self.mtime = mtime
        self.objid = objid
        self.uid = uid
        self.comment = comment

    def __repr__(self):
        return f"Event<{self.uid}({self.type}); {self.comment}>"

    @classmethod
    def fromdb(cls, type: str, mtime: float, objid: int, uid: str, comment: str):
        return cls(type, dt.datetime.fromtimestamp(mtime), objid, uid, comment)

    @classmethod
    def find_latest(cls, db: sqlite3.Connection):
        """Find the latest event, or return None."""
        cursor = db.execute(
            "SELECT type, mtime, objid, uid, comment FROM event ORDER BY mtime DESC LIMIT 1"
        )
        if (row := cursor.fetchone()) is None:
            return None

        return cls.fromdb(*row)

    def insert(self, db: sqlite3.Connection | sqlite3.Cursor):
        """Insert this record into the given db."""
        cursor = db.execute(
            "INSERT INTO event(type, mtime, objid, uid, comment) VALUES (?,?,?,?,?) "
            "RETURNING type, mtime, objid, uid, comment",
            (self.type, self.mtime.timestamp(), self.objid, self.uid, self.comment),
        )
        event = Event.fromdb(*cursor.fetchone())
        return event


@dataclasses.dataclass(repr=False)
class Manifest:
    """Represents a manifest entry corresponding with a check-in."""

    @typing.final
    @dataclasses.dataclass
    class File:
        """Represents an F card in a manifest."""

        filename: str
        """The filepath of the file, relative to the repo root."""

        blob: str
        """The blob holding the file's contents"""

        permissions: FilePermissions = dataclasses.field(default="w", kw_only=True)
        """The permissions to assign the file."""

        old_filename: str | None = dataclasses.field(default=None, kw_only=True)
        """If the file was renamed, this is the previous name."""

        def __str__(self):
            parts = ["F", self.filename, self.blob]

            if self.permissions:
                parts.append(self.permissions)

            if self.old_filename:
                parts.append(self.old_filename)

            return " ".join(parts)

    baseline: Blob | None = dataclasses.field(default=None, kw_only=True)
    """The baseline manifest, only used for delta manifests."""

    comment: str = dataclasses.field(default="", kw_only=True)
    """The check-in comment."""

    date: dt.datetime | None = dataclasses.field(default=None, kw_only=True)
    """The check-in date."""

    files: dict[str, File] = dataclasses.field(default_factory=dict, kw_only=True)
    """The files included in the check-in"""

    mimetype: str | None = dataclasses.field(default=None, kw_only=True)
    """Mime type of the check-in comment"""

    previous: str | None = dataclasses.field(default=None, kw_only=True)
    """The previous manifest this one supercedes."""

    rchecksum: str | None = dataclasses.field(default=None, kw_only=True)
    """Checksum of all files included in check-in"""

    tags: list[Tag] = dataclasses.field(default_factory=list, kw_only=True)
    """Tags."""

    user: str = dataclasses.field(default="", kw_only=True)
    """The user who made the check-in"""

    zchecksum: str | None = dataclasses.field(default=None)
    """Checksum of the manifest record itself."""

    def __repr__(self) -> str:
        date = "NO DATE"
        if self.date:
            date = format_date(self.date)

        return f"Manifest<{date}: {self.comment}; {len(self.files)} files>"

    @classmethod
    def fromblob(cls, blob: Artifact | Blob):
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

                case "F":
                    filename, uuid, *rest = value.split(" ")
                    # TODO: Handle permissions, old_filename
                    manifest.files[filename] = Manifest.File(filename, uuid)

                case "P":
                    manifest.previous = value

                case "R":
                    manifest.rchecksum = value

                case "T":
                    manifest.add_tag(Tag.fromstring(line))

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
        blob: str,
        permissions: FilePermissions,
        old_filename: pathlib.Path | None = None,
    ) -> tuple[Manifest.File, FileStatus]:
        """Add a file to the manifest

        Parameters
        ----------
        filename
           The file's path relative to the root of the repo.

        blob
           The content's uuid

        permissions
           The file's permissions

        old_filename
           If the file was renamed, the previous name for the file.

        Returns
        -------
        Manifest.File, FileStatus
           The file's manifest record and a string indicating if the file is new, changed
           relative to the previous version or unchanged.
        """
        fname = escape_filename(filename)
        old_fname = None

        if old_filename:
            old_fname = escape_filename(old_filename)

        pending_file = Manifest.File(
            fname, blob, permissions=permissions, old_filename=old_fname
        )

        if (existing_file := self.files.get(fname)) is not None:
            if existing_file == pending_file:
                return existing_file, "unchanged"
            else:
                self.files[fname] = pending_file
                return pending_file, "updated"
        else:
            self.files[fname] = pending_file
            return pending_file, "created"

    def get_file(self, filename: os.PathLike[str]) -> Manifest.File | None:
        """Return the record for the given file if it exists, taking into account any
        escape sequences."""
        return self.files.get(escape_filename(filename))

    def find_files(
        self, *, prefix: str | None = None, contains: str | None = None
    ) -> Generator[Manifest.File, None, None]:
        """Find files that match the given criteria.

        Parameters
        ----------
        prefix
           Return files with a filepath matching the given prefix.

        contains
           Return files with a filepath containing the given value.

        Returns
        -------
        Generator[Manifest.File, None, None]
           A generator yielding matching entries
        """
        if prefix is not None:
            prefix = escape_filename(pathlib.Path(prefix))

        for fpath, file in self.files.items():
            if prefix is not None and not fpath.startswith(prefix):
                continue

            if contains is not None and contains not in fpath:
                continue

            yield file

    def delete_file(self, filename: os.PathLike[str]):
        """Delete the given file from the manifest."""
        if (fpath := escape_filename(filename)) in self.files:
            del self.files[fpath]

    def add_tag(self, tag: Tag):
        """Add a tag to the manifest."""
        self.tags.append(tag)

    def build(self) -> str:
        """Close the manifest by appending the ``Z`` checksum card and return it."""

        cards: list[str] = [
            f"C {escape_text(self.comment)}",
            f"D {format_date(self.date)}",
        ]

        for _, file in sorted(self.files.items(), key=operator.itemgetter(0)):
            cards.append(str(file))

        if self.previous:
            cards.append(f"P {self.previous}")

        # The rchecksum is optional
        if self.rchecksum is not None:
            cards.append(f"R {self.rchecksum}")

        tags = sorted([str(t) for t in self.tags])
        cards.extend(tags)

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
            "INSERT INTO rcvfrom(uid,mtime,nonce,ipaddr) "
            "VALUES (?,julianday(?, 'unixepoch'),?,?) "
            "RETURNING rcvid,uid,strftime('%FT%TZ', mtime, 'unixepoch'),nonce,ipaddr",
            (self.uid, self.mtime.timestamp(), self.nonce, self.ipaddr),
        )
        return Rcvfrom.fromdb(*cursor.fetchone())


@typing.final
@dataclasses.dataclass
class Tag:
    """Represents a ``T`` card."""

    type: TagType
    """Indicates the propogation rules for the tag.

    - ``+``: One time application to the target artifact.
    - ``-``: Remove a one time tag, or cancel a propagating tag.
    - ``*``: Apply to the target artifact and all its children.
    """

    name: str
    """The tag's name"""

    uuid: str
    """The uuid of the artifact the tag should apply to. When used within a manifest,
    ``*`` should be used."""

    value: str | None = dataclasses.field(default=None)
    """The value in the case of a property, e.g. branch=value"""

    def __str__(self):
        tag = f"T {self.type}{self.name} {self.uuid}"
        if self.value:
            tag += f" {self.value}"
        return tag

    @classmethod
    def fromstring(cls, tag: str):
        t, name, target, *value = tag.split(" ")
        if t != "T":
            raise ValueError(f"String does not represent a tag: {tag!r}")

        type_, name = name[0], name[1:]
        if type_ not in {"*", "+", "-"}:
            raise ValueError(f"Invalid tag type: {type_!r}")

        if (N := len(value)) == 0:
            v = None
        elif N == 1:
            v = value[0]
        else:
            raise ValueError(f"Extra elements in tag card: {value[1:]}")

        return cls(type_, name, target, v)


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

    if chr(ASCII.NEWLINE) in filename or chr(ASCII.BACKSLASH) in filename:
        raise ValueError(
            f"Invalid path: {filename!r}, newlines and backslashes are not permitted"
        )

    return filename.replace(chr(ASCII.SPACE), ASCII.escape(ASCII.SPACE))


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
        text.replace(chr(ASCII.BACKSLASH), ASCII.escape(ASCII.BACKSLASH))
        .replace(chr(ASCII.SPACE), ASCII.escape(ASCII.SPACE))
        .replace(chr(ASCII.NEWLINE), ASCII.escape(ASCII.NEWLINE))
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
        text.replace(ASCII.escape(ASCII.BACKSLASH), chr(ASCII.BACKSLASH))
        .replace(ASCII.escape(ASCII.SPACE), chr(ASCII.SPACE))
        .replace(ASCII.escape(ASCII.NEWLINE), chr(ASCII.NEWLINE))
    )


def format_date(datetime: dt.datetime) -> str:
    """Format a datetime for inclusion in a fossil record.

    .. pull-quote::

       The sole argument to the D card is a date-time stamp in the ISO8601 format.

       The date and time should be in coordinated universal time (UTC).
       The format one of:

       - YYYY-MM-DDTHH:MM:SS
       - YYYY-MM-DDTHH:MM:SS.SSS
    """
    return datetime.isoformat("T", "milliseconds").replace("+00:00", "")


def apply_delta(
    baseline: bytes, delta: bytes, logger: logging.Logger | None = None
) -> bytes:
    """Apply the given fossil delta to the given baseline

    see: https://fossil-scm.org/home/doc/trunk/www/delta_format.wiki
    """
    logger = logger or logging.getLogger(__name__)

    point = delta.find(ASCII.NEWLINE)
    header, delta = delta[:point], delta[point + 1 :]
    target_length = b64_decode(header)
    logger.debug("header: %r, target: %s bytes", header, target_length)

    chunks: list[bytes] = []
    buffer: list[int] = []

    # Borrow mark and point terminology from Emacs
    point = 0
    checksum = None

    while point < len(delta):
        match b := delta[point]:
            case ASCII.COLON:
                length = b64_decode(buffer)
                buffer.clear()

                literal = delta[point + 1 : point + length + 1]
                logger.debug("literal: %r bytes, %r ", length, literal)

                chunks.append(literal)
                buffer.clear()
                point += length + 1

            case ASCII.AT:
                length = b64_decode(buffer)
                buffer.clear()

                mark = point + 1
                point = mark + delta[mark:].index(ASCII.COMMA)
                offset = b64_decode(delta[mark:point])
                logger.debug("range: %r bytes, %r offset", length, offset)

                chunks.append(baseline[offset : offset + length])
                point += 1

            case ASCII.SEMICOLON:
                if point != len(delta) - 1:
                    raise ValueError(
                        "Failed to apply delta, trailer found before end of blob"
                    )

                checksum = b64_decode(buffer)
                buffer.clear()
                point += 1

            case _:
                point += 1
                buffer.append(b)

    # Validate the blob
    if checksum is None:
        raise ValueError("Failed to apply delta, incomplete payload")

    content = b"".join(chunks)
    if checksum != (actual := delta_checksum(content)):
        raise ValueError(
            f"Failed to apply delta, checksum mismatch: {checksum} != {actual}"
        )
    return content


B64 = b"0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ_abcdefghijklmnopqrstuvwxyz~"
TOP_BIT = 1 << 31


def b64_decode(value: list[int] | bytes, signed: bool = False) -> int:
    """Decode a base64 encoded 32bit int."""
    v = 0
    for shift, b in enumerate(reversed(value)):
        v += B64.index(b) << (shift * 6)

    # Negative numbers will have the top-bit set
    if signed and (v & TOP_BIT) == TOP_BIT:
        v -= 1 << 32

    return v


def delta_checksum(content: bytes) -> int:
    """Calculate the "delta checksum" of the given blob"""
    value = 0

    if (rem := len(content) % 4) != 0:
        content = b"".join([content, b"\x00" * (4 - rem)])

    for b1, b2, b3, b4 in itertools.batched(content, n=4, strict=True):
        value += (b1 << 24) + (b2 << 16) + (b3 << 8) + b4

    return value & 0xFFFFFFFF
