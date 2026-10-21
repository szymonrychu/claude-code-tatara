"""The flow references describe the remarks-2026-10-18 epic: one pinned phrase per item."""

import re
from pathlib import Path

REFS = Path(__file__).resolve().parents[1] / "references"

PINS = {
    "run-handback.md": [
        "agent-output-invalid",
        "impl-agent-died",
        "fix-agent-died",
        "review-agent-died",
        "triageRejected",
        "ruling",
        "rulingsIgnored",
        "ticket.py continue",
        "ticket.py rule",
        "ruled-accepted",
        "process-only",
    ],
    "tickets.md": [
        "dated note line",
        "carries the finding as its AC",
        "rulings.json",
        "docs/plans/contracts.json",
        "docs/plans/facts.md",
        "gitignored",
        "`rule`",
        "`args`",
        "`continue`",
        "`contract`",
        "graph --todo",
        "`roadmap`",
        "`facts`",
        "`decide`",
        "`questions`",
        "`amend`",
        "worktrees --refresh",
        "reap --task",
        "ticket_cmds",
        "`decide`, `questions` and `amend` write design.md, approvals.json and task files",
        "`rule` writes rulings.json",
    ],
    "approvals.md": ["ticket.py decide", "into the ledger and design"],
    "task-fields.md": [
        "package root",
        "refRunners",
        ".claude/workbench.json",
        "no runner",
        "overlapIgnore",
        "git ls-files <path>",
        "deletion",
    ],
    "worktrees.md": [
        "worktrees <epic> --refresh",
        "reap --epic <epic> --task <task>",
        "prunes empty directories",
        "union-merge",
        "suites",
    ],
}


def flat(name):
    return re.sub(r"\s+", " ", (REFS / name).read_text())


def _check(name):
    missing = [p for p in PINS[name] if p not in flat(name)]
    assert not missing, missing


def test_run_handback_remarks():
    _check("run-handback.md")


def test_tickets_remarks():
    _check("tickets.md")


def test_approvals_decide():
    _check("approvals.md")


def test_task_fields_remarks():
    _check("task-fields.md")


def test_worktrees_remarks():
    _check("worktrees.md")
