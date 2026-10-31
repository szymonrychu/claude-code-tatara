"""The workbench:plan-writer agent carries the plan-writing method once, in two modes."""

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
REPO = ROOT.parents[1]
AGENT = ROOT / "agents" / "plan-writer.md"
TOOLS = "[Read, Write, Edit, Grep, Glob, Bash, LSP, ToolSearch]"


def _text():
    return AGENT.read_text()


def _flat():
    return " ".join(_text().split())


def _tracked(rel):
    return subprocess.run(
        ["git", "ls-files", "--", rel], cwd=REPO, capture_output=True, text=True, check=True
    ).stdout.strip()


def test_frontmatter():
    m = re.match(r"---\n(.*?)\n---\n", _text(), re.S)
    assert m
    fm = m.group(1)
    assert re.search(r"^name: plan-writer$", fm, re.M)
    assert re.search(r"^model: opus$", fm, re.M)
    assert re.search(rf"^tools: {re.escape(TOOLS)}$", fm, re.M)
    src = (ROOT / "scripts" / "tests" / "test_repo_hygiene.py").read_text()
    block = re.search(r"AGENT_KEYS = \((.*?)\)", src, re.S).group(1)
    allowed = set(re.findall(r"""['"](\w+)['"]""", block))
    assert set(re.findall(r"^([A-Za-z]+):", fm, re.M)) <= allowed


def test_two_modes_and_inputs():
    t = _flat()
    for s in (
        "## Mode: plan",
        "## Mode: implementation",
        "{plan, briefs[]}",
        "absolute file paths",
        "the user's gate answer verbatim",
    ):
        assert s in t, s


def test_plan_mode():
    t = _flat()
    for s in (
        "references/tickets.md",
        "templates/plan.md",
        "scope ladder",
        "from the absolute MVP to the most complete delivery",
        "cumulative",
        "every open question",
        "recommended answer",
        "`(my call)`",
        "docs(plan): <plan> plan",
        "workbench.py runner <ref> --repo <dir>",
        "Plan inputs",
        "Research",
        "grep its `^#` headings first, then read only the sections the plan needs",
    ):
        assert s in t, s


def test_implementation_mode():
    t = _flat()
    for s in (
        "Agreed scope",
        "the answers",
        "sets `rung`",
        "implementation-plan.md for the agreed rung only",
        "templates/implementation-plan.md",
        "chunks",
        "model: <sonnet|opus>",
        "Covers",
        "Test first",
        "Verify",
        "Final verify",
        "Files to delete",
        "After merge",
        "docs(plan): <plan> implementation plan",
        "no second gate",
        "one test file's worth of behaviour, at most 8 files",
        "never the full suite",
        "more than five files",
    ):
        assert s in t, s


def test_writes_only_under_its_plan_dir():
    t = _flat()
    assert "writes only under its plan dir" in t
    assert "ticket.py path <plan> plan" in t
    assert "200 words" in t
    assert "never write `.py` scratch files" in t.lower()
    assert "git ls-files <path>" in t
    assert "LSP and grep" in t


def test_discipline():
    t = _flat()
    for s in (
        "list every file",
        "one pass",
        "edits, deletes, skips or xfails",
        "no longer accurate",
        "open question",
        "Never guess",
        "No backward compatibility",
    ):
        assert s in t, s


def test_no_retired_machinery():
    t = _flat()
    for gone in (
        "epic",
        "points",
        "ticket.py new-task",
        "ticket.py lint",
        "ticket.py questions",
        "ticket.py retro",
        "design.md",
        "builder check",
        "calibration",
        "expected minutes",
    ):
        assert gone not in t, gone
    AGENT.read_text().encode("ascii")


def test_planner_is_retired():
    assert _tracked("plugins/workbench/agents/planner.md") == ""
    assert _tracked("plugins/workbench/skills/start-development/tests/test_planner_agent.py") == ""
