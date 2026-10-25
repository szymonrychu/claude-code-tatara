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
    ignore = shutil.ignore_patterns("__pycache__")
    shutil.copytree(SCRIPTS / "lib", root / "scripts" / "lib", ignore=ignore)
    fake = root / "skills" / "fake" / "tests"
    fake.mkdir(parents=True)
    (fake / "test_fake.py").write_text(FAKE_TEST)
    other = root / "skills" / "other" / "tests"
    other.mkdir(parents=True)
    (other / "test_other.py").write_text(OTHER_TEST)
    tmpdir = tmp_path / "tmpdir"
    tmpdir.mkdir()
    main = tmp_path / "main"
    main.mkdir()
    skip = ("RUN_TESTS_LOG_DIR", "WORKBENCH_ROOT", "CLAUDE_PROJECT_DIR")
    env = {k: v for k, v in os.environ.items() if k not in skip}
    env["WORKBENCH_ROOT"] = str(main)
    env["PYTEST"] = pt
    env["TMPDIR"] = str(tmpdir)

    def control(mode):
        (fake / "control").write_text(mode)

    def run(*cmd):
        return subprocess.run(
            ["bash", *cmd], cwd=root, env=env, capture_output=True, text=True, timeout=120
        )

    return SimpleNamespace(root=root, main=main, tmpdir=tmpdir, control=control, run=run, env=env)


def test_failing_component_keeps_full_output(tree):
    tree.control("fail")
    r = tree.run("scripts/run-tests.sh", "--only", "fake")
    assert r.returncode == 1, r.stdout + r.stderr
    assert "FAIL  fake" in r.stdout
    m = re.search(r"^        full output: (\S+)$", r.stdout, re.M)
    assert m, r.stdout
    log = Path(m.group(1))
    assert log.exists()
    assert log.parent.parent == tree.main / ".logs" / "run-tests"
    assert "line 1\n" in log.read_text()
    assert "line 1\n" not in r.stdout  # the 15-line tail cannot show it
    assert "failure logs:" in r.stdout
    assert r.stdout.index("FAILED:") < r.stdout.index("failure logs:")


def test_log_dir_override_and_fallback(tree, tmp_path):
    tree.control("fail")
    custom = tmp_path / "custom"
    tree.env["RUN_TESTS_LOG_DIR"] = str(custom)
    r = tree.run("scripts/run-tests.sh", "--only", "fake")
    assert r.returncode == 1, r.stdout + r.stderr
    assert (custom / "fake.log").exists()
    assert not (tree.main / ".logs").exists()
    del tree.env["RUN_TESTS_LOG_DIR"]
    del tree.env["WORKBENCH_ROOT"]  # tmp tree is not in git: no main checkout
    r = tree.run("scripts/run-tests.sh", "--only", "fake")
    assert r.returncode == 1, r.stdout + r.stderr
    m = re.search(r"^        full output: (\S+)$", r.stdout, re.M)
    assert m, r.stdout
    assert Path(m.group(1)).parent.parent == tree.tmpdir
    assert not (tree.main / ".logs").exists()


def test_green_run_leaves_nothing(tree):
    tree.control("pass")
    r = tree.run("scripts/run-tests.sh", "--only", "fake")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "all green" in r.stdout
    assert "full output:" not in r.stdout
    assert "failure logs:" not in r.stdout
    assert list(tree.tmpdir.glob("run-tests.*")) == []
    assert list((tree.main / ".logs" / "run-tests").glob("*")) == []


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
    hunts = tree.main / ".logs" / "flake-hunt"
    assert all(hunts in Path(p).parents for p in logs)


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


IDENT_TEST = """
import os
from pathlib import Path


def test_ident():
    keys = ("GIT_AUTHOR_NAME", "GIT_AUTHOR_EMAIL", "GIT_COMMITTER_NAME", "GIT_COMMITTER_EMAIL")
    out = Path(__file__).parent / "ident.txt"
    out.write_text("\\n".join(f"{k}={os.environ.get(k, '')}" for k in keys))
"""


def test_suites_get_a_git_identity_unless_one_is_set(tree):
    # CI runners have no git identity; suites that commit must not depend on the host's.
    ident = tree.root / "skills" / "ident" / "tests"
    ident.mkdir(parents=True)
    (ident / "test_ident.py").write_text(IDENT_TEST)
    for k in ("GIT_AUTHOR_NAME", "GIT_AUTHOR_EMAIL", "GIT_COMMITTER_NAME", "GIT_COMMITTER_EMAIL"):
        tree.env.pop(k, None)
    r = tree.run("scripts/run-tests.sh", "--only", "ident")
    assert r.returncode == 0, r.stdout + r.stderr
    got = dict(line.split("=", 1) for line in (ident / "ident.txt").read_text().splitlines())
    assert all(got.values()), got
    tree.env["GIT_AUTHOR_NAME"] = "Caller"
    tree.run("scripts/run-tests.sh", "--only", "ident")
    assert "GIT_AUTHOR_NAME=Caller" in (ident / "ident.txt").read_text()


PROBE_TEST = """
import os
from pathlib import Path


def test_probe(request):
    out = Path(__file__).parent / "probe.txt"
    out.write_text(f"basetemp={request.config.getoption('basetemp')}\\nTMPDIR={os.environ.get('TMPDIR', '')}")
"""


def _under_gitmodules_dir(path):
    return any((p / ".gitmodules").exists() for p in [path, *path.parents])


def test_suite_temp_dirs_are_outside_any_checkout(tree):
    # A fabricated initialised workbench: root finders walking up from a suite's
    # temp dir must never find it, so the temp dirs cannot live inside it.
    subprocess.run(["git", "init", "-q", str(tree.main)], check=True)
    (tree.main / "code").mkdir()
    (tree.main / ".gitmodules").write_text("")
    probe = tree.root / "skills" / "probe" / "tests"
    probe.mkdir(parents=True)
    (probe / "test_probe.py").write_text(PROBE_TEST)
    r = tree.run("scripts/run-tests.sh", "--only", "probe")
    assert r.returncode == 0, r.stdout + r.stderr
    got = dict(ln.split("=", 1) for ln in (probe / "probe.txt").read_text().splitlines())
    main = tree.main.resolve()
    for key in ("basetemp", "TMPDIR"):
        p = Path(got[key]).resolve()
        assert main not in p.parents and p != main, got
        assert not _under_gitmodules_dir(p), got
    # the log still goes to the tree's .logs/run-tests/<stamp>/<component>.log on red
    (tree.root / "skills" / "fake" / "tests" / "control").write_text("fail")
    r = tree.run("scripts/run-tests.sh", "--only", "fake")
    m = re.search(r"^        full output: (\S+)$", r.stdout, re.M)
    assert m, r.stdout
    log = Path(m.group(1))
    assert log.name == "fake.log" and log.parent.parent == tree.main / ".logs" / "run-tests"


def test_temp_dir_kept_on_failure_removed_on_green(tree):
    tree.control("pass")
    r = tree.run("scripts/run-tests.sh", "--only", "fake")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "temp dirs:" not in r.stdout
    assert list(tree.tmpdir.glob("run-tests*")) == []
    assert list((tree.main / ".logs" / "run-tests").glob("*")) == []
    tree.control("fail")
    r = tree.run("scripts/run-tests.sh", "--only", "fake")
    assert r.returncode == 1, r.stdout + r.stderr
    m = re.search(r"^temp dirs: (\S+)$", r.stdout, re.M)
    assert m, r.stdout
    assert r.stdout.index("full output:") < r.stdout.index("temp dirs:")
    kept = Path(m.group(1))
    assert kept.is_dir() and kept.parent == tree.tmpdir.resolve()
    assert (tree.main / ".logs" / "run-tests").is_dir()
    assert len(list((tree.main / ".logs" / "run-tests").glob("*/fake.log"))) == 1
