"""Export a project to a fossil source repo.

.. seealso::

   `src/schema.c <https://fossil-scm.org/home/file?name=src%2Fschema.c>`__
      The code defining the structure of the database

   `Fossil File Format <https://fossil-scm.org/home/doc/trunk/www/fileformat.wiki>`__
      Defines the structure of each of the main db records, manifest, tickets, etc.

   `Fossil is not Relational <https://fossil-scm.org/home/doc/trunk/www/fossil-is-not-relational.md>`__
      Notes on the overall data model.
"""

from __future__ import annotations

import hashlib
import pathlib
import sqlite3
import struct
import typing
import zlib
from datetime import datetime
from datetime import timezone

UTC = timezone.utc


if typing.TYPE_CHECKING:
    from .project import Project
    from .project import ProjectFile


SCHEMA = pathlib.Path(__file__).parent / "fossil_schema.sql"

ASCII_SPACE = chr(0x20)
ASCII_NL = chr(0x0A)
ASCII_BSLASH = chr(0x5C)

ESC_SPACE = chr(0x5C) + chr(0x73)
ESC_NL = chr(0x5C) + chr(0x6E)
ESC_BSLASH = 2 * ASCII_BSLASH


class FossilExporter:
    def export(self, project: Project, output: pathlib.Path):
        db = init_db(output)
        db.close()


def init_db(output: pathlib.Path):
    """Initialize the db ready for writing."""
    db = sqlite3.connect(output.with_suffix(".fossil"))
    _ = db.executescript(SCHEMA.read_text())

    # now = datetime.now(tz=UTC)
    now = datetime.fromisoformat("2026-09-06T19:47:21.579")
    mtime = int(now.timestamp())

    _ = db.executemany(
        "INSERT INTO config(name,value,mtime) VALUES (?,?,?)",
        [
            ("aux-schema", "2015-01-24", mtime),
            ("content-schema", "2", mtime),
            ("hash-policy", "2", mtime),
            # TODO: generate proper codes,
            ("project-code", "12", mtime),
            ("server-code", "34", mtime),
        ],
    )

    # Without some user accounts ``fossil ui`` will not show anything.
    username = "alex"
    users = {
        u.login: u.insert(db)
        for u in [
            # TODO: generate an admin account with default password
            User(username, pw="", cap="s", info=username, mtime=now),
            User("anonymous", pw="", cap="hz", info="Anon", mtime=now),
            User("nobody", pw="", cap="gjorz", info="Noobdy", mtime=now),
            User("developer", pw="", cap="ei", info="Dev", mtime=now),
            User("reader", pw="", cap="kptw", info="Reader", mtime=now),
        ]
    }
    user = users[username]

    # Write the blob containing the initial check-in
    manifest = Manifest(comment="initial empty check-in", date=now, user=user.login)
    manifest.add_tag("branch", "trunk")
    manifest.add_tag("sym-trunk")

    blob = Blob.create(manifest.build())
    blob = blob.insert(db)

    # Update rcvfrom
    _ = db.execute(
        "INSERT INTO rcvfrom(rcvid,uid,mtime) VALUES (?,?,julianday(?, 'unixepoch'))",
        (1, user.uid, mtime),
    )

    db.commit()
    return db


@typing.final
class Manifest:
    """Responsible for building the manifest entry for a check-in."""

    def __init__(self, comment: str, date: datetime, user: str):
        self.comment = comment
        self.date = date
        self.repo_checksum = hashlib.md5()
        self.tags: list[tuple[str, str]] = []
        self.user = user

    def add_tag(self, name: str, value: str = ""):
        self.tags.append((name, value))

    def build(self) -> str:
        """Close the manifest by appending the ``Z`` checksum card and return it."""
        cards: list[str] = [
            f"C {escape_text(self.comment)}",
            f"D {format_date(self.date)}",
        ]

        # TODO: Include files...

        cards.append(f"R {self.repo_checksum.hexdigest()}")

        for name, value in self.tags:
            # '*' refers to 'self' i.e. this manifest, see file format spec  for details.
            cards.append(f"T *{name} * {value}".strip())

        cards.append(f"U {self.user}")

        record = "\n".join(cards) + "\n"
        checksum = hashlib.md5(record.encode()).hexdigest()
        l = record + f"Z {checksum}\n"
        print(l)
        return l


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

    def __repr__(self):
        return f"Blob<{self.uuid}; {self.size} bytes>"

    @classmethod
    def fromdb(cls, rid: int, rcvid: int, size: int, uuid: str, content: bytes):
        return cls(rid, rcvid, size, uuid, content)

    def insert(self, db: sqlite3.Connection | sqlite3.Cursor):
        """Insert this record into the db."""
        cursor = db.execute(
            "INSERT INTO blob(rcvid, size, uuid, content) VALUES (?,?,?,?) RETURNING *",
            (self.rcvid, self.size, self.uuid, self.content),
        )
        return Blob.fromdb(*cursor.fetchone())

    @classmethod
    def create(cls, content: str):
        """Create a new blob record."""
        bcontent = content.encode()
        uuid = hashlib.sha3_256(bcontent).hexdigest()

        data = zlib.compress(bcontent)
        size = len(bcontent)
        header = struct.pack(">I", size)

        # Not entirely sure what this should be... I have a feeling it's related
        # to syncing, so *should* be ok to set to 1 for now.
        rcvid = 1

        return cls(None, rcvid, size, uuid, header + data)


@typing.final
class User:
    """Represents a row from the ``user`` table."""

    def __init__(
        self,
        login: str,
        *,
        uid: int | None = None,
        pw: str | None = None,
        cap: str | None,
        cookie: str | None = None,
        ipaddr: str | None = None,
        cexpire: str | None = None,
        info: str | None = None,
        mtime: datetime | None = None,
        photo: bytes | None = None,
        jx: str = "",
    ):
        self.login = login
        self.uid = uid
        self.pw = pw
        self.cap = cap
        self.cookie = cookie
        self.ipaddr = ipaddr
        self.cexpire = cexpire
        self.info = info
        self.mtime = mtime
        self.photo = photo
        self.jx = jx

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
            mtime=datetime.fromisoformat(mtime),
            photo=photo,
            jx=jx,
        )

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
