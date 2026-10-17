# 🚀 Lift — Free Open-Source Render Alternative

**Deploy Python, Node.js and static web apps in seconds. 100% free, forever.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![No deps](https://img.shields.io/badge/dependencies-zero-brightgreen.svg)]()
[![Free](https://img.shields.io/badge/price-free-success.svg)]()

> Looking for a **Render alternative**? A **free Heroku alternative**? **Lift** is a free, open-source, self-hosted PaaS that deploys your apps with one command — no credit card, no free-tier limits, no vendor lock-in.

---

## ✨ Features

- **One-command deploys** — `lift deploy ./myapp` and you're live
- **Auto-detection** — Python (`requirements.txt`/`app.py`), Node.js (`package.json`), or static sites (`index.html`)
- **Web dashboard** — manage apps, view logs, start/stop from your browser
- **Per-app logs** — every app gets its own log file
- **Auto port assignment** — no port conflicts, ever
- **Zero dependencies** — pure Python stdlib, runs anywhere Python runs
- **100% free** — no tokens, no credits, no paid APIs, no telemetry

## 🚀 Quickstart

```bash
git clone https://github.com/MisbahAliKhokha/lift.git
cd lift

# Deploy a static site
python3 lift.py deploy ./my-website

# Deploy a Python app
python3 lift.py deploy ./my-python-app

# Deploy a Node.js app
python3 lift.py deploy ./my-node-app

# Manage
python3 lift.py list
python3 lift.py logs myapp
python3 lift.py stop myapp
python3 lift.py start myapp
python3 lift.py remove myapp

# Web dashboard
python3 server.py
```

## 🆚 Lift vs Render vs Heroku vs Railway

| | **Lift** | Render | Heroku | Railway |
|---|---|---|---|---|
| Price | **Free forever** | Free tier, then $7+/mo | $5+/mo | $5 credit/mo |
| Open source | ✅ MIT | ❌ | ❌ | ❌ |
| Self-hosted | ✅ | ❌ | ❌ | ❌ |
| Dependencies | **Zero** | — | — | — |
| Credit card | **Never** | Some tiers | Yes | Yes |
| Vendor lock-in | **None** | Yes | Yes | Yes |

## 🔁 LOOP SYSTEM (MANDATORY)

Lift has a mandatory looping system — every task runs in a loop until PERFECT. No unfinished work is ever delivered.

```bash
python3 loop.py start "my-task"
python3 loop.py reject "my-task" "reason"
python3 loop.py approve "my-task"
python3 loop.py status
```

## 📄 License

MIT — see LICENSE.

---
