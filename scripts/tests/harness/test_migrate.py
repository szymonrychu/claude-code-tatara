import importlib.util
import json
import subprocess
from pathlib import Path

import pytest
from harness import emit, migrate, setup

CORE = Path(__file__).resolve().parents[3] / "plugins/workbench/scripts/lib/workbench.py"
_spec = importlib.util.spec_from_file_location("wb_core_test", CORE)
wb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(wb)

OTHERS = [h for h in wb.HARNESS_DIRS if h != "claude"]


def snapshot(root: Path) -> dict[str, bytes]:
    return {
        str(p.relative_to(root)): p.read_bytes()
        for p in sorted(root.rglob("*"))
        if p.is_file() and ".git/" not in str(p)
    }


@pytest.fixture
def mtree(tree):
    cdir = tree / ".claude"
    (cdir / "workbench.json").write_text(
        json.dumps({"harness": {"targets": ["cursor"]}, "overlapIgnore": ["x"]}, indent=2) + "\n"
    )
    (cdir / "settings.local.json").write_text('{"a": 1}\n')
    (cdir / "harness-manifest.json").write_text('{"cursor": []}\n')
    (cdir / "worktrees").mkdir()
    (cdir / "worktrees/note.txt").write_text("keep\n")
    return tree


def git(cwd, *args):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


@pytest.mark.parametrize("harness", OTHERS)
def test_roundtrip_per_harness(mtree, harness):
    before = snapshot(mtree)
    d = mtree / wb.HARNESS_DIRS[harness]
    assert migrate.migrate(mtree, harness) == d
    assert json.loads((d / "workbench.json").read_text())["harness"]["active"] == harness
    assert (d / "settings.local.json").is_file()
    assert (d / "harness-manifest.json").is_file()
    assert (d / "worktrees/note.txt").is_file()
    assert not (mtree / ".claude/workbench.json").exists()
    assert (mtree / ".claude/settings.json").is_file()  # claude-specific files stay
    assert (mtree / ".claude/rules/always.md").is_file()
    assert migrate.migrate(mtree, "claude") == mtree / ".claude"
    assert snapshot(mtree) == before
    if harness != "claude":
        assert not any(mtree.joinpath(wb.HARNESS_DIRS[harness]).glob("workbench.json"))


@pytest.mark.parametrize("harness", OTHERS)
def test_idempotent(mtree, harness):
    migrate.migrate(mtree, harness)
    once = snapshot(mtree)
    migrate.migrate(mtree, harness)
    assert snapshot(mtree) == once


def test_claude_when_already_claude_is_noop(mtree):
    before = snapshot(mtree)
    migrate.migrate(mtree, "claude")
    assert snapshot(mtree) == before


def test_tools_follow_the_move(mtree):
    git(mtree, "init", "-q")
    migrate.migrate(mtree, "codex")
    assert wb.config_dir(mtree) == mtree / ".codex"
    assert wb.worktrees_dir(mtree) == mtree / ".codex/worktrees"
    assert wb.active_harness(mtree) == "codex"
    assert wb.load_config(mtree)["overlapIgnore"][-1] == "x"
    migrate.migrate(mtree, "claude")
    assert wb.worktrees_dir(mtree) == mtree / ".claude/worktrees"
    assert wb.active_harness(mtree) == "claude"


def test_refuses_with_registered_worktree(mtree):
    git(mtree, "init", "-q")
    git(mtree, "-c", "user.name=t", "-c", "user.email=t@t", "add", "-A")
    git(mtree, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "x")
    (mtree / ".claude/worktrees/note.txt").unlink()
    git(mtree, "worktree", "add", "-q", str(mtree / ".claude/worktrees/w1"), "-b", "w1")
    before = snapshot(mtree)
    with pytest.raises(migrate.MigrateError, match="worktree"):
        migrate.migrate(mtree, "cursor")
    assert snapshot(mtree) == before
    assert migrate.main([str(Path("cursor")), "--root", str(mtree)]) == 1
    assert snapshot(mtree) == before
    git(mtree, "worktree", "remove", str(mtree / ".claude/worktrees/w1"))
    migrate.migrate(mtree, "cursor")
    assert (mtree / ".cursor/workbench.json").is_file()


def test_refuses_on_destination_conflict(mtree):
    (mtree / ".gemini").mkdir()
    (mtree / ".gemini/workbench.json").write_text('{"other": true}\n')
    before = snapshot(mtree)
    with pytest.raises(migrate.MigrateError, match="already exists"):
        migrate.migrate(mtree, "gemini")
    assert snapshot(mtree) == before
    assert migrate.main(["gemini", "--root", str(mtree)]) == 1


def test_destination_conflict_on_other_owned_file(mtree):
    (mtree / ".gemini").mkdir()
    (mtree / ".gemini/settings.local.json").write_text('{"different": 1}\n')
    before = snapshot(mtree)
    with pytest.raises(migrate.MigrateError, match="differs"):
        migrate.migrate(mtree, "gemini")
    assert snapshot(mtree) == before


def test_generator_files_in_destination_untouched(mtree):
    (mtree / ".cursor/rules").mkdir(parents=True)
    (mtree / ".cursor/rules/a.mdc").write_text("gen\n")
    migrate.migrate(mtree, "cursor")
    migrate.migrate(mtree, "claude")
    assert (mtree / ".cursor/rules/a.mdc").read_text() == "gen\n"


def test_unknown_harness(mtree):
    assert migrate.main(["nope", "--root", str(mtree)]) == 1


class Fake(emit.Emitter):
    def __init__(self, target):
        self.target = target

    def render(self, sources):
        return {f".{self.target}/a.txt": "a\n"}


@pytest.fixture
def fakes(monkeypatch):
    reg = {t: Fake(t) for t in ("cursor", "codex", "gemini")}
    monkeypatch.setattr(emit, "registry", lambda: reg)


def test_setup_single_target_migrates(mtree, fakes):
    assert setup.main(["cursor", "--root", str(mtree)]) == 0
    assert (mtree / ".cursor/a.txt").is_file()
    assert wb.config_dir(mtree) == mtree / ".cursor"
    assert wb.active_harness(mtree) == "cursor"


def test_setup_claude_migrates_back_and_generates_nothing(mtree, fakes):
    setup.main(["cursor", "--root", str(mtree)])
    gen = snapshot(mtree / ".cursor")
    assert setup.main(["claude", "--root", str(mtree)]) == 0
    assert wb.config_dir(mtree) == mtree / ".claude"
    assert wb.active_harness(mtree) == "claude"
    assert (mtree / ".cursor/a.txt").read_bytes() == gen[("a.txt")]


def test_setup_several_targets_do_not_migrate(mtree, fakes, capsys):
    assert setup.main(["cursor", "codex", "--root", str(mtree)]) == 0
    assert wb.config_dir(mtree) == mtree / ".claude"
    assert str(mtree / ".claude") in capsys.readouterr().out
    assert setup.main(["all", "--root", str(mtree)]) == 0
    assert wb.config_dir(mtree) == mtree / ".claude"


def test_clean_of_active_harness_migrates_back_first(mtree, fakes):
    setup.main(["cursor", "--root", str(mtree)])
    assert setup.main(["--clean", "cursor", "--root", str(mtree)]) == 0
    assert wb.config_dir(mtree) == mtree / ".claude"
    assert wb.active_harness(mtree) == "claude"
    assert not (mtree / ".cursor/a.txt").exists()
    cfg = json.loads((mtree / ".claude/workbench.json").read_text())
    assert cfg.get("harness", {}).get("targets", []) == []


def test_refusals_move_nothing(mtree):
    git(mtree, "init", "-q")
    git(mtree, "-c", "user.name=t", "-c", "user.email=t@t", "add", "-A")
    git(mtree, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "x")
    git(mtree, "worktree", "add", "-q", str(mtree / ".claude/worktrees/w1"), "-b", "w1")
    before = snapshot(mtree)
    with pytest.raises(migrate.MigrateError, match="worktree"):
        migrate.migrate(mtree, "cursor")
    assert snapshot(mtree) == before
    git(mtree, "worktree", "remove", str(mtree / ".claude/worktrees/w1"))
    (mtree / ".gemini").mkdir()
    (mtree / ".gemini/workbench.json").write_text('{"other": true}\n')
    before = snapshot(mtree)
    with pytest.raises(migrate.MigrateError, match="already exists"):
        migrate.migrate(mtree, "gemini")
    assert snapshot(mtree) == before


def test_setup_migration_rules(mtree, fakes):
    assert setup.main(["cursor", "--root", str(mtree)]) == 0
    assert wb.config_dir(mtree) == mtree / ".cursor"
    assert setup.main(["claude", "--root", str(mtree)]) == 0
    assert wb.config_dir(mtree) == mtree / ".claude"
    assert setup.main(["all", "--root", str(mtree)]) == 0
    assert wb.config_dir(mtree) == mtree / ".claude"


def test_tools_follow_move(mtree):
    git(mtree, "init", "-q")
    migrate.migrate(mtree, "gemini")
    assert wb.worktrees_dir(mtree) == mtree / ".gemini/worktrees"
    assert wb.load_config(mtree)["overlapIgnore"][-1] == "x"
    migrate.migrate(mtree, "claude")
    assert wb.worktrees_dir(mtree) == mtree / ".claude/worktrees"


def test_setup_single_target_no_migrate(mtree, fakes, capsys):
    assert setup.main(["cursor", "--no-migrate", "--root", str(mtree)]) == 0
    assert (mtree / ".cursor/a.txt").is_file()
    assert wb.config_dir(mtree) == mtree / ".claude"
    assert wb.active_harness(mtree) == "claude"
    assert str(mtree / ".claude") in capsys.readouterr().out


def test_setup_no_migrate_keeps_a_teammates_migrated_dir(mtree, fakes):
    setup.main(["cursor", "--root", str(mtree)])
    assert setup.main(["codex", "--no-migrate", "--root", str(mtree)]) == 0
    assert (mtree / ".codex/a.txt").is_file()
    assert wb.config_dir(mtree) == mtree / ".cursor"
    assert wb.active_harness(mtree) == "cursor"


def test_extra_target_keeps_config_dir(mtree, fakes):
    setup.main(["cursor", "--root", str(mtree)])
    assert setup.main(["codex", "gemini", "--root", str(mtree)]) == 0
    assert (mtree / ".codex/a.txt").is_file()
    assert wb.config_dir(mtree) == mtree / ".cursor"
    assert wb.active_harness(mtree) == "cursor"


def test_claude_with_no_migrate_is_rejected(mtree, fakes):
    setup.main(["cursor", "--root", str(mtree)])
    with pytest.raises(SystemExit) as e:
        setup.main(["claude", "--no-migrate", "--root", str(mtree)])
    assert e.value.code == 2
    assert wb.config_dir(mtree) == mtree / ".cursor"
