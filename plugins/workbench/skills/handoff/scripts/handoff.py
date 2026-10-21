#!/usr/bin/env python3
"""Create and redact handoff files.

  handoff.py new --slug <slug>   create docs/handoffs/<YYYY-MM-DD>-<slug>.md at the
                                 workbench root; refuses to overwrite
  handoff.py redact <path>       replace secret-looking values with <redacted>

The directory is gitignored and, unlike the OS temp dir, survives reboots.
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts" / "lib"))
import workbench  # noqa: E402

REDACTED = "<redacted>"
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$", re.I)

TEMPLATE = """Resume in a fresh session with: continue from {path}

# Handoff: {slug}

Use references (paths, commit SHAs, PR URLs), not copies of their content.

## State

## Done

## Next

1.

## Gotchas

## Suggested skills
"""

_NAME = r"[A-Za-z0-9_.-]*(?:TOKEN|SECRET|PASSWORD|API_?KEY|PRIVATE)[A-Za-z0-9_.-]*"
ASSIGN_RE = re.compile(rf"(?i)\b({_NAME}\s*[=:]\s*)(?!<redacted>)(\S.*?)\s*$")
BEARER_RE = re.compile(r"(?i)(\bBearer\s+)(?!<redacted>)[A-Za-z0-9._~+/=-]{8,}")
PEM_BEGIN = re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")
PEM_END = re.compile(r"-----END [A-Z ]*PRIVATE KEY-----")


def redact_text(text: str) -> str:
    out: list[str] = []
    in_pem = False
    emitted = False
    for line in text.split("\n"):
        if in_pem:
            if PEM_END.search(line):
                in_pem = False
                out.append(line)
            elif not emitted:
                out.append(REDACTED)
                emitted = True
            continue
        if PEM_BEGIN.search(line):
            in_pem, emitted = True, False
            out.append(line)
            continue
        line = ASSIGN_RE.sub(lambda m: m.group(1) + REDACTED, line)
        line = BEARER_RE.sub(lambda m: m.group(1) + REDACTED, line)
        out.append(line)
    return "\n".join(out)


def cmd_new(slug: str) -> int:
    if not SLUG_RE.match(slug):
        print(f"handoff: bad slug {slug!r} (letters, digits, . _ -)", file=sys.stderr)
        return 2
    found = workbench.find_root()
    if not found:
        print("handoff: no workbench root found", file=sys.stderr)
        return 1
    path = found[0] / "docs" / "handoffs" / f"{date.today().isoformat()}-{slug}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("x") as f:
            f.write(TEMPLATE.format(path=path, slug=slug))
    except FileExistsError:
        print(f"handoff: {path} already exists, not overwriting", file=sys.stderr)
        return 1
    print(path)
    return 0


def cmd_redact(path: Path) -> int:
    if not path.is_file():
        print(f"handoff: no such file {path}", file=sys.stderr)
        return 1
    path.write_text(redact_text(path.read_text()))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    n = sub.add_parser("new")
    n.add_argument("--slug", required=True)
    r = sub.add_parser("redact")
    r.add_argument("path", type=Path)
    a = ap.parse_args()
    return cmd_new(a.slug) if a.cmd == "new" else cmd_redact(a.path)


if __name__ == "__main__":
    sys.exit(main())
