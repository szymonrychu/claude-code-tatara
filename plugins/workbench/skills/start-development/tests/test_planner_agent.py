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
    assert re.search(r"^model: opus$", fm, re.M)
    src = (Path(__file__).parent / "test_repo_hygiene.py").read_text()
    block = re.search(r"AGENT_KEYS = \((.*?)\)", src, re.S).group(1)
    AGENT_KEYS = re.findall(r"""['"](\w+)['"]""", block)
    keys = set(re.findall(r"^([A-Za-z]+):", fm, re.M))
    assert keys <= set(AGENT_KEYS)
    needles = (
        "epic",
        "briefs",
        "userDecisions",
        "[{id, text}]",
        "absolute file paths",
    )
    for s in needles:
        assert s in t, s


def test_planner_boilerplate():
    t = _text()
    for s in (
        "references/tickets.md",
        "templates/design.md",
        "templates/task.md",
        "phases 2 and 3",
        "ticket.py new-task",
        "workbench.py runner <ref> --repo <dir>",
        "`command:` ref",
        "design.md",
        "chore(ticket): <epic> plan",
        "ticket.py lint <epic>",
        "ticket.py questions --add",
        "200 words",
        "dependency order",
        "preference questions",
    ):
        assert s in t, s
    for gone in (
        "relatedEpics",
        "approvals",
        "contract",
        "ticket.py graph",
        "ticket.py facts",
        "ticket.py estimate",
        "validate-tasks",
        "facts.md",
    ):
        assert gone not in t, gone


def test_planner_rules():
    t = _text()
    assert "never write `.py` scratch files" in t.lower() or "Never write `.py` scratch files" in t
    assert "git ls-files <path>" in t
    assert "scratchpad" in t
    assert "LSP and grep" in t


def test_planner_dispatched_in_phase_three():
    readme = (ROOT / "README.md").read_text()
    rows = [ln for ln in readme.splitlines() if ln.startswith("| `start-development` phase 3 |")]
    assert any("`planner`" in r for r in rows), rows
    skill = (SD / "SKILL.md").read_text()
    phase3 = skill[skill.index("## Phase 3") : skill.index("## The gate")]
    assert "workbench:planner" in phase3


def test_task_template_retirement_rule():
    t = (SD / "templates" / "task.md").read_text()
    assert "git ls-files <path>" in t and "never on the filesystem" in t


def test_planner_sizing_and_heading_index():
    t = " ".join(_text().split())
    assert "one test file's worth of behaviour, at most 8 files" in t
    assert "never the full suite" in t
    assert "more than five files" in t
    assert "grep its `^#` headings first, then read only the sections the plan needs" in t


def test_planner_discipline():
    t = " ".join(_text().split())
    for s in (
        "list every file",
        "one pass",
        "edits, deletes, skips or xfails",
        "no longer accurate",
        "open question",
        "Never guess",
    ):
        assert s in t, s
