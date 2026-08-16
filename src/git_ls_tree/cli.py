"""Command-line entry point for git-ls-tree."""

from __future__ import annotations

import argparse
import atexit
import json
import os
import sys
import tempfile
import webbrowser
from pathlib import Path

from . import __version__
from .gitdata import GitError, build_payload
from .server import make_server


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="git-ls-tree",
        description=(
            "Browse the file tree of the current git repository across all "
            "branches in a local webpage."
        ),
    )
    parser.add_argument(
        "--remotes",
        action="store_true",
        help="also include remote-tracking branches",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=0,
        help="port to serve on (default: a free port chosen by the OS)",
    )
    parser.add_argument(
        "--no-open",
        action="store_true",
        help="do not open the page in a browser automatically",
    )
    parser.add_argument("--version", action="version", version=__version__)
    args = parser.parse_args(argv)

    try:
        payload = build_payload(include_remotes=args.remotes)
    except GitError as exc:
        print(f"git-ls-tree: error: {exc}", file=sys.stderr)
        return 1

    fd, raw_path = tempfile.mkstemp(prefix="git-ls-tree-", suffix=".json")
    data_path = Path(raw_path)

    def cleanup() -> None:
        data_path.unlink(missing_ok=True)

    atexit.register(cleanup)
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        json.dump(payload, fh)

    try:
        server = make_server(data_path, args.port)
    except OSError as exc:
        print(f"git-ls-tree: error: cannot bind port {args.port}: {exc}", file=sys.stderr)
        return 1

    url = f"http://127.0.0.1:{server.server_address[1]}/"
    print(
        f"{payload['repo']}: {len(payload['files'])} files across "
        f"{len(payload['branches'])} branches"
    )
    print(f"Serving on {url} — Ctrl+C to stop")
    print(f"Temporary data file: {data_path} (deleted on exit)")

    if not args.no_open:
        webbrowser.open(url)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping.")
    finally:
        server.server_close()
        cleanup()
    return 0


if __name__ == "__main__":
    sys.exit(main())
