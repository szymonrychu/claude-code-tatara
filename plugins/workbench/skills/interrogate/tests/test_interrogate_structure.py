"""interrogate: a one-pass, multi-model review panel with lead judgment.

Ported from pstack's interrogate. It replaces a review->fix loop for contested
designs and high-risk diffs: one panel, one verdict, nothing auto-applied.
"""

from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
ROOT = SKILL_DIR.parents[1]
SKILL = SKILL_DIR / "SKILL.md"
AGENT = ROOT / "agents" / "panel-reviewer.md"
START_DEVELOPMENT = ROOT / "skills" / "start-development" / "SKILL.md"
PHASES_1_3 = ROOT / "skills" / "start-development" / "references" / "phases-1-3.md"
RUN_HANDBACK = ROOT / "skills" / "start-development" / "references" / "run-handback.md"


def frontmatter(path):
    text = path.read_text()
    assert text.startswith("---\n"), f"{path.name} missing YAML frontmatter"
    end = text.index("\n---", 4)
    fm = {}
    for line in text[4:end].splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            fm[key.strip()] = value.strip().strip('"')
    return fm


def test_skill_frontmatter():
    fm = frontmatter(SKILL)
    assert fm.get("name") == "interrogate"
    assert fm.get("description")


def test_panel_spans_three_models_on_a_read_only_agent():
    text = SKILL.read_text()
    for model in ("fable", "opus", "sonnet"):
        assert f"`{model}`" in text, f"panel is missing {model}"
    assert "panel-reviewer" in text
    fm = frontmatter(AGENT)
    assert fm.get("name") == "panel-reviewer"
    tools = fm.get("tools", "")
    assert "Read" in tools
    for mutating in ("Edit", "Write", "NotebookEdit"):
        assert mutating not in tools, f"panel reviewers must be read-only, found {mutating}"


def test_verdict_uses_lead_judgment_buckets():
    text = SKILL.read_text()
    for bucket in ("### Act on", "### Consider", "### Noted", "### Dismissed"):
        assert bucket in text, f"verdict missing {bucket!r}"
    assert "2 or more reviewers" in text, "consensus must be weighted explicitly"


def test_it_is_one_pass_and_never_auto_applies():
    text = SKILL.read_text()
    assert "One pass" in text
    assert "Never auto-apply" in text


def test_start_development_routes_to_interrogate():
    assert "workbench:interrogate" in START_DEVELOPMENT.read_text()
    handback = RUN_HANDBACK.read_text()
    escalated = handback[handback.index("Handle what the run hands back") :]
    assert "workbench:interrogate" in escalated[:2500], (
        "an escalated task should get one panel verdict, not another fix round"
    )


def test_start_development_classifies_questions_before_asking():
    text = PHASES_1_3.read_text()
    assert "### Ask only what no probe can answer" in text
    section = text[text.index("### Ask only what no probe can answer") :][:2000]
    assert "probe" in section and "preference" in section


def test_interrogate_runs_before_the_gate_when_contested():
    """With one gate, a contested design gets its panel before the human sees it."""
    for path in (SKILL, START_DEVELOPMENT):
        assert "before the gate" in path.read_text(), f"{path} does not say 'before the gate'"
