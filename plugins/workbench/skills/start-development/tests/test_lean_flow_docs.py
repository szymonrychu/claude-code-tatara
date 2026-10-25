"""start-development describes only the lean loop: one integration tree per epic, one implementer
and one reviewer per task, at most two fix rounds, one scope audit per epic.

The retired words below are named on purpose: this file pins their absence.
"""

import json
import re
import subprocess
from pathlib import Path

SD = Path(__file__).resolve().parents[1]
ROOT = SD.parents[1]  # plugins/workbench
REPO = ROOT.parents[1]
SKILL = SD / "SKILL.md"
REFS = "plugins/workbench/skills/start-development/references"

KEPT = {
    "tickets.md",
    "worktrees.md",
    "non-negotiables.md",
    "hooks.md",
    "merge-hosts.md",
    "user-run-steps.md",
    "workbench-config.md",
}
DELETED = (
    "phase-4-execute.md",
    "phases-1-3.md",
    "phases-5-7.md",
    "run-handback.md",
    "approvals.md",
    "agents.md",
    "builder-check.md",
    "mode-flags.md",
    "multi-epic.md",
    "plan-inputs.md",
    "task-fields.md",
)
SKILL_FORBIDDEN = (
    "plan-execute",
    "Workflow(",
    "heartbeat",
    "approvals.json",
    "verifier",
    "forward-merge",
    "land",
    "rulings",
    "apply-run",
)
RETIRED = (
    "plan-execute",
    "heartbeat",
    "approvals.json",
    "apply-run",
    "forwardMerged",
    "verify-task",
)


def flat(text):
    return re.sub(r"\s+", " ", text)


def tracked(rel):
    out = subprocess.run(
        ["git", "ls-files", "--", rel], cwd=REPO, capture_output=True, text=True, check=True
    ).stdout
    return [p for p in out.splitlines() if p]


def section(text, heading):
    m = re.search(rf"^## {re.escape(heading)}\s*$", text, re.M)
    assert m, f"SKILL.md has no section {heading!r}"
    rest = text[m.end() :]
    nxt = re.search(r"^## ", rest, re.M)
    return flat(rest[: nxt.start()] if nxt else rest)


def test_skill_is_lean():
    lines = SKILL.read_text().splitlines()
    assert len(lines) <= 150, f"SKILL.md is {len(lines)} lines, cap 150"
    names = {Path(p).name for p in tracked(REFS)}
    assert len(names) <= 7, sorted(names)
    assert names == KEPT, sorted(names ^ KEPT)
    for name in DELETED:
        assert not tracked(f"{REFS}/{name}"), f"references/{name} is still tracked"


def test_skill_describes_lean_loop():
    text = SKILL.read_text()
    for n in range(8):
        assert re.search(rf"^## Phase {n} - ", text, re.M), f"no Phase {n} heading"
    assert len(re.findall(r"^## The gate\s*$", text, re.M)) == 1
    gate = section(text, "The gate")
    for item in (
        "README",
        "design.md",
        "project brief",
        "id, title, value, files, depends_on, model, points, expected_minutes, expected_tokens",
        "ran",
        "skipped",
        "numbered",
        "recommended answer",
        "irreversible operation",
        '"Approve, or tell me what to change."',
        "approves the README goals and every task's acceptance conditions",
    ):
        assert item in gate, f"the gate does not name {item!r}"
    phase4 = section(text, "Phase 4 - Execute")
    for item in (
        "`epic-run`",
        "ticket.py move <epic> in-progress",
        "ticket.py tasks <epic>",
        "every dependency before its dependents",
        "sequential",
        "workbench:implementer",
        "in the background",
        "workbench:reviewer",
        "`SendMessage`",
        "at most two fix rounds",
        "ticket.py task <epic> <task> --status done --verified-head <head>",
        "--status escalated",
        "`undelivered`",
        "`discovered`",
        "ticket.py new-task",
        "workbench:interrogate",
        "cannot close while a task is not `done`",
        "never implement a task yourself",
        "never merge a tree yourself",
        "every agent call (implementer, reviewer, each continued in a fix round) "
        "runs in the background",
        "the reviewer checks a clean tree at HEAD, runs the task's `verify` on HEAD, checks every "
        "acceptance condition against the files, greps for debt markers, then reviews quality",
    ):
        assert item in phase4, f"Phase 4 does not name {item!r}"
    low = text.lower()
    for word in SKILL_FORBIDDEN:
        assert word.lower() not in low, f"SKILL.md names {word!r}"


def test_gate_table_shows_estimates():
    gate = section(SKILL.read_text(), "The gate")
    assert "points, expected_minutes, expected_tokens" in gate
    text = " ".join(SKILL.read_text().split())
    assert text.count("new-task --points") >= 2


def test_phase_five_runs_review_audit_suite_in_order():
    sec = section(SKILL.read_text(), "Phase 5 - Epic review")
    at = -1
    for s in (
        "ticket.py stage <epic> review",
        "start-review",
        "scope-auditor",
        "suite-lock.sh",
        "security-researcher",
        "ticket.py stage <epic> build",
        "ticket.py review <epic> --verdict pass",
    ):
        i = sec.find(s, at + 1)
        assert i != -1, f"Phase 5 lacks {s!r} after position {at}"
        at = i


def test_phase_six_closes_meta_and_merges_component():
    sec = section(SKILL.read_text(), "Phase 6 - Close or merge")
    for s in (
        "ticket.py close <epic> --verify",
        "ticket.py move <epic> done",
        "ticket.py reap --epic <epic>",
        "pullrequests-update",
        "pullrequests-watch",
        "references/merge-hosts.md",
        "deploy-hook.py",
        "references/user-run-steps.md",
    ):
        assert s in sec, s


def test_every_named_reference_and_template_exists():
    text = SKILL.read_text()
    named = set(re.findall(r"(?:references|templates)/[a-z-]+\.md", text))
    assert named
    for rel in sorted(named):
        assert (SD / rel).is_file(), rel


def _owned_files():
    files = [p for p in SD.rglob("*") if p.is_file() and "tests" not in p.relative_to(SD).parts]
    files = [p for p in files if "__pycache__" not in p.parts]
    return [
        *files,
        ROOT / "agents" / "record-writer.md",
        ROOT / "README.md",
        ROOT / ".claude-plugin" / "plugin.json",
    ]


def test_no_retired_words_outside_tests():
    hits = []
    for p in _owned_files():
        text = p.read_text(errors="ignore")
        hits += [f"{p.relative_to(ROOT)}: {w}" for w in RETIRED if w in text]
    assert not hits, hits


def test_record_template_and_writer_are_lean():
    template = (SD / "templates" / "record.md").read_text()
    writer = (ROOT / "agents" / "record-writer.md").read_text()
    for text in (template, writer):
        for gone in ("return value", "forwardMerged", "plan-execute", "approvals", "tdd-revert"):
            assert gone not in text, gone
    t = flat(template)
    for s in (
        "what was asked",
        "what shipped",
        "status, verified head, review rounds, verification tail",
        "not pushed",
    ):
        assert s in t.lower(), s
    w = flat(writer)
    for s in ("task files", "git log", "orchestrator's notes", "verified_head", "unverified"):
        assert s in w, s


def test_plugin_json_and_readme_describe_the_lean_loop():
    meta = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text())
    desc = meta["description"]
    for s in ("one approval gate", "epic-run", "one implementer and one reviewer per task"):
        assert s in desc, s
    for gone in ("approval ledger", "verifier", "tiered review", "per-task git worktrees"):
        assert gone not in desc, gone
    readme = (ROOT / "README.md").read_text()
    for s in (
        "`epic-run`",
        "one implementer and one reviewer per task",
        "at most two fix rounds",
        "one scope audit per epic",
        "ticket.py task",
    ):
        assert s in readme, s
    for gone in ("approval ledger", "script+haiku", "risk tier", "forward-merged", "<epic>-<task>"):
        assert gone not in readme, gone


def test_every_new_task_command_carries_points():
    root = Path(__file__).resolve().parents[3]
    files = [*root.glob("agents/*.md"), *root.glob("skills/**/*.md")]
    found = 0
    for f in files:
        if "/tests/" in str(f) or f.name == "CHANGELOG.md":
            continue
        for span in re.findall(r"`([^`]*ticket\.py new-task[^`]*)`", f.read_text(), re.S):
            found += 1
            assert "--points" in span, f"{f}: {span!r}"
    assert found >= 5
