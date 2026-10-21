"""workbench.py root locator: from the root, from a component, env precedence."""

import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS / "lib"))
import workbench  # noqa: E402

CLI = SCRIPTS / "lib" / "workbench.py"
GIT = ["git", "-c", "protocol.file.allow=always", "-c", "user.email=a@b.c", "-c", "user.name=t"]


def git(cwd, *args):
    subprocess.run([*GIT, *args], cwd=cwd, check=True, capture_output=True)


def metarepo(base: Path, name="meta") -> Path:
    comp = base / "src-comp"
    comp.mkdir()
    git(comp, "init", "-q")
    (comp / "sub").mkdir()
    (comp / "sub" / "f").write_text("x")
    git(comp, "add", ".")
    git(comp, "commit", "-qm", "init")
    root = base / name
    (root / "code").mkdir(parents=True)
    git(root, "init", "-q")
    git(root, "submodule", "add", str(comp), "code/x")
    git(root, "commit", "-qm", "sub")
    return root


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    monkeypatch.delenv("WORKBENCH_ROOT", raising=False)
    monkeypatch.delenv("CLAUDE_PROJECT_DIR", raising=False)


def test_root_from_root(tmp_path):
    root = metarepo(tmp_path)
    assert workbench.find_root(root) == (root.resolve(), workbench.METAREPO)


def test_root_from_component(tmp_path):
    root = metarepo(tmp_path)
    assert workbench.find_root(root / "code" / "x") == (root.resolve(), workbench.METAREPO)


def test_root_from_component_subdir(tmp_path):
    root = metarepo(tmp_path)
    assert workbench.find_root(root / "code" / "x" / "sub") == (root.resolve(), workbench.METAREPO)


def test_root_cli_from_component(tmp_path):
    root = metarepo(tmp_path)
    r = subprocess.run(
        [sys.executable, str(CLI), "root", "--from", str(root / "code" / "x" / "sub")],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0 and r.stdout.strip() == str(root.resolve())


def test_standalone_repo_has_no_root(tmp_path):
    d = tmp_path / "lone"
    d.mkdir()
    git(d, "init", "-q")
    assert workbench.find_root(d) is None


def test_workbench_root_env_wins(tmp_path, monkeypatch):
    a = metarepo(tmp_path, "a")
    (tmp_path / "b").mkdir()
    b = metarepo(tmp_path / "b", "b")
    monkeypatch.setenv("WORKBENCH_ROOT", str(a))
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(b))
    assert workbench.find_root(b / "code" / "x")[0] == a.resolve()


def test_project_dir_env_beats_walk(tmp_path, monkeypatch):
    a = metarepo(tmp_path, "a")
    (tmp_path / "b").mkdir()
    b = metarepo(tmp_path / "b", "b")
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(a))
    assert workbench.find_root(b / "code" / "x")[0] == a.resolve()


def test_doctor_no_gitmodules_exits_zero(tmp_path):
    d = tmp_path / "lone"
    d.mkdir()
    for action in ("root", "doctor"):
        r = subprocess.run(
            [sys.executable, str(CLI), action, "--from", str(d)], capture_output=True, text=True
        )
        assert r.returncode == 0, r.stderr
        assert "kind: none (uninitialised, no .gitmodules)" in r.stdout


def test_superproject_fallback_when_walk_up_misses(tmp_path, monkeypatch):
    root = metarepo(tmp_path)
    away = tmp_path / "away"
    away.mkdir()
    real_run = subprocess.run

    def fake(cmd, *a, **k):
        if "--show-superproject-working-tree" in cmd:
            return subprocess.CompletedProcess(cmd, 0, stdout=f"{root}\n", stderr="")
        return real_run(cmd, *a, **k)

    monkeypatch.setattr(workbench.subprocess, "run", fake)
    assert workbench.find_root(away) == (root.resolve(), workbench.METAREPO)


def test_env_precedence(tmp_path, monkeypatch):
    a = metarepo(tmp_path, "a")
    (tmp_path / "b").mkdir()
    b = metarepo(tmp_path / "b", "b")
    start = b / "code" / "x"
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(a))
    assert workbench.find_root(start)[0] == a.resolve()
    monkeypatch.setenv("WORKBENCH_ROOT", str(b))
    assert workbench.find_root(start)[0] == b.resolve()
