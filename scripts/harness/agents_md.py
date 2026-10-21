"""Render the generated rules and path-rules blocks of AGENTS.md (D3, D11)."""

from __future__ import annotations

import re
from pathlib import Path
from types import SimpleNamespace

from harness.sources import _rules, parse_frontmatter

RULE_FILES = ("tdd.md", "boy-scout.md", "concise-orchestrator.md")
NOTE = "_Generated from plugins/workbench/rules/; edit there, then run `mise run harness-setup`._"
PATH_NOTE = "_Generated from .claude/rules/; edit there, then run `mise run harness-setup`._"


def _demote(body: str) -> str:
    out, fenced = [], False
    for line in body.splitlines():
        if line.lstrip().startswith("```"):
            fenced = not fenced
        elif not fenced and re.match(r"#{1,5} ", line):
            line = "#" + line
        out.append(line)
    return "\n".join(out).strip("\n")


def render_rules_block(root: Path) -> str | None:
    """Block body, or None when the repo carries no plugin rule files."""
    parts = []
    for name in RULE_FILES:
        f = root / "plugins/workbench/rules" / name
        if f.is_file():
            parts.append(_demote(parse_frontmatter(f.read_text(), str(f))[1]))
    if not parts:
        return None
    return "\n\n".join([NOTE, *parts]) + "\n"


def render_path_rules_block(sources) -> str:
    """Path-rules block body from `sources.rules` (a harness.sources.Sources)."""
    lines = [
        f"- When touching {', '.join(f'`{g}`' for g in r.paths)}, read `.claude/rules/{r.name}.md`."
        for r in sources.rules
        if r.paths
    ]
    return "\n".join([PATH_NOTE, "", *lines]) + "\n"


def _markers(name: str) -> tuple[str, str]:
    return f"<!-- workbench:{name}:begin -->", f"<!-- workbench:{name}:end -->"


def replace_block(text: str, name: str, body: str | None, after: str | None = None) -> str:
    """Set the named block body; None removes the block. A missing block is inserted after the
    `after` block's end marker, else appended."""
    b, e = _markers(name)
    new = None if body is None else f"{b}\n{body}{e}"
    pat = re.compile(re.escape(b) + r".*?" + re.escape(e), re.S)
    if pat.search(text):
        if new is None:
            # the exact inverse of how a missing block is inserted: "\n\n" + block
            undone = re.sub(r"\n\n" + pat.pattern, "", text, count=1, flags=re.S)
            if undone != text:
                return undone
            return re.sub(r"\n?" + pat.pattern + r"\n?", "\n", text, count=1, flags=re.S)
        return pat.sub(lambda _m: new, text, count=1)
    if new is None:
        return text
    if after and _markers(after)[1] in text:
        end = _markers(after)[1]
        return text.replace(end, f"{end}\n\n{new}", 1)
    return text.rstrip("\n") + f"\n\n{new}\n"


def sync_text(root: Path, text: str, with_path_rules: bool) -> str:
    rules = render_rules_block(root)
    if rules is not None:
        text = replace_block(text, "rules", rules)
    path_rules = (
        render_path_rules_block(SimpleNamespace(rules=_rules(root))) if with_path_rules else None
    )
    return replace_block(text, "path-rules", path_rules, after="rules")


def sync(root: Path, with_path_rules: bool, write: bool = True) -> bool:
    """Bring AGENTS.md in line; True when it differed. No AGENTS.md means nothing to do."""
    f = root / "AGENTS.md"
    if not f.is_file():
        return False
    old = f.read_text()
    new = sync_text(root, old, with_path_rules)
    if new != old and write:
        f.write_text(new)
    return new != old
