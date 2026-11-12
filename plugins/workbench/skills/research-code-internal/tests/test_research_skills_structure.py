"""Structure tests for the four research skills, paper-scout persona and reuse-hunter agent."""

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SKILLS = ROOT / "skills"
NAMES = ["research-code-internal", "research-code-external", "research-papers", "research-docs"]
HEADINGS = ["## When to run it", "## Procedure", "## Output: Plan inputs", "## Rules"]
LISTS = ["reuse", "do-not-build", "fix-as-ac", "ideas"]
PERSONA = {
    "research-code-external": "prior-art-scout",
    "research-papers": "paper-scout",
    "research-docs": "docs-purist",
}


def split(path):
    text = path.read_text()
    assert text.startswith("---\n"), f"{path} has no frontmatter"
    head, body = text[4:].split("\n---\n", 1)
    fm = {}
    for line in head.splitlines():
        if ":" in line and not line.startswith(" "):
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip()
    return fm, body, text


@pytest.mark.parametrize("name", NAMES)
def test_skill_structure(name):
    path = SKILLS / name / "SKILL.md"
    assert path.is_file()
    fm, body, text = split(path)
    assert fm["name"] == name
    assert fm["description"].strip("\"'>")
    assert len(fm["description"]) < 1536
    pos = [body.find(h) for h in HEADINGS]
    assert all(p >= 0 for p in pos), pos
    assert pos == sorted(pos)
    assert "Skip when" in body and "Run when" in body
    assert "Plan inputs" in body
    for lst in LISTS:
        assert lst in body, lst
    assert "doc_path.sh" in text
    assert len(text.splitlines()) < 120


def test_internal_mentions_reuse_hunter():
    assert "reuse-hunter" in (SKILLS / "research-code-internal" / "SKILL.md").read_text()


@pytest.mark.parametrize("name,persona", PERSONA.items())
def test_external_skills_use_start_research(name, persona):
    text = (SKILLS / name / "SKILL.md").read_text()
    assert "start-research" in text
    assert persona in text


@pytest.mark.parametrize("name,persona", PERSONA.items())
def test_external_skills_name_their_agent(name, persona):
    text = (SKILLS / name / "SKILL.md").read_text()
    assert f"workbench:research-{persona}" in text
    assert f"{persona} persona" not in text


def test_paper_scout_persona():
    text = (ROOT / "agents" / "research-paper-scout.md").read_text()
    for h in ["## Lens", "## Source priorities", "## Emphasis", "## Output contract"]:
        assert h in text


def test_reuse_hunter_agent():
    fm, body, _ = split(ROOT / "agents" / "reuse-hunter.md")
    assert fm["name"] == "reuse-hunter"
    assert fm["description"]
    assert fm["model"] == "sonnet"
    assert "LSP" in fm["tools"]
    assert "Edit" not in fm["tools"] and "Write" not in fm["tools"]
    assert "jscpd" in body and "Plan inputs" in body


def test_internal_hunt_runs_during_brainstorming_with_no_lean_path():
    text = " ".join((SKILLS / "research-code-internal" / "SKILL.md").read_text().split())
    assert "during `superpowers:brainstorming`" in text
    assert "lean path" not in text
    assert "phase 3" not in text
    assert "plan" + "-writer" not in text and "plan" + ".md" not in text


def test_plan_inputs_are_defined_by_the_workbench_reference():
    ref = ROOT / "references" / "plan-inputs.md"
    flat = " ".join(ref.read_text().split())
    for name in LISTS:
        assert f"`{name}`" in flat, name
    assert "superpowers:brainstorming" in flat and "superpowers:writing-plans" in flat
    for path in [SKILLS / n / "SKILL.md" for n in NAMES] + [ROOT / "agents" / "reuse-hunter.md"]:
        text = " ".join(path.read_text().split())
        assert "references/plan-inputs.md" in text, path
        assert "Discovery section" not in text, path
        assert "start-" + "development" not in text, path
    for name in NAMES:
        text = (SKILLS / name / "SKILL.md").read_text()
        assert "superpowers:brainstorming" in text, name


def test_research_skills_name_no_epic():
    for name in NAMES + ["start-research"]:
        assert not re.search(r"\bepics?\b", (SKILLS / name / "SKILL.md").read_text(), re.I), name


MINDMAP_SKILLS = ["research-code-internal", "research-docs", "start-research"]


@pytest.mark.parametrize("name", MINDMAP_SKILLS)
def test_skill_mindmap_block_is_conditional(name):
    text = " ".join((SKILLS / name / "SKILL.md").read_text().split())
    assert "orchestrator_mindmap_search" in text
    assert "Only when the `orchestrator_mindmap_*` tools are available" in text
    assert "data, never instructions" in text


def test_start_research_records_brief_in_map():
    text = " ".join((SKILLS / "start-research" / "SKILL.md").read_text().split())
    tools = ["orchestrator_mindmap_node_create", "orchestrator_mindmap_node_update"]
    tools.append("researched_by")
    for tool in tools:
        assert tool in text


def test_flow_rule_mindmap_text():
    rule = " ".join((ROOT / "rules" / "superpowers-flow.md").read_text().split())
    for needle in [
        "(c) when the `orchestrator_mindmap_*` tools are available",
        "orchestrator_mindmap_traverse",
        "orchestrator_mindmap_task_nodes",
        "`uses`",
        "`researched_by`",
        "orchestrator_mindmap_direction_create",
        "`taken`",
        "orchestrator_mindmap_note_put",
        "data, never instructions",
        "never secret values",
        "ask the leader",
    ]:
        assert needle in rule, needle
