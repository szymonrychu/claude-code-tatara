#!/usr/bin/env python3
"""Fail when a tracked text file holds a denylisted personal reference.

Usage: check_personal.py [--root DIR]

Reads DIR/scripts/personal-denylist.json (falling back to the file next to this
script): {"patterns": [...], "hashes": [...], "allow": [...]}. "hashes" holds
SHA-256 hex digests of lowercased private terms, so the file never publishes
them: each line is cut into words (alphanumerics and underscore), every run of up to MAX_WORDS
adjacent words with no whitespace between them (original separators kept, so
hyphenated names stay whole) is hashed, and a digest match is reported as
"path:line: <digest>". A pattern is a string (matched
case-insensitively, as a whole token: no word character directly outside either
end) or {"name": ..., "regex": ...} for shapes a literal cannot express. An allow
entry is {"path": <glob>, "pattern": <optional name or digest>, "line_contains": <optional
substring>}; "**" crosses directories, "*" does not. Prints "path:line: pattern"
per hit; exit 1 on any hit, else 0.

A project may add DIR/scripts/personal-allow.local.json, {"allow": [...]} with the
same entry shape; its entries are appended to the allow list. It can only add
allowances: patterns and hashes come from the denylist alone. The template ships
no such file and template-update never touches it.
"""

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

DENYLIST = "scripts/personal-denylist.json"
LOCAL_ALLOW = "scripts/personal-allow.local.json"
MAX_WORDS = 4
_WORD = re.compile(r"[a-z0-9_]+")  # underscore joins: identifiers are not split


def _candidates(line: str):
    """Yield every lowercased word n-gram of the line, ungapped by whitespace."""
    low = line.lower()
    words = list(_WORD.finditer(low))
    for i, first in enumerate(words):
        for j in range(i, min(i + MAX_WORDS, len(words))):
            span = low[first.start() : words[j].end()]
            if any(c.isspace() for c in span):
                break
            yield span
            if j > i:
                yield "-".join(w.group() for w in words[i : j + 1])


def _digest(term: str) -> str:
    return hashlib.sha256(term.encode()).hexdigest()


def _compile(entry) -> tuple[str, re.Pattern]:
    if isinstance(entry, dict):
        return entry["name"], re.compile(entry["regex"], re.IGNORECASE)
    body = re.escape(entry)
    if re.match(r"\w", entry):
        body = r"(?<!\w)" + body
    if re.search(r"\w$", entry):
        body += r"(?!\w)"
    return entry, re.compile(body, re.IGNORECASE)


def _glob(pattern: str) -> re.Pattern:
    out, i = "", 0
    while i < len(pattern):
        if pattern.startswith("**", i):
            out, i = out + ".*", i + 2
        elif pattern[i] == "*":
            out, i = out + "[^/]*", i + 1
        elif pattern[i] == "?":
            out, i = out + "[^/]", i + 1
        else:
            out, i = out + re.escape(pattern[i]), i + 1
    return re.compile(out + r"\Z")


def _tracked(root: Path) -> list[str]:
    raw = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-z"], capture_output=True, check=True
    ).stdout
    return sorted(n for n in raw.decode().split("\0") if n)


def _text(path: Path) -> str | None:
    try:
        data = path.read_bytes()
    except OSError:
        return None
    if b"\0" in data[:8192]:
        return None
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return None


def _allowed(rules, name: str, line: str) -> bool:
    return any((p is None or p == name) and (c is None or c in line) for _, p, c in rules)


def scan(root: Path) -> list[str]:
    cfg_path = root / DENYLIST
    if not cfg_path.is_file():
        cfg_path = Path(__file__).resolve().parent / "personal-denylist.json"
    cfg = json.loads(cfg_path.read_text())
    patterns = [_compile(p) for p in cfg["patterns"]]
    hashes = set(cfg.get("hashes", []))
    entries = list(cfg["allow"])
    local = root / LOCAL_ALLOW
    if local.is_file():
        entries += json.loads(local.read_text()).get("allow", [])
    allow = [(_glob(a["path"]), a.get("pattern"), a.get("line_contains")) for a in entries]
    hits = []
    for rel in _tracked(root):
        whole = [a for a in allow if a[0].match(rel) and a[1] is None and a[2] is None]
        if whole:
            continue
        text = _text(root / rel)
        if text is None:
            continue
        rules = [a for a in allow if a[0].match(rel)]
        for n, line in enumerate(text.splitlines(), 1):
            for name, rx in patterns:
                if not rx.search(line):
                    continue
                if _allowed(rules, name, line):
                    continue
                hits.append(f"{rel}:{n}: {name}")
            for digest in sorted({_digest(c) for c in _candidates(line)} & hashes):
                if _allowed(rules, digest, line):
                    continue
                hits.append(f"{rel}:{n}: {digest}")
    return hits


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", default=".")
    hits = scan(Path(ap.parse_args(argv).root).resolve())
    for h in hits:
        print(h)
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
