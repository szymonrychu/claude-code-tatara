"""Pins the root config: ignore entries, local-only pre-commit hooks, workbench.json keys."""

import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIRS = [".claude", ".github", ".cursor", ".codex", ".gemini", ".agents"]
RUNTIME = [
    "scheduled_tasks.lock",
    "scheduled_tasks.json",
    "routines/.state/",
    "checkpoints/",
    "mailbox/",
    "agent-registry.json",
    "agent-memory-local",
    "first-run",
    "assistant-daemon-state.json",
]
ACCEPTED_KEYS = {"refRunners", "suites", "deploy", "overlapIgnore"}


def _ignore() -> set[str]:
    lines = (ROOT / ".gitignore").read_text().splitlines()
    return {x.strip() for x in lines if x.strip() and not x.startswith("#")}


def _tracked(path: str) -> bool:
    out = subprocess.run(
        ["git", "ls-files", path], cwd=ROOT, capture_output=True, text=True, check=True
    )
    return bool(out.stdout.strip())


def test_gitignore_base_entries():
    entries = _ignore()
    for e in [
        "__pycache__/", "*.pyc", ".pytest_cache/", ".ruff_cache/", ".venv/",
        "node_modules/", ".DS_Store", ".env", ".env.*", "!.env.example", ".logs/",
        ".worktrees/", "**/.claude/settings.local.json", "docs/plans/index.json",
        "docs/plans/facts.md", "docs/research/", "docs/handoffs/",
    ]:  # fmt: skip
        assert e in entries, e


def test_gitignore_per_config_dir_and_runtime():
    entries = _ignore()
    for d in CONFIG_DIRS:
        assert f"{d}/worktrees/" in entries
        assert f"{d}/settings.local.json" in entries
        assert f"{d}/harness.json" in entries or f"{d}/.harness-owned.json" in entries
    for r in RUNTIME:
        assert f".claude/{r}" in entries, r


def test_gitignore_has_no_superpowers_and_plugin_gitignore_retired():
    assert not any("superpowers" in e for e in _ignore())
    assert not _tracked("plugins/workbench/.gitignore")


def test_precommit_is_local_only():
    # Stdlib only (the template ships no PyYAML): every hook is a one-line flow mapping.
    text = (ROOT / ".pre-commit-config.yaml").read_text()
    repos = re.findall(r"^\s*-\s*repo:\s*(\S+)", text, re.M)
    assert repos and all(r == "local" for r in repos), repos
    hooks = re.findall(r"^\s*-\s*\{(.*)\}\s*$", text, re.M)
    assert hooks
    ids = set()
    for h in hooks:
        fields = dict(re.findall(r"(\w+):\s*([^,]+?)\s*(?:,|$)", h))
        assert fields.get("language") == "system", h
        ids.add(fields["id"])
    for want in [
        "trailing-whitespace", "end-of-file-fixer", "check-yaml", "check-json",
        "check-toml", "check-merge-conflict", "check-added-large-files",
        "ruff", "ruff-format", "shellcheck",
    ]:  # fmt: skip
        assert want in ids, want


def test_shellcheckrc():
    assert "disable=SC1090,SC1091" in (ROOT / ".shellcheckrc").read_text()


def test_workbench_config_keys():
    cfg = json.loads((ROOT / ".claude/workbench.json").read_text())
    assert set(cfg) <= ACCEPTED_KEYS
    assert "harness" not in cfg
    glob = "plugins/workbench/workflows/tests/*.test.mjs"
    cmd = "node --test --test-name-pattern {name} {file}"
    assert cfg["refRunners"] == {glob: cmd}
    assert not _tracked("plugins/workbench/.claude/workbench.json")


def test_gitignore_entries():
    test_gitignore_base_entries()
    test_gitignore_per_config_dir_and_runtime()
    test_gitignore_has_no_superpowers_and_plugin_gitignore_retired()
    assert "uv.lock" not in _ignore()
