"""Loopback-only demonstration server; no mission-command endpoint."""

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from .__main__ import ROOT, demo
from .solver import repair


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def reply(self, code, data, kind="application/json"):
        content = data if isinstance(data, bytes) else json.dumps(data).encode()
        self.send_response(code)
        self.send_header("Content-Type", kind + "; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/demo":
            return self.reply(200, demo())
        if path in ("/", "/app.js", "/style.css"):
            file = "index.html" if path == "/" else path[1:]
            kind = {"index.html": "text/html", "app.js": "text/javascript", "style.css": "text/css"}[file]
            return self.reply(200, (ROOT / "web" / file).read_bytes(), kind)
        self.reply(404, {"error": "not_found", "messages": ["Introuvable", "Not found", "No encontrado"]})

    def do_POST(self):
        if self.path != "/api/repair":
            return self.reply(404, {"error": "not_found"})
        origin = self.headers.get("Origin")
        if origin and origin != f"http://127.0.0.1:{self.server.server_port}":
            return self.reply(403, {"error": "origin_denied"})
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if not 0 < size <= 200_000:
                raise ValueError("invalid_size")
            case = json.loads(self.rfile.read(size))
            self.reply(200, repair(case, seconds=3))
        except (ValueError, KeyError, TypeError) as error:
            self.reply(400, {"error": str(error) if str(error).startswith("invalid_") else "invalid_input",
                             "messages": ["Entrée non valide", "Invalid input", "Entrada no válida"]})


def serve(port=8764):
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()
