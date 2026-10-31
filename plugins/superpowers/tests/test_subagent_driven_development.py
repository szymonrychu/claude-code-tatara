"""Pins subagent-driven-development: one implementer per chunk, one whole-diff review."""

import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from skill_checks import SKILLS, flat, problems, skill_text  # noqa: E402

NAME = "subagent-driven-development"
SKILL = SKILLS / NAME
SCRIPTS = ("task-brief", "review-package", "sdd-workspace")
FIXTURE = """# Demo implementation plan

## Agreed rung

Rung 1.

## Chunk 1: First (model: sonnet)

### S1: one

- Files: `a.py`

```markdown
## Chunk 2: inside a fence is not a header
```

### S2: two

- Files: `b.py`

## Chunk 2: Second (model: opus)

### S3: three

## Chunk 10: Tenth (model: sonnet)

### S9: nine

## Files to delete

none
"""


def text() -> str:
    return flat(skill_text(NAME))


def test_structure():
    assert problems(NAME) == []


def test_claim_and_one_implementer_per_chunk():
    t = text()
    assert "ticket.py move <plan> in-progress" in t
    assert "workbench:implementer" in t
    assert "one `workbench:implementer` per chunk" in t
    assert "sequential" in t
    assert "one tree" in t
    assert "model from the chunk header" in t


def test_one_whole_diff_reviewer():
    t = text()
    assert "workbench:reviewer" in t
    assert "(sonnet)" in t
    assert "git diff <base>...HEAD" in t
    assert "under-delivery against every agreed item" in t
    assert "over-delivery of any change no step covers" in t
    assert "then quality" in t


def test_security_researcher_lane():
    t = text()
    assert "security-researcher" in t
    assert "secrets, SOPS, RBAC, ingress, privilege, CI vars, image pins or hooks" in t


def test_two_fix_rounds_by_continuing_the_same_agents():
    t = text()
    assert "at most two fix rounds" in t
    assert "continuing the same agents" in t


def test_undelivered_and_discovered():
    t = text()
    assert "`undelivered` is a finding" in t
    assert "`discovered` is recommended and never built" in t


def test_retro_on_a_pass():
    t = text()
    assert "retro.md" in t
    assert "templates/retro.md" in t
    assert "Recommendations" in t


def test_rulings_not_stalls_and_stop_conditions():
    t = text()
    assert "Rulings, not stalls" in t
    for stop in (
        "an irreversible or destructive operation",
        "a security-sensitive action",
        "a side effect outside this worktree",
        "a plan so broken that every path forward is a guess",
        "an irreversible operation not listed at the gate stops the run",
    ):
        assert stop in t, stop


def test_every_dispatch_sets_the_model():
    assert "Always specify the model explicitly" in text()
    for prompt in ("implementer-prompt.md", "re-review-prompt.md"):
        assert "model:" in (SKILL / prompt).read_text(), prompt


def test_upstream_loop_parts_absent():
    t = text()
    low = t.lower()
    assert "5 rounds" not in low
    assert "rounds 4-5" not in low
    assert "escalat" not in low
    assert "more capable model" not in low
    assert "task reviewer" not in low
    assert "task-reviewer-prompt.md" not in t
    assert "superpowers:executing-plans" not in t
    assert not (SKILL / "task-reviewer-prompt.md").exists()


def test_scripts_pass_shellcheck():
    assert shutil.which("shellcheck"), "shellcheck is required"
    paths = [str(SKILL / "scripts" / s) for s in SCRIPTS]
    result = subprocess.run(["shellcheck", *paths], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout


def test_task_brief_extracts_one_chunk(tmp_path):
    plan = tmp_path / "implementation-plan.md"
    plan.write_text(FIXTURE)
    out = tmp_path / "brief.md"
    script = SKILL / "scripts" / "task-brief"
    done = subprocess.run(
        ["bash", str(script), str(plan), "1", str(out)], capture_output=True, text=True
    )
    assert done.returncode == 0, done.stderr
    brief = out.read_text()
    assert brief.startswith("## Chunk 1: First (model: sonnet)")
    assert "### S1: one" in brief
    assert "### S2: two" in brief
    assert "inside a fence is not a header" in brief
    assert "Second" not in brief
    assert "Tenth" not in brief
    assert "Files to delete" not in brief
    assert "Agreed rung" not in brief

    out10 = tmp_path / "brief10.md"
    done = subprocess.run(
        ["bash", str(script), str(plan), "10", str(out10)], capture_output=True, text=True
    )
    assert done.returncode == 0, done.stderr
    assert "### S9: nine" in out10.read_text()
    assert "Files to delete" not in out10.read_text()


def test_task_brief_missing_chunk_exits_3(tmp_path):
    plan = tmp_path / "implementation-plan.md"
    plan.write_text(FIXTURE)
    done = subprocess.run(
        ["bash", str(SKILL / "scripts" / "task-brief"), str(plan), "3", str(tmp_path / "x.md")],
        capture_output=True,
        text=True,
    )
    assert done.returncode == 3
    assert "chunk 3 not found" in done.stderr
