-- Fossil database schema:

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

CREATE TABLE backlink(
  target TEXT,
  srctype INT,
  srcid INT,
  mtime TIMESTAMP,
  UNIQUE(target, srctype, srcid)
);

CREATE TABLE blob(
  rid INTEGER PRIMARY KEY,
  rcvid INTEGER,
  size INTEGER,
  uuid TEXT UNIQUE NOT NULL,
  content BLOB,
  CHECK( length(uuid)>=40 AND rid>0 )
);

CREATE TABLE cherrypick(
  parentid INT,
  childid INT,
  isExclude BOOLEAN DEFAULT false,
  PRIMARY KEY(parentid, childid)
) WITHOUT ROWID;

CREATE TABLE concealed(
  hash TEXT PRIMARY KEY,
  mtime DATE,
  content TEXT
) WITHOUT ROWID;

CREATE TABLE config(
  name TEXT PRIMARY KEY NOT NULL,
  value CLOB,
  mtime DATE,
  CHECK( typeof(name)='text' AND length(name)>=1 )
) WITHOUT ROWID;

CREATE TABLE delta(
  rid INTEGER PRIMARY KEY,
  srcid INTEGER NOT NULL REFERENCES blob
);

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

CREATE TABLE orphan(
  rid INTEGER PRIMARY KEY,
  baseline INTEGER
);

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

CREATE TABLE private(rid INTEGER PRIMARY KEY);

CREATE TABLE rcvfrom(
  rcvid INTEGER PRIMARY KEY,
  uid INTEGER REFERENCES user,
  mtime DATETIME,
  nonce TEXT UNIQUE,
  ipaddr TEXT
);

CREATE TABLE reportfmt(
   rn INTEGER PRIMARY KEY,
   owner TEXT,
   title TEXT UNIQUE,
   mtime DATE,
   cols TEXT,
   sqlcode TEXT,
   jx TEXT DEFAULT '{}'
);

CREATE TABLE shun(
  uuid TEXT PRIMARY KEY,
  mtime DATE,
  scom TEXT
) WITHOUT ROWID;

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

CREATE TABLE unclustered(
  rid INTEGER PRIMARY KEY
);

CREATE TABLE unsent(
  rid INTEGER PRIMARY KEY
);

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
