import json
import os
import re
from pathlib import Path

import pytest
from harness.skills_emit import SkillError, render_skills
from harness.sources import load_sources

REAL = Path(__file__).resolve().parents[3]
GOLDEN_SKILLS = Path(__file__).parent / "golden" / "skills"


def skill(tree, plugin, name, body, fm=None, dirname=None):
    d = tree / "plugins" / plugin / "skills" / (dirname or name)
    d.mkdir(parents=True, exist_ok=True)
    head = fm if fm is not None else f"name: {name}\ndescription: d {name}"
    (d / "SKILL.md").write_text(f"---\n{head}\n---\n{body}\n")


def test_emits_skill_md_only(tree):
    (tree / "plugins/core/skills/alpha/scripts").mkdir()
    (tree / "plugins/core/skills/alpha/scripts/run.py").write_text("x")
    out = render_skills(load_sources(tree))
    assert sorted(out) == [
        ".agents/skills/alpha/SKILL.md",
        ".agents/skills/beta/SKILL.md",
        ".agents/skills/gamma/SKILL.md",
    ]
    assert not any(p.startswith(".claude/") for p in out)


def test_rewrites_plugin_root_and_relative_paths(tree):
    skill(
        tree,
        "core",
        "paths",
        'Run `python3 "${CLAUDE_PLUGIN_ROOT}/skills/x/scripts/a.py"`, '
        "then $CLAUDE_PLUGIN_ROOT/r.md.\n"
        "See `references/doc.md` and (templates/t.md) and scripts/run.sh.\n"
        "Not docs/scripts/z and and/or.",
    )
    body = render_skills(load_sources(tree))[".agents/skills/paths/SKILL.md"]
    assert '"plugins/core/skills/x/scripts/a.py"' in body
    assert "plugins/core/r.md" in body
    assert "`plugins/core/skills/paths/references/doc.md`" in body
    assert "(plugins/core/skills/paths/templates/t.md)" in body
    assert " plugins/core/skills/paths/scripts/run.sh" in body
    assert "docs/scripts/z" in body
    assert "CLAUDE_PLUGIN_ROOT" not in body
    assert "plugins/core/skills/paths/skills" not in body


def test_rewrites_skill_references(tree):
    skill(tree, "core", "refs", "Use workbench:foo-bar then extra:gamma, not other:thing.")
    body = render_skills(load_sources(tree))[".agents/skills/refs/SKILL.md"]
    assert "Use foo-bar then gamma, not other:thing." in body


def test_frontmatter_roundtrip(tree):
    out = render_skills(load_sources(tree))
    text = out[".agents/skills/beta/SKILL.md"]
    assert text.startswith("---\nname: beta\n")
    assert 'description: "Quoted: description with a colon."' in text
    assert 'argument-hint: ["target", "mode"]' in text
    gamma = out[".agents/skills/gamma/SKILL.md"]
    assert 'description: "Literal line one.\\nLiteral line two."' in gamma
    assert gamma.endswith("Gamma body.\n")


@pytest.mark.parametrize("name", ["Bad", "-lead", "trail-", "dou--ble", "has_underscore", "a" * 65])
def test_invalid_names_rejected(tree, name):
    skill(tree, "core", name, "b", dirname=name)
    with pytest.raises(SkillError, match="name"):
        render_skills(load_sources(tree))


def test_name_must_equal_dir(tree):
    skill(tree, "core", "other", "b", fm="name: mismatch\ndescription: d", dirname="other")
    with pytest.raises(SkillError, match="mismatch"):
        render_skills(load_sources(tree))


def test_duplicate_across_plugins(tree):
    skill(tree, "extra", "alpha", "b")
    with pytest.raises(SkillError, match="alpha.*core.*extra|duplicate"):
        render_skills(load_sources(tree))


def test_claude_only_skills_not_emitted(tree):
    skill(tree, "core", "heartbeat", "b")
    skill(tree, "core", "hook-probe", "b")
    out = render_skills(load_sources(tree))
    assert not any("heartbeat" in p or "hook-probe" in p for p in out)


def test_disabled_plugin_skipped(tree):
    skill(tree, "off", "offskill", "b")
    assert ".agents/skills/offskill/SKILL.md" not in render_skills(load_sources(tree))


def test_never_touches_settings(tree):
    before = (tree / ".claude/settings.json").read_text()
    render_skills(load_sources(tree))
    assert (tree / ".claude/settings.json").read_text() == before
    assert json.loads(before)


def test_paths_rewritten_and_exist(tree):
    (tree / "plugins/core/scripts").mkdir()
    (tree / "plugins/core/scripts/tool.py").write_text("x")
    (tree / "plugins/core/skills/alpha/references").mkdir(parents=True)
    (tree / "plugins/core/skills/alpha/references/r.md").write_text("x")
    skill(tree, "core", "pathy", "Run scripts/tool.py.")
    skill(tree, "core", "alpha", "See references/r.md and ${CLAUDE_PLUGIN_ROOT}/scripts/tool.py.")
    out = render_skills(load_sources(tree))
    assert "plugins/core/scripts/tool.py" in out[".agents/skills/pathy/SKILL.md"]
    assert "plugins/core/skills/alpha/references/r.md" in out[".agents/skills/alpha/SKILL.md"]
    check_paths_exist(tree, out)


def check_paths_exist(root, out):
    for path, text in out.items():
        assert "CLAUDE_PLUGIN_ROOT" not in text, path
        for m in re.finditer(r"plugins/[\w-]+/[\w./-]*[\w]", text):
            assert (root / m.group(0)).exists(), f"{path}: dangling {m.group(0)}"


def test_paths_rewritten_and_exist_real_tree():
    check_paths_exist(REAL, render_skills(load_sources(REAL)))


def test_names_and_exclusions(tree):
    skill(tree, "core", "heartbeat", "b")
    skill(tree, "core", "hook-probe", "b")
    out = render_skills(load_sources(tree))
    assert not any("heartbeat" in p or "hook-probe" in p for p in out)
    assert not any(p.startswith(".claude/skills") for p in out)
    skill(tree, "core", "Bad_Name", "b")
    with pytest.raises(SkillError):
        render_skills(load_sources(tree))
    (tree / "plugins/core/skills/Bad_Name").rename(tree / "plugins/core/skills/-x")
    skill(tree, "extra", "alpha", "dup")
    with pytest.raises(SkillError):
        render_skills(load_sources(tree))


CLAUDE_TOKENS = ("Workflow(", "Monitor", "AskUserQuestion", "status.md", "heartbeat.py")
CLAUDE_CONSTRUCTS = """Then run the epic through `workbench:plan-execute`, one run per epic,
named by the epic slug through a named copy (`meta.name` must be a literal):

```
Workflow({
  scriptPath: '<the printed path>',   // resume with the same scriptPath
  args: { epic: '<epic>', brief: { what: '...' } },
})
```

On return, `ticket.py apply-run <epic> <return.json>` writes results back into the task files.

To wait on the run, arm `heartbeat.py --run <id>` (one Monitor; keepalive off by default; costs in
skills/heartbeat/SKILL.md); on END read the return per references/run-handback.md.
**Relaunch:** `ticket.py continue <epic> --out-dir <dir> --accept <ids>` applies the return.

`AskUserQuestion` for genuine option choices, prose otherwise. Ask with `AskUserQuestion`.
Arm a Monitor on the log."""


def test_claude_construct_rewrite_golden(tree):
    skill(tree, "core", "claudy", CLAUDE_CONSTRUCTS)
    text = render_skills(load_sources(tree))[".agents/skills/claudy/SKILL.md"]
    golden = GOLDEN_SKILLS / "claudy" / "SKILL.md"
    if os.environ.get("UPDATE_GOLDEN"):
        golden.parent.mkdir(parents=True, exist_ok=True)
        golden.write_text(text)
    assert text == golden.read_text()
    for token in CLAUDE_TOKENS:
        assert token not in text, token
    assert "`plan-execute` skill" in text
    assert "<scratchpad dir>/<epic>-return.json" in text
    assert "10 minutes" in text
    assert "numbered" in text.lower()


def test_no_claude_only_constructs_emitted():
    from harness.emit import registry

    sources = load_sources(REAL)
    reg = registry()
    assert {"antigravity", "codex", "copilot", "cursor", "gemini"} <= set(reg)
    skills = render_skills(sources)
    for target, emitter in reg.items():
        out = {**skills, **emitter.render(sources)}
        emitted = {p: t for p, t in out.items() if "skills/" in p}
        assert ".agents/skills/start-development/SKILL.md" in emitted, target
        assert ".agents/skills/plan-execute/SKILL.md" in emitted, target
        for path, text in emitted.items():
            for token in CLAUDE_TOKENS:
                assert token not in text, f"{target}: {path} carries {token!r}"
    sd = skills[".agents/skills/start-development/SKILL.md"]
    assert "`plan-execute` skill" in sd
    assert "ticket.py apply-run <epic> <scratchpad dir>/<epic>-return.json" in sd
    assert "--return <scratchpad dir>/<epic>-return.json" in sd


def _ticket():
    import importlib.util

    path = REAL / "plugins/workbench/skills/start-development/scripts/ticket.py"
    spec = importlib.util.spec_from_file_location("ticket_fallback_test", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_fallback_uses_ticket_py():
    text = render_skills(load_sources(REAL))[".agents/skills/plan-execute/SKILL.md"]
    ticket = "plugins/workbench/skills/start-development/scripts/ticket.py"
    for needle in (
        f"{ticket} tasks <epic>",
        f"{ticket} worktrees <epic>",
        f"{ticket} path <epic> approvals",
        f"{ticket} apply-run <epic> <scratchpad dir>/<epic>-return.json",
        f"{ticket} continue <epic>",
        "--return <scratchpad dir>/<epic>-return.json",
        "approvals.json",
        "verify-task.py",
    ):
        assert needle in text, needle
    for token in CLAUDE_TOKENS:
        assert token not in text, token
    blocks = re.findall(r"```json\n(.*?)```", text, re.S)
    assert blocks, "the fallback shows the return schema as a json block"
    ret = json.loads(blocks[0])
    t = _ticket()
    task = ret["tasks"][0]
    assert task["verification"]["head"] and task["branch"]
    blocked = t._ids(ret.get("blocked"), "id", "taskId")
    escalated = t._ids(ret.get("escalated"), "id", "taskId")
    assert t._run_status(task, blocked, escalated, ret.get("escalated")) == "done"
    for d in ret["discovered"]:
        assert d["taskId"] and d["what"]
    assert {a["status"] for a in ret["approvals"]} <= {
        "delivered",
        "blocked",
        "escalated",
        "unverified",
    }
