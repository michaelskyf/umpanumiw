import sqlite3
import threading
import os

# To be set by backend.py before use
ROOT_DIR = None
_lock = threading.Lock()

CREATE_USER = '''
CREATE TABLE IF NOT EXISTS USER (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pubkey TEXT UNIQUE NOT NULL
);
'''
CREATE_SHARE = '''
CREATE TABLE IF NOT EXISTS SHARE (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_id INTEGER NOT NULL,
    path TEXT NOT NULL,
    mode TEXT NOT NULL,
    user_id INTEGER NOT NULL,
    FOREIGN KEY(owner_id) REFERENCES USER(id)
);
'''


def _connect():
    if not ROOT_DIR:
        raise RuntimeError("ROOT_DIR not set")
    os.makedirs(ROOT_DIR, exist_ok=True)
    db_path = os.path.join(ROOT_DIR, 'backend.db')
    return sqlite3.connect(db_path, check_same_thread=False)


def init_db():
    with _lock, _connect() as conn:
        conn.execute(CREATE_USER)
        conn.execute(CREATE_SHARE)
        conn.commit()