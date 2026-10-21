"""The workbench:planner agent carries the planner boilerplate once."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
AGENT = ROOT / "agents" / "planner.md"
SD = ROOT / "skills" / "start-development"


def _text():
    return AGENT.read_text()


def test_planner_frontmatter_and_input():
    t = _text()
    m = re.match(r"---\n(.*?)\n---\n", t, re.S)
    assert m
    fm = m.group(1)
    assert re.search(r"^name: planner$", fm, re.M)
    assert re.search(r"^model: sonnet$", fm, re.M)
    src = (Path(__file__).parent / "test_repo_hygiene.py").read_text()
    block = re.search(r"AGENT_KEYS = \((.*?)\)", src, re.S).group(1)
    AGENT_KEYS = re.findall(r"""['"](\w+)['"]""", block)
    keys = set(re.findall(r"^([A-Za-z]+):", fm, re.M))
    assert keys <= set(AGENT_KEYS)
    needles = (
        "epic",
        "briefs",
        "userDecisions",
        "relatedEpics",
        "[{id, text}]",
        "absolute file paths",
    )
    for s in needles:
        assert s in t, s


def test_planner_boilerplate():
    t = _text()
    for s in (
        "task-fields",
        "approvals",
        "tickets",
        "plan-inputs",
        "builder-check",
        "templates/design.md",
        "phases 2 and 3",
        "docs/plans/facts.md",
        "ticket.py facts",
        "ticket.py contract list",
        "ticket.py contract add",
        "ticket.py graph --todo",
        "workbench.py runner <ref> --repo <dir>",
        "`command:` ref",
        "verify hints",
        "approvals.json",
        "design.md",
        "chore(ticket): <epic> plan",
        "validate-tasks.mjs --epic",
        "ticket.py lint",
        "ticket.py questions --add",
        "200 words",
        "critical path",
        "preference questions",
    ):
        assert s in t, s


def test_planner_rules():
    t = _text()
    assert "never write `.py` scratch files" in t.lower() or "Never write `.py` scratch files" in t
    assert "git ls-files <path>" in t
    assert "scratchpad" in t
    assert "LSP and grep" in t


def test_planner_cross_epic_steps():
    t = _text()
    for s in (
        "ticket.py contract list",
        "ticket.py contract add",
        "ticket.py graph --todo",
        "ticket.py facts",
    ):
        assert s in t, s


def test_agents_row():
    rows = [
        ln
        for ln in (SD / "references" / "agents.md").read_text().splitlines()
        if ln.startswith("| `planner`")
    ]
    assert len(rows) == 1
    assert rows[0].rstrip().endswith("| 3 |")


def test_task_template_retirement_rule():
    t = (SD / "templates" / "task.md").read_text()
    assert "git ls-files <path>" in t and "never on the filesystem" in t
