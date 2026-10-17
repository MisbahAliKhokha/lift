#!/usr/bin/env python3
"""
⏰ LIFT CRON — scheduled jobs like Render Cron / Heroku Scheduler.

Usage:
    lift cron add "<schedule>" "<command>" [--name NAME]
    lift cron list
    lift cron remove <id>
    lift cron run          # daemon: checks every 60s, runs due jobs

Schedule format: "MIN HOUR DOM MON DOW" (5 fields)
  Supports: * (any), */N (every N), N (exact), N-M (range), N,M,K (list)

Examples:
    lift cron add "*/5 * * * *" "python3 /home/u/backup.py" --name backup
    lift cron add "0 2 * * *" "python3 cleanup.py"
"""
import json
import os
import subprocess
import sys
import time
from datetime import datetime

LIFT_HOME = os.path.expanduser("~/.lift")
CRONS_FILE = os.path.join(LIFT_HOME, "crons.json")
LOGS_DIR = os.path.join(LIFT_HOME, "logs")


def _load():
    os.makedirs(LIFT_HOME, exist_ok=True)
    if not os.path.exists(CRONS_FILE):
        return {}
    try:
        with open(CRONS_FILE) as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}


def _save(crons):
    os.makedirs(LIFT_HOME, exist_ok=True)
    tmp = CRONS_FILE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(crons, f, indent=2)
    os.replace(tmp, CRONS_FILE)


def _match_field(value, spec, lo, hi):
    """Check if a cron field value matches its spec."""
    if spec == "*":
        return True
    for part in spec.split(","):
        if part.startswith("*/"):
            step = int(part[2:])
            if value % step == 0:
                return True
        elif "-" in part:
            a, b = part.split("-", 1)
            if int(a) <= value <= int(b):
                return True
        else:
            if value == int(part):
                return True
    return False


def is_due(schedule, now=None):
    """Is this cron schedule due right now (minute precision)?"""
    now = now or datetime.now()
    try:
        minute, hour, dom, mon, dow = schedule.split()
    except ValueError:
        raise ValueError(f"Bad schedule '{schedule}' — expected 5 fields.")
    # Python weekday: Mon=0..Sun=6 ; cron: Sun=0..Sat=6
    cron_dow = (now.weekday() + 1) % 7
    return (
        _match_field(now.minute, minute, 0, 59)
        and _match_field(now.hour, hour, 0, 23)
        and _match_field(now.day, dom, 1, 31)
        and _match_field(now.month, mon, 1, 12)
        and _match_field(cron_dow, dow, 0, 6)
    )


def cmd_add(args):
    if len(args) < 2:
        print('Usage: lift cron add "<schedule>" "<command>" [--name NAME]')
        print('Example: lift cron add "*/5 * * * *" "python3 job.py" --name myjob')
        return 1
    schedule, command = args[0], args[1]
    name = None
    if "--name" in args:
        try:
            name = args[args.index("--name") + 1]
        except IndexError:
            pass
    # validate schedule
    try:
        is_due(schedule)
    except ValueError as e:
        print(f"Error: {e}")
        return 1
    crons = _load()
    cid = name or f"cron-{len(crons) + 1}"
    if cid in crons:
        cid = f"{cid}-{int(time.time()) % 10000}"
    crons[cid] = {
        "id": cid,
        "schedule": schedule,
        "command": command,
        "created": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "last_run": None,
        "runs": 0,
    }
    _save(crons)
    print(f"⏰ Cron added: '{cid}' → {schedule} → {command}")
    print("   Start the scheduler: lift cron run &")
    return 0


def cmd_list(_args):
    crons = _load()
    if not crons:
        print("No cron jobs. Add one: lift cron add \"*/5 * * * *\" \"cmd\"")
        return 0
    print(f"{'ID':<20} {'SCHEDULE':<18} {'LAST RUN':<17} {'RUNS':<5} COMMAND")
    print("-" * 90)
    for cid in sorted(crons):
        c = crons[cid]
        print(f"{cid:<20} {c['schedule']:<18} {str(c['last_run']):<17} "
              f"{c['runs']:<5} {c['command']}")
    return 0


def cmd_remove(args):
    if not args:
        print("Usage: lift cron remove <id>")
        return 1
    crons = _load()
    if args[0] not in crons:
        print(f"Unknown cron '{args[0]}'.")
        return 1
    del crons[args[0]]
    _save(crons)
    print(f"🗑 Cron '{args[0]}' removed.")
    return 0


def _run_job(cid, job):
    os.makedirs(LOGS_DIR, exist_ok=True)
    log_path = os.path.join(LOGS_DIR, f"cron-{cid}.log")
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_path, "a") as lf:
        lf.write(f"\n===== {ts} : {job['command']} =====\n")
        lf.flush()
        p = subprocess.run(job["command"], shell=True, stdout=lf,
                           stderr=subprocess.STDOUT, timeout=600)
        lf.write(f"===== exit {p.returncode} =====\n")
    return p.returncode


def cmd_run(_args):
    """Daemon: check every 60s, run due jobs."""
    print("⏰ Lift cron scheduler running (checks every 60s). Ctrl+C to stop.")
    last_minute = None
    while True:
        now = datetime.now()
        if now.minute != last_minute:
            last_minute = now.minute
            crons = _load()
            for cid, job in crons.items():
                try:
                    due = is_due(job["schedule"], now)
                except ValueError:
                    continue
                if due and job.get("last_run") != now.strftime("%Y-%m-%d %H:%M"):
                    print(f"[{now.strftime('%H:%M')}] Running '{cid}': {job['command']}",
                          flush=True)
                    rc = _run_job(cid, job)
                    crons[cid]["last_run"] = now.strftime("%Y-%m-%d %H:%M")
                    crons[cid]["runs"] = job.get("runs", 0) + 1
                    crons[cid]["last_exit"] = rc
                    _save(crons)
        time.sleep(10)


def main(argv):
    if not argv:
        print(__doc__)
        return 0
    cmd, args = argv[0], argv[1:]
    if cmd == "add":
        return cmd_add(args)
    if cmd == "list":
        return cmd_list(args)
    if cmd == "remove":
        return cmd_remove(args)
    if cmd == "run":
        return cmd_run(args)
    print(f"Unknown cron command '{cmd}'.")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
