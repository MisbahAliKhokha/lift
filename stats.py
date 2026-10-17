#!/usr/bin/env python3
"""
📊 LIFT STATS — metrics like Render/Railway dashboards.

Usage:
    lift stats <app>   # uptime, restarts, port, pid, memory
    lift stats         # all apps table
"""
import json
import os
import sys
import time
from datetime import datetime

LIFT_HOME = os.path.expanduser("~/.lift")
REGISTRY = os.path.join(LIFT_HOME, "apps.json")


def _load():
    try:
        with open(REGISTRY) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def pid_alive(pid):
    if not pid:
        return False
    try:
        os.kill(pid, 0)
        return True
    except (OSError, ProcessLookupError):
        return False


def proc_info(pid):
    """Memory (KB) + start time from /proc (Linux)."""
    try:
        with open(f"/proc/{pid}/status") as f:
            mem = None
            for line in f:
                if line.startswith("VmRSS:"):
                    mem = int(line.split()[1])  # KB
                    break
        with open(f"/proc/{pid}/stat") as f:
            start_ticks = int(f.read().split()[21])
        with open("/proc/stat") as f:
            btime = int([l for l in f if l.startswith("btime")][0].split()[1])
        hz = os.sysconf(os.sysconf_names["SC_CLK_TCK"])
        started = btime + start_ticks / hz
        uptime = time.time() - started
        return mem, uptime
    except (FileNotFoundError, ProcessLookupError, IndexError, ValueError):
        return None, None


def fmt_uptime(secs):
    if secs is None:
        return "—"
    secs = int(secs)
    d, secs = divmod(secs, 86400)
    h, secs = divmod(secs, 3600)
    m, s = divmod(secs, 60)
    if d:
        return f"{d}d {h}h"
    if h:
        return f"{h}h {m}m"
    return f"{m}m {s}s"


def cmd_one(app):
    reg = _load()
    if app not in reg:
        print(f"Unknown app '{app}'.")
        return 1
    a = reg[app]
    alive = pid_alive(a.get("pid", 0))
    mem, uptime = proc_info(a["pid"]) if alive else (None, None)
    print(f"📊 {app}:")
    print(f"   Status:    {'🟢 running' if alive else '🔴 stopped'}")
    print(f"   Type:      {a.get('type', '?')}")
    print(f"   URL:       http://localhost:{a.get('port', '?')}")
    print(f"   PID:       {a.get('pid', '—')}")
    print(f"   Uptime:    {fmt_uptime(uptime)}")
    print(f"   Memory:    {f'{mem:,} KB' if mem else '—'}")
    print(f"   Restarts:  {a.get('restarts', 0)}")
    print(f"   Workers:   {len(a.get('workers', []))}")
    print(f"   Domains:   {', '.join(a.get('domains', [])) or '—'}")
    print(f"   Deployed:  {a.get('deployed_at', '?')}")
    return 0


def cmd_all(_args):
    reg = _load()
    if not reg:
        print("No apps yet.")
        return 0
    print(f"{'NAME':<18} {'STATUS':<9} {'PORT':<6} {'UPTIME':<9} {'MEM':<10} {'RESTARTS'}")
    print("-" * 70)
    for name in sorted(reg):
        a = reg[name]
        alive = pid_alive(a.get("pid", 0))
        mem, uptime = proc_info(a["pid"]) if alive else (None, None)
        print(f"{name:<18} {'running' if alive else 'stopped':<9} "
              f"{a.get('port', '?'):<6} {fmt_uptime(uptime):<9} "
              f"{(f'{mem:,}K' if mem else '—'):<10} {a.get('restarts', 0)}")
    return 0


def main(argv):
    if len(argv) >= 1 and argv[0] not in ("--help", "-h"):
        return cmd_one(argv[0])
    return cmd_all(argv)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
