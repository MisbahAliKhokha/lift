#!/usr/bin/env python3
"""
Lift Dashboard — simple web UI for the Lift deploy system.
Stdlib only. Run:  python3 server.py [--port 8080]
"""

import html
import json
import os
import sys
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lift  # noqa: E402  (reuses registry + process helpers)

DASH_PORT = 8080


def app_rows():
    reg = lift.load_registry()
    rows = []
    for name in sorted(reg):
        a = reg[name]
        alive = lift.pid_alive(a.get("pid", 0))
        status = "running" if alive else "stopped"
        color = "#16a34a" if alive else "#dc2626"
        rows.append(f"""
        <tr>
          <td><b>{html.escape(name)}</b><br><small>{html.escape(str(a.get('type','')))}</small></td>
          <td><a href="http://localhost:{a.get('port')}" target="_blank">:{a.get('port')}</a></td>
          <td style="color:{color};font-weight:bold">● {status}</td>
          <td>
            <form style="display:inline" method="post" action="/action"><input type="hidden" name="app" value="{html.escape(name)}"><button name="op" value="logs">Logs</button></form>
            <form style="display:inline" method="post" action="/action"><input type="hidden" name="app" value="{html.escape(name)}"><button name="op" value="stop">Stop</button></form>
            <form style="display:inline" method="post" action="/action"><input type="hidden" name="app" value="{html.escape(name)}"><button name="op" value="start">Start</button></form>
            <form style="display:inline" method="post" action="/action" onsubmit="return confirm('Remove {html.escape(name)}?')"><input type="hidden" name="app" value="{html.escape(name)}"><button name="op" value="remove">Remove</button></form>
          </td>
        </tr>""")
    return "\n".join(rows) or '<tr><td colspan="4">No apps yet. Deploy one below ↓</td></tr>'


PAGE = """<!DOCTYPE html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Lift — Free App Hosting Dashboard</title>
<style>
body{font-family:system-ui,sans-serif;max-width:900px;margin:2rem auto;padding:0 1rem;color:#111}
h1{font-size:1.6rem} table{width:100%;border-collapse:collapse;margin:1rem 0}
td,th{border:1px solid #ddd;padding:.5rem;text-align:left}th{background:#f5f5f5}
button{padding:.3rem .7rem;margin:.1rem;cursor:pointer}
input[type=text]{padding:.4rem;width:300px}
pre{background:#111;color:#0f0;padding:1rem;overflow:auto;max-height:400px;border-radius:6px}
.card{border:1px solid #ddd;border-radius:8px;padding:1rem;margin:1rem 0}
small{color:#666}
</style></head><body>
<h1>🚀 Lift Dashboard</h1>
<p><small>Free open-source app hosting — deploy python / node / static apps in seconds.</small></p>
<div class="card"><h3>Deployed apps</h3>
<table><tr><th>App</th><th>Port</th><th>Status</th><th>Actions</th></tr>
%ROWS%
</table></div>
<div class="card"><h3>Deploy new app</h3>
<form method="post" action="/deploy">
<input type="text" name="folder" placeholder="/path/to/app/folder" required>
<input type="text" name="name" placeholder="app-name (optional)" style="width:180px">
<button>Deploy</button></form>
<small>CLI: <code>python3 lift.py deploy &lt;folder&gt;</code></small></div>
%LOGS%
</body></html>"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _page(self, logs_html=""):
        body = PAGE.replace("%ROWS%", app_rows()).replace("%LOGS%", logs_html)
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(body.encode())

    def do_GET(self):
        if self.path == "/":
            self._page()
        elif self.path == "/api/apps":
            reg = lift.load_registry()
            out = {n: {**a, "alive": lift.pid_alive(a.get("pid", 0))} for n, a in reg.items()}
            data = json.dumps(out).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(data)
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        form = urllib.parse.parse_qs(self.rfile.read(length).decode())
        get = lambda k: form.get(k, [""])[0]

        if self.path == "/deploy":
            folder, name = get("folder"), get("name")
            args = [folder] + (["--name", name] if name else [])
            rc = lift.cmd_deploy(args)
            msg = "deployed" if rc == 0 else "deploy failed — check CLI output"
            self._page(f'<div class="card"><b>Deploy {html.escape(msg)}</b></div>')
        elif self.path == "/action":
            app, op = get("app"), get("op")
            if op == "logs":
                lp = os.path.join(lift.LOGS_DIR, f"{app}.log")
                content = ""
                if os.path.isfile(lp):
                    with open(lp) as f:
                        content = "".join(f.readlines()[-80:])
                logs_html = (f'<div class="card"><h3>Logs: {html.escape(app)}</h3>'
                             f'<pre>{html.escape(content) or "(empty)"}</pre></div>')
                self._page(logs_html)
            else:
                {"stop": lift.cmd_stop, "start": lift.cmd_start,
                 "remove": lift.cmd_remove}[op]([app])
                self.send_response(303)
                self.send_header("Location", "/")
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()


if __name__ == "__main__":
    port = int(sys.argv[sys.argv.index("--port") + 1]) if "--port" in sys.argv else DASH_PORT
    print(f"🚀 Lift dashboard → http://localhost:{port}")
    HTTPServer(("127.0.0.1", port), Handler).serve_forever()
