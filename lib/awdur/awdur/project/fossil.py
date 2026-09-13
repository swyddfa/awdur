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
import logging
import operator
import os
import pathlib
import sqlite3
import struct
import subprocess
import textwrap
import typing
import zlib
from datetime import datetime
from datetime import timezone

from jinja2 import Environment
from jinja2 import Template

UTC = timezone.utc


if typing.TYPE_CHECKING:
    from .manager import Project
    from .manager import ProjectFile


SCHEMA = pathlib.Path(__file__).parent / "fossil_schema.sql"

ASCII_SPACE = chr(0x20)
ASCII_NL = chr(0x0A)
ASCII_BSLASH = chr(0x5C)

ESC_SPACE = chr(0x5C) + chr(0x73)
ESC_NL = chr(0x5C) + chr(0x6E)
ESC_BSLASH = 2 * ASCII_BSLASH


class FossilExporter:
    def __init__(self, logger: logging.Logger | None = None):
        self.logger = logger or logging.getLogger(__name__)
        self.username = "awdur"
        self.users = {}

    def export(self, project: Project, output: pathlib.Path):
        dbpath = output.with_suffix(".fossil")
        if dbpath.exists():
            raise RuntimeError(
                f"File {str(dbpath)!r} already exists and incremental exports are not "
                "supported please delete the existing file or choose another filepath"
            )

        self.logger.info("Initialising database...")
        db, checkin = self.init_db(dbpath)

        self.logger.info("Writing artifacts...")
        env = Environment(loader=project.templates)

        now = datetime.now(tz=UTC)
        user = self.users[self.username]
        manifest = Manifest(
            comment=f"Export files from {project.name}",
            date=now,
            user=user.login,
            previous=[checkin],
            logger=self.logger,
        )
        rcvid = 2

        # Update rcvfrom
        _ = db.execute(
            "INSERT INTO rcvfrom(rcvid,uid,mtime) VALUES (?,?,julianday(?, 'unixepoch'))",
            (rcvid, user.uid, now.timestamp()),
        )

        for filename, file in project.iter_files():
            content = self.render_file(env, filename, file)
            blob = Blob.create(content, rcvid).insert(db)
            self.logger.debug("Blob: %s %s %s bytes", blob.uuid, filename, blob.size)
            manifest.add_file(filename, blob)

        blob = Blob.create(manifest.build(), rcvid).insert(db)
        db.commit()
        db.close()

        # The majority of the fossil db can be derived from the sequence of artifacts.
        # Rather than attempt to keep up with implementation details of the tool, just
        # run the command provided for this purpose
        self.logger.info("Rebuilding metadata...")
        result = subprocess.run(
            ["fossil", "rebuild", "--stats", str(dbpath)], capture_output=True
        )
        if result.returncode == 0:
            self.logger.info(result.stdout.decode("utf8"))

    def init_db(self, dbpath: pathlib.Path) -> tuple[sqlite3.Connection, Blob]:
        """Initialize the db ready for writing.

        Also creates an empty first commit on which the rest of the history can be
        linked to.
        """
        db = sqlite3.connect(dbpath)
        _ = db.executescript(SCHEMA.read_text())

        now = datetime.now(tz=UTC)
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
        self.users = {
            u.login: u.insert(db)
            for u in [
                # TODO: generate an admin account with default password
                User(self.username, pw="", cap="s", info=self.username, mtime=now),
                User("anonymous", pw="", cap="hz", info="Anon", mtime=now),
                User("nobody", pw="", cap="gjorz", info="Noobdy", mtime=now),
                User("developer", pw="", cap="ei", info="Dev", mtime=now),
                User("reader", pw="", cap="kptw", info="Reader", mtime=now),
            ]
        }
        user = self.users[self.username]

        # Write the blob containing the initial check-in
        manifest = Manifest(
            comment="Initialize project",
            date=now,
            user=user.login,
            logger=self.logger,
        )
        manifest.add_tag("branch", "trunk")
        manifest.add_tag("sym-trunk")

        rcvid = 1
        blob = Blob.create(manifest.build(), rcvid)
        blob = blob.insert(db)

        # Update rcvfrom
        _ = db.execute(
            "INSERT INTO rcvfrom(rcvid,uid,mtime) VALUES (?,?,julianday(?, 'unixepoch'))",
            (1, user.uid, mtime),
        )

        db.commit()
        return db, blob

    def render_file(
        self, env: Environment, filename: pathlib.Path, file: ProjectFile
    ) -> str:
        """Render a file to plain text"""
        context = {
            "output": {"path": filename},
            "slots": file.slots,
        }

        def insert(lines: list[str], indent: int | str | None = None) -> str:
            """Insert code into the file."""
            code = "\n\n".join(lines)

            # Treat the code as a template so we can expand nested substiutions
            # - is this a horrible idea??
            t = Template(code)
            code = t.render(**context, insert=insert)

            # Handle indentation
            if isinstance(indent, int):
                indent = indent * " "

            if indent:
                code = textwrap.indent(code, indent)

            return code

        template = env.get_template(file.template)
        return template.render(**context, insert=insert)


@typing.final
class Manifest:
    """Responsible for building the manifest entry for a check-in."""

    def __init__(
        self,
        comment: str,
        date: datetime,
        user: str,
        previous: list[Blob] | None = None,
        logger: logging.Logger | None = None,
    ):
        self.comment = comment
        self.date = date
        self.files: list[tuple[str, Blob]] = []
        self.previous = previous or []
        self.repo_checksum = hashlib.md5()
        self.tags: list[tuple[str, str]] = []
        self.user = user

        self.logger = logger or logging.getLogger(__name__)

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

        self.logger.debug("Check-in:\n%s", record)
        return record


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
        """Insert this record into the db."""
        cursor = db.execute(
            "INSERT INTO blob(rcvid, size, uuid, content) VALUES (?,?,?,?) RETURNING *",
            (self.rcvid, self.size, self.uuid, self.content),
        )
        return Blob.fromdb(*cursor.fetchone())

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
