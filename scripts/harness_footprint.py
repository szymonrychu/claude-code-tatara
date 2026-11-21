#!/usr/bin/env python3
"""Measure the always-loaded context footprint of the Claude Code harness.

Counts only what is in context before the first prompt: root CLAUDE.md and AGENTS.md,
rules without `paths:` frontmatter, skill and agent descriptions, and the superpowers
SessionStart bootstrap (full text of using-superpowers/SKILL.md).

Tokens are approximated as ceil(chars / 4).
"""

import argparse
import datetime
import math
import os
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(
    0, str(Path(__file__).resolve().parents[1] / "plugins" / "workbench" / "scripts" / "lib")
)
from workbench import HARNESS_DIRS  # noqa: E402

KINDS = ("instructions", "rule", "skill-description", "agent-description", "session-start")


@dataclass(frozen=True)
class Source:
    name: str
    kind: str
    chars: int
    tokens: int


def _source(name: str, kind: str, text: str) -> Source:
    return Source(name, kind, len(text), math.ceil(len(text) / 4))


def _frontmatter(text: str) -> dict[str, str]:
    """Parse the block between the first two `---` lines; folded and literal scalars joined."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    out: dict[str, str] = {}
    key = None
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if line[:1] in (" ", "\t", "-") and key is not None:
            out[key] = (out[key] + " " + line.strip().lstrip("- ")).strip()
        elif ":" in line:
            key, _, val = line.partition(":")
            key = key.strip()
            val = val.strip()
            out[key] = "" if val in (">", ">-", "|", "|-") else val.strip("\"'")
    return out


def _description(path: Path) -> str | None:
    return _frontmatter(path.read_text()).get("description")


def _rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def measure(root: Path, superpowers_dir: Path | None) -> list[Source]:
    out: list[Source] = []
    for name in ("CLAUDE.md", "AGENTS.md"):
        f = root / name
        if f.is_file():
            out.append(_source(name, "instructions", f.read_text()))
    for f in sorted((root / ".claude" / "rules").glob("*.md")):
        if "paths" not in _frontmatter(f.read_text()):
            out.append(_source(_rel(f, root), "rule", f.read_text()))
    for f in sorted(root.glob("plugins/*/skills/*/SKILL.md")):
        desc = _description(f)
        if desc is not None:
            out.append(_source(_rel(f, root), "skill-description", desc))
    for f in sorted(root.glob("plugins/*/agents/*.md")):
        desc = _description(f)
        if desc is not None:
            out.append(_source(_rel(f, root), "agent-description", desc))
    if superpowers_dir is not None:
        for f in sorted(superpowers_dir.glob("skills/*/SKILL.md")):
            desc = _description(f)
            if desc is not None:
                out.append(_source(f"superpowers:{f.parent.name}", "skill-description", desc))
        boot = superpowers_dir / "skills" / "using-superpowers" / "SKILL.md"
        if boot.is_file():
            out.append(_source("superpowers:using-superpowers", "session-start", boot.read_text()))
    return out


def render(sources: list[Source], date: str) -> str:
    rows = sorted(sources, key=lambda s: (-s.tokens, s.name))
    lines = [f"Measured {date}. Tokens are ceil(chars / 4), an approximation.", ""]
    if not any(s.name.startswith("superpowers:") for s in sources):
        lines += ["superpowers: not found (rows omitted)", ""]
    lines += ["| Source | Kind | Chars | Tokens |", "|---|---|---|---|"]
    lines += [f"| {s.name} | {s.kind} | {s.chars} | {s.tokens} |" for s in rows]
    lines += [
        f"| **Total** | | {sum(s.chars for s in rows)} | {sum(s.tokens for s in rows)} |",
        "",
        "## Subtotals per kind",
        "",
        "| Kind | Sources | Chars | Tokens |",
        "|---|---|---|---|",
    ]
    per: dict[str, list[Source]] = defaultdict(list)
    for s in rows:
        per[s.kind].append(s)
    for kind in KINDS:
        if kind in per:
            g = per[kind]
            lines.append(
                f"| {kind} | {len(g)} | {sum(s.chars for s in g)} | {sum(s.tokens for s in g)} |"
            )
    return "\n".join(lines) + "\n"


def default_superpowers_dir() -> Path | None:
    bases = []
    if os.environ.get("CLAUDE_CONFIG_DIR"):
        bases.append(Path(os.environ["CLAUDE_CONFIG_DIR"]))
    bases.append(Path.home() / HARNESS_DIRS["claude"])
    for base in bases:
        cache = base / "plugins" / "cache" / "claude-plugins-official" / "superpowers"
        versions = sorted(
            (d for d in cache.glob("*") if d.is_dir()),
            key=lambda d: [int(p) if p.isdigit() else 0 for p in d.name.split(".")],
        )
        if versions:
            return versions[-1]
    return None


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--superpowers-dir", type=Path)
    ap.add_argument("--date", default=datetime.date.today().isoformat())
    args = ap.parse_args(argv)
    sp = args.superpowers_dir or default_superpowers_dir()
    if sp is not None and not sp.is_dir():
        sp = None
    root = Path(__file__).resolve().parents[1]
    sys.stdout.write(render(measure(root, sp), args.date))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
