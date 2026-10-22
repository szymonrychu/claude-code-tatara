"""Pins the workbench root tooling: tool pins, task families, file tasks, pyproject."""

import os
import re
from pathlib import Path

import tomllib

ROOT = Path(__file__).resolve().parents[2]
EXACT = re.compile(r"^\d+(\.\d+)*$")
FILE_TASKS = {
    "mise-tasks/test/plugin": "mise run --cd plugins/workbench test",
    "mise-tasks/test/scripts": 'pytest scripts/tests -m "not slow"',
    "mise-tasks/lint/plugin": "mise run --cd plugins/workbench lint",
    "mise-tasks/lint/root": "shellcheck",
}


def _mise() -> dict:
    return tomllib.loads((ROOT / ".mise.toml").read_text())


def test_tools_are_pinned_exactly():
    tools = _mise()["tools"]
    expected = {
        "python": "3.14.6",
        "ruff": "0.15.20",
        "shellcheck": "0.11.0",
        "bats": "1.13.0",
        "pipx:pytest": "9.1.1",
        "pipx:pre-commit": "4.6.0",
    }
    for name, version in expected.items():
        assert tools[name] == version
    for name in ("uv", "node", "jq", "gh", "pipx:pre-commit-hooks"):
        assert name in tools
    for name, version in tools.items():
        assert EXACT.match(version), f"{name} is not an exact version: {version}"


def test_root_mise_has_no_env_section():
    assert "env" not in _mise()


def _aggregators():
    tasks = _mise()["tasks"]
    assert tasks["test"]["depends"] == ["test:*"]
    assert tasks["lint"]["depends"] == ["lint:*"]
    assert tasks["fmt"]["run"] in ("ruff format plugins scripts", ["ruff format plugins scripts"])


def _markers():
    text = (ROOT / ".mise.toml").read_text()
    m = re.search(
        r"^# workbench:code-tasks:begin\n(.*?)^# workbench:code-tasks:end$", text, re.M | re.S
    )
    assert m, "markers missing"
    assert m.group(1).strip() == ""


def test_file_tasks_are_executable():
    for rel, needle in FILE_TASKS.items():
        p = ROOT / rel
        assert os.access(p, os.X_OK), f"{rel} not executable"
        body = p.read_text()
        assert body.startswith("#!/usr/bin/env bash")
        assert re.search(r"^#MISE description=\S", body, re.M)
        assert needle in body


def test_lint_root_covers_scripts_and_mise_tasks():
    body = (ROOT / "mise-tasks/lint/root").read_text()
    assert "ruff check" in body and "scripts" in body
    assert "mise-tasks" in body


def test_plugin_config_keeps_tasks_only():
    data = tomllib.loads((ROOT / "plugins/workbench/.mise.toml").read_text())
    assert "tools" not in data
    assert {"test", "lint", "fmt", "doctor"} <= set(data["tasks"])


def test_pyproject_holds_only_ruff_and_pytest():
    data = tomllib.loads((ROOT / "pyproject.toml").read_text())
    assert set(data) == {"tool"}
    assert set(data["tool"]) == {"ruff", "pytest"}
    ruff = data["tool"]["ruff"]
    assert ruff["line-length"] == 100
    assert ruff["lint"]["select"] == ["E", "F", "I", "UP", "B"]
    pt = data["tool"]["pytest"]["ini_options"]
    assert pt["testpaths"] == ["scripts/tests"]
    assert "--import-mode=importlib" in pt["addopts"]
    assert pt["pythonpath"] == ["scripts"]


def test_task_families_and_markers():
    _aggregators()
    _markers()


def test_tasks_call_the_pinned_pytest_binary():
    # pytest is a pipx tool pinned in .mise.toml, not a module of the mise python,
    # so `python -m pytest` only works where pytest happens to be importable.
    offenders = [
        str(p.relative_to(ROOT))
        for p in sorted((ROOT / "mise-tasks").rglob("*"))
        if p.is_file() and re.search(r"python3?\s+-m\s+pytest", p.read_text())
    ]
    assert not offenders, offenders


def test_e2e_task_runs_slow_tests():
    p = ROOT / "mise-tasks/e2e"
    assert os.access(p, os.X_OK)
    body = p.read_text()
    assert body.startswith("#!/usr/bin/env bash")
    assert re.search(r"^#MISE description=\S", body, re.M)
    assert "pytest scripts/tests -m slow" in body
    # outside the test: namespace, so root `test` (depends on test:*) never pulls it in
    assert not (ROOT / "mise-tasks/test/e2e").exists()
    assert "e2e" not in _mise()["tasks"].get("test", {}).get("depends", [])


def test_ci_runs_e2e_job():
    text = (ROOT / ".github/workflows/ci.yml").read_text()
    m = re.search(r"^  e2e:\n(.*?)(?=^  \S|\Z)", text, re.M | re.S)
    assert m, "no e2e job"
    assert "run: mise run e2e" in m.group(1)
