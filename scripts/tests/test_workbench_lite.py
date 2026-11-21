"""workbench-lite: the portable user-scope pack stays generated, portable and opt-in."""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LITE = ROOT / "plugins" / "workbench-lite"
SYNC = ROOT / "scripts" / "sync_lite.py"
FORBIDDEN = re.compile(
    r"workbench\.py|_lib\b|\.scratchpad|\.logs|\bcode/|mise exec|orchestrator_|WORKBENCH_ROOT"
)
SKIP_PARTS = {"overrides", "__pycache__"}
SKIP_NAMES = {"README.md", "plugin.json", "LICENSE"}


def _generated():
    for p in LITE.rglob("*"):
        rel = p.relative_to(LITE)
        if p.is_file() and not SKIP_PARTS & set(rel.parts) and p.name not in SKIP_NAMES:
            yield p


def test_lite_in_sync():
    r = subprocess.run([sys.executable, str(SYNC), "--check"], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr


def test_lite_check_lists_drift(tmp_path):
    victim = LITE / "agents" / "reuse-hunter.md"
    original = victim.read_text()
    try:
        victim.write_text(original + "drift\n")
        r = subprocess.run([sys.executable, str(SYNC), "--check"], capture_output=True, text=True)
    finally:
        victim.write_text(original)
    assert r.returncode == 1
    assert "agents/reuse-hunter.md" in r.stderr


def test_lite_not_enabled_in_project_settings():
    enabled = json.loads((ROOT / ".claude/settings.json").read_text())["enabledPlugins"]
    # absent or explicitly false (the doctor wants every marketplace plugin listed)
    assert not [k for k, v in enabled.items() if k.startswith("workbench-lite@") and v]


def test_lite_no_workbench_only_refs():
    files = list(_generated())
    assert files
    for p in files:
        hits = FORBIDDEN.findall(p.read_text())
        assert not hits, f"{p.relative_to(LITE)}: {hits}"


def test_lite_ships_listed_items_and_no_hooks():
    manifest = json.loads((LITE / ".claude-plugin/plugin.json").read_text())
    assert "hooks" not in manifest and not (LITE / "hooks").exists()
    for a in (
        "codebase-cartographer architect-researcher reuse-hunter submodule-auditor scm-shepherd "
        "spec-reviewer research-docs-purist research-practitioner research-prior-art-scout "
        "research-paper-scout research-reviewer"
    ).split():
        assert (LITE / "agents" / f"{a}.md").is_file()
    for s in ("handoff", "start-research"):
        assert (LITE / "skills" / s / "SKILL.md").is_file()
    assert not list((LITE / "skills").rglob("tests"))


def test_handoff_runs_outside_workbench(tmp_path):
    repo = tmp_path / "flat"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    env = {k: v for k, v in os.environ.items() if k not in ("WORKBENCH_ROOT", "CLAUDE_PROJECT_DIR")}
    script = LITE / "skills/handoff/scripts/handoff.py"
    r = subprocess.run(
        [sys.executable, str(script), "new", "--slug", "demo"],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stderr
    out = Path(r.stdout.strip())
    assert out.is_file() and out.parent == repo / ".handoff"
    assert "# Handoff: demo" in out.read_text()


def test_start_research_path_helper_outside_workbench(tmp_path):
    repo = tmp_path / "flat"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    script = LITE / "skills/start-research/scripts/doc_path.sh"
    r = subprocess.run(
        ["bash", str(script), "research", "My Topic"], cwd=repo, capture_output=True, text=True
    )
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip().endswith("-my-topic.md")
    assert Path(r.stdout.strip()).parent == repo / "docs" / "research"
