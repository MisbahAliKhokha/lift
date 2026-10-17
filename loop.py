#!/usr/bin/env python3
"""
🔁 LIFT LOOP SYSTEM — waqas ka hukum (2026-10-17)

MANDATORY loop inside Lift. Har kaam loop me chalega.
Jab tak PERFECT na ho → wapas → fix → phir check.
Time kitna bhi lage — finish kiye baghair AAGE NAHI.

Rule:
  1. KAAM MILA
  2. LOG START (loop_state/<task>.json)
  3. WORKER kaam kare
  4. INSPECTOR check kare (independent)
  5. PERFECT? NO → wapas step 3 (loops+1)
  6. PERFECT? YES → LOG DONE + DELIVER

Reverse engineering mode:
  - Bar-bar screenshot lo
  - Bar-bar compare karo
  - Jab tak 100% match na ho → loop chalao
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
    """Naya kaam loop me daalo."""
    p = _path(name)
    data = {
        "task": name,
        "detail": detail,
        "status": "in_progress",
        "loops": 0,
        "screenshots": 0,
        "started": _now(),
        "history": [{"at": _now(), "event": "started"}],
    }
    with open(p, "w") as f:
        json.dump(data, f, indent=2)
    print(f"🔁 Loop START: {name}")
    return data


def _load(name):
    p = _path(name)
    if not os.path.exists(p):
        print(f"❌ Task nahi mila: {name}")
        sys.exit(1)
    with open(p) as f:
        return json.load(f), p


def _save(data, p):
    with open(p, "w") as f:
        json.dump(data, f, indent=2)


def reject(name, reason):
    """Inspector ne reject kiya — wapas kaam par."""
    data, p = _load(name)
    data["loops"] += 1
    data["status"] = "in_progress"
    data["history"].append({"at": _now(), "event": "rejected", "reason": reason})
    _save(data, p)
    print(f"🔁 Loop #{data['loops']}: {name} wapas — {reason}")


def screenshot_taken(name):
    """Reverse engineering me screenshot ka hisaab."""
    data, p = _load(name)
    data["screenshots"] += 1
    data["history"].append({"at": _now(), "event": "screenshot", "n": data["screenshots"]})
    _save(data, p)


def approve(name):
    """Inspector pass — deliver ke liye ready."""
    data, p = _load(name)
    data["status"] = "done"
    data["history"].append({"at": _now(), "event": "approved", "loops": data["loops"]})
    _save(data, p)
    print(f"✅ {name} PERFECT — {data['loops']} loops, {data['screenshots']} screenshots — DELIVER")


def status():
    """Sab tasks ka haal."""
    files = [f for f in os.listdir(LOOP_DIR) if f.endswith(".json")]
    if not files:
        print("Koi task nahi.")
        return
    for f in sorted(files):
        with open(os.path.join(LOOP_DIR, f)) as fh:
            d = json.load(fh)
        icon = {"in_progress": "🔨", "done": "✅"}.get(d["status"], "❓")
        print(f"{icon} {d['task']}: {d['status']} (loops: {d['loops']}, screenshots: {d['screenshots']})")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Use: loop.py start|reject|approve|status ...")
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "start" and len(sys.argv) >= 3:
        start(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "")
    elif cmd == "reject" and len(sys.argv) >= 4:
        reject(sys.argv[2], sys.argv[3])
    elif cmd == "approve" and len(sys.argv) >= 3:
        approve(sys.argv[2])
    elif cmd == "status":
        status()
    else:
        print("Use: loop.py start <name> | reject <name> <reason> | approve <name> | status")
