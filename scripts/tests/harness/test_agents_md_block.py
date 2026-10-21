import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from harness import agents_md, emit, setup
from harness.sources import _rules

REPO = Path(__file__).resolve().parents[3]
RULE_NAMES = ("tdd.md", "boy-scout.md", "concise-orchestrator.md")


class Fake(emit.Emitter):
    def __init__(self, target):
        self.target = target

    def render(self, sources):
        return {f".{self.target}/a.txt": "x\n"}


@pytest.fixture(autouse=True)
def fakes(monkeypatch):
    reg = {t: Fake(t) for t in ("cursor", "codex", "gemini")}
    monkeypatch.setattr(emit, "registry", lambda: reg)


@pytest.fixture
def wb(tree):
    rules = tree / "plugins/workbench/rules"
    rules.mkdir(parents=True)
    (rules / "tdd.md").write_text(
        "---\nname: tdd\n---\n\n# Test-driven\n\nBody one.\n\n```\n# not a heading\n```\n\n## Sub\n"
    )
    (rules / "boy-scout.md").write_text("# Boy scout\n\nBody two.\n")
    (rules / "concise-orchestrator.md").write_text("# Concise\n\nBody three.\n")
    (tree / ".claude/workbench.json").write_text(json.dumps({"harness": {"targets": []}}))
    return tree


def run(tree, *args):
    return setup.main([*args, "--root", str(tree)])


def block(text, name):
    b, e = f"<!-- workbench:{name}:begin -->", f"<!-- workbench:{name}:end -->"
    if b not in text:
        return None
    return text.split(b)[1].split(e)[0]


def test_rules_block_rendered(wb):
    out = agents_md.render_rules_block(wb)
    assert "enerated from plugins/workbench/rules/; edit there" in out
    assert "name: tdd" not in out and "---" not in out
    assert "## Test-driven\n" in out and "### Sub" in out
    assert "# not a heading" in out and "## not a heading" not in out
    assert out.index("Body one") < out.index("Body two") < out.index("Body three")


def test_render_path_rules_block(wb):
    out = agents_md.render_path_rules_block(SimpleNamespace(rules=_rules(wb)))
    assert "hen touching `**/*.py`, `**/pyproject.toml`, read `.claude/rules/python.md`" in out
    assert "always.md" not in out


def test_setup_refreshes_rules_block_for_any_target(wb):
    assert run(wb, "cursor") == 0
    text = (wb / "AGENTS.md").read_text()
    assert "Body one." in block(text, "rules")
    assert block(text, "path-rules") is None
    assert "Project block body." in text
    assert run(wb, "--check") == 0


def test_rules_block_drift(wb, capsys):
    run(wb, "cursor")
    src = wb / "plugins/workbench/rules/tdd.md"
    src.write_text(src.read_text() + "\nChanged.\n")
    assert run(wb, "--check") == 1
    assert "AGENTS.md" in capsys.readouterr().out
    run(wb, "cursor")
    assert "Changed." in (wb / "AGENTS.md").read_text()
    assert run(wb, "--check") == 0


def test_path_rules_only_for_codex_gemini(wb):
    run(wb, "codex")
    assert "python.md" in block((wb / "AGENTS.md").read_text(), "path-rules")
    assert run(wb, "--check") == 0
    run(wb, "gemini")
    assert run(wb, "--clean", "codex") == 0
    text = (wb / "AGENTS.md").read_text()
    assert block(text, "path-rules") is not None
    assert run(wb, "--clean", "gemini") == 0
    text = (wb / "AGENTS.md").read_text()
    assert "path-rules" not in text
    assert block(text, "rules") is not None


def test_rules_block_hand_edit_is_drift(wb, capsys):
    run(wb, "cursor")
    p = wb / "AGENTS.md"
    p.write_text(p.read_text().replace("Body one.", "Hand edited."))
    assert run(wb, "--check") == 1
    assert "AGENTS.md" in capsys.readouterr().out
    run(wb, "cursor")
    assert "Body one." in p.read_text() and "Hand edited." not in p.read_text()


def test_path_rules_missing_is_drift(wb):
    run(wb, "codex")
    p = wb / "AGENTS.md"
    p.write_text(agents_md.replace_block(p.read_text(), "path-rules", None))
    assert run(wb, "--check") == 1


def test_repo_agents_md_has_current_rules_block():
    text = (REPO / "AGENTS.md").read_text()
    assert block(text, "rules") == "\n" + agents_md.render_rules_block(REPO)
    for needle in ("Test-driven development", "Boy scout", "Concise orchestrator"):
        assert needle in block(text, "rules")


def lint(tmp_path, agents, claude):
    (tmp_path / "AGENTS.md").write_bytes(agents)
    (tmp_path / "CLAUDE.md").write_bytes(claude)
    task = REPO / "mise-tasks/lint/agents-md"
    return subprocess.run(
        ["bash", str(task)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env={"PATH": "/usr/bin:/bin", "WORKBENCH_ROOT": str(tmp_path)},
    )


def test_lint_size_limits(tmp_path):
    assert lint(tmp_path, b"a" * 23_999, b"b" * 100).returncode == 0
    r = lint(tmp_path, b"a" * 24_001, b"b")
    assert r.returncode == 1 and "AGENTS.md" in r.stderr
    r = lint(tmp_path, b"a" * 20_000, b"b" * 12_800)
    assert r.returncode == 1 and "32768" in r.stderr
    assert lint(tmp_path, b"a" * 20_000, b"b" * 12_000).returncode == 0
    assert sys.executable
