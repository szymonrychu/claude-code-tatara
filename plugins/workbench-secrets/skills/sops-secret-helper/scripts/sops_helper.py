#!/usr/bin/env python3
"""Edit SOPS-encrypted YAML files without ever exposing secret values.

Subcommands:
  keys <file>                      list key paths (names only, never values)
  set <file> <key-path> [--from-env VAR]
                                   value from stdin or $VAR, applied with `sops set`
  remove <file> <key-path>         applied with `sops unset`

The file must match a `path_regex` creation rule in the nearest `.sops.yaml`.
This helper never decrypts: `keys` reads the plaintext key names of the
encrypted file, and `set`/`remove` only hand edits to `sops`.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

KEY_SEGMENT = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_\-]*$")


def die(msg: str) -> None:
    print(f"sops_helper: {msg}", file=sys.stderr)
    raise SystemExit(1)


def find_config(start: Path) -> Path:
    for d in [start, *start.parents]:
        cand = d / ".sops.yaml"
        if cand.is_file():
            return cand
    die("no .sops.yaml found above the file")
    raise AssertionError


def path_regexes(config: Path) -> list[str]:
    """Collect every `path_regex` value with a line parser (no YAML dependency)."""
    out = []
    for line in config.read_text().splitlines():
        m = re.match(r"^\s*(?:-\s+)?path_regex:\s*(.*?)\s*$", line)
        if not m:
            continue
        val = m.group(1)
        if len(val) >= 2 and val[0] == val[-1] and val[0] in "'\"":
            q, val = val[0], val[1:-1]
            val = val.replace("''", "'") if q == "'" else val.replace("\\\\", "\\")
        else:
            val = re.sub(r"\s+#.*$", "", val)
        out.append(val)
    return out


def check_file(arg: str) -> Path:
    path = Path(arg).resolve()
    if not path.is_file():
        die(f"file not found: {arg}")
    config = find_config(path.parent)
    rel = (
        path.relative_to(config.parent).as_posix()
        if path.is_relative_to(config.parent)
        else path.as_posix()
    )
    for rx in path_regexes(config):
        try:
            if re.search(rx, rel):
                return path
        except re.error:
            continue
    die(f"{arg} matches no path_regex creation rule in {config}; refusing")
    raise AssertionError


def sops_path(key_path: str) -> str:
    segs = key_path.split(".")
    if not all(KEY_SEGMENT.match(s) for s in segs):
        die(f"invalid key path {key_path!r}: use dot-separated names ([A-Za-z0-9_-])")
    return "".join(f'["{s}"]' for s in segs)


def list_keys(path: Path) -> list[str]:
    """Key paths from the plaintext structure of an encrypted YAML file."""
    paths: list[str] = []
    stack: list[tuple[int, str]] = []
    for line in path.read_text().splitlines():
        if not line.strip() or line.lstrip().startswith(("#", "-")):
            continue
        m = re.match(r"^(\s*)([A-Za-z0-9_][A-Za-z0-9_\-]*):(\s|$)", line)
        if not m:
            continue
        indent = len(m.group(1))
        while stack and stack[-1][0] >= indent:
            stack.pop()
        stack.append((indent, m.group(2)))
        if indent == 0 and m.group(2) == "sops":
            stack = [(0, "sops")]
        paths.append(".".join(k for _, k in stack))
    top_sops = [p for p in paths if p == "sops" or p.startswith("sops.")]
    names = [p for p in paths if p not in top_sops]
    # Keep only leaves: drop any path that is a prefix of another.
    return [p for p in names if not any(o.startswith(p + ".") for o in names)]


def run_sops(args: list[str]) -> None:
    r = subprocess.run(["sops", *args], capture_output=True, text=True)
    if r.returncode != 0:
        # sops stderr carries no values for set/unset; keep it short.
        die(f"sops failed ({r.returncode}): {r.stderr.strip()[:300]}")


def read_value(from_env: str | None) -> str:
    if from_env:
        if from_env not in os.environ:
            die(f"environment variable {from_env} is not set")
        value = os.environ[from_env]
    else:
        value = sys.stdin.read().rstrip("\n")
    if not value:
        die("empty value refused")
    return value


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    k = sub.add_parser("keys")
    k.add_argument("file")
    s = sub.add_parser("set")
    s.add_argument("file")
    s.add_argument("key_path")
    s.add_argument("--from-env", metavar="VAR")
    r = sub.add_parser("remove")
    r.add_argument("file")
    r.add_argument("key_path")
    a = ap.parse_args(argv)

    path = check_file(a.file)
    if a.cmd == "keys":
        for p in list_keys(path):
            print(p)
    elif a.cmd == "set":
        sp = sops_path(a.key_path)
        run_sops(["set", str(path), sp, json.dumps(read_value(a.from_env))])
        print(f"set {a.key_path} in {a.file}")
    else:
        run_sops(["unset", str(path), sops_path(a.key_path)])
        print(f"removed {a.key_path} from {a.file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
