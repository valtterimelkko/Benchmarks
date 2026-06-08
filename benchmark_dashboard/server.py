from __future__ import annotations

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLIC_DIR = ROOT / "public"


class DashboardHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, directory: str | None = None, **kwargs):
        super().__init__(*args, directory=directory or str(PUBLIC_DIR), **kwargs)

    def do_GET(self):  # noqa: N802 - stdlib API
        if self.path in {"/healthz", "/health"}:
            body = b"ok\n"
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)
            return
        return super().do_GET()

    def end_headers(self):
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")
        self.send_header("Cache-Control", "public, max-age=300")
        super().end_headers()


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve the static benchmark dashboard.")
    parser.add_argument("--host", default="172.18.0.1", help="Bind host. Use Docker bridge gateway for Caddy access.")
    parser.add_argument("--port", type=int, default=8766, help="Bind port.")
    parser.add_argument("--directory", default=str(PUBLIC_DIR), help="Static directory to serve.")
    args = parser.parse_args()
    directory = str(Path(args.directory).resolve())
    handler = partial(DashboardHandler, directory=directory)
    server = ThreadingHTTPServer((args.host, args.port), handler)
    print(f"Serving benchmark dashboard from {directory} on http://{args.host}:{args.port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
