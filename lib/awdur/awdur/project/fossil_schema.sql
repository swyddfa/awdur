-- Fossil database schema
--
-- Provides the schema for the main *.fossil project repo.
--
-- see: https://fossil-scm.org/home/file?&name=src%252Fschema.c

CREATE TABLE IF NOT EXISTS blob(
  rid INTEGER PRIMARY KEY,
  rcvid INTEGER,
  size INTEGER,
  uuid TEXT UNIQUE NOT NULL,
  content BLOB,
  CHECK( length(uuid)>=40 AND rid>0 )
);

CREATE TABLE IF NOT EXISTS delta(
  rid INTEGER PRIMARY KEY,
  srcid INTEGER NOT NULL REFERENCES blob
);
CREATE INDEX IF NOT EXISTS delta_i1 ON delta(srcid);


CREATE TABLE IF NOT EXISTS rcvfrom(
  rcvid INTEGER PRIMARY KEY,
  uid INTEGER REFERENCES user,
  mtime DATETIME,
  nonce TEXT UNIQUE,
  ipaddr TEXT
);


CREATE TABLE IF NOT EXISTS config(
  name TEXT PRIMARY KEY NOT NULL,
  value CLOB,
  mtime DATE,
  CHECK( typeof(name)='text' AND length(name)>=1 )
) WITHOUT ROWID;

CREATE TABLE IF NOT EXISTS user(
  uid INTEGER PRIMARY KEY,
  login TEXT UNIQUE,
  pw TEXT,
  cap TEXT,
  cookie TEXT,
  ipaddr TEXT,
  cexpire DATETIME,
  info TEXT,
  mtime DATE,
  photo BLOB,
  jx TEXT DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS shun(
  uuid TEXT PRIMARY KEY,
  mtime DATE,
  scom TEXT
) WITHOUT ROWID;


CREATE TABLE IF NOT EXISTS private(rid INTEGER PRIMARY KEY);


CREATE TABLE IF NOT EXISTS reportfmt(
   rn INTEGER PRIMARY KEY,
   owner TEXT,
   title TEXT UNIQUE,
   mtime DATE,
   cols TEXT,
   sqlcode TEXT,
   jx TEXT DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS concealed(
  hash TEXT PRIMARY KEY,
  mtime DATE,
  content TEXT
) WITHOUT ROWID;

-- The application ID helps the unix "file" command to identify the
-- database as a fossil repository.
--PRAGMA application_id=252006673;


-- Everything below this line is needed to be considered a valid
-- fossil project, but is can be derived from the above using
-- ``fossil rebuild`` and so shouldn't ever have to touch it.

CREATE TABLE IF NOT EXISTS attachment(
  attachid INTEGER PRIMARY KEY,
  isLatest BOOLEAN DEFAULT 0,
  mtime TIMESTAMP,
  src TEXT,
  target TEXT,
  filename TEXT,
  comment TEXT,
  user TEXT
);
CREATE INDEX IF NOT EXISTS attachment_idx1 ON attachment(target, filename, mtime);
CREATE INDEX IF NOT EXISTS attachment_idx2 ON attachment(src);

CREATE TABLE IF NOT EXISTS backlink(
  target TEXT,
  srctype INT,
  srcid INT,
  mtime TIMESTAMP,
  UNIQUE(target, srctype, srcid)
);
CREATE INDEX IF NOT EXISTS backlink_src ON backlink(srcid, srctype);

CREATE TABLE IF NOT EXISTS cherrypick(
  parentid INT,
  childid INT,
  isExclude BOOLEAN DEFAULT false,
  PRIMARY KEY(parentid, childid)
) WITHOUT ROWID;
CREATE INDEX IF NOT EXISTS cherrypick_cid ON cherrypick(childid);

CREATE TABLE IF NOT EXISTS event(
  type TEXT,
  mtime DATETIME,
  objid INTEGER PRIMARY KEY,
  tagid INTEGER,
  uid INTEGER REFERENCES user,
  bgcolor TEXT,
  euser TEXT,
  user TEXT,
  ecomment TEXT,
  comment TEXT,
  brief TEXT,
  omtime DATETIME
);
CREATE INDEX IF NOT EXISTS event_i1 ON event(mtime);

CREATE TABLE IF NOT EXISTS filename(
  fnid INTEGER PRIMARY KEY,
  name TEXT UNIQUE
);

CREATE TABLE IF NOT EXISTS leaf(rid INTEGER PRIMARY KEY);

CREATE TABLE IF NOT EXISTS mlink(
  mid INTEGER,
  fid INTEGER,
  pmid INTEGER,
  pid INTEGER,
  fnid INTEGER REFERENCES filename,
  pfnid INTEGER,
  mperm INTEGER,
  isaux BOOLEAN DEFAULT 0
);
CREATE INDEX IF NOT EXISTS mlink_i1 ON mlink(mid);
CREATE INDEX IF NOT EXISTS mlink_i2 ON mlink(fnid);
CREATE INDEX IF NOT EXISTS mlink_i3 ON mlink(fid);
CREATE INDEX IF NOT EXISTS mlink_i4 ON mlink(pid);

CREATE TABLE IF NOT EXISTS orphan(
  rid INTEGER PRIMARY KEY,
  baseline INTEGER
);
CREATE INDEX IF NOT EXISTS orphan_baseline ON orphan(baseline);

CREATE TABLE IF NOT EXISTS phantom(
  rid INTEGER PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS plink(
  pid INTEGER REFERENCES blob,
  cid INTEGER REFERENCES blob,
  isprim BOOLEAN,
  mtime DATETIME,
  baseid INTEGER REFERENCES blob,
  UNIQUE(pid, cid)
);
CREATE INDEX IF NOT EXISTS plink_i2 ON plink(cid,pid);

CREATE TABLE IF NOT EXISTS tag(
  tagid INTEGER PRIMARY KEY,
  tagname TEXT UNIQUE
);

CREATE TABLE IF NOT EXISTS tagxref(
  tagid INTEGER REFERENCES tag,
  tagtype INTEGER,
  srcid INTEGER REFERENCES blob,
  origid INTEGER REFERENCES blob,
  value TEXT,
  mtime TIMESTAMP,
  rid INTEGER REFERENCE blob,
  UNIQUE(rid, tagid)
);
CREATE INDEX IF NOT EXISTS tagxref_i1 ON tagxref(tagid, mtime);

CREATE TABLE IF NOT EXISTS ticket(
  tkt_id INTEGER PRIMARY KEY,
  tkt_uuid TEXT UNIQUE,
  tkt_mtime DATE,
  tkt_ctime DATE,
  type TEXT,
  status TEXT,
  subsystem TEXT,
  priority TEXT,
  severity TEXT,
  foundin TEXT,
  private_contact TEXT,
  resolution TEXT,
  title TEXT,
  comment TEXT
);

CREATE TABLE IF NOT EXISTS ticketchng(
  tkt_id INTEGER REFERENCES ticket,
  tkt_rid INTEGER REFERENCES blob,
  tkt_mtime DATE,
  tkt_user TEXT,
  login TEXT,
  username TEXT,
  mimetype TEXT,
  icomment TEXT
);
CREATE INDEX IF NOT EXISTS ticketchng_idx1 ON ticketchng(tkt_id, tkt_mtime);

CREATE TABLE IF NOT EXISTS unclustered(
  rid INTEGER PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS unsent(
  rid INTEGER PRIMARY KEY
);

CREATE VIEW IF NOT EXISTS artifact(
  rid,
  rcvid,
  size,
  atype,
  srcid,
  hash,
  content
) AS SELECT blob.rid,rcvid,size,1,srcid,uuid,content
FROM blob LEFT JOIN delta ON (blob.rid=delta.rid);
