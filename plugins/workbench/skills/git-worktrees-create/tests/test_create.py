import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "create.py"


def _git(args, cwd):
    subprocess.run(["git"] + args, cwd=cwd, check=True, capture_output=True, text=True)


def _init_origin(path):
    path.mkdir(parents=True)
    _git(["init", "-q", "-b", "main"], path)
    _git(["config", "user.email", "test@test.local"], path)
    _git(["config", "user.name", "Test"], path)
    (path / "README.md").write_text("hello\n")
    _git(["add", "README.md"], path)
    _git(["commit", "-q", "-m", "init"], path)


def _add_branch(origin, branch, filename, content):
    _git(["checkout", "-q", "-b", branch], origin)
    (origin / filename).write_text(content)
    _git(["add", filename], origin)
    _git(["commit", "-q", "-m", f"add {filename}"], origin)
    _git(["checkout", "-q", "main"], origin)


def _rev_parse(path, ref):
    result = subprocess.run(
        ["git", "rev-parse", ref], cwd=path, check=True, capture_output=True, text=True
    )
    return result.stdout.strip()


@pytest.fixture
def workbench(tmp_path):
    root = tmp_path / "workbench"
    root.mkdir()
    (root / ".gitmodules").write_text(
        '[submodule "repo1"]\n\tpath = code/repo1\n\turl = ../origin/repo1\n\tbranch = main\n'
    )
    code_dir = root / "code"
    code_dir.mkdir()

    origin = tmp_path / "origin_repo1"
    _init_origin(origin)

    repo1 = code_dir / "repo1"
    _git(["clone", "-q", str(origin), str(repo1)], tmp_path)

    return root, origin, repo1


def _run_script(workbench_root, branch, repos):
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--branch", branch, "--repos", repos],
        cwd=workbench_root,
        capture_output=True,
        text=True,
    )
    return result


def test_creates_worktree_under_config_dir(workbench):
    root, origin, repo1 = workbench

    result = _run_script(root, "feature-new", "repo1")

    assert result.returncode == 0, result.stdout + result.stderr
    wt_path = root / ".claude" / "worktrees" / "feature-new" / "repo1"
    assert wt_path.is_dir()
    assert (wt_path / "README.md").is_file()

    list_result = subprocess.run(
        ["git", "worktree", "list"],
        cwd=repo1,
        check=True,
        capture_output=True,
        text=True,
    )
    assert str(wt_path) in list_result.stdout

    branch_head = _rev_parse(wt_path, "feature-new")
    main_head = _rev_parse(origin, "main")
    assert branch_head == main_head

    assert "repo1" in result.stdout
    assert "ok" in result.stdout
    assert "created" in result.stdout.lower()


def test_reuses_existing_remote_branch(workbench):
    root, origin, repo1 = workbench
    _add_branch(origin, "feature-existing", "extra.txt", "extra content\n")

    result = _run_script(root, "feature-existing", "repo1")

    assert result.returncode == 0, result.stdout + result.stderr
    wt_path = root / ".claude" / "worktrees" / "feature-existing" / "repo1"
    assert wt_path.is_dir()
    assert (wt_path / "extra.txt").is_file()

    branch_head = _rev_parse(wt_path, "feature-existing")
    remote_head = _rev_parse(origin, "feature-existing")
    assert branch_head == remote_head

    assert "reused" in result.stdout.lower()


def test_skips_existing_integration_tree(workbench):
    root, origin, repo1 = workbench

    first = _run_script(root, "feature-new", "repo1")
    assert first.returncode == 0, first.stdout + first.stderr

    second = _run_script(root, "feature-new", "repo1")

    assert second.returncode == 0, second.stdout + second.stderr
    assert "skipped" in second.stdout.lower()


def test_skips_tree_created_by_claim(workbench):
    root, origin, repo1 = workbench
    tree = root / ".claude" / "worktrees" / "my-epic" / "repo1"
    _git(["worktree", "add", "-q", "-b", "my-epic", str(tree)], repo1)
    head = _rev_parse(tree, "HEAD")

    result = _run_script(root, "my-epic", "repo1")

    assert result.returncode == 0, result.stdout + result.stderr
    assert "skipped" in result.stdout.lower()
    assert _rev_parse(tree, "HEAD") == head


def test_unknown_repo_reports_failure(workbench):
    root, origin, repo1 = workbench

    result = _run_script(root, "feature-new", "nope")

    assert result.returncode == 1
    assert "nope" in result.stdout
    assert "failed" in result.stdout.lower()

    wt_path = root / ".claude" / "worktrees" / "feature-new" / "nope"
    assert not wt_path.exists()


def test_multi_repo_continues_on_error(workbench):
    root, origin, repo1 = workbench

    result = _run_script(root, "feature-new", "repo1,nope")

    assert result.returncode == 1
    wt_path = root / ".claude" / "worktrees" / "feature-new" / "repo1"
    assert wt_path.is_dir()
    assert "repo1" in result.stdout
    assert "nope" in result.stdout
