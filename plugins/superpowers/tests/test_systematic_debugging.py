"""Pins systematic-debugging: the four phases kept, the post-deploy hand-off, models on dispatch."""

import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from skill_checks import SKILLS, flat, problems, skill_text  # noqa: E402

NAME = "systematic-debugging"
SKILL = SKILLS / NAME
FILES = {
    "SKILL.md",
    "root-cause-tracing.md",
    "defense-in-depth.md",
    "condition-based-waiting.md",
    "condition-based-waiting-example.ts",
    "find-polluter.sh",
}


def text() -> str:
    return flat(skill_text(NAME))


def test_structure():
    assert problems(NAME) == []


def test_the_four_phases_kept():
    t = text()
    for phase in (
        "Phase 1: Root Cause Investigation",
        "Phase 2: Pattern Analysis",
        "Phase 3: Hypothesis and Testing",
        "Phase 4: Implementation",
    ):
        assert phase in t, phase
    assert "NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST" in t


def test_post_deploy_failure_continues_from_grafana():
    t = text()
    assert "post-deploy failure" in t
    assert "continues from `grafana-debugging-start`" in t
    assert "when the `workbench-observability` pack is enabled" in t


def test_every_dispatch_sets_the_model():
    t = text()
    assert "every dispatch sets the model explicitly" in t
    assert "research on opus" in t


def test_only_the_vendored_files_are_tracked():
    tracked = subprocess.run(
        ["git", "ls-files", "--", "."], cwd=SKILL, capture_output=True, text=True, check=True
    ).stdout.split()
    assert set(tracked) == FILES
    assert not (SKILL / "CREATION-LOG.md").exists()
    assert not list(SKILL.glob("test-*.md"))


def test_find_polluter_passes_shellcheck():
    assert shutil.which("shellcheck"), "shellcheck is required"
    result = subprocess.run(
        ["shellcheck", str(SKILL / "find-polluter.sh")], capture_output=True, text=True
    )
    assert result.returncode == 0, result.stdout
