"""Tiered memory: working (ring buffer), episodic (Qdrant), semantic (SQLite)."""
import sqlite3
from collections import defaultdict, deque
_work = defaultdict(lambda: deque(maxlen=20))      # swap for Redis LPUSH/LTRIM in production
_db = sqlite3.connect("/tmp/apex_semantic.db", check_same_thread=False)
_db.execute("CREATE TABLE IF NOT EXISTS facts(user TEXT, key TEXT, value TEXT, PRIMARY KEY(user,key))")

def remember_turn(session, role, text): _work[session].append({"role": role, "content": text})
def history(session): return list(_work[session])
def set_fact(user, key, value):
    _db.execute("INSERT OR REPLACE INTO facts VALUES(?,?,?)", (user, key, value)); _db.commit()
def facts(user): return dict(_db.execute("SELECT key,value FROM facts WHERE user=?", (user,)).fetchall())
