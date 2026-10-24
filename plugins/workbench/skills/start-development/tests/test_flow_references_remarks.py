"""The kept flow references describe the lean loop: one pinned phrase per item, no retired word."""

import re
from pathlib import Path

REFS = Path(__file__).resolve().parents[1] / "references"

PINS = {
    "tickets.md": [
        "docs/plans/<phase>/<epic>/README.md",
        "tasks/<task>.md",
        "record.md",
        "close.json",
        "`task`",
        "`amend`",
        "`questions`",
        "`roadmap`",
        "`close`",
        "worktrees <epic> --refresh",
        "reap --epic <epic>",
        "ticket_cmds",
        "title, status, repo, value, files, verify, depends_on, model, review, verified_head",
        "`test`, `symbol`, `command`, `doc-section`, `judgement`",
        "refRunners",
        "package root",
        "git ls-files <path>",
        "deletion pinned by a retirement test",
        "{what, where, why}",
        "Collision rule",
        "still on disk",
        "exit 3",
    ],
    "worktrees.md": [
        "One integration tree per epic",
        "<configdir>/worktrees/<epic>",
        "move <epic> in-progress",
        "worktrees <epic> --refresh",
        "reap --epic <epic>",
        "never calls the built-in `EnterWorktree`",
        "A helper spawned by an implementer",
        "read-only like its parent",
        "worktree-merger",
        "move <epic> done",
        "sequential",
    ],
    "non-negotiables.md": [
        "## Delivery is not optional",
        "## Orchestrate. Do not implement.",
        "## Loop until it is actually finished",
        "## Test-driven, and verified before it is believed",
        "## Boy scout rule",
        "## Gates and autonomy",
        "## Scope is not negotiable",
        "75%",
        "two fix rounds",
        "`undelivered`",
        "`discovered`",
    ],
    "hooks.md": ["commit guard", "verification-freshness", "reviewer"],
}
RETIRED = (
    "plan-execute",
    "rulings.json",
    "approvals",
    "apply-run",
    "MERGE <task>",
    "fork_point",
    "LAUNCH",
    "heartbeat",
    "estimate",
    "Workflow",
    "verifier",
    "hook-probe",
    "validate-tasks",
    "verify-task",
    "<epic>-<task>",
)


def flat(name):
    return re.sub(r"\s+", " ", (REFS / name).read_text())


def _check(name):
    missing = [p for p in PINS[name] if p not in flat(name)]
    assert not missing, missing


def test_tickets_remarks():
    _check("tickets.md")


def test_worktrees_remarks():
    _check("worktrees.md")


def test_non_negotiables_remarks():
    _check("non-negotiables.md")


def test_non_negotiables_is_half_its_old_length():
    assert len((REFS / "non-negotiables.md").read_text().splitlines()) <= 50


def test_hooks_remarks():
    _check("hooks.md")


def test_kept_references_name_no_retired_machinery():
    hits = []
    for p in sorted(REFS.glob("*.md")):
        text = p.read_text()
        hits += [f"{p.name}: {w}" for w in RETIRED if w in text]
    assert not hits, hits
