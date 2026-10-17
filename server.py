#!/usr/bin/env python3
"""Lift Dashboard — web UI. Run: python3 server.py"""
import html, json, os, sys, urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lift

DASH_PORT = 8080

def app_rows():
    reg = lift.load_registry()
    rows = []
    for name in sorted(reg):
        a = reg[name]
        alive = lift.pid_alive(a.get("pid", 0))
        status = "running" if alive else "stopped"
        color = "#16a34a" if alive else "#dc2626"
        rows.append(f"<tr><td><b>{html.escape(name)}</b></td><td>:{a.get('port')}</td><td style='color:{color}'>{status}</td></tr>")
    return "\n".join(rows) or "<tr><td colspan=3>No apps yet</td></tr>"

PAGE = """<!DOCTYPE html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Lift Dashboard</title>
<style>body{font-family:system-ui;max-width:900px;margin:2rem auto;padding:0 1rem}
table{width:100%;border-collapse:collapse}td,th{border:1px solid #ddd;padding:.5rem}th{background:#f5f5f5}</style>
</head><body><h1>Lift Dashboard</h1>
<table><tr><th>App</th><th>Port</th><th>Status</th></tr>%ROWS%</table>
</body></html>"""

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        if self.path == "/":
            body = PAGE.replace("%ROWS%", app_rows())
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(body.encode())
        elif self.path == "/api/apps":
            reg = lift.load_registry()
            data = json.dumps(reg).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(data)
        else:
            self.send_response(404); self.end_headers()

if __name__ == "__main__":
    port = int(sys.argv[sys.argv.index("--port")+1]) if "--port" in sys.argv else DASH_PORT
    print(f"Lift dashboard -> http://localhost:{port}")
    HTTPServer(("127.0.0.1", port), Handler).serve_forever()
