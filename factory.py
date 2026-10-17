#!/usr/bin/env python3
"""
LIFT FACTORY — multi-agent hierarchy inside Lift.
Worker → Supervisor → Manager → CEO. Mandatory review loop.
Parallel workers for speed.
"""
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import loop as loop_sys

FACTORY_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "factory_state")
os.makedirs(FACTORY_DIR, exist_ok=True)

DEPARTMENTS = {
    "deploy": {"workers": 4, "supervisors": 1, "manager": 1},
    "build": {"workers": 4, "supervisors": 1, "manager": 1},
    "verify": {"workers": 2, "supervisors": 1, "manager": 1},
}

def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def log(dept, level, msg):
    line = f"[{_now()}] [{dept}/{level}] {msg}"
    print(line, flush=True)
    with open(os.path.join(FACTORY_DIR, "factory.log"), "a") as f:
        f.write(line + "\n")

def worker_task(dept, worker_id, job):
    log(dept, f"worker-{worker_id}", f"start: {job['name']}")
    t0 = time.time()
    try:
        result = job["fn"]()
        dt = time.time() - t0
        log(dept, f"worker-{worker_id}", f"done: {job['name']} ({dt:.2f}s)")
        return {"ok": True, "name": job["name"], "result": result, "time": dt}
    except Exception as e:
        dt = time.time() - t0
        log(dept, f"worker-{worker_id}", f"FAIL: {job['name']} — {e}")
        return {"ok": False, "name": job["name"], "error": str(e), "time": dt}

def supervisor_check(dept, results):
    bad = [r for r in results if not r["ok"]]
    if bad:
        log(dept, "supervisor", f"{len(bad)} failed — back to workers")
        return False, bad
    log(dept, "supervisor", f"{len(results)} all OK")
    return True, []

def manager_review(dept, results):
    total = sum(r["time"] for r in results)
    log(dept, "manager", f"review OK — {len(results)} jobs, {total:.2f}s")
    return True

def ceo_approve(task_name, all_results):
    flat = [r for rs in all_results.values() for r in rs]
    failed = [r for r in flat if not r["ok"]]
    if failed:
        loop_sys.reject(task_name, f"{len(failed)} jobs failed")
        return False
    loop_sys.approve(task_name)
    log("factory", "CEO", f"{task_name} APPROVED — deliver!")
    return True

def run_factory(task_name, jobs_by_dept, max_workers=8):
    loop_sys.start(task_name, f"factory: {list(jobs_by_dept.keys())}")
    log("factory", "CEO", f"FACTORY START: {task_name}")
    all_results = {}
    for dept, jobs in jobs_by_dept.items():
        cfg = DEPARTMENTS.get(dept, {"workers": 2})
        n = min(cfg["workers"], len(jobs), max_workers)
        results = []
        with ThreadPoolExecutor(max_workers=n) as ex:
            futs = {ex.submit(worker_task, dept, i % n, job): job
                    for i, job in enumerate(jobs)}
            for fut in as_completed(futs):
                results.append(fut.result())
        ok, bad = supervisor_check(dept, results)
        if not ok:
            loop_sys.reject(task_name, f"{dept}: {len(bad)} failed")
            return False
        manager_review(dept, results)
        all_results[dept] = results
    return ceo_approve(task_name, all_results)

def render_features():
    return {
        "instant_deploy": "git push auto deploy",
        "preview_urls": "per-deploy URL",
        "auto_ssl": "free SSL per app",
        "health_checks": "auto restart on fail",
        "zero_downtime": "new starts before old stops",
        "rollback": "one-command rollback",
    }

if __name__ == "__main__":
    print("LIFT FACTORY")
    print("Departments:", list(DEPARTMENTS.keys()))
    for k, v in render_features().items():
        print(f"  - {k}: {v}")
