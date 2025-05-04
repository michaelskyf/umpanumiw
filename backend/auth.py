import sqlite3
from db import _connect, _lock


def terminal_prompt():
    print("=== Admin: Add or List Users (Ctrl+C to exit) ===")
    while True:
        cmd = input("[add/list]> ").strip().lower()
        if cmd == 'add':
            pub = input("Public key (openssh): ").strip()
            with _lock, _connect() as c:
                c.execute("INSERT OR IGNORE INTO USER(pubkey) VALUES(?)", (pub,))
                c.commit()
                print("Added.")
        elif cmd == 'list':
            with _lock, _connect() as c:
                for row in c.execute("SELECT id, pubkey FROM USER"): print(row)
        else:
            print("Unknown command.")


def find_user_by_pubkey(pubkey):
    with _lock, _connect() as c:
        r = c.execute("SELECT id FROM USER WHERE pubkey=?", (pubkey,)).fetchone()
        return r[0] if r else None