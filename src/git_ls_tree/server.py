"""Local HTTP server that serves the viewer page and the temporary JSON data file."""

from __future__ import annotations

import importlib.resources
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


def _load_index() -> bytes:
    return (
        importlib.resources.files("git_ls_tree")
        .joinpath("assets/index.html")
        .read_bytes()
    )


def make_server(data_path: Path, port: int) -> ThreadingHTTPServer:
    index_html = _load_index()

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            if self.path in ("/", "/index.html"):
                self._send(200, "text/html; charset=utf-8", index_html)
            elif self.path == "/data.json":
                try:
                    body = data_path.read_bytes()
                except OSError:
                    self._send(500, "text/plain", b"data file unavailable")
                    return
                self._send(200, "application/json", body)
            else:
                self._send(404, "text/plain", b"not found")

        def _send(self, status: int, content_type: str, body: bytes) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args) -> None:
            pass  # keep the terminal quiet while serving

    return ThreadingHTTPServer(("127.0.0.1", port), Handler)
