"""Fail on em dashes, smart quotes and unicode arrows in pill sources.

Usage: lint_text.py FILE [FILE ...]

Prints one `path:line:col: U+XXXX NAME (use ...)` line per hit and exits 1 when
any hit is found, 0 when clean, 2 on a usage or read error. The banned
characters are written as code points so this file passes its own check.
"""

import sys
import unicodedata
from pathlib import Path

# char -> plain replacement the author should use instead
REPLACEMENTS = {
    chr(0x2014): "-",  # em dash
    chr(0x2015): "-",  # horizontal bar (em dash look-alike)
    chr(0x2018): "'",
    chr(0x2019): "'",
    chr(0x201A): "'",
    chr(0x201B): "'",
    chr(0x201C): '"',
    chr(0x201D): '"',
    chr(0x201E): '"',
    chr(0x201F): '"',
    chr(0x2032): "'",
    chr(0x2033): '"',
    chr(0x00AB): '"',
    chr(0x00BB): '"',
    chr(0x2039): "'",
    chr(0x203A): "'",
}

# unicode arrow blocks: Arrows, Supplemental Arrows-A/B, Misc Symbols and Arrows (arrows part)
ARROW_RANGES = (
    (0x2190, 0x21FF),
    (0x27F0, 0x27FF),
    (0x2900, 0x297F),
    (0x2B00, 0x2B2F),
    (0x2B30, 0x2B4F),
    (0x2B5E, 0x2BFF),
    (0x1F800, 0x1F8FF),
)


def banned(ch: str) -> str | None:
    """Return the suggested replacement for a banned char, or None if allowed."""
    if ch in REPLACEMENTS:
        return REPLACEMENTS[ch]
    cp = ord(ch)
    if any(lo <= cp <= hi for lo, hi in ARROW_RANGES):
        return "-> or <-"
    return None


def scan_text(text: str, label: str) -> list[str]:
    hits = []
    for lineno, line in enumerate(text.splitlines(), 1):
        for col, ch in enumerate(line, 1):
            fix = banned(ch)
            if fix is not None:
                name = unicodedata.name(ch, "UNKNOWN")
                hits.append(f"{label}:{lineno}:{col}: U+{ord(ch):04X} {name} (use {fix})")
    return hits


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if not args or args[0] in ("-h", "--help"):
        print(__doc__.strip(), file=sys.stderr)
        return 2
    hits: list[str] = []
    for arg in args:
        try:
            text = Path(arg).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as e:
            print(f"lint_text: cannot read {arg}: {e}", file=sys.stderr)
            return 2
        hits += scan_text(text, arg)
    for h in hits:
        print(h)
    if hits:
        print(f"lint_text: {len(hits)} banned character(s)", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
