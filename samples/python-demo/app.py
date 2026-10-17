"""Sample Python app for Lift — reads PORT from env, stdlib only."""
import os
from http.server import BaseHTTPRequestHandler, HTTPServer

PORT = int(os.environ.get("PORT", 8000))


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        body = "<h1>Lift Python Demo</h1><p>Python app deployed via Lift!</p>".encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    print(f"Python demo listening on port {PORT}", flush=True)
    HTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
