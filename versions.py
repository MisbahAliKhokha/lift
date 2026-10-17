#!/usr/bin/env python3
"""
⏪ LIFT VERSIONS — rollback like Render/Heroku releases.
Keeps last 3 deploys per app in ~/.lift/versions/<app>/.

Usage:
    lift versions <app>    # list saved versions
    lift rollback <app>    # restore previous version
"""
import os
import shutil
import sys
import time
from datetime import datetime

LIFT_HOME = os.path.expanduser("~/.lift")
VERSIONS_DIR = os.path.join(LIFT_HOME, "versions")
KEEP = 3


def app_versions_dir(app):
    d = os.path.join(VERSIONS_DIR, app)
    os.makedirs(d, exist_ok=True)
    return d


def snapshot(app, src_dir):
    """Save current deploy as a version before overwriting."""
    if not os.path.isdir(src_dir):
        return
    vdir = app_versions_dir(app)
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    dest = os.path.join(vdir, ts)
    shutil.copytree(src_dir, dest,
                    ignore=shutil.ignore_patterns(".git", "__pycache__",
                                                  "node_modules", ".venv", "venv"))
    # prune to KEEP
    versions = sorted(os.listdir(vdir))
    for old in versions[:-KEEP]:
        shutil.rmtree(os.path.join(vdir, old), ignore_errors=True)
    return ts


def list_versions(app):
    vdir = os.path.join(VERSIONS_DIR, app)
    if not os.path.isdir(vdir):
        return []
    out = []
    for ts in sorted(os.listdir(vdir), reverse=True):
        p = os.path.join(vdir, ts)
        if os.path.isdir(p):
            size = sum(os.path.getsize(os.path.join(r, f))
                       for r, _, fs in os.walk(p) for f in fs)
            out.append((ts, size))
    return out


def cmd_versions(app):
    vs = list_versions(app)
    if not vs:
        print(f"No saved versions for '{app}'.")
        return 0
    print(f"Versions for '{app}' (newest first):")
    for i, (ts, size) in enumerate(vs):
        tag = " ← current would restore here" if i == 0 else ""
        print(f"  {ts}  ({size:,} bytes){tag}")
    return 0


def cmd_rollback(app, stop_fn=None, start_fn=None):
    vs = list_versions(app)
    if not vs:
        print(f"No versions to roll back for '{app}'.")
        return 1
    ts, _ = vs[0]
    src = os.path.join(VERSIONS_DIR, app, ts)
    if stop_fn:
        stop_fn(app)
    # find app dir from registry via start_fn context — caller handles
    print(f"⏪ Rolling back '{app}' to version {ts}...")
    return src  # caller copies src → app dir, then starts


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 0
    cmd, app = argv[0], argv[1]
    if cmd == "versions":
        return cmd_versions(app)
    print(f"Unknown versions command '{cmd}'. Use: lift versions <app> / lift rollback <app>")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
