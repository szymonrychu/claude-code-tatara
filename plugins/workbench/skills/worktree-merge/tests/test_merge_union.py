import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "worktree-create" / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from create import WorktreeError, create  # noqa: E402
from merge import merge_back  # noqa: E402

GIT = ["git", "-c", "user.email=t@t", "-c", "user.name=T", "-c", "commit.gpgsign=false"]


def git(repo, *args):
    return subprocess.run(GIT + list(args), cwd=repo, check=True, capture_output=True, text=True)


@pytest.fixture
def repo(tmp_path):
    r = tmp_path / "proj"
    git(tmp_path, "init", "-q", "-b", "main", str(r))
    (r / "README.md").write_text("# T\n\nbase line\n")
    (r / "code.txt").write_text("one\n")
    git(r, "add", "-A")
    git(r, "commit", "-qm", "base")
    return r


def commit(repo, rel, text, msg=None):
    (repo / rel).write_text(text)
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", msg or f"edit {rel}")


def test_readme_conflict_union_merged(repo):
    wt = Path(create("feat", start=repo)["path"])
    commit(wt, "README.md", "# T\n\nbase line\nagent line\n")
    commit(repo, "README.md", "# T\n\nbase line\nmain line\n")
    info = merge_back("feat", start=repo)
    text = (repo / "README.md").read_text()
    assert "agent line" in text and "main line" in text and "<<<<" not in text
    assert info["unionMerged"] == ["README.md"]
    assert any("union-merged" in n and "README.md" in n for n in info["notes"])
    assert not wt.exists()


def test_union_repeats_per_replayed_commit(repo):
    wt = Path(create("multi", start=repo)["path"])
    commit(wt, "README.md", "# T\n\nbase line\nagent one\n")
    commit(wt, "README.md", "# T\n\nbase line\nagent one\nagent two\n")
    commit(repo, "README.md", "# T\n\nbase line\nmain line\n")
    info = merge_back("multi", start=repo)
    text = (repo / "README.md").read_text()
    assert "agent one" in text and "agent two" in text and "main line" in text
    assert "<<<<" not in text
    assert info["unionMerged"] == ["README.md"]


def test_source_conflict_stops(repo):
    wt = Path(create("mixed", start=repo)["path"])
    commit(wt, "README.md", "# T\n\nbase line\nagent line\n")
    commit(wt, "code.txt", "agent\n")
    commit(repo, "README.md", "# T\n\nbase line\nmain line\n")
    commit(repo, "code.txt", "main\n")
    with pytest.raises(WorktreeError) as e:
        merge_back("mixed", start=repo)
    assert "conflict" in str(e.value).lower() and "code.txt" in str(e.value)
    assert wt.exists()
    assert (wt / "code.txt").read_text() == "agent\n"
    assert "rebase" not in git(wt, "status").stdout.lower().split("\n")[0]


def test_repo_glob_union_merged(repo):
    (repo / ".claude").mkdir()
    commit(repo, ".claude/workbench.json", '{"overlapIgnore": ["notes.txt"]}\n')
    commit(repo, "notes.txt", "a\n")
    wt = Path(create("cfg", start=repo)["path"])
    commit(wt, "notes.txt", "a\nagent\n")
    commit(repo, "notes.txt", "a\nmain\n")
    info = merge_back("cfg", start=repo)
    assert info["unionMerged"] == ["notes.txt"]
    text = (repo / "notes.txt").read_text()
    assert "agent" in text and "main" in text


def test_union_merge_lands_in_the_integration_tree(repo):
    ept = Path(create("ep", start=repo)["path"])
    task = Path(create("ep-t", base="ep", start=repo)["path"])
    commit(task, "README.md", "# T\n\nbase line\nagent line\n")
    commit(ept, "README.md", "# T\n\nbase line\nepic line\n")
    info = merge_back("ep-t", base="ep", start=repo)
    text = (ept / "README.md").read_text()
    assert "agent line" in text and "epic line" in text and "<<<<" not in text
    assert info["unionMerged"] == ["README.md"]
    assert "agent line" not in (repo / "README.md").read_text()
