"""Collect file listings across all branches of a git repository."""

from __future__ import annotations

import os
import subprocess
from datetime import datetime, timezone


class GitError(Exception):
    """Raised when git is unavailable or the current directory is not a repository."""


def _git(*args: str) -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            capture_output=True,
            text=True,
            check=True,
        )
    except FileNotFoundError:
        raise GitError("git executable not found on PATH") from None
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.strip() or f"git {' '.join(args)} failed"
        raise GitError(stderr) from None
    return result.stdout


def list_branches(include_remotes: bool = False) -> list[str]:
    refs = ["refs/heads"]
    if include_remotes:
        refs.append("refs/remotes")
    out = _git("for-each-ref", "--format=%(refname:short)", *refs)
    branches = []
    for name in out.splitlines():
        name = name.strip()
        # Skip symbolic refs like origin/HEAD
        if not name or name == "HEAD" or name.endswith("/HEAD"):
            continue
        branches.append(name)
    return branches


def list_files(branch: str) -> list[str]:
    out = _git("ls-tree", "-r", "-z", "--name-only", branch)
    return [path for path in out.split("\0") if path]


def get_remote_info() -> dict:
    """Return the origin remote name, its normalized HTTPS URL, and all remote names."""
    try:
        all_remotes = [r for r in _git("remote").splitlines() if r.strip()]
    except GitError:
        return {"remote_name": None, "remote_url": None, "all_remotes": []}

    if not all_remotes:
        return {"remote_name": None, "remote_url": None, "all_remotes": []}

    preferred = "origin" if "origin" in all_remotes else all_remotes[0]

    try:
        url = _git("remote", "get-url", preferred).strip()
    except GitError:
        return {"remote_name": preferred, "remote_url": None, "all_remotes": all_remotes}

    if url.startswith("git@"):
        url = "https://" + url.removeprefix("git@").replace(":", "/", 1)
    url = url.removesuffix(".git")

    return {"remote_name": preferred, "remote_url": url, "all_remotes": all_remotes}


def collect() -> dict:
    """Verify the cwd is a git repository, or raise GitError."""
    _git("rev-parse", "--is-inside-work-tree")
    toplevel = _git("rev-parse", "--show-toplevel").strip()
    return {"repo": os.path.basename(toplevel)}


def build_payload(include_remotes: bool = False) -> dict:
    meta = collect()
    branches = list_branches(include_remotes)
    if not branches:
        raise GitError("no branches found (does the repository have any commits?)")

    files: dict[str, list[int]] = {}
    for index, branch in enumerate(branches):
        for path in list_files(branch):
            files.setdefault(path, []).append(index)

    remote = get_remote_info()

    return {
        "repo": meta["repo"],
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "branches": branches,
        "files": files,
        "remote_url": remote["remote_url"],
        "remote_name": remote["remote_name"],
        "all_remotes": remote["all_remotes"],
    }
