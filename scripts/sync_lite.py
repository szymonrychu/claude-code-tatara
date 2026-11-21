#!/usr/bin/env python3
"""Generate plugins/workbench-lite from plugins/workbench.

workbench-lite is the portable user-scope pack: it must work in an arbitrary git repo, so it
may not depend on the workbench root, scripts/lib/workbench.py, skills/_lib, .scratchpad,
.logs, code/, mise or the orchestrator_* tools. Every file is one of:

  verbatim   copied byte for byte from plugins/workbench (SOURCES)
  adapted    copied, then the SUBSTITUTIONS for that path are applied in order
             (literal old/new strings, or a regex that must match at least once)
  override   plugins/workbench-lite/overrides/<same relative path> replaces the file, used
             where a rewrite is cleaner than substitution (the file leans on the workbench
             root helpers)

The generated tree is: agents/, skills/, references/ plus LICENSE. README.md, the manifest and
overrides/ are hand-written and never touched.

  sync_lite.py           regenerate
  sync_lite.py --check   exit 1 listing every drifted, missing or stray file
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "plugins" / "workbench"
DST = ROOT / "plugins" / "workbench-lite"
OVERRIDES = DST / "overrides"

AGENTS = [
    "codebase-cartographer",
    "architect-researcher",
    "reuse-hunter",
    "submodule-auditor",
    "scm-shepherd",
    "spec-reviewer",
    "research-docs-purist",
    "research-practitioner",
    "research-prior-art-scout",
    "research-paper-scout",
    "research-reviewer",
]

# Files taken from plugins/workbench (relative to it) and written to the same relative path.
SOURCES: list[str] = (
    ["LICENSE", "references/plan-inputs.md"]
    + [f"agents/{a}.md" for a in AGENTS]
    + [
        "skills/handoff/SKILL.md",
        "skills/handoff/scripts/handoff.py",
        "skills/start-research/SKILL.md",
        "skills/start-research/scripts/brief_path.sh",
        "skills/start-research/scripts/doc_path.sh",
    ]
)

# Dirs under DST that are fully generated: anything in them not produced here is stray.
GENERATED_DIRS = ["agents", "skills", "references"]

# path -> list of (pattern, replacement, is_regex). Applied only when no override exists.
SUBSTITUTIONS: dict[str, list[tuple[str, str, bool]]] = {
    "agents/spec-reviewer.md": [
        (
            "(`docs/plans/<name>/retro.md`, or `.scratchpad/<name>/spec/retro.md` with the spec "
            "tools); you",
            "(for example `docs/plans/<name>/retro.md`); you",
            False,
        ),
        (
            "Tests satisfy item 12 of `plugins/workbench/rules/superpowers-flow.md`: only "
            "observable\n   behaviour named in the step, one test per behaviour, none that could "
            "not signal a real\n   defect.",
            "Tests have value: only observable behaviour named in the step, one test per\n"
            "   behaviour, none that could not signal a real defect.",
            False,
        ),
    ],
    "agents/reuse-hunter.md": [
        (" Use before planning, via research-code-internal.", " Use before planning.", False),
        (
            "defined in the workbench plugin's `references/plan-inputs.md`",
            "defined in this plugin's `references/plan-inputs.md`",
            False,
        ),
    ],
    "skills/start-research/SKILL.md": [
        (r"\bworkbench:(?=research-)", "workbench-lite:", True),
        ("mise exec -- bash ", "bash ", False),
        # the orchestrator mind map section needs orchestrator_* tools lite never assumes
        (
            "- The four `research-*` skills (`research-docs`, `research-code-external`,\n"
            "  `research-code-internal`, `research-papers`) are the single-lens entry points;\n"
            "  use this skill when several lenses are wanted at once.\n",
            "",
            False,
        ),
        (
            "- `docs/research/` is gitignored; briefs stay local.",
            "- Add `docs/research/` to the repo's ignore list if briefs should stay local.",
            False,
        ),
        (r"## Mind map hand-off and recording\n.*?\n\n(?=## )", "", True),
    ],
}


def _apply(rel: str, text: str) -> str:
    for pat, new, is_regex in SUBSTITUTIONS.get(rel, []):
        if is_regex:
            text, n = re.subn(pat, new, text, flags=re.S)
        else:
            n = text.count(pat)
            text = text.replace(pat, new)
        if n == 0:
            raise SystemExit(f"sync_lite: substitution matched nothing in {rel}: {pat[:60]!r}")
    return text


def expected() -> dict[str, tuple[bytes, int]]:
    """Relative target path -> (content, file mode)."""
    out: dict[str, tuple[bytes, int]] = {}
    for rel in SOURCES:
        ov = OVERRIDES / rel
        if ov.is_file():
            out[rel] = (ov.read_bytes(), ov.stat().st_mode & 0o777)
            continue
        src = SRC / rel
        data = _apply(rel, src.read_text()).encode()
        out[rel] = (data, src.stat().st_mode & 0o777)
    for ov in OVERRIDES.rglob("*"):
        if ov.is_file() and ov.relative_to(OVERRIDES).as_posix() not in out:
            raise SystemExit(f"sync_lite: override {ov} has no entry in SOURCES")
    return out


def stray(want: dict) -> list[str]:
    found = []
    for d in GENERATED_DIRS:
        for p in (DST / d).rglob("*"):
            rel = p.relative_to(DST).as_posix()
            if p.is_file() and rel not in want and "__pycache__" not in rel:
                found.append(rel)
    return found


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true")
    check = ap.parse_args().check
    want = expected()
    drift = []
    for rel, (data, mode) in want.items():
        p = DST / rel
        if not p.is_file() or p.read_bytes() != data or (p.stat().st_mode ^ mode) & 0o111:
            drift.append(rel)
            if not check:
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_bytes(data)
                p.chmod(mode)
    extra = stray(want)
    if check:
        for rel in drift + [f"{r} (stray)" for r in extra]:
            print(f"workbench-lite drift: {rel}", file=sys.stderr)
        return 1 if drift or extra else 0
    for rel in extra:
        (DST / rel).unlink()
    print(f"workbench-lite: wrote {len(drift)} file(s), removed {len(extra)} stray")
    return 0


if __name__ == "__main__":
    sys.exit(main())
