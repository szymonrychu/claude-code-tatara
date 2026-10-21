import textwrap
from pathlib import Path

import pytest
from harness import emit
from harness.sources import (
    FrontmatterError,
    HarnessConfig,
    HookReg,
    load_sources,
    parse_frontmatter,
)

REPO = Path(__file__).resolve().parents[3]


def test_agents_md_and_blocks(tree):
    s = load_sources(tree)
    assert s.agents_md.startswith("<!-- workbench:uninitialised:begin -->")
    assert set(s.agents_blocks) == {"uninitialised", "project", "rules"}
    assert s.agents_blocks["project"].strip() == "Project block body."
    assert s.agents_blocks["rules"] == "\n"


def test_rules(tree):
    s = load_sources(tree)
    assert [r.name for r in s.rules] == ["always", "python"]
    always, py = s.rules
    assert always.paths == ()
    assert py.paths == ("**/*.py", "**/pyproject.toml")
    assert py.body.lstrip().startswith("# Python")


def test_mcp_present_and_absent(tree):
    assert load_sources(tree).mcp["mcpServers"]["docs"]["url"].startswith("https://")
    (tree / ".mcp.json").unlink()
    assert load_sources(tree).mcp is None


def test_harness_config(tree):
    h = load_sources(tree).harness
    assert h == HarnessConfig(("cursor", "codex"), {"cursor": {"opus": "gpt-fixture"}}, "")
    (tree / ".claude" / "workbench.json").unlink()
    assert load_sources(tree).harness == HarnessConfig((), {}, "")


def test_loads_enabled_plugins_only(tree):
    s = load_sources(tree)
    assert [p.name for p in s.plugins] == ["core", "extra"]
    assert s.plugins[0].root == tree / "plugins" / "core"


def test_skills(tree):
    core, extra = load_sources(tree).plugins
    assert [k.name for k in core.skills] == ["alpha", "beta"]
    alpha, beta = core.skills
    assert alpha.description == "Folded description that spans two lines and ends here."
    assert alpha.dir == core.root / "skills" / "alpha"
    assert "${CLAUDE_PLUGIN_ROOT}" in alpha.body
    assert beta.description == "Quoted: description with a colon."
    assert beta.frontmatter["argument-hint"] == ["target", "mode"]
    assert extra.skills[0].description == "Literal line one.\nLiteral line two."


def test_agents(tree):
    core, extra = load_sources(tree).plugins
    scout = core.agents[0]
    assert (scout.name, scout.model, scout.tools) == (
        "scout",
        "opus",
        ("Read", "Grep", "Glob", "Bash"),
    )
    assert scout.description == "Read-only scout that maps code."
    assert scout.body.strip() == "You are a scout."
    assert extra.agents[0].tools == ("Read", "Bash")


def test_hooks(tree):
    core, extra = load_sources(tree).plugins
    assert extra.hooks == ()
    assert core.hooks == (
        HookReg("PreToolUse", "Bash", "bash-output-filter"),
        HookReg("PreToolUse", "Bash", "guard-bash"),
        HookReg("PreToolUse", "Edit|MultiEdit|NotebookEdit|Write", "protect-files"),
        HookReg("PostToolUse", "Edit|MultiEdit|NotebookEdit|Write", "format-file"),
        HookReg("PostToolUse", "Bash", "verify-recorder"),
        HookReg("SubagentStop", "", "subagent-commit-guard"),
    )


def test_missing_settings_means_no_plugins(tree):
    (tree / ".claude" / "settings.json").unlink()
    assert load_sources(tree).plugins == ()


def test_folded_and_literal_scalars():
    text = textwrap.dedent(
        """\
        ---
        a: plain
        b: 'single'
        c: true
        d: [x, "y z"]
        e:
          - one
          - two
        f: >-
          folded
          text

          para
        ---
        body
        """
    )
    fm, body = parse_frontmatter(text, "f.md")
    assert fm == {
        "a": "plain",
        "b": "single",
        "c": True,
        "d": ["x", "y z"],
        "e": ["one", "two"],
        "f": "folded text\npara",
    }
    assert body == "body\n"


def test_inline_list_keeps_commas_in_quotes():
    fm, _ = parse_frontmatter("---\na: [\"x, y\", 'p,q', z]\n---\n", "f.md")
    assert fm["a"] == ["x, y", "p,q", "z"]


def test_frontmatter_none():
    assert parse_frontmatter("# no fm\n", "f.md") == ({}, "# no fm\n")


@pytest.mark.parametrize(
    "text,line",
    [
        ("---\na: [x\n---\n", 2),
        ("---\na: {b: c}\n---\n", 2),
        ("---\njunk line\n---\n", 2),
        ("---\na: 1\n", 1),
        ('---\na: "open\n---\n', 2),
        ("---\na:\n  -\n---\n", 3),
        ("---\na: [x,,y]\n---\n", 2),
    ],
)
def test_bad_frontmatter_names_location(text, line):
    with pytest.raises(FrontmatterError) as e:
        parse_frontmatter(text, "dir/x.md")
    assert str(e.value).startswith(f"dir/x.md:{line}:")


def test_bad_file_error_names_path(tree):
    p = tree / "plugins" / "core" / "skills" / "beta" / "SKILL.md"
    p.write_text("---\nname: [oops\n---\n")
    with pytest.raises(FrontmatterError, match=r"beta/SKILL\.md:2:"):
        load_sources(tree)


def test_real_repo_frontmatter_parses():
    files = [
        *REPO.glob("plugins/*/skills/*/SKILL.md"),
        *REPO.glob("plugins/*/agents/*.md"),
        *REPO.glob(".claude/rules/*.md"),
    ]
    assert len(files) > 30
    for f in files:
        parse_frontmatter(f.read_text(), str(f))


def test_registry_autodiscovers(tmp_path, monkeypatch):
    import harness.targets as targets

    pkg = tmp_path / "targets"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("")
    (pkg / "zzfake.py").write_text(
        "from harness.emit import Emitter\n"
        "class Fake(Emitter):\n"
        "    target = 'zzfake'\n"
        "    def render(self, sources):\n"
        "        return {'x.txt': 'hi'}\n"
    )
    monkeypatch.setattr(targets, "__path__", [str(pkg)])
    reg = emit.registry()
    assert "zzfake" in reg
    assert reg["zzfake"].render(None) == {"x.txt": "hi"}
    init = (REPO / "scripts/harness/targets/__init__.py").read_text()
    assert "import" not in init.replace("auto-discovers", "")


def test_emitter_base_is_abstract():
    class E(emit.Emitter):
        target = "t"

    with pytest.raises(TypeError):
        E()


def test_registry_handles_dataclass_targets(tmp_path, monkeypatch):
    import harness.targets as targets

    pkg = tmp_path / "targets"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("")
    (pkg / "zzdc.py").write_text(
        "from __future__ import annotations\n"
        "from dataclasses import dataclass\n"
        "from harness.emit import Emitter\n"
        "@dataclass\nclass Cfg:\n    x: int = 1\n"
        "class Dc(Emitter):\n"
        "    target = 'zzdc'\n"
        "    def render(self, sources):\n"
        "        return {}\n"
    )
    monkeypatch.setattr(targets, "__path__", [str(pkg)])
    assert "zzdc" in emit.registry()


def test_parses_components(tree):
    test_rules(tree)
    test_skills(tree)
    test_agents(tree)
    test_hooks(tree)
