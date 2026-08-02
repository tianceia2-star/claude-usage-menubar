"""網頁面板的 HTTP server，供 usage_server.py 與 menu_bar_app.py 共用。"""
import json
import threading
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import usage_core

PORT = 8765
BASE_DIR = Path(__file__).resolve().parent
DASHBOARD_HTML = BASE_DIR / "dashboard.html"


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def _send_json(self, payload, status=200):
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/":
            html = DASHBOARD_HTML.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(html)))
            self.end_headers()
            self.wfile.write(html)
        elif self.path == "/api/usage":
            payload = usage_core.get_state_snapshot()
            payload["server_time"] = datetime.now(timezone.utc).isoformat()
            self._send_json(payload)
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == "/api/refresh":
            t = threading.Thread(target=usage_core.refresh_state, kwargs={"force": False})
            t.start()
            t.join(timeout=15)
            self._send_json(usage_core.get_state_snapshot())
        else:
            self.send_response(404)
            self.end_headers()


def start_server_thread():
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    return server
