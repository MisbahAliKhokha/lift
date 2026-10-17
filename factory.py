#!/usr/bin/env python3
"""
🏭 LIFT FACTORY — waqas ka hukum (2026-10-17)

Factory system INSIDE Lift. Multi-agent hierarchy:
  Worker → Supervisor → Manager → CEO

Har level par MANDATORY review loop.
Speed ke liye: parallel workers (ThreadPool), caching, batch deploys.

Loop + Speed DONO — looping ke baad bhi tez kaam!
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

# Hierarchy: har department me teams
DEPARTMENTS = {
    "deploy":   {"workers": 4, "supervisors": 1, "manager": 1},
    "build":    {"workers": 4, "supervisors": 1, "manager": 1},
    "verify":   {"workers": 2, "supervisors": 1, "manager": 1},
}


def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def log(dept, level, msg):
    line = f"[{_now()}] [{dept}/{level}] {msg}"
    print(line, flush=True)
    p = os.path.join(FACTORY_DIR, "factory.log")
    with open(p, "a") as f:
        f.write(line + "\n")


def worker_task(dept, worker_id, job):
    """Worker: asal kaam karta hai."""
    log(dept, f"worker-{worker_id}", f"start: {job['name']}")
    t0 = time.time()
    try:
        result = job["fn"]()
        dt = time.time() - t0
        log(dept, f"worker-{worker_id}", f"done: {job['name']} ({dt:.2f}s)")
        return {"ok": True, "name": job["name"], "result": result, "time": dt}
    except Exception as e:
        dt = time.time() - t0
        log(dept, f"worker-{worker_id}", f"FAIL: {job['name']} — {e} ({dt:.2f}s)")
        return {"ok": False, "name": job["name"], "error": str(e), "time": dt}


def supervisor_check(dept, results):
    """Supervisor: har worker ka result check karta hai."""
    bad = [r for r in results if not r["ok"]]
    if bad:
        log(dept, "supervisor", f"❌ {len(bad)} failed — wapas workers ko")
        return False, bad
    log(dept, "supervisor", f"✅ {len(results)} sab OK")
    return True, []


def manager_review(dept, results):
    """Manager: final review, CEO ko bhejta hai."""
    total_t = sum(r["time"] for r in results)
    log(dept, "manager", f"review OK — {len(results)} jobs, {total_t:.2f}s total")
    return True


def ceo_approve(task_name, all_results):
    """CEO: sab departments ka result — loop me daal ke verify."""
    flat = [r for dept_rs in all_results.values() for r in dept_rs]
    failed = [r for r in flat if not r["ok"]]
    if failed:
        loop_sys.reject(task_name, f"{len(failed)} jobs failed: {[r['name'] for r in failed]}")
        return False
    loop_sys.approve(task_name)
    log("factory", "CEO", f"✅ {task_name} APPROVED — deliver!")
    return True


def run_factory(task_name, jobs_by_dept, max_workers=8):
    """
    Factory chalao — parallel workers, har level review.
    jobs_by_dept: {"deploy": [{"name":..., "fn":...}], "build": [...]}
    """
    loop_sys.start(task_name, f"factory run: {list(jobs_by_dept.keys())}")
    log("factory", "CEO", f"🏭 FACTORY START: {task_name}")

    all_results = {}
    for dept, jobs in jobs_by_dept.items():
        cfg = DEPARTMENTS.get(dept, {"workers": 2})
        n = min(cfg["workers"], len(jobs), max_workers)
        log(dept, "manager", f"{len(jobs)} jobs → {n} parallel workers")

        results = []
        with ThreadPoolExecutor(max_workers=n) as ex:
            futs = {ex.submit(worker_task, dept, i % n, job): job
                    for i, job in enumerate(jobs)}
            for fut in as_completed(futs):
                results.append(fut.result())

        ok, bad = supervisor_check(dept, results)
        if not ok:
            # Failed jobs dobara — ek retry
            log(dept, "supervisor", "retry failed jobs (1x)")
            retry_results = []
            with ThreadPoolExecutor(max_workers=n) as ex:
                futs = {ex.submit(worker_task, dept, 0,
                                 {"name": r["name"] + " [retry]",
                                  "fn": next(j["fn"] for j in jobs if j["name"] == r["name"])}): r
                        for r in bad}
                for fut in as_completed(futs):
                    retry_results.append(fut.result())
            # merge: retry wale replace
            names = {r["name"].replace(" [retry]", "") for r in retry_results}
            results = [r for r in results if r["name"] not in names] + \
                      [{**r, "name": r["name"].replace(" [retry]", "")} for r in retry_results]
            ok, bad = supervisor_check(dept, results)
            if not ok:
                loop_sys.reject(task_name, f"{dept}: {len(bad)} jobs still failing")
                return False

        manager_review(dept, results)
        all_results[dept] = results

    return ceo_approve(task_name, all_results)


# ---- Render-style features (ALL IMPLEMENTED ✅) ----
def render_features():
    """Render/Heroku/Railway/Fly.io jaisi features — Lift ke andar, tez, FREE."""
    return {
        # Deploy
        "instant_deploy": "lift deploy <folder> — auto-detect python/node/static ✅",
        "preview_deploys": "lift deploy --preview — PR-style preview env ✅",
        "git_autodeploy": "lift autodeploy <repo> --name app — push → redeploy ✅",
        "zero_downtime": "purana band hone se pehle naya start ✅",
        "rollback": "lift rollback <app> — last 3 versions ✅",
        # Compute
        "background_workers": "lift worker add <app> 'cmd' — Heroku worker dynos ✅",
        "cron_jobs": "lift cron add '*/5 * * * *' 'cmd' — Render cron ✅",
        "health_checks": "lift health <app> — HTTP check ✅",
        "auto_restart": "lift autorestart <app> on + lift monitor — dead → restart ✅",
        # Data
        "database": "lift db create <app> — free SQLite + DATABASE_URL ✅",
        "env_vars": "lift env set <app> KEY=VAL — config vars ✅",
        # Network
        "custom_domains": "lift domain add <app> example.com ✅",
        "preview_urls": "har deploy ka alag port/URL ✅",
        # Observe
        "metrics": "lift stats [app] — uptime, memory, restarts ✅",
        "logs": "lift logs <app> — per-app log files ✅",
    }


if __name__ == "__main__":
    print("🏭 LIFT FACTORY")
    print("Departments:", list(DEPARTMENTS.keys()))
    print("\nRender-style features:")
    for k, v in render_features().items():
        print(f"  • {k}: {v}")
    print("\nLoop + Speed: parallel workers, auto-retry, CEO approve tabhi deliver.")
