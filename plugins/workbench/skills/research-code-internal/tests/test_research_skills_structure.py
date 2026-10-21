"""Structure tests for the four research skills, paper-scout persona and reuse-hunter agent."""

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
