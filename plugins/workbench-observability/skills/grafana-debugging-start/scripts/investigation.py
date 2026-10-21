#!/usr/bin/env python3
"""Maintain a phase-gated Grafana MCP investigation report."""

from __future__ import annotations

import argparse
import importlib.util
import re
from pathlib import Path

REPORTS_SUBDIR = Path("docs/grafana-investigations")


def _core_locator():
    """Load the core plugin's find_root, or None when the core lib is not reachable.

    The pack ships beside the core plugin (plugins/workbench-observability next to
    plugins/workbench), so the core lib sits at a sibling path.
    """
    here = Path(__file__).resolve()
    for plugin_root in (here.parents[3],):
        lib = plugin_root.parent / "workbench" / "scripts" / "lib" / "workbench.py"
        if lib.is_file():
            spec = importlib.util.spec_from_file_location("_workbench_core_lib", lib)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            return mod.find_root
    return None


def default_base() -> Path:
    """Report directory under the workbench root; under the cwd when no root is found."""
    find_root = _core_locator()
    found = find_root() if find_root else None
    root = found[0] if found else Path.cwd()
    return root / REPORTS_SUBDIR


SKELETON = """# Grafana investigation: {slug}

**Date:** {day}

## Plan

_State the hypothesis and the funnel stages you intend to walk._

## Phase 1

## Final review

_Populated by `investigation.py finalize`: each claim traced to tool evidence._
"""


def slugify(text: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return s


def report_path(slug: str, day: str, base: Path) -> Path:
    return base / f"{day}-{slug}.md"


def init(slug: str, day: str, base: Path) -> Path:
    base.mkdir(parents=True, exist_ok=True)
    slug = slugify(slug)
    path = report_path(slug, day, base)
    if path.exists():
        raise FileExistsError(f"report already exists: {path}")
    path.write_text(SKELETON.format(slug=slug, day=day))
    return path


def _today() -> str:
    from datetime import date

    return date.today().isoformat()


def _now_iso() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


FINAL_HEADING = "## Final review"

STEP_TMPL = "- **[{ts}] {stage}** via `{tool}`\n  - query: `{query}`\n  - finding: {finding}\n"


def append_step(
    path: Path, phase: int, stage: str, tool: str, query: str, finding: str, ts: str
) -> None:
    body = path.read_text()
    block = STEP_TMPL.format(ts=ts, stage=stage, tool=tool, query=query, finding=finding)
    phase_head = f"## Phase {phase}"
    phase_head_re = rf"^## Phase {phase}$"
    if not re.search(phase_head_re, body, re.M):
        # insert a new phase heading immediately before Final review
        body = body.replace(FINAL_HEADING, f"{phase_head}\n\n{FINAL_HEADING}", 1)
    # insert the block at the end of that phase's section (right before the next "## " heading)
    head_match = re.search(phase_head_re, body, re.M)
    start = head_match.end()
    rest = body[start:]
    # find next top-level heading after this phase
    m = re.search(r"\n## ", rest)
    cut = start + (m.start() if m else len(rest))
    new_body = body[:cut].rstrip("\n") + "\n\n" + block + "\n" + body[cut:].lstrip("\n")
    path.write_text(new_body)


def parse_claim(spec: str) -> tuple[str, str]:
    claim, sep, evidence = spec.partition("::")
    return (claim.strip(), evidence.strip())


def finalize(path: Path, claims: list[tuple[str, str]]) -> None:
    lines = []
    for i, (claim, evidence) in enumerate(claims, 1):
        if evidence:
            lines.append(f"{i}. {claim}")
            lines.append(f"   - evidence: {evidence}")
        else:
            lines.append(f"[!] {i}. {claim}")
            lines.append("   - evidence: EVIDENCE MISSING")
    section = FINAL_HEADING + "\n\n" + "\n".join(lines) + "\n"
    body = path.read_text()
    idx = body.index(FINAL_HEADING)
    path.write_text(body[:idx] + section)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_init = sub.add_parser("init", help="create a new investigation report")
    p_init.add_argument("slug")
    p_init.add_argument("--date", default=None)
    p_init.add_argument("--base", default=None)

    p_app = sub.add_parser("append", help="append an investigation step")
    p_app.add_argument("report")
    p_app.add_argument("--phase", type=int, required=True)
    p_app.add_argument("--stage", required=True)
    p_app.add_argument("--tool", required=True)
    p_app.add_argument("--query", required=True)
    p_app.add_argument("--finding", required=True)
    p_app.add_argument("--ts", default=None)

    p_fin = sub.add_parser("finalize", help="write the final review")
    p_fin.add_argument("report")
    p_fin.add_argument(
        "--claim",
        action="append",
        default=[],
        help='"claim text::evidence" (evidence optional)',
    )

    args = parser.parse_args(argv)
    if args.cmd == "init":
        day = args.date or _today()
        path = init(args.slug, day, Path(args.base) if args.base else default_base())
        print(path)
        return 0
    if args.cmd == "append":
        ts = args.ts or _now_iso()
        append_step(
            Path(args.report),
            args.phase,
            args.stage,
            args.tool,
            args.query,
            args.finding,
            ts,
        )
        return 0
    if args.cmd == "finalize":
        claims = [parse_claim(c) for c in args.claim]
        finalize(Path(args.report), claims)
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
