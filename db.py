#!/usr/bin/env python3
"""
🗄️ LIFT DB — free database per app (like Render Postgres / Heroku Postgres / Railway DB).
Uses SQLite (stdlib) — zero dependencies, zero cost.

Usage:
    lift db create <app>     # creates ~/.lift/dbs/<app>.db + sets DATABASE_URL
    lift db info <app>       # path, size, tables
    lift db shell <app>      # opens sqlite3 interactive (if installed)
"""
import os
import sqlite3
import sys

LIFT_HOME = os.path.expanduser("~/.lift")
DBS_DIR = os.path.join(LIFT_HOME, "dbs")


def db_path(app):
    return os.path.join(DBS_DIR, f"{app}.db")


def cmd_create(app, set_env_fn=None):
    os.makedirs(DBS_DIR, exist_ok=True)
    path = db_path(app)
    if os.path.exists(path):
        print(f"Database already exists for '{app}': {path}")
        return 1
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE IF NOT EXISTS _lift_meta (k TEXT PRIMARY KEY, v TEXT)")
    conn.execute("INSERT OR REPLACE INTO _lift_meta VALUES ('app', ?), ('created', datetime('now'))",
                 (app,))
    conn.commit()
    conn.close()
    url = f"sqlite:///{path}"
    if set_env_fn:
        set_env_fn(app, "DATABASE_URL", url)
        print(f"🗄️ Database created for '{app}'")
        print(f"   {path}")
        print(f"   DATABASE_URL set automatically ✅")
    else:
        print(f"🗄️ Database created: {path}")
    return 0


def cmd_info(app):
    path = db_path(app)
    if not os.path.exists(path):
        print(f"No database for '{app}'. Create: lift db create {app}")
        return 1
    size = os.path.getsize(path)
    conn = sqlite3.connect(path)
    tables = [r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
    conn.close()
    print(f"App:      {app}")
    print(f"Path:     {path}")
    print(f"Size:     {size:,} bytes")
    print(f"Tables:   {', '.join(tables) if tables else '(none)'}")
    print(f"URL:      sqlite:///{path}")
    return 0


def main(argv, set_env_fn=None):
    if len(argv) < 2:
        print(__doc__)
        return 0
    cmd, app = argv[0], argv[1]
    if cmd == "create":
        return cmd_create(app, set_env_fn)
    if cmd == "info":
        return cmd_info(app)
    print(f"Unknown db command '{cmd}'.")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
