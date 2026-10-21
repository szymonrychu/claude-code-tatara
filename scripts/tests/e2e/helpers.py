"""Shared e2e helpers."""

import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]


def run(*args, cwd, check=True, **kw):
    p = subprocess.run(list(args), cwd=cwd, capture_output=True, text=True, **kw)
    if check:
        assert p.returncode == 0, f"{args}: {p.stdout}\n{p.stderr}"
    return p


def git(*args, cwd):
    return run("git", *args, cwd=cwd).stdout.strip()
