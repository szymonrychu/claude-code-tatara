#!/usr/bin/env python3
"""Fail when a tracked text file holds an em dash (U+2014).

Usage: check_em_dash.py [--root DIR]

Walks the tracked files of DIR with check_personal's helpers: untracked files and
binary files (a NUL in the first 8192 bytes) are skipped. There is no allow list
and no exempt path; tests that need the character write the escape. Prints
"path:line: em dash" per hit; exit 1 on any hit, else 0.
"""

import argparse
import sys
from pathlib import Path

from check_personal import _text, _tracked

EM_DASH = "\u2014"


def scan(root: Path) -> list[str]:
    hits = []
    for rel in _tracked(root):
        text = _text(root / rel)
        if text is None:
            continue
        for n, line in enumerate(text.splitlines(), 1):
            if EM_DASH in line:
                hits.append(f"{rel}:{n}: em dash")
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
