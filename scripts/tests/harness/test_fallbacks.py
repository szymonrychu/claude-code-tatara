import pytest
from harness.skills_emit import SkillError, render_skills
from harness.sources import load_sources

REAL = __import__("pathlib").Path(__file__).resolve().parents[3]


def fallback(tree, name, body="Body", fm=None, dirname=None):
    d = tree / "scripts/harness/fallbacks" / (dirname or name)
    d.mkdir(parents=True)
    head = fm if fm is not None else f"name: {name}\ndescription: d {name}"
    (d / "SKILL.md").write_text(f"---\n{head}\n---\n{body}\n")


def test_fallback_skill_is_emitted(tree):
    fallback(
        tree,
        "plan-execute",
        "Run ${CLAUDE_PLUGIN_ROOT}/scripts/verify-task.py via workbench:review",
    )
    out = render_skills(load_sources(tree))
    body = out[".agents/skills/plan-execute/SKILL.md"]
    assert body.startswith("---\nname: plan-execute\n")
    assert "CLAUDE_PLUGIN_ROOT" not in body
    assert "workbench:" not in body
    assert "plugins/workbench/scripts/verify-task.py" in body


def test_fallback_name_validated(tree):
    fallback(tree, "Bad_Name", dirname="Bad_Name")
    with pytest.raises(SkillError):
        render_skills(load_sources(tree))


def test_fallback_collision_with_plugin_skill(tree):
    fallback(tree, "alpha")
    with pytest.raises(SkillError, match="duplicate"):
        render_skills(load_sources(tree))


def test_real_plan_execute_fallback_content():
    out = render_skills(load_sources(REAL))
    text = out[".agents/skills/plan-execute/SKILL.md"]
    for needle in (
        "verify-task.py",
        "worktree",
        "test-first",
        "three fix rounds",
        "scope audit",
        "resume",
        "Fan-out caps",
    ):
        assert needle in text
    assert "CLAUDE_PLUGIN_ROOT" not in text


def test_plan_execute_fallback_epic_lifecycle():
    out = render_skills(load_sources(REAL))
    text = out[".agents/skills/plan-execute/SKILL.md"]
    for needle in (
        "--base <epic>",
        "merge.py",
        "move <epic> done",
        "worktrees <epic> --integration",
        "ticket.py close <epic>",
        "never the harness's built-in worktree feature",
        "main never moves onto an untested tip",
    ):
        assert needle in text


def test_fallback_emitted_for_every_target():
    out = render_skills(load_sources(REAL))
    paths = [p for p in out if p.endswith("/plan-execute/SKILL.md")]
    assert paths
    for p in paths:
        assert out[p].startswith("---\nname: plan-execute\n")
        assert "workbench:" not in out[p]


def test_fallback_content():
    out = render_skills(load_sources(REAL))
    text = out[".agents/skills/plan-execute/SKILL.md"]
    for needle in ("verify-task.py", "three fix rounds", "scope audit", "What you lose"):
        assert needle in text


def test_no_workflow_scripts_emitted():
    out = render_skills(load_sources(REAL))
    assert not any("workflow" in p.lower() for p in out)
    assert not any(p.endswith((".js", ".mjs")) for p in out)
