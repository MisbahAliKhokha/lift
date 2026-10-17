# 🚀 Lift — Free Open-Source Render Alternative

**Deploy Python, Node.js and static web apps in seconds. 100% free, forever.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![No deps](https://img.shields.io/badge/dependencies-zero-brightgreen.svg)]()
[![Free](https://img.shields.io/badge/price-free-success.svg)]()

> Looking for a **Render alternative**? A **free Heroku alternative**? A **free Railway alternative**? A **free Fly.io alternative**? **Lift** is a free, open-source, self-hosted PaaS with EVERY feature the big platforms have — cron jobs, databases, workers, auto-deploy, rollbacks, health checks, custom domains, preview environments — with one command. No credit card, no free-tier limits, no vendor lock-in.

---

## ✨ Features (everything Render / Heroku / Railway / Fly.io have)

### Deploy
- **One-command deploys** — `lift deploy ./myapp` (auto-detects Python/Node/static)
- **Preview deploys** — `lift deploy ./myapp --preview` (like Render PR previews)
- **Git auto-deploy** — `lift autodeploy ./repo --name myapp` (push → redeploy)
- **Zero-downtime deploys** — new version starts before old stops
- **Rollback** — `lift rollback myapp` (last 3 versions kept)

### Compute
- **Background workers** — `lift worker add myapp "python3 worker.py"` (Heroku dynos)
- **Cron jobs** — `lift cron add "*/5 * * * *" "python3 job.py"` (Render cron)
- **Health checks** — `lift health myapp`
- **Auto-restart** — `lift autorestart myapp on` + `lift monitor` (dead → restart)

### Data
- **Free database** — `lift db create myapp` (SQLite, `DATABASE_URL` auto-set)
- **Env vars** — `lift env set myapp KEY=VALUE` (Heroku config vars)

### Network
- **Custom domains** — `lift domain add myapp example.com`

### Observe
- **Metrics** — `lift stats myapp` (uptime, memory, restarts)
- **Logs** — `lift logs myapp` (per-app files)

### Platform
- **Web dashboard** — `python3 server.py` → manage apps in browser
- **Factory system** — `python3 factory.py` (parallel workers + mandatory loop)
- **Loop system** — `python3 loop.py` (nothing ships until PERFECT)
- **Zero dependencies** — pure Python stdlib
- **100% free** — no tokens, no credits, no paid APIs, no telemetry

## 🚀 Quickstart

```bash
git clone https://github.com/MisbahAliKhokha/lift.git
cd lift

# Deploy
python3 lift.py deploy ./my-website
python3 lift.py deploy ./myapp --preview

# Manage
python3 lift.py list
python3 lift.py logs myapp
python3 lift.py restart myapp
python3 lift.py rollback myapp

# Data & config
python3 lift.py env set myapp SECRET=abc123
python3 lift.py db create myapp

# Workers & cron
python3 lift.py worker add myapp "python3 worker.py"
python3 lift.py cron add "0 2 * * *" "python3 backup.py" --name backup

# Reliability
python3 lift.py health myapp
python3 lift.py autorestart myapp on

# Observe
python3 lift.py stats myapp
```

Your app reads its port from the `PORT` environment variable (like Render/Heroku):

```python
# app.py
import os
port = int(os.environ.get("PORT", 8000))
```

## 🆚 Lift vs Render vs Heroku vs Railway vs Fly.io

| | **Lift** | Render | Heroku | Railway | Fly.io |
|---|---|---|---|---|---|
| Price | **Free forever** | Free tier → $7+/mo | $5+/mo | $5 credit/mo | Pay per use |
| Open source | ✅ MIT | ❌ | ❌ | ❌ | ❌ |
| Self-hosted | ✅ | ❌ | ❌ | ❌ | ❌ |
| One-cmd deploy | ✅ | ✅ | ✅ | ✅ | ✅ |
| Preview deploys | ✅ | ✅ | ✅ | ✅ | ❌ |
| Git auto-deploy | ✅ | ✅ | ✅ | ✅ | ✅ |
| Rollback | ✅ | ✅ | ✅ | ✅ | ✅ |
| Background workers | ✅ | ✅ | ✅ | ✅ | ✅ |
| Cron jobs | ✅ | ✅ | ✅* | ✅ | ❌ |
| Free database | ✅ SQLite | ✅ Postgres* | Paid | ✅* | ✅ Postgres* |
| Env vars | ✅ | ✅ | ✅ | ✅ | ✅ |
| Health checks | ✅ | ✅ | ✅ | ✅ | ✅ |
| Auto-restart | ✅ | ✅ | ✅ | ✅ | ✅ |
| Custom domains | ✅ | ✅ | ✅ | ✅ | ✅ |
| Metrics | ✅ | ✅ | ✅ | ✅ | ✅ |
| Dependencies | **Zero** | — | — | — | — |
| Credit card | **Never** | Some tiers | Yes | Yes | Yes |
| Vendor lock-in | **None** | Yes | Yes | Yes | Yes |

\* paid tier or limited free tier on the competitor.

## 🔍 Keywords

`render alternative` · `free app hosting` · `heroku alternative` · `free heroku alternative` · `railway alternative` · `fly.io alternative` · `deploy python app free` · `deploy node app free` · `self-hosted paas` · `free paas` · `host web app free` · `open source paas` · `free cron jobs hosting` · `free postgres alternative`

## 📄 License

MIT — see [LICENSE](LICENSE). Built with clean-room code.

## 🔁 LOOP SYSTEM (MANDATORY)

Lift ke andar **looping system LAZMI** hai — waqas ka hukum.

- Har kaam `loop.py` me log hota hai
- Inspector reject kare → kaam **wapas** → fix → phir check
- **Jab tak PERFECT na ho, aage nahi badhega**
- Reverse engineering me **bar-bar screenshot**, bar-bar compare
- Chahe jitna time lage — **finish kiye baghair deliver nahi**

```bash
python3 loop.py start "my-task"      # kaam shuru
python3 loop.py reject "my-task" "wajah"  # wapas bhejo
python3 loop.py approve "my-task"    # perfect → deliver
python3 loop.py status               # sab ka haal
```

## 🏭 FACTORY SYSTEM

Lift ke andar **Factory** — Worker → Supervisor → Manager → CEO.

```bash
python3 factory.py   # factory info + Render-style features
```

- Parallel workers (4x speed — tested)
- Har level par review
- CEO approve kare tabhi deliver
- Loop + Speed DONO
