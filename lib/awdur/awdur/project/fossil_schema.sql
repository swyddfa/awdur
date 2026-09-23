-- Fossil database schema
--
-- Provides the schema for the main *.fossil project repo.
--
-- see: https://fossil-scm.org/home/file?&name=src%252Fschema.c

CREATE TABLE blob(
  rid INTEGER PRIMARY KEY,
  rcvid INTEGER,
  size INTEGER,
  uuid TEXT UNIQUE NOT NULL,
  content BLOB,
  CHECK( length(uuid)>=40 AND rid>0 )
);

CREATE TABLE delta(
  rid INTEGER PRIMARY KEY,
  srcid INTEGER NOT NULL REFERENCES blob
);
CREATE INDEX  delta_i1 ON delta(srcid);


CREATE TABLE rcvfrom(
  rcvid INTEGER PRIMARY KEY,
  uid INTEGER REFERENCES user,
  mtime DATETIME,
  nonce TEXT UNIQUE,
  ipaddr TEXT
);


CREATE TABLE config(
  name TEXT PRIMARY KEY NOT NULL,
  value CLOB,
  mtime DATE,
  CHECK( typeof(name)='text' AND length(name)>=1 )
) WITHOUT ROWID;

CREATE TABLE user(
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

CREATE TABLE shun(
  uuid TEXT PRIMARY KEY,
  mtime DATE,
  scom TEXT
) WITHOUT ROWID;


CREATE TABLE private(rid INTEGER PRIMARY KEY);


CREATE TABLE reportfmt(
   rn INTEGER PRIMARY KEY,
   owner TEXT,
   title TEXT UNIQUE,
   mtime DATE,
   cols TEXT,
   sqlcode TEXT,
   jx TEXT DEFAULT '{}'
);

CREATE TABLE concealed(
  hash TEXT PRIMARY KEY,
  mtime DATE,
  content TEXT
) WITHOUT ROWID;

-- The application ID helps the unix "file" command to identify the
-- database as a fossil repository.
--PRAGMA application_id=252006673;


-- Everything below this line is needed to be considered a valid
-- fossil project, but is can be derived from the above using
-- ``fossil rebuild`` and so we shouldn't ever have to touch it.

CREATE TABLE attachment(
  attachid INTEGER PRIMARY KEY,
  isLatest BOOLEAN DEFAULT 0,
  mtime TIMESTAMP,
  src TEXT,
  target TEXT,
  filename TEXT,
  comment TEXT,
  user TEXT
);
CREATE INDEX attachment_idx1 ON attachment(target, filename, mtime);
CREATE INDEX attachment_idx2 ON attachment(src);

CREATE TABLE backlink(
  target TEXT,
  srctype INT,
  srcid INT,
  mtime TIMESTAMP,
  UNIQUE(target, srctype, srcid)
);
CREATE INDEX backlink_src ON backlink(srcid, srctype);

CREATE TABLE cherrypick(
  parentid INT,
  childid INT,
  isExclude BOOLEAN DEFAULT false,
  PRIMARY KEY(parentid, childid)
) WITHOUT ROWID;
CREATE INDEX cherrypick_cid ON cherrypick(childid);

CREATE TABLE event(
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
CREATE INDEX event_i1 ON event(mtime);

CREATE TABLE filename(
  fnid INTEGER PRIMARY KEY,
  name TEXT UNIQUE
);

CREATE TABLE leaf(rid INTEGER PRIMARY KEY);

CREATE TABLE mlink(
  mid INTEGER,
  fid INTEGER,
  pmid INTEGER,
  pid INTEGER,
  fnid INTEGER REFERENCES filename,
  pfnid INTEGER,
  mperm INTEGER,
  isaux BOOLEAN DEFAULT 0
);
CREATE INDEX mlink_i1 ON mlink(mid);
CREATE INDEX mlink_i2 ON mlink(fnid);
CREATE INDEX mlink_i3 ON mlink(fid);
CREATE INDEX mlink_i4 ON mlink(pid);

CREATE TABLE orphan(
  rid INTEGER PRIMARY KEY,
  baseline INTEGER
);
CREATE INDEX orphan_baseline ON orphan(baseline);

CREATE TABLE phantom(
  rid INTEGER PRIMARY KEY
);

CREATE TABLE plink(
  pid INTEGER REFERENCES blob,
  cid INTEGER REFERENCES blob,
  isprim BOOLEAN,
  mtime DATETIME,
  baseid INTEGER REFERENCES blob,
  UNIQUE(pid, cid)
);
CREATE INDEX plink_i2 ON plink(cid,pid);

CREATE TABLE tag(
  tagid INTEGER PRIMARY KEY,
  tagname TEXT UNIQUE
);

CREATE TABLE tagxref(
  tagid INTEGER REFERENCES tag,
  tagtype INTEGER,
  srcid INTEGER REFERENCES blob,
  origid INTEGER REFERENCES blob,
  value TEXT,
  mtime TIMESTAMP,
  rid INTEGER REFERENCE blob,
  UNIQUE(rid, tagid)
);
CREATE INDEX tagxref_i1 ON tagxref(tagid, mtime);

CREATE TABLE ticket(
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

CREATE TABLE ticketchng(
  tkt_id INTEGER REFERENCES ticket,
  tkt_rid INTEGER REFERENCES blob,
  tkt_mtime DATE,
  tkt_user TEXT,
  login TEXT,
  username TEXT,
  mimetype TEXT,
  icomment TEXT
);
CREATE INDEX ticketchng_idx1 ON ticketchng(tkt_id, tkt_mtime);

CREATE TABLE unclustered(
  rid INTEGER PRIMARY KEY
);

CREATE TABLE unsent(
  rid INTEGER PRIMARY KEY
);

CREATE VIEW artifact(
  rid,
  rcvid,
  size,
  atype,
  srcid,
  hash,
  content
) AS SELECT blob.rid,rcvid,size,1,srcid,uuid,content
FROM blob LEFT JOIN delta ON (blob.rid=delta.rid);
