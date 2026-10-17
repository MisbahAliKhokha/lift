#!/usr/bin/env python3
"""
Lift Loop System — every task runs in a loop until PERFECT.
"""
import json
import os
import sys
from datetime import datetime

LOOP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "loop_state")
os.makedirs(LOOP_DIR, exist_ok=True)

def _path(name):
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in name)
    return os.path.join(LOOP_DIR, f"{safe}.json")

def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M")

def start(name, detail=""):
    p = _path(name)
    data = {"task": name, "detail": detail, "status": "in_progress",
            "loops": 0, "screenshots": 0, "started": _now(),
            "history": [{"at": _now(), "event": "started"}]}
    with open(p, "w") as f:
        json.dump(data, f, indent=2)
    print(f"Loop START: {name}")

def _load(name):
    p = _path(name)
    with open(p) as f:
        return json.load(f), p

def _save(data, p):
    with open(p, "w") as f:
        json.dump(data, f, indent=2)

def reject(name, reason):
    data, p = _load(name)
    data["loops"] += 1
    data["status"] = "in_progress"
    data["history"].append({"at": _now(), "event": "rejected", "reason": reason})
    _save(data, p)
    print(f"Loop #{data['loops']}: {name} back — {reason}")

def approve(name):
    data, p = _load(name)
    data["status"] = "done"
    data["history"].append({"at": _now(), "event": "approved"})
    _save(data, p)
    print(f"{name} PERFECT — DELIVER")

def status():
    files = [f for f in os.listdir(LOOP_DIR) if f.endswith(".json")]
    for f in sorted(files):
        with open(os.path.join(LOOP_DIR, f)) as fh:
            d = json.load(fh)
        print(f"{d['task']}: {d['status']} (loops: {d['loops']})")

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "start" and len(sys.argv) >= 3:
        start(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "")
    elif cmd == "reject" and len(sys.argv) >= 4:
        reject(sys.argv[2], sys.argv[3])
    elif cmd == "approve" and len(sys.argv) >= 3:
        approve(sys.argv[2])
    elif cmd == "status":
        status()
