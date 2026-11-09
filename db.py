
import sqlite3
from datetime import datetime, timezone
from .config import DB_PATH
def now(): return datetime.now(timezone.utc).isoformat()
def conn():
    c=sqlite3.connect(DB_PATH, timeout=30); c.row_factory=sqlite3.Row; return c
def init_db():
    with conn() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS jobs(
        id TEXT PRIMARY KEY,status TEXT,app_name TEXT,package_id TEXT,source_path TEXT,
        created_at TEXT,updated_at TEXT,error TEXT,apk_path TEXT)""")
def add_job(jid,name,pkg,path):
    t=now()
    with conn() as c: c.execute("INSERT INTO jobs VALUES(?,?,?,?,?,?,?,?,?)",
        (jid,"queued",name,pkg,path,t,t,None,None))
def get_job(jid):
    with conn() as c:
        r=c.execute("SELECT * FROM jobs WHERE id=?",(jid,)).fetchone()
        return dict(r) if r else None
def all_jobs():
    with conn() as c: return [dict(x) for x in c.execute(
        "SELECT id,status,app_name,package_id,created_at,updated_at,error FROM jobs ORDER BY created_at DESC LIMIT 40")]
def claim():
    with conn() as c:
        c.execute("BEGIN IMMEDIATE")
        r=c.execute("SELECT id FROM jobs WHERE status='queued' ORDER BY created_at LIMIT 1").fetchone()
        if not r: return None
        jid=r["id"]; c.execute("UPDATE jobs SET status='building',updated_at=? WHERE id=?",(now(),jid))
    return get_job(jid)
def update(jid, **kw):
    kw["updated_at"]=now(); cols=",".join(k+"=?" for k in kw)
    with conn() as c: c.execute("UPDATE jobs SET "+cols+" WHERE id=?",(*kw.values(),jid))
