#!/usr/bin/env python3
"""
❤️ LIFT HEALTH — health checks + auto-restart (like Render/Fly.io).

Usage:
    lift health <app>              # HTTP check on app port
    lift autorestart <app> on|off  # auto-restart dead apps
    lift monitor                   # daemon: restarts dead apps (every 30s)
"""
import json
import os
import sys
import time
import urllib.request
from datetime import datetime

LIFT_HOME = os.path.expanduser("~/.lift")
REGISTRY = os.path.join(LIFT_HOME, "apps.json")


def _load():
    try:
        with open(REGISTRY) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save(reg):
    tmp = REGISTRY + ".tmp"
    with open(tmp, "w") as f:
        json.dump(reg, f, indent=2)
    os.replace(tmp, REGISTRY)


def pid_alive(pid):
    if not pid:
        return False
    try:
        os.kill(pid, 0)
        return True
    except (OSError, ProcessLookupError):
        return False


def check_http(port, timeout=5):
    """Returns (ok, status_or_error)."""
    try:
        req = urllib.request.Request(f"http://127.0.0.1:{port}/")
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return True, r.status
    except Exception as e:
        return False, str(e)[:80]


def cmd_health(app):
    reg = _load()
    if app not in reg:
        print(f"Unknown app '{app}'.")
        return 1
    a = reg[app]
    alive = pid_alive(a.get("pid", 0))
    ok, detail = check_http(a["port"]) if alive else (False, "process dead")
    icon = "💚" if ok else ("💛" if alive else "❤️‍🩹")
    print(f"{icon} {app}:")
    print(f"   Process: {'alive (pid ' + str(a.get('pid')) + ')' if alive else 'DEAD'}")
    print(f"   HTTP:    {'200 OK' if ok else 'FAIL — ' + str(detail)}")
    print(f"   Uptime:  since {a.get('deployed_at', '?')}")
    return 0 if ok else 1


def cmd_autorestart(app, state):
    reg = _load()
    if app not in reg:
        print(f"Unknown app '{app}'.")
        return 1
    on = state.lower() in ("on", "true", "1", "yes")
    reg[app]["autorestart"] = on
    _save(reg)
    print(f"🔄 Auto-restart for '{app}': {'ON' if on else 'OFF'}")
    if on:
        print("   Start the monitor: lift monitor &")
    return 0


def cmd_monitor(_args, restart_fn=None):
    """Daemon: every 30s, restart dead apps with autorestart=on."""
    print("❤️ Lift monitor running (checks every 30s). Ctrl+C to stop.")
    while True:
        reg = _load()
        for name, a in reg.items():
            if not a.get("autorestart"):
                continue
            if not pid_alive(a.get("pid", 0)):
                ts = datetime.now().strftime("%H:%M:%S")
                print(f"[{ts}] ⚠️ '{name}' is dead — restarting...", flush=True)
                if restart_fn:
                    try:
                        restart_fn(name)
                        print(f"[{ts}] ✅ '{name}' restarted", flush=True)
                    except Exception as e:
                        print(f"[{ts}] ❌ restart failed: {e}", flush=True)
                a["restarts"] = a.get("restarts", 0) + 1
                _save(reg)
        time.sleep(30)


def main(argv, restart_fn=None):
    if not argv:
        print(__doc__)
        return 0
    if argv[0] == "health" and len(argv) >= 2:
        return cmd_health(argv[1])
    if argv[0] == "autorestart" and len(argv) >= 3:
        return cmd_autorestart(argv[1], argv[2])
    if argv[0] == "monitor":
        return cmd_monitor(argv[1:], restart_fn)
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
