"""--tdd-revert gives red evidence for deletions: no empty directories left behind."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import test_verify_task as base  # noqa: E402
from test_verify_task import branch, commit, git, verify  # noqa: E402

repo = base.repo

RETIRED = "from pathlib import Path\nassert not Path('pkg/old').exists()\n"


def retire(repo):
    commit(repo, {"pkg/old/a.py": "x\n", "keep.py": "k\n"}, "seed")
    branch(repo)
    commit(repo, {"pkg/old/a.py": None, "tests/retire_check.py": RETIRED})


def test_deletion_red_green_evidence(repo):
    retire(repo)
    out = verify(repo, "python3 tests/retire_check.py", "--no-triage", "--tdd-revert")
    assert out["tdd"]["ran"] is True
    assert out["tdd"]["failedOnBase"] is True
    assert out["tdd"]["passedOnHead"] is True
    assert not (repo / "pkg" / "old").exists()
    assert not (repo / "pkg").exists()
    assert git(repo, "status", "--porcelain") == ""


def test_prunes_before_checks(repo):
    retire(repo)
    (repo / "pkg" / "old").mkdir(parents=True, exist_ok=True)
    out = verify(repo, "python3 tests/retire_check.py", "--no-triage")
    assert out["passed"] is True
    assert not (repo / "pkg").exists()


def test_nonempty_sibling_dir_survives(repo):
    retire(repo)
    commit(repo, {"pkg/other.py": "o\n"})
    out = verify(repo, "python3 tests/retire_check.py", "--no-triage", "--tdd-revert")
    assert out["tdd"]["passedOnHead"] is True
    assert (repo / "pkg" / "other.py").exists()


def test_restore_prunes_created_dirs(repo, monkeypatch):
    commit(repo, {"gen/sub/x.py": "x\n"}, "seed")
    git(repo, "rm", "-rq", "gen")
    git(repo, "commit", "-qm", "drop")
    assert not (repo / "gen").exists()
    monkeypatch.setattr(base.vt, "prune_deleted_dirs", lambda cwd, changes: [])
    made = []
    base.vt._put(str(repo), "HEAD~1", "gen/sub/x.py", None, made)
    assert (repo / "gen" / "sub" / "x.py").exists()
    base.vt._restore(str(repo), [{"file": "gen/sub/x.py", "status": "D"}], {}, made)
    assert not (repo / "gen").exists()


def test_changed_field_lists_name_status(repo):
    retire(repo)
    out = verify(repo, "python3 tests/retire_check.py", "--no-triage")
    got = {(c["file"], c["status"]) for c in out["changed"]}
    assert ("pkg/old/a.py", "D") in got
    assert ("tests/retire_check.py", "A") in got
