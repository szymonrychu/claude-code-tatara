"""run-tests.sh keeps failing output on disk; flake-hunt.sh repeats a component."""

import glob
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent

FAKE_TEST = """
from pathlib import Path


def test_fake(request):
    assert request.config.getoption("basetemp") is not None, "no --basetemp given"
    mode = (Path(__file__).parent / "control").read_text().strip()
    if mode == "fail":
        for i in range(1, 21):
            print(f"line {i}")
        assert False
"""

OTHER_TEST = """
def test_other():
    print("OTHER_RAN")
    assert False
"""


def _pytest_bin(shim_dir):
    found = shutil.which("pytest")
    if found and "/mise/shims/" not in found:
        return found
    mise = "~/.local/share/mise/installs/pipx-pytest/*/bin/pytest"
    for c in sorted(glob.glob(os.path.expanduser(mise))):
        if os.access(c, os.X_OK):
            return c
    if found:
        return found
    # No pytest binary anywhere: this process is itself pytest, so shim it.
    shim = Path(shim_dir) / "pytest"
    shim.write_text(f'#!/bin/sh\nexec "{sys.executable}" -m pytest "$@"\n')
    shim.chmod(0o755)
    return str(shim)


def test_pytest_bin_never_needs_a_skip(tmp_path, monkeypatch):
    monkeypatch.setenv("PATH", "/nonexistent")
    monkeypatch.setenv("HOME", str(tmp_path))
    pt = _pytest_bin(tmp_path)
    assert os.access(pt, os.X_OK)


@pytest.fixture
def tree(tmp_path):
    pt = _pytest_bin(tmp_path)
    root = tmp_path / "tree"
    (root / "scripts").mkdir(parents=True)
    for name in ("run-tests.sh", "flake-hunt.sh"):
        shutil.copy(SCRIPTS / name, root / "scripts" / name)
    fake = root / "skills" / "fake" / "tests"
    fake.mkdir(parents=True)
    (fake / "test_fake.py").write_text(FAKE_TEST)
    other = root / "skills" / "other" / "tests"
    other.mkdir(parents=True)
    (other / "test_other.py").write_text(OTHER_TEST)
    tmpdir = tmp_path / "tmpdir"
    tmpdir.mkdir()
    env = {k: v for k, v in os.environ.items() if k != "RUN_TESTS_LOG_DIR"}
    env["PYTEST"] = pt
    env["TMPDIR"] = str(tmpdir)

    def control(mode):
        (fake / "control").write_text(mode)

    def run(*cmd):
        return subprocess.run(
            ["bash", *cmd], cwd=root, env=env, capture_output=True, text=True, timeout=120
        )

    return SimpleNamespace(root=root, tmpdir=tmpdir, control=control, run=run)


def test_failing_component_keeps_full_output(tree):
    tree.control("fail")
    r = tree.run("scripts/run-tests.sh", "--only", "fake")
    assert r.returncode == 1, r.stdout + r.stderr
    assert "FAIL  fake" in r.stdout
    m = re.search(r"^        full output: (\S+)$", r.stdout, re.M)
    assert m, r.stdout
    log = Path(m.group(1))
    assert log.exists()
    assert "line 1\n" in log.read_text()
    assert "line 1\n" not in r.stdout  # the 15-line tail cannot show it
    assert "failure logs:" in r.stdout
    assert r.stdout.index("FAILED:") < r.stdout.index("failure logs:")


def test_green_run_leaves_nothing(tree):
    tree.control("pass")
    r = tree.run("scripts/run-tests.sh", "--only", "fake")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "all green" in r.stdout
    assert "full output:" not in r.stdout
    assert "failure logs:" not in r.stdout
    assert list(tree.tmpdir.glob("run-tests.*")) == []


def test_only_runs_one_component(tree):
    tree.control("pass")
    r = tree.run("scripts/run-tests.sh", "--only", "fake")
    assert "OTHER_RAN" not in r.stdout
    assert "other" not in r.stdout.split("components with tests")[0]
    r = tree.run("scripts/run-tests.sh")
    assert r.returncode == 1  # other fails when everything runs
    assert "OTHER_RAN" in r.stdout


def test_only_unknown_component_exits_2(tree):
    r = tree.run("scripts/run-tests.sh", "--only", "nope")
    assert r.returncode == 2
    assert "run-tests: no such component nope" in r.stderr


def test_flake_hunt_reports_failures_and_keeps_logs(tree):
    tree.control("fail")
    r = tree.run("scripts/flake-hunt.sh", "fake", "2", "2")
    assert r.returncode == 1, r.stdout + r.stderr
    assert "fails: 2/2" in r.stdout
    assert "run 1: FAIL" in r.stdout and "run 2: FAIL" in r.stdout
    logs = [ln.strip() for ln in r.stdout.splitlines() if ln.strip().endswith(".log")]
    assert len(logs) == 2
    assert all(Path(p).exists() for p in logs)


def test_flake_hunt_all_pass(tree):
    tree.control("pass")
    r = tree.run("scripts/flake-hunt.sh", "fake", "2")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "fails: 0/2" in r.stdout
    assert "run 1: PASS" in r.stdout
    assert list(tree.tmpdir.glob("flake-hunt.*")) == []


@pytest.mark.parametrize("args", [(), ("fake",), ("fake", "x"), ("fake", "0"), ("fake", "2", "0")])
def test_flake_hunt_bad_args_exit_2(tree, args):
    r = tree.run("scripts/flake-hunt.sh", *args)
    assert r.returncode == 2
    assert "usage:" in r.stderr
