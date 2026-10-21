"""workbench.py config-dir resolver: one case per harness directory, none, two, mismatch."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS / "lib"))
import workbench  # noqa: E402

CLI = SCRIPTS / "lib" / "workbench.py"


def put(root: Path, d: str, body=None):
    (root / d).mkdir(parents=True, exist_ok=True)
    (root / d / "workbench.json").write_text(json.dumps(body if body is not None else {}))


@pytest.mark.parametrize("key,d", list(workbench.HARNESS_DIRS.items()))
def test_each_harness_dir(tmp_path, key, d):
    put(tmp_path, d)
    assert workbench.config_dir(tmp_path) == tmp_path / d
    assert workbench.worktrees_dir(tmp_path) == tmp_path / d / "worktrees"


def test_harness_dirs_table():
    assert workbench.HARNESS_DIRS == {
        "claude": ".claude",
        "copilot": ".github",
        "cursor": ".cursor",
        "codex": ".codex",
        "gemini": ".gemini",
        "antigravity": ".agents",
    }


def test_none_defaults_to_claude(tmp_path):
    assert workbench.config_dir(tmp_path) == tmp_path / ".claude"
    assert workbench.active_harness(tmp_path) == "claude"


def test_two_raises_naming_both(tmp_path):
    put(tmp_path, ".claude")
    put(tmp_path, ".cursor")
    with pytest.raises(workbench.ConfigError) as e:
        workbench.config_dir(tmp_path)
    assert ".claude" in str(e.value) and ".cursor" in str(e.value)


def test_mismatch_raises(tmp_path):
    put(tmp_path, ".cursor", {"harness": {"targets": [], "active": "codex"}})
    with pytest.raises(workbench.ConfigError, match="codex"):
        workbench.config_dir(tmp_path)


def test_match_ok_and_active_harness(tmp_path):
    put(tmp_path, ".codex", {"harness": {"targets": [], "active": "codex"}})
    assert workbench.config_dir(tmp_path) == tmp_path / ".codex"
    assert workbench.active_harness(tmp_path) == "codex"


def test_active_unknown_rejected(tmp_path):
    put(tmp_path, ".claude", {"harness": {"targets": [], "active": "vim"}})
    with pytest.raises(workbench.ConfigError, match="harness"):
        workbench.load_config(tmp_path)


def test_load_config_reads_config_dir(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    put(tmp_path, ".gemini", {"suites": ["x"], "harness": {"active": "gemini"}})
    c = workbench.load_config(tmp_path)
    assert c["suites"] == ["x"]
    assert c["harness"]["active"] == "gemini"


def test_worktree_markers():
    m = workbench.worktree_markers()
    for d in workbench.HARNESS_DIRS.values():
        assert f"{d}/worktrees/" in m
    assert ".worktrees/" in m


def test_cli_config_dir(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    (tmp_path / ".gitmodules").write_text("")
    (tmp_path / "code").mkdir()
    put(tmp_path, ".cursor")
    r = subprocess.run(
        [sys.executable, str(CLI), "config-dir"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env={"PATH": "/usr/bin:/bin", "WORKBENCH_ROOT": str(tmp_path)},
    )
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == str(tmp_path / ".cursor")
