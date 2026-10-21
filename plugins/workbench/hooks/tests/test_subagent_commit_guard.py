"""Tests for the SubagentStop commit guard.

Written after an orchestration run where five independent
subagents ended their turn reporting "waiting on the background run" while
holding uncommitted work (11, 14 and 118 dirty files, zero commits). Each had
been told in its brief to commit verified work and to bound every wait, and two
earlier agents in the same session had already lost a full run's work to a spend
limit for exactly this reason. Instructions did not hold, so this is mechanical.
"""

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

HOOK = Path(__file__).resolve().parents[1] / "subagent-commit-guard.py"


def _load_filter():
    spec = importlib.util.spec_from_file_location(
        "bash_output_filter", HOOK.parent / "bash-output-filter.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_hook(payload):
    """Run the hook exactly as Claude Code does. Returns (reason or None, rc)."""
    proc = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
    )
    if not proc.stdout.strip():
        return None, proc.returncode
    out = json.loads(proc.stdout)
    if out.get("decision") != "block":
        return None, proc.returncode
    return out.get("reason", ""), proc.returncode


def git(repo: Path, *args: str):
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)


def make_repo(path: Path) -> Path:
    """A git repo with one commit, at an arbitrary path."""
    path.mkdir(parents=True)
    git(path, "init", "-q", "-b", "main")
    git(path, "config", "user.email", "t@example.com")
    git(path, "config", "user.name", "T")
    (path / "seed.txt").write_text("seed\n")
    git(path, "add", "seed.txt")
    git(path, "commit", "-qm", "seed")
    return path


@pytest.fixture
def worktree(tmp_path: Path) -> Path:
    """A repo at a Claude-managed worktree path, as worktree-create makes."""
    return make_repo(tmp_path / "wb" / ".claude" / "worktrees" / "t4-decode-cardstate")


def test_blocks_when_worktree_has_modified_files(worktree: Path):
    (worktree / "seed.txt").write_text("changed\n")
    reason, rc = run_hook({"cwd": str(worktree)})
    assert reason is not None, "a dirty worktree must not be allowed to end the turn"
    assert rc == 0
    assert "1 " in reason and "uncommitted" in reason.lower()


def test_blocks_when_worktree_has_only_untracked_files(worktree: Path):
    (worktree / "new_module.py").write_text("x = 1\n")
    reason, _ = run_hook({"cwd": str(worktree)})
    assert reason is not None, "untracked work is still work that can be lost"


def test_reason_names_the_worktree_and_the_remedy(worktree: Path):
    (worktree / "seed.txt").write_text("changed\n")
    reason, _ = run_hook({"cwd": str(worktree)})
    assert reason is not None
    assert str(worktree) in reason
    assert "commit" in reason.lower()


def test_reason_counts_every_dirty_file(worktree: Path):
    for i in range(14):
        (worktree / f"f{i}.py").write_text("x\n")
    reason, _ = run_hook({"cwd": str(worktree)})
    assert reason is not None
    assert "14" in reason


def test_allows_a_clean_worktree(worktree: Path):
    reason, rc = run_hook({"cwd": str(worktree)})
    assert reason is None
    assert rc == 0


def test_allows_when_stop_hook_already_fired(worktree: Path):
    """Second pass must let the agent go, or the turn never ends."""
    (worktree / "seed.txt").write_text("changed\n")
    reason, _ = run_hook({"cwd": str(worktree), "stop_hook_active": True})
    assert reason is None


def test_ignores_a_dirty_repo_outside_a_worktree(tmp_path: Path):
    """The guard is scoped to agent worktrees; the main checkout is the human's."""
    repo = make_repo(tmp_path / "plain-repo")
    (repo / "seed.txt").write_text("changed\n")
    reason, _ = run_hook({"cwd": str(repo)})
    assert reason is None


def test_recognises_the_dotworktrees_layout(tmp_path: Path):
    """git-worktrees-create uses .worktrees/<branch>/<repo>."""
    repo = make_repo(tmp_path / "wb" / ".worktrees" / "feat-x" / "helmfile")
    (repo / "seed.txt").write_text("changed\n")
    reason, _ = run_hook({"cwd": str(repo)})
    assert reason is not None


def test_ignores_a_non_git_directory(tmp_path: Path):
    d = tmp_path / "wb" / ".claude" / "worktrees" / "not-a-repo"
    d.mkdir(parents=True)
    (d / "file.txt").write_text("x\n")
    reason, rc = run_hook({"cwd": str(d)})
    assert reason is None
    assert rc == 0


def test_ignores_a_missing_directory(tmp_path: Path):
    gone = tmp_path / "wb" / ".claude" / "worktrees" / "gone"
    reason, rc = run_hook({"cwd": str(gone)})
    assert reason is None
    assert rc == 0


def test_survives_malformed_stdin():
    proc = subprocess.run(
        [sys.executable, str(HOOK)],
        input="not json at all",
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    assert proc.stdout.strip() == ""


def test_survives_missing_cwd():
    reason, rc = run_hook({})
    assert reason is None
    assert rc == 0


# --- verification freshness (record written by verify-recorder.py) ---


def write_record(repo: Path, **fields):
    rec = {
        "command": "pytest tests/",
        "head": subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True
        ).stdout.strip(),
        "dirty": False,
        "passed": True,
        "at": "2026-10-11T00:00:00+00:00",
    }
    rec.update(fields)
    (repo / ".git" / "workbench-verify.json").write_text(json.dumps(rec))


def head_of(repo: Path) -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True
    ).stdout.strip()


def test_stale_record_blocks_and_names_both_shas(worktree: Path):
    old = head_of(worktree)
    (worktree / "b.txt").write_text("b\n")
    git(worktree, "add", "b.txt")
    git(worktree, "commit", "-qm", "second")
    write_record(worktree, head=old)
    reason, _ = run_hook({"cwd": str(worktree)})
    assert reason is not None
    assert f"last verification ran on {old} but HEAD is {head_of(worktree)}" in reason
    assert "Re-run pytest tests/" in reason
    assert "read the output" in reason
    assert str(worktree) in reason


def test_dirty_record_blocks(worktree: Path):
    write_record(worktree, dirty=True)
    reason, _ = run_hook({"cwd": str(worktree)})
    assert reason is not None
    assert "last verification ran on a dirty tree" in reason


def test_failed_record_blocks(worktree: Path):
    write_record(worktree, passed=False)
    reason, _ = run_hook({"cwd": str(worktree)})
    assert reason is not None
    assert "last verification did not pass" in reason


def test_fresh_passing_record_allows(worktree: Path):
    write_record(worktree)
    reason, _ = run_hook({"cwd": str(worktree)})
    assert reason is None


def test_no_record_allows(worktree: Path):
    reason, _ = run_hook({"cwd": str(worktree)})
    assert reason is None


def test_transcript_worktree_is_checked(worktree: Path, tmp_path: Path):
    old = head_of(worktree)
    (worktree / "b.txt").write_text("b\n")
    git(worktree, "add", "b.txt")
    git(worktree, "commit", "-qm", "second")
    write_record(worktree, head=old)
    plain = tmp_path / "plain"
    plain.mkdir()
    transcript = tmp_path / "agent.jsonl"
    lines = [
        "not json",
        json.dumps({"type": "user"}),
        json.dumps(
            {
                "message": {
                    "content": [
                        {
                            "type": "tool_use",
                            "name": "Bash",
                            "input": {"command": f"cd {worktree} && pytest"},
                        }
                    ]
                }
            }
        ),
    ]
    transcript.write_text("\n".join(lines) + "\n")
    reason, _ = run_hook({"cwd": str(plain), "agent_transcript_path": str(transcript)})
    assert reason is not None
    assert "last verification ran on" in reason
    assert str(worktree) in reason


def test_transcript_worktree_is_found_through_output_filter_wrapper(worktree: Path, tmp_path: Path):
    old = head_of(worktree)
    (worktree / "b.txt").write_text("b\n")
    git(worktree, "add", "b.txt")
    git(worktree, "commit", "-qm", "second")
    write_record(worktree, head=old)
    plain = tmp_path / "plain"
    plain.mkdir()
    wrapped = _load_filter().build_new_cmd(f"cd {worktree} && pytest -q")
    assert wrapped.startswith("TMP_OUT=")
    transcript = tmp_path / "agent.jsonl"
    entry = {
        "message": {
            "content": [{"type": "tool_use", "name": "Bash", "input": {"command": wrapped}}]
        }
    }
    transcript.write_text(json.dumps(entry) + "\n")
    reason, _ = run_hook({"cwd": str(plain), "agent_transcript_path": str(transcript)})
    assert reason is not None
    assert str(worktree) in reason


def test_missing_transcript_file_is_harmless(tmp_path: Path):
    reason, rc = run_hook({"cwd": str(tmp_path), "agent_transcript_path": str(tmp_path / "nope")})
    assert reason is None
    assert rc == 0


def test_stop_hook_active_allows_with_stale_record(worktree: Path):
    write_record(worktree, passed=False)
    reason, _ = run_hook({"cwd": str(worktree), "stop_hook_active": True})
    assert reason is None


def test_dirty_reason_wins_over_stale_record(worktree: Path):
    write_record(worktree, passed=False)
    (worktree / "seed.txt").write_text("changed\n")
    reason, _ = run_hook({"cwd": str(worktree)})
    assert reason is not None
    assert "uncommitted" in reason.lower()
    assert "last verification" not in reason


def test_worktrees_follow_config_dir(tmp_path: Path):
    """With a .cursor config dir, worktree-create lands under .cursor/worktrees
    and the commit guard treats that worktree as an agent worktree."""
    root = make_repo(tmp_path / "wb")
    (root / "code").mkdir()
    (root / ".gitmodules").write_text("")
    (root / ".cursor").mkdir()
    (root / ".cursor" / "workbench.json").write_text('{"harness": {"active": "cursor"}}')
    git(root, "add", "-A")
    git(root, "commit", "-qm", "cursor config")

    create = HOOK.parents[1] / "skills" / "worktree-create" / "scripts" / "create.py"
    proc = subprocess.run(
        [sys.executable, str(create), "--name", "cursor-wt"],
        cwd=root,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    wt = root / ".cursor" / "worktrees" / "cursor-wt"
    assert wt.is_dir()
    assert not (root / ".claude" / "worktrees").exists()

    (wt / "seed.txt").write_text("changed\n")
    reason, _ = run_hook({"cwd": str(wt)})
    assert reason is not None, "the guard must treat a .cursor worktree as an agent worktree"
