#!/usr/bin/env python3
"""
Lift — Free Open-Source Render Alternative
Deploy web apps easily. 100% free, zero dependencies, stdlib only.

Usage:
    lift deploy <folder> [--name NAME] [--port PORT] [--preview]
    lift list | logs <app> | stop <app> | start <app> | remove <app> | info <app>
    lift env set <app> KEY=VAL | env list <app> | env unset <app> KEY
    lift db create <app> | db info <app>
    lift versions <app> | rollback <app>
    lift health <app> | autorestart <app> on|off | monitor
    lift worker add <app> "<cmd>" [--name N] | worker list <app> | worker remove <app> <id>
    lift stats [app]
    lift domain add <app> <domain> | domain list <app> | domain remove <app> <domain>
    lift autodeploy <folder> --name <app> | autodeploy list|remove|check|watch
    lift cron add "<sched>" "<cmd>" | cron list | cron remove <id> | cron run
"""

import json
import os
import re
import shutil
import signal
import socket
import subprocess
import sys
import time
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

LIFT_HOME = os.path.expanduser("~/.lift")
APPS_DIR = os.path.join(LIFT_HOME, "apps")
LOGS_DIR = os.path.join(LIFT_HOME, "logs")
REGISTRY = os.path.join(LIFT_HOME, "apps.json")
PORT_START, PORT_END = 9000, 9999


def ensure_dirs():
    for d in (LIFT_HOME, APPS_DIR, LOGS_DIR):
        os.makedirs(d, exist_ok=True)
    if not os.path.exists(REGISTRY):
        with open(REGISTRY, "w") as f:
            json.dump({}, f)


def load_registry():
    ensure_dirs()
    try:
        with open(REGISTRY) as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}


def save_registry(reg):
    ensure_dirs()
    tmp = REGISTRY + ".tmp"
    with open(tmp, "w") as f:
        json.dump(reg, f, indent=2)
    os.replace(tmp, REGISTRY)


def port_free(port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(("127.0.0.1", port))
        return True
    except OSError:
        return False
    finally:
        s.close()


def pick_port():
    reg = load_registry()
    used = {a["port"] for a in reg.values()}
    for p in range(PORT_START, PORT_END + 1):
        if p not in used and port_free(p):
            return p
    raise RuntimeError("No free ports in range 9000-9999")


def detect_type(folder):
    files = set(os.listdir(folder))
    if "requirements.txt" in files or "app.py" in files or "main.py" in files or "server.py" in files:
        return "python"
    if "package.json" in files:
        return "node"
    if "index.html" in files:
        return "static"
    for root, _, fs in os.walk(folder):
        if "index.html" in fs:
            return "static"
        if os.path.relpath(root, folder).count(os.sep) >= 2:
            break
    return "static"


def find_entry(folder, app_type):
    for cand in ("app.py", "main.py", "server.py", "index.py", "wsgi.py"):
        if os.path.isfile(os.path.join(folder, cand)):
            return cand
    if app_type == "node":
        for cand in ("index.js", "server.js", "app.js", "main.js"):
            if os.path.isfile(os.path.join(folder, cand)):
                return cand
    return None


def _kill_pid(pid):
    if pid_alive(pid):
        try:
            os.killpg(os.getpgid(pid), signal.SIGTERM)
        except (OSError, ProcessLookupError):
            try:
                os.kill(pid, signal.SIGTERM)
            except OSError:
                pass
        for _ in range(20):
            if not pid_alive(pid):
                break
            time.sleep(0.25)


def pid_alive(pid):
    if not pid:
        return False
    try:
        os.kill(pid, 0)
        return True
    except (OSError, ProcessLookupError):
        return False


def _build_env(app_cfg):
    """Base env + PORT + per-app env vars."""
    env = dict(os.environ)
    env["PORT"] = str(app_cfg["port"])
    for k, v in app_cfg.get("env", {}).items():
        env[k] = v
    return env


def _start_workers(app_cfg):
    """Start background workers for an app. Returns list of pids."""
    import subprocess as sp
    pids = []
    for w in app_cfg.get("workers", []):
        log_path = os.path.join(LOGS_DIR, f"{app_cfg['name']}-worker-{w['id']}.log")
        lf = open(log_path, "a")
        env = _build_env(app_cfg)
        proc = sp.Popen(w["command"], shell=True, cwd=app_cfg["dir"],
                        stdout=lf, stderr=sp.STDOUT, env=env, start_new_session=True)
        w["pid"] = proc.pid
        pids.append(proc.pid)
    return pids


def _stop_workers(app_cfg):
    for w in app_cfg.get("workers", []):
        pid = w.get("pid", 0)
        if pid_alive(pid):
            try:
                os.killpg(os.getpgid(pid), signal.SIGTERM)
            except (OSError, ProcessLookupError):
                try:
                    os.kill(pid, signal.SIGTERM)
                except OSError:
                    pass
        w["pid"] = 0


def _launch(app_cfg):
    """Launch the main process for an app. Returns Popen."""
    dest, port, app_type = app_cfg["dir"], app_cfg["port"], app_cfg["type"]
    logf = open(os.path.join(LOGS_DIR, f"{app_cfg['name']}.log"), "a")
    env = _build_env(app_cfg)
    if app_type == "python":
        cmd = [sys.executable, app_cfg.get("entry") or "app.py"]
    elif app_type == "node":
        cmd = [shutil.which("node") or "node", app_cfg.get("entry") or "index.js"]
    else:
        cmd = [sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1"]
    return subprocess.Popen(cmd, cwd=dest, stdout=logf, stderr=subprocess.STDOUT,
                            env=env, start_new_session=True)


def cmd_deploy(args):
    if not args:
        print("Usage: lift deploy <folder> [--name NAME] [--port PORT] [--preview]")
        return 1
    folder = os.path.abspath(args[0])
    if not os.path.isdir(folder):
        print(f"Error: folder not found: {folder}")
        return 1

    name, port, preview = None, None, False
    i = 1
    while i < len(args):
        if args[i] == "--name" and i + 1 < len(args):
            name = re.sub(r"[^a-zA-Z0-9_-]", "-", args[i + 1]).strip("-") or None
            i += 2
        elif args[i] == "--port" and i + 1 < len(args):
            port = int(args[i + 1])
            i += 2
        elif args[i] == "--preview":
            preview = True
            i += 1
        else:
            i += 1
    if not name:
        name = os.path.basename(folder.rstrip("/")) or "app"
        name = re.sub(r"[^a-zA-Z0-9_-]", "-", name).strip("-")
    if preview:
        name = f"{name}-preview-{datetime.now().strftime('%H%M%S')}"

    reg = load_registry()
    if name in reg and pid_alive(reg[name].get("pid", 0)):
        print(f"🔄 Updating '{name}' (zero-downtime)...")
        _stop_workers(reg[name])
        _kill_pid(reg[name].get("pid", 0))
        reg[name]["status"] = "stopped"

    # Snapshot previous version for rollback
    old_dir = os.path.join(APPS_DIR, name)
    if os.path.isdir(old_dir):
        import versions as _v
        _v.snapshot(name, old_dir)

    app_type = detect_type(folder)
    prev_port = reg.get(name, {}).get("port")
    if port is None:
        # redeploy: keep same port (old process already stopped)
        if prev_port and port_free(prev_port):
            port = prev_port
        else:
            port = pick_port()
    elif not port_free(port):
        print(f"Error: port {port} is busy.")
        return 1

    dest = os.path.join(APPS_DIR, name)
    if os.path.isdir(dest):
        shutil.rmtree(dest)
    shutil.copytree(folder, dest, ignore=shutil.ignore_patterns(
        ".git", "__pycache__", "node_modules", ".venv", "venv"))

    if app_type == "python" and not find_entry(dest, "python"):
        print("Error: no python entry file found (app.py / main.py / server.py).")
        return 1
    if app_type == "node":
        if not find_entry(dest, "node"):
            print("Error: no node entry file found.")
            return 1
        if not shutil.which("node"):
            print("Error: node.js not installed.")
            return 1

    # preserve env/workers/domains/autorestart from previous deploy
    prev = reg.get(name, {})
    app_cfg = {
        "name": name,
        "type": app_type,
        "port": port,
        "pid": 0,
        "source": folder,
        "dir": dest,
        "entry": find_entry(dest, app_type) if app_type != "static" else "index.html",
        "deployed_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "status": "running",
        "env": prev.get("env", {}),
        "workers": prev.get("workers", []),
        "domains": prev.get("domains", []),
        "autorestart": prev.get("autorestart", False),
        "restarts": prev.get("restarts", 0),
        "preview": preview,
    }
    proc = _launch(app_cfg)
    time.sleep(1.0)
    if proc.poll() is not None:
        print(f"Error: app exited immediately (code {proc.returncode}). See: lift logs {name}")
        return 1
    app_cfg["pid"] = proc.pid
    _start_workers(app_cfg)
    reg[name] = app_cfg
    save_registry(reg)
    tag = " [PREVIEW]" if preview else ""
    print(f"✅ Deployed '{name}' ({app_type}){tag} → http://localhost:{port}")
    return 0


def cmd_list(_args):
    reg = load_registry()
    if not reg:
        print("No apps deployed yet. Try: lift deploy <folder>")
        return 0
    print(f"{'NAME':<22} {'TYPE':<8} {'PORT':<6} {'STATUS':<9} URL")
    print("-" * 72)
    for name in sorted(reg):
        a = reg[name]
        alive = pid_alive(a.get("pid", 0))
        print(f"{name:<22} {a.get('type','?'):<8} {a.get('port','?'):<6} "
              f"{'running' if alive else 'stopped':<9} http://localhost:{a.get('port','?')}")
    return 0


def cmd_logs(args):
    if not args:
        print("Usage: lift logs <app> [--tail N]")
        return 1
    tail = 50
    if "--tail" in args:
        try:
            tail = int(args[args.index("--tail") + 1])
        except (IndexError, ValueError):
            pass
    log_path = os.path.join(LOGS_DIR, f"{args[0]}.log")
    if not os.path.isfile(log_path):
        print(f"No logs for '{args[0]}'.")
        return 1
    with open(log_path) as f:
        print("".join(f.readlines()[-tail:]), end="")
    return 0


def cmd_stop(args):
    if not args:
        print("Usage: lift stop <app>")
        return 1
    name = args[0]
    reg = load_registry()
    if name not in reg:
        print(f"Unknown app '{name}'.")
        return 1
    a = reg[name]
    _stop_workers(a)
    pid = a.get("pid", 0)
    if pid_alive(pid):
        try:
            os.killpg(os.getpgid(pid), signal.SIGTERM)
        except (OSError, ProcessLookupError):
            try:
                os.kill(pid, signal.SIGTERM)
            except OSError:
                pass
        for _ in range(20):
            if not pid_alive(pid):
                break
            time.sleep(0.25)
    a["status"] = "stopped"
    save_registry(reg)
    print(f"⏹ Stopped '{name}'.")
    return 0


def cmd_start(args):
    if not args:
        print("Usage: lift start <app>")
        return 1
    name = args[0]
    reg = load_registry()
    if name not in reg:
        print(f"Unknown app '{name}'.")
        return 1
    a = reg[name]
    if pid_alive(a.get("pid", 0)):
        print(f"'{name}' is already running.")
        return 0
    proc = _launch(a)
    time.sleep(1.0)
    if proc.poll() is not None:
        print(f"Error: app exited immediately. See: lift logs {name}")
        return 1
    a["pid"] = proc.pid
    a["status"] = "running"
    _start_workers(a)
    save_registry(reg)
    print(f"▶ Started '{name}' → http://localhost:{a['port']}")
    return 0


def cmd_remove(args):
    if not args:
        print("Usage: lift remove <app>")
        return 1
    name = args[0]
    cmd_stop([name])
    reg = load_registry()
    a = reg.pop(name, None)
    save_registry(reg)
    if a and os.path.isdir(a.get("dir", "")):
        shutil.rmtree(a["dir"], ignore_errors=True)
    for suffix in ("", "-worker-*"):
        import glob
        for lp in glob.glob(os.path.join(LOGS_DIR, f"{name}{suffix}.log")):
            os.remove(lp)
    print(f"🗑 Removed '{name}'.")
    return 0


def cmd_info(args):
    if not args:
        print("Usage: lift info <app>")
        return 1
    reg = load_registry()
    if args[0] not in reg:
        print(f"Unknown app '{args[0]}'.")
        return 1
    a = reg[args[0]]
    alive = pid_alive(a.get("pid", 0))
    print(f"Name:     {a['name']}")
    print(f"Type:     {a.get('type')}")
    print(f"Status:   {'running' if alive else 'stopped'} (pid {a.get('pid')})")
    print(f"URL:      http://localhost:{a.get('port')}")
    print(f"Source:   {a.get('source')}")
    print(f"Deployed: {a.get('deployed_at')}")
    print(f"Env vars: {len(a.get('env', {}))}")
    print(f"Workers:  {len(a.get('workers', []))}")
    print(f"Domains:  {', '.join(a.get('domains', [])) or '—'}")
    return 0


# ---- env ----
def cmd_env(args):
    if len(args) < 2:
        print("Usage: lift env set <app> KEY=VAL | env list <app> | env unset <app> KEY")
        return 1
    sub, app = args[0], args[1]
    reg = load_registry()
    if app not in reg:
        print(f"Unknown app '{app}'.")
        return 1
    env = reg[app].setdefault("env", {})
    if sub == "set" and len(args) >= 3:
        if "=" not in args[2]:
            print("Usage: lift env set <app> KEY=VALUE")
            return 1
        k, v = args[2].split("=", 1)
        env[k] = v
        save_registry(reg)
        print(f"✅ {k}={v} set for '{app}' (takes effect on restart)")
        return 0
    if sub == "list":
        if not env:
            print(f"No env vars for '{app}'.")
            return 0
        for k in sorted(env):
            print(f"  {k}={env[k]}")
        return 0
    if sub == "unset" and len(args) >= 3:
        if args[2] in env:
            del env[args[2]]
            save_registry(reg)
            print(f"🗑 Unset {args[2]} for '{app}'.")
        else:
            print(f"'{args[2]}' not set for '{app}'.")
        return 0
    print("Usage: lift env set <app> KEY=VAL | env list <app> | env unset <app> KEY")
    return 1


# ---- worker ----
def cmd_worker(args):
    if len(args) < 2:
        print('Usage: lift worker add <app> "<cmd>" [--name N] | worker list <app> | worker remove <app> <id>')
        return 1
    sub, app = args[0], args[1]
    reg = load_registry()
    if app not in reg:
        print(f"Unknown app '{app}'.")
        return 1
    workers = reg[app].setdefault("workers", [])
    if sub == "add" and len(args) >= 3:
        wname = None
        if "--name" in args:
            try:
                wname = args[args.index("--name") + 1]
            except IndexError:
                pass
        wid = wname or f"worker-{len(workers) + 1}"
        workers.append({"id": wid, "command": args[2], "pid": 0,
                        "added": datetime.now().strftime("%Y-%m-%d %H:%M")})
        save_registry(reg)
        print(f"👷 Worker '{wid}' added to '{app}'. Restart app to start it: lift restart {app}")
        return 0
    if sub == "list":
        if not workers:
            print(f"No workers for '{app}'.")
            return 0
        for w in workers:
            st = "running" if pid_alive(w.get("pid", 0)) else "stopped"
            print(f"  {w['id']}: {w['command']} [{st}]")
        return 0
    if sub == "remove" and len(args) >= 3:
        wid = args[2]
        reg[app]["workers"] = [w for w in workers if w["id"] != wid]
        save_registry(reg)
        print(f"🗑 Worker '{wid}' removed from '{app}'.")
        return 0
    print('Usage: lift worker add <app> "<cmd>" | worker list <app> | worker remove <app> <id>')
    return 1


# ---- rollback ----
def cmd_rollback(args):
    if not args:
        print("Usage: lift rollback <app>")
        return 1
    name = args[0]
    import versions as _v
    vs = _v.list_versions(name)
    if not vs:
        print(f"No versions to roll back for '{name}'.")
        return 1
    ts, _ = vs[0]
    src = os.path.join(_v.VERSIONS_DIR, name, ts)
    cmd_stop([name])
    reg = load_registry()
    dest = reg[name]["dir"]
    shutil.rmtree(dest, ignore_errors=True)
    shutil.copytree(src, dest, ignore=shutil.ignore_patterns(
        ".git", "__pycache__", "node_modules", ".venv", "venv"))
    print(f"⏪ Restored '{name}' to version {ts}")
    return cmd_start([name])


def cmd_restart(args):
    if not args:
        print("Usage: lift restart <app>")
        return 1
    cmd_stop(args)
    return cmd_start(args)


# ---- subcommand dispatch to modules ----
def _mod(name):
    import importlib
    return importlib.import_module(name)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 0
    cmd, args = sys.argv[1], sys.argv[2:]
    handlers = {
        "deploy": cmd_deploy, "list": cmd_list, "logs": cmd_logs,
        "stop": cmd_stop, "start": cmd_start, "remove": cmd_remove,
        "info": cmd_info, "env": cmd_env, "worker": cmd_worker,
        "rollback": cmd_rollback, "restart": cmd_restart,
    }
    if cmd in handlers:
        return handlers[cmd](args)

    # module-based commands
    if cmd == "cron":
        return _mod("cron").main(args)
    if cmd == "db":
        def _set_env(app, k, v):
            reg = load_registry()
            if app in reg:
                reg[app].setdefault("env", {})[k] = v
                save_registry(reg)
        return _mod("db").main(args, _set_env)
    if cmd == "versions":
        return _mod("versions").main(["versions"] + args)
    if cmd == "health":
        return _mod("health").main(["health"] + args)
    if cmd == "autorestart":
        return _mod("health").main(["autorestart"] + args)
    if cmd == "monitor":
        def _restart(name):
            cmd_stop([name])
            cmd_start([name])
        return _mod("health").main(["monitor"], _restart)
    if cmd == "stats":
        return _mod("stats").main(args)
    if cmd == "domain":
        return _mod("domains").main(args)
    if cmd == "autodeploy":
        def _redeploy(name, folder):
            cmd_stop([name])
            # redeploy keeping same name
            cmd_deploy([folder, "--name", name])
        return _mod("autodeploy").main(args, _redeploy)

    print(f"Unknown command '{cmd}'.")
    print("Try: deploy, list, logs, stop, start, restart, remove, info, env,")
    print("     db, versions, rollback, health, autorestart, monitor,")
    print("     worker, stats, domain, autodeploy, cron")
    return 1


if __name__ == "__main__":
    sys.exit(main())
