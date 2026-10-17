#!/usr/bin/env python3
"""
🔗 LIFT DOMAINS — custom domains like Render/Heroku/Railway.
Stores domain config per app (for reverse proxy / DNS setup).

Usage:
    lift domain add <app> example.com
    lift domain list <app>
    lift domain remove <app> example.com
"""
import json
import os
import re
import sys

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


def _valid(domain):
    return re.match(r"^(?!-)[a-z0-9-]{1,63}(?<!-)(\.[a-z0-9-]{1,63})+$", domain.lower()) is not None


def cmd_add(app, domain):
    reg = _load()
    if app not in reg:
        print(f"Unknown app '{app}'.")
        return 1
    domain = domain.lower()
    if not _valid(domain):
        print(f"Invalid domain '{domain}'.")
        return 1
    domains = reg[app].setdefault("domains", [])
    if domain in domains:
        print(f"'{domain}' already added for '{app}'.")
        return 0
    domains.append(domain)
    _save(reg)
    print(f"🔗 Domain '{domain}' → '{app}' (port {reg[app]['port']})")
    print("   DNS: point an A/CNAME record to your server IP.")
    print("   Reverse proxy (nginx/caddy) should forward to "
          f"127.0.0.1:{reg[app]['port']}.")
    return 0


def cmd_list(app):
    reg = _load()
    if app not in reg:
        print(f"Unknown app '{app}'.")
        return 1
    domains = reg[app].get("domains", [])
    if not domains:
        print(f"No custom domains for '{app}'.")
        return 0
    print(f"Domains for '{app}':")
    for d in domains:
        print(f"  • {d} → 127.0.0.1:{reg[app]['port']}")
    return 0


def cmd_remove(app, domain):
    reg = _load()
    if app not in reg:
        print(f"Unknown app '{app}'.")
        return 1
    domains = reg[app].get("domains", [])
    if domain.lower() not in domains:
        print(f"'{domain}' not found for '{app}'.")
        return 1
    domains.remove(domain.lower())
    _save(reg)
    print(f"🗑 Removed '{domain}' from '{app}'.")
    return 0


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 0
    cmd, app = argv[0], argv[1]
    if cmd == "add" and len(argv) >= 3:
        return cmd_add(app, argv[2])
    if cmd == "list":
        return cmd_list(app)
    if cmd == "remove" and len(argv) >= 3:
        return cmd_remove(app, argv[2])
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
