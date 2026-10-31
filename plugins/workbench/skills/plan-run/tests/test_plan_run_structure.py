"""plan-run: the post-gate loop, one implementer per chunk, one whole-diff reviewer, a merger."""

import re
import subprocess
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1] / "SKILL.md"
ROOT = Path(__file__).resolve().parents[3]
REPO = ROOT.parents[1]
MAX_LINES = 100


def flat(text):
    return re.sub(r"\s+", " ", text)


def frontmatter():
    text = SKILL.read_text()
    assert text.startswith("---\n")
    end = text.index("\n---", 4)
    fm = {}
    for line in text[4:end].splitlines():
        key, _, value = line.partition(":")
        fm[key.strip()] = value.strip().strip('"')
    return fm


def test_frontmatter_and_size():
    fm = frontmatter()
    assert fm["name"] == "plan-run"
    assert fm["description"]
    assert len(SKILL.read_text().splitlines()) <= MAX_LINES


def test_entry_conditions_and_claim():
    text = flat(SKILL.read_text())
    for term in (
        "## Entry conditions",
        "`rung` is set",
        "implementation-plan.md",
        "Main is clean",
        "ticket.py move <plan> in-progress",
        "start-development",
        "main checkout",
    ):
        assert term in text, term


def test_implementer_per_chunk():
    text = flat(SKILL.read_text())
    for term in (
        "one `workbench:implementer` per chunk",
        "the chunk's model",
        "first line `[wb <plan>/impl]`",
        "the plan path and the chunk number",
        "never file contents",
        "sequential",
        "work only in the plan tree, never the main checkout, never docs/plans",
        "report in at most 200 words",
        "branch `<plan>`",
        "cd <tree>",
    ):
        assert term in text, term


def test_reviewer_on_the_whole_diff():
    text = flat(SKILL.read_text())
    for term in (
        "`workbench:reviewer` (sonnet)",
        "first line `[wb <plan>/review]`",
        "`git diff <base>...HEAD`",
        "report in at most 250 words",
        "under-delivery",
        "over-delivery",
        "clean tree at HEAD",
        "every step's Verify",
        "Final verify",
        "writes retro.md",
    ):
        assert term in text, term


def test_fix_rounds_and_findings():
    text = flat(SKILL.read_text())
    for term in (
        "at most two fix rounds",
        "`SendMessage`",
        "the same implementer",
        "the same reviewer",
        "`undelivered`",
        "`discovered`",
        "recommended, never built",
        "every agent call, fix rounds via SendMessage included, runs in the background",
    ):
        assert term in text, term


def test_security_review_for_sensitive_diffs():
    text = flat(SKILL.read_text())
    assert "`security-researcher`" in text
    for topic in ("secrets", "RBAC", "ingress", "privilege", "CI vars", "image pins", "hooks"):
        assert topic in text, topic


def test_merger_and_closing_message():
    text = flat(SKILL.read_text())
    for term in (
        "`workbench:worktree-merger` (sonnet",
        "opus when `merge.py --assess` predicts a conflict",
        "first line `[wb <plan>/merge]`",
        "report in at most 150 words",
        "ticket.py close <plan> --verify",
        "ticket.py move <plan> done",
        "closing message",
        "three lines",
        "the retro.md path",
        "recommendations",
        "one line each",
        "never implement",
        "never merge",
    ):
        assert term in text, term


def test_no_retired_words():
    text = SKILL.read_text()
    for word in (
        "plan-execute",
        "heartbeat",
        "Workflow(",
        "approvals",
        "scope-auditor",
        "record-writer",
        "retro-writer",
        "points",
        "builder check",
    ):
        assert word not in text, f"SKILL.md still contains {word!r}"
    assert not re.search(r"\bepics?\b|\btasks?\b", text, re.I)


def test_named_agents_and_scripts_exist():
    for agent in ("implementer", "reviewer", "worktree-merger", "security-researcher"):
        assert (ROOT / "agents" / f"{agent}.md").is_file(), agent
    assert (ROOT / "skills" / "start-development" / "SKILL.md").is_file()
    assert (REPO / "plugins" / "superpowers" / "scripts" / "ticket.py").is_file()
    assert (ROOT / "skills" / "worktree-merge" / "scripts" / "merge.py").is_file()


def test_epic_run_is_gone():
    out = subprocess.run(
        ["git", "ls-files", "--", "plugins/workbench/skills/epic-run"],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    assert out.strip() == ""
