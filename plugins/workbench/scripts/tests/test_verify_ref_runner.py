"""verify-task.py re-runs an AC test ref with its package's runner from the package root."""

import json
import os
import stat
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import test_verify_task as base  # noqa: E402
from test_verify_task import ac, branch, by_id, commit, verify  # noqa: E402

repo = base.repo


def stub_pwd(tmp_path, monkeypatch, names, exit_code=0):
    """Fake executables that append 'cwd| name argv' to a record file."""
    d = tmp_path / "bin"
    d.mkdir(exist_ok=True)
    rec = tmp_path / "record.txt"
    for n in names:
        p = d / n
        p.write_text(f'#!/bin/bash\necho "$(pwd -P)| {n} $*" >> "{rec}"\nexit {exit_code}\n')
        p.chmod(p.stat().st_mode | stat.S_IEXEC)
    monkeypatch.setenv("PATH", f"{d}{os.pathsep}{os.environ['PATH']}")
    return rec


def lines(rec):
    return rec.read_text().splitlines() if rec.exists() else []


def test_rerun_from_package_root(repo, tmp_path, monkeypatch):
    rec = stub_pwd(tmp_path, monkeypatch, ["uv"])
    branch(repo)
    commit(repo, {
        "nodes/web_ui/pyproject.toml": "",
        "nodes/web_ui/uv.lock": '[[package]]\nname = "pytest"\n',
        "nodes/web_ui/tests/test_x.py": "def test_name():\n    pass\n",
    })  # fmt: skip
    ref = "nodes/web_ui/tests/test_x.py::test_name"
    out = verify(repo, "echo nothing", "--no-triage", acs=[ac("A1", "x", "test", ref)])
    a = by_id(out)["A1"]
    pkg = (repo / "nodes/web_ui").resolve()
    assert a["met"] is True
    assert a["how"] == (
        "re-ran (builtin, nodes/web_ui) "
        "uv run --frozen pytest tests/test_x.py::test_name -q: exit 0"
    )
    assert lines(rec) == [f"{pkg}| uv run --frozen pytest tests/test_x.py::test_name -q"]


def test_ref_runners_entry_used(repo, tmp_path, monkeypatch):
    rec = stub_pwd(tmp_path, monkeypatch, ["mytool"])
    branch(repo)
    commit(repo, {
        ".claude/workbench.json": json.dumps({"refRunners": {"**/*.rs": "mytool {file}"}}),
        "crate/src/lib.rs": "x\n",
    })  # fmt: skip
    out = verify(
        repo, "echo nothing", "--no-triage", acs=[ac("A1", "x", "test", "crate/src/lib.rs")]
    )
    a = by_id(out)["A1"]
    assert a["met"] is True and "(refRunners, " in a["how"]
    assert lines(rec) == [f"{repo.resolve()}| mytool crate/src/lib.rs"]


def test_no_runner_message(repo):
    branch(repo)
    commit(repo, {"docs/spec.xyz": "x\n"})
    out = verify(
        repo, "echo nothing", "--no-triage", acs=[ac("A1", "x", "test", "docs/spec.xyz::t")]
    )
    a = by_id(out)["A1"]
    assert a["met"] is False
    assert a["how"] == (
        "ref not in command output and no runner for docs/spec.xyz: "
        "add a refRunners entry in .claude/workbench.json"
    )


def test_install_deps_per_package_root(repo, tmp_path, monkeypatch):
    rec = stub_pwd(tmp_path, monkeypatch, ["uv", "npm"])
    branch(repo)
    commit(repo, {
        "pyproject.toml": "",
        "uv.lock": "",
        "svc/pyproject.toml": "",
        "svc/uv.lock": "",
        "svc/tests/test_a.py": "def test_a():\n    pass\n",
        "svc/tests/test_b.py": "def test_b():\n    pass\n",
        "web/package.json": "{}",
        "web/package-lock.json": "{}",
        "web/a.test.mjs": "test('c', () => {})\n",
    })  # fmt: skip
    refs = ["svc/tests/test_a.py::test_a", "svc/tests/test_b.py::test_b", "web/a.test.mjs::c"]
    verify(
        repo, "true", "--install", "--no-triage",
        acs=[ac(f"A{i}", "x", "test", r) for i, r in enumerate(refs)],
    )  # fmt: skip
    top, svc, web = [(repo / p).resolve() for p in (".", "svc", "web")]
    installs = [x for x in lines(rec) if "sync" in x or " ci" in x]
    assert sorted(installs) == sorted([
        f"{top}| uv sync --frozen",
        f"{svc}| uv sync --frozen",
        f"{web}| npm ci",
    ])  # fmt: skip
