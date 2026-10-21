#!/usr/bin/env python3
"""Write a gitignored .env from a committed .env.op reference file.

Uses `op inject` (1Password CLI) or the command in WORKBENCH_SECRETS_CMD
(called with the reference file path as its only argument; stdout is the
dotenv content). Never prints secret values, only key names and a count.
"""

from __future__ import annotations

import argparse
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def git(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)


def check_out_path(out: Path) -> str | None:
    """Return a refusal message, or None when out is safe to write."""
    cwd = out.parent if out.parent.is_dir() else Path.cwd()
    if git(["rev-parse", "--is-inside-work-tree"], cwd).returncode != 0:
        return f"{out} is not inside a git work tree; cannot confirm it is ignored"
    if git(["ls-files", "--error-unmatch", out.name], cwd).returncode == 0:
        return f"{out} is tracked by git; refusing to write secrets into it"
    if git(["check-ignore", "-q", out.name], cwd).returncode != 0:
        return f"{out} is not ignored by git; add it to .gitignore first"
    return None


def key_names(path: Path) -> list[str]:
    keys = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key = line.split("=", 1)[0].strip()
        if key.startswith("export "):
            key = key[len("export ") :].strip()
        keys.append(key)
    return keys


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ref", default=".env.op", help="reference file (default .env.op)")
    ap.add_argument("--out", default=".env", help="output file (default .env)")
    args = ap.parse_args(argv)

    ref, out = Path(args.ref).resolve(), Path(args.out).resolve()
    loader = os.environ.get("WORKBENCH_SECRETS_CMD", "").strip()
    if not loader and not shutil.which("op"):
        print(
            "error: neither the 1Password CLI `op` nor WORKBENCH_SECRETS_CMD is available",
            file=sys.stderr,
        )
        return 2
    if not ref.is_file():
        print(f"error: reference file {ref} not found", file=sys.stderr)
        return 2
    refusal = check_out_path(out)
    if refusal:
        print(f"error: {refusal}", file=sys.stderr)
        return 3

    fd, tmp_name = tempfile.mkstemp(dir=out.parent, prefix=".secrets-env-")
    os.close(fd)
    tmp = Path(tmp_name)
    try:
        os.chmod(tmp, 0o600)
        if loader:
            with tmp.open("wb") as fh:
                res = subprocess.run(
                    [*shlex.split(loader), str(ref)], stdout=fh, stderr=subprocess.PIPE, text=True
                )
        else:
            res = subprocess.run(
                ["op", "inject", "-f", "-i", str(ref), "-o", str(tmp)],
                capture_output=True,
                text=True,
            )
        if res.returncode != 0:
            print(f"error: secrets loader failed (exit {res.returncode})", file=sys.stderr)
            return 4
        os.chmod(tmp, 0o600)
        keys = key_names(tmp)
        os.replace(tmp, out)
    finally:
        tmp.unlink(missing_ok=True)

    print(f"wrote {out} with {len(keys)} keys")
    for k in keys:
        print(f"  {k}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
