from __future__ import annotations

import argparse
import http.server
import socketserver
from functools import partial
from pathlib import Path

from build_static_site import OUT_PATH, main as build_static_site


ROOT = Path(__file__).resolve().parent
DOCS_DIR = ROOT / "docs"


class ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build and serve the static BTS dashboard.",
    )
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind. Default: 127.0.0.1")
    parser.add_argument("--port", type=int, default=8501, help="Port to bind. Default: 8501")
    parser.add_argument(
        "--no-build",
        action="store_true",
        help="Serve the existing docs/index.html without rebuilding from the CSV.",
    )
    return parser.parse_args()


def ensure_static_dashboard(skip_build: bool) -> None:
    if not skip_build:
        build_static_site()
    if not OUT_PATH.exists():
        raise FileNotFoundError(f"Static dashboard was not found: {OUT_PATH}")


def serve(host: str, port: int) -> None:
    handler = partial(http.server.SimpleHTTPRequestHandler, directory=str(DOCS_DIR))
    with ReusableTCPServer((host, port), handler) as server:
        print(f"Serving static dashboard at http://{host}:{port}/")
        print(f"Document root: {DOCS_DIR}")
        server.serve_forever()


def main() -> None:
    args = parse_args()
    ensure_static_dashboard(args.no_build)
    serve(args.host, args.port)


if __name__ == "__main__":
    main()
