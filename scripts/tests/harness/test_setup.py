import json
import subprocess
import sys
from pathlib import Path

import pytest
from harness import emit, setup

SETUP = Path(__file__).resolve().parents[2] / "harness" / "setup.py"


class Fake(emit.Emitter):
    def __init__(self, target):
        self.target = target

    def render(self, sources):
        return {f".{self.target}/a.txt": f"{self.target} a\n", f".{self.target}/b/c.txt": "c\n"}


@pytest.fixture(autouse=True)
def fakes(monkeypatch):
    reg = {t: Fake(t) for t in ("cursor", "codex", "gemini")}
    monkeypatch.setattr(emit, "registry", lambda: reg)


@pytest.fixture
def clean_tree(tree):
    cfg = tree / ".claude/workbench.json"
    cfg.write_text(
        json.dumps(
            {
                "harness": {"targets": [], "models": {"cursor": {"opus": "x"}}},
                "overlapIgnore": ["x.lock"],
            }
        )
    )
    return tree


def cfg(tree):
    for d in (".claude", ".cursor", ".codex", ".gemini", ".agents", ".github"):
        if (tree / d / "workbench.json").is_file():
            return json.loads((tree / d / "workbench.json").read_text())
    raise AssertionError("no workbench.json")


def run(tree, *args):
    return setup.main([*args, "--root", str(tree)])


def test_writes_targets_and_skills_and_records(clean_tree):
    assert run(clean_tree, "cursor") == 0
    assert (clean_tree / ".cursor/a.txt").read_text() == "cursor a\n"
    assert (clean_tree / ".agents/skills/alpha/SKILL.md").is_file()
    assert not (clean_tree / ".codex").exists()
    c = cfg(clean_tree)
    assert c["harness"]["targets"] == ["cursor"]
    assert c["harness"]["active"] == "cursor"  # a single target migrates the config dir
    assert c["harness"]["models"] == {"cursor": {"opus": "x"}}
    assert c["overlapIgnore"] == ["x.lock"]
    assert not (clean_tree / ".claude/skills").exists()


def test_all_and_union(clean_tree):
    run(clean_tree, "cursor", "codex")
    assert run(clean_tree, "all") == 0
    assert set(cfg(clean_tree)["harness"]["targets"]) == {"cursor", "codex", "gemini"}
    assert (clean_tree / ".gemini/b/c.txt").is_file()


def test_unknown_target_exits_2(clean_tree, capsys):
    assert run(clean_tree, "nope") == 2
    assert "nope" in capsys.readouterr().err
    assert cfg(clean_tree)["harness"]["targets"] == []


def test_writes_into_resolved_config_dir(clean_tree):
    (clean_tree / ".agents").mkdir(exist_ok=True)
    (clean_tree / ".claude/workbench.json").rename(clean_tree / ".agents/workbench.json")
    (clean_tree / ".agents/workbench.json").write_text(
        json.dumps({"harness": {"active": "antigravity"}})
    )
    assert run(clean_tree, "codex", "gemini") == 0
    c = json.loads((clean_tree / ".agents/workbench.json").read_text())
    assert c["harness"] == {"active": "antigravity", "targets": ["codex", "gemini"]}
    assert not (clean_tree / ".claude/workbench.json").exists()


def test_check_nothing_recorded_passes(clean_tree):
    assert run(clean_tree, "--check") == 0


def test_check_clean_then_drift(clean_tree, capsys):
    run(clean_tree, "cursor", "codex")
    assert run(clean_tree, "--check") == 0
    (clean_tree / ".cursor/a.txt").write_text("changed")
    (clean_tree / ".codex/b/c.txt").unlink()
    (clean_tree / ".agents/skills/beta/SKILL.md").write_text("x")
    capsys.readouterr()
    assert run(clean_tree, "--check") == 1
    out = capsys.readouterr().out
    for p in (".cursor/a.txt", ".codex/b/c.txt", ".agents/skills/beta/SKILL.md"):
        assert p in out
    assert ".codex/a.txt" not in out


def test_check_only_recorded_targets(clean_tree):
    run(clean_tree, "cursor")
    assert run(clean_tree, "--check") == 0  # gemini/codex were never written


def test_clean_removes_only_own_files(clean_tree):
    run(clean_tree, "cursor", "codex")
    (clean_tree / ".cursor/mine.txt").write_text("user file")
    assert run(clean_tree, "--clean", "cursor") == 0
    assert not (clean_tree / ".cursor/a.txt").exists()
    assert not (clean_tree / ".cursor/b").exists()
    assert (clean_tree / ".cursor/mine.txt").read_text() == "user file"
    assert (clean_tree / ".codex/a.txt").is_file()
    assert (clean_tree / ".agents/skills/alpha/SKILL.md").is_file()  # codex still owns it
    assert cfg(clean_tree)["harness"]["targets"] == ["codex"]
    assert run(clean_tree, "--clean", "codex") == 0
    assert not (clean_tree / ".agents/skills").exists()
    assert "targets" not in cfg(clean_tree)["harness"]
    assert (clean_tree / "AGENTS.md").is_file()


def test_clean_never_removes_unowned_file(clean_tree):
    (clean_tree / ".cursor").mkdir()
    (clean_tree / ".cursor/a.txt").write_text("not written by us")
    assert run(clean_tree, "--clean", "cursor") == 0
    assert (clean_tree / ".cursor/a.txt").read_text() == "not written by us"


def test_clean_unknown_target_exits_2(clean_tree):
    assert run(clean_tree, "--clean", "nope") == 2


def test_stale_files_pruned_on_rewrite(clean_tree, monkeypatch):
    run(clean_tree, "cursor")

    class Smaller(Fake):
        def render(self, sources):
            return {".cursor/a.txt": "new\n"}

    monkeypatch.setattr(emit, "registry", lambda: {"cursor": Smaller("cursor")})
    run(clean_tree, "cursor")
    assert (clean_tree / ".cursor/a.txt").read_text() == "new\n"
    assert not (clean_tree / ".cursor/b/c.txt").exists()


def test_cli_check_and_unknown_target_real_registry(clean_tree):
    r = subprocess.run(
        [sys.executable, str(SETUP), "--check", "--root", str(clean_tree)],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stderr
    r = subprocess.run(
        [sys.executable, str(SETUP), "bogus", "--root", str(clean_tree)],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 2


def test_setup_then_check_clean(clean_tree):
    assert run(clean_tree, "cursor", "codex") == 0
    assert cfg(clean_tree)["harness"]["targets"] == ["cursor", "codex"]
    assert run(clean_tree, "--check") == 0


def test_check_detects_drift(clean_tree, capsys):
    run(clean_tree, "cursor")
    (clean_tree / ".cursor/a.txt").write_text("hand edited")
    capsys.readouterr()
    assert run(clean_tree, "--check") == 1
    assert ".cursor/a.txt" in capsys.readouterr().out


def test_clean_removes_only_generated(clean_tree):
    run(clean_tree, "cursor")
    (clean_tree / ".cursor/mine.txt").write_text("user file")
    assert run(clean_tree, "--clean", "cursor") == 0
    assert not (clean_tree / ".cursor/a.txt").exists()
    assert (clean_tree / ".cursor/mine.txt").read_text() == "user file"
