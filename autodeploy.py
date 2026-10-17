#!/usr/bin/env python3
"""
🔄 LIFT AUTODEPLOY — git push → auto deploy (like Render/Heroku/Railway).

Usage:
    lift autodeploy <folder> --name <app>   # watch a git repo, redeploy on push
    lift autodeploy list                    # watched repos
    lift autodeploy remove <app>            # stop watching
    lift autodeploy check                   # one poll: pull + redeploy if changed
    lift autodeploy watch                   # daemon: poll every 60s

The folder must be a git repo. On new commits: git pull → redeploy app.
"""
import json
import os
import subprocess
import sys
import time
from datetime import datetime

LIFT_HOME = os.path.expanduser("~/.lift")
WATCH_FILE = os.path.join(LIFT_HOME, "autodeploy.json")


def _load():
    os.makedirs(LIFT_HOME, exist_ok=True)
    try:
        with open(WATCH_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save(w):
    tmp = WATCH_FILE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(w, f, indent=2)
    os.replace(tmp, WATCH_FILE)


def _git(cmd, cwd):
    r = subprocess.run(["git"] + cmd, cwd=cwd, capture_output=True, text=True, timeout=60)
    return r.returncode, r.stdout.strip(), r.stderr.strip()


def cmd_add(folder, name):
    folder = os.path.abspath(folder)
    if not os.path.isdir(os.path.join(folder, ".git")):
        print(f"Error: '{folder}' is not a git repo.")
        return 1
    rc, head, _ = _git(["rev-parse", "HEAD"], folder)
    if rc != 0:
        print("Error: cannot read git HEAD.")
        return 1
    w = _load()
    w[name] = {"folder": folder, "last_commit": head,
               "added": datetime.now().strftime("%Y-%m-%d %H:%M")}
    _save(w)
    print(f"🔄 Auto-deploy ON for '{name}' ← {folder}")
    print(f"   Watching commit {head[:8]}. Run 'lift autodeploy watch &' for daemon.")
    return 0


def cmd_list(_args):
    w = _load()
    if not w:
        print("No auto-deploy watches.")
        return 0
    print(f"{'APP':<18} {'LAST COMMIT':<12} FOLDER")
    print("-" * 70)
    for name in sorted(w):
        print(f"{name:<18} {w[name]['last_commit'][:8]:<12} {w[name]['folder']}")
    return 0


def cmd_remove(app):
    w = _load()
    if app not in w:
        print(f"'{app}' is not watched.")
        return 1
    del w[app]
    _save(w)
    print(f"🗑 Auto-deploy OFF for '{app}'.")
    return 0


def check_once(redeploy_fn=None):
    """Poll all watched repos once. Returns list of redeployed apps."""
    w = _load()
    done = []
    for name, cfg in w.items():
        folder = cfg["folder"]
        _git(["fetch", "origin"], folder)
        rc, head, _ = _git(["rev-parse", "HEAD"], folder)
        rc2, remote, _ = _git(["rev-parse", "@{u}"], folder)
        new_commit = remote if rc2 == 0 else head
        if new_commit != cfg["last_commit"]:
            print(f"[{datetime.now():%H:%M:%S}] 🔄 New commit for '{name}': "
                  f"{cfg['last_commit'][:8]} → {new_commit[:8]}", flush=True)
            _git(["pull", "--ff-only"], folder)
            if redeploy_fn:
                redeploy_fn(name, folder)
            w[name]["last_commit"] = new_commit
            w[name]["last_deploy"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            done.append(name)
    if done:
        _save(w)
    return done


def cmd_check(_args, redeploy_fn=None):
    done = check_once(redeploy_fn)
    if done:
        print(f"✅ Redeployed: {', '.join(done)}")
    else:
        print("No changes.")
    return 0


def cmd_watch(_args, redeploy_fn=None):
    print("🔄 Auto-deploy watcher running (polls every 60s). Ctrl+C to stop.")
    while True:
        try:
            check_once(redeploy_fn)
        except Exception as e:
            print(f"watch error: {e}", flush=True)
        time.sleep(60)


def main(argv, redeploy_fn=None):
    if not argv:
        print(__doc__)
        return 0
    cmd, args = argv[0], argv[1:]
    if cmd == "list":
        return cmd_list(args)
    if cmd == "remove" and args:
        return cmd_remove(args[0])
    if cmd == "check":
        return cmd_check(args, redeploy_fn)
    if cmd == "watch":
        return cmd_watch(args, redeploy_fn)
    # default: autodeploy <folder> --name <app>
    if args and "--name" in args:
        try:
            name = args[args.index("--name") + 1]
        except IndexError:
            print("Usage: lift autodeploy <folder> --name <app>")
            return 1
        return cmd_add(argv[0], name)
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
