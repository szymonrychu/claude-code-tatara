import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "worktree-create" / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from create import create  # noqa: E402
from merge import merge_back, prune_empty_dirs  # noqa: E402

GIT = ["git", "-c", "user.email=t@t", "-c", "user.name=T", "-c", "commit.gpgsign=false"]


def git(repo, *args):
    return subprocess.run(GIT + list(args), cwd=repo, check=True, capture_output=True, text=True)


def test_prunes_nested_empty_dirs_up_to_root(tmp_path):
    (tmp_path / "a" / "b" / "c").mkdir(parents=True)
    removed = prune_empty_dirs(tmp_path, ["a/b/c/f.py"])
    assert removed == ["a", "a/b", "a/b/c"]
    assert tmp_path.is_dir()
    assert not (tmp_path / "a").exists()


def test_stops_at_dir_holding_a_file(tmp_path):
    (tmp_path / "a" / "b" / "c").mkdir(parents=True)
    (tmp_path / "a" / "keep.txt").write_text("x")
    removed = prune_empty_dirs(tmp_path, ["a/b/c/f.py"])
    assert removed == ["a/b", "a/b/c"]
    assert (tmp_path / "a" / "keep.txt").exists()


def test_removes_dirs_holding_only_empty_dirs(tmp_path):
    (tmp_path / "a" / "x" / "y").mkdir(parents=True)
    (tmp_path / "a" / "b").mkdir()
    removed = prune_empty_dirs(tmp_path, ["a/b/f.py"])
    assert removed == ["a", "a/b", "a/x", "a/x/y"]


def test_prune_stops_at_untracked_file(tmp_path):
    (tmp_path / "a").mkdir()
    (tmp_path / "a" / "untracked.log").write_text("x")
    outside = tmp_path / "outside"
    (outside / "empty").mkdir(parents=True)
    (tmp_path / "link").symlink_to(outside)
    assert prune_empty_dirs(tmp_path, ["a/f.py", "link/empty/f.py"]) == []
    assert (outside / "empty").is_dir()
    assert (tmp_path / "a" / "untracked.log").exists()


def test_prune_never_removes_root(tmp_path):
    root = tmp_path / "r"
    (root / "z" / "a").mkdir(parents=True)
    (root / "b").mkdir()
    removed = prune_empty_dirs(root, ["z/a/f.py", "b/g.py", "h.py"])
    assert removed == sorted(removed) == ["b", "z", "z/a"]
    assert root.is_dir()


def test_missing_dirs_and_root_level_paths_are_fine(tmp_path):
    assert prune_empty_dirs(tmp_path, ["nope/f.py", "top.py"]) == []
    assert tmp_path.is_dir()


def test_merge_back_prunes_deleted_dirs(tmp_path):
    repo = tmp_path / "proj"
    (repo / "old" / "sub").mkdir(parents=True)
    git(tmp_path, "init", "-q", "-b", "main", str(repo))
    (repo / "old" / "sub" / "m.py").write_text("x\n")
    (repo / "README.md").write_text("b\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "base")
    wt = Path(create("rm", start=repo)["path"])
    (repo / "old" / "sub" / "leftover").mkdir()
    git(wt, "rm", "-q", "old/sub/m.py")
    git(wt, "commit", "-qm", "delete")
    info = merge_back("rm", start=repo)
    assert not (repo / "old").exists()
    assert any("old/sub/leftover" in n and "pruned" in n for n in info["notes"])
