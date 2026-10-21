import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "worktree-create" / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from create import create  # noqa: E402
from merge import main, merge_back  # noqa: E402

GIT = ["git", "-c", "user.email=t@t", "-c", "user.name=T", "-c", "commit.gpgsign=false"]


def git(repo, *args):
    return subprocess.run(GIT + list(args), cwd=repo, check=True, capture_output=True, text=True)


def setup(tmp_path, suites, monkeypatch):
    monkeypatch.setenv("SUITE_LOCK_DIR", str(tmp_path / "lock"))
    repo = tmp_path / "proj"
    git(tmp_path, "init", "-q", "-b", "main", str(repo))
    (repo / ".claude").mkdir()
    cfg = {"suites": suites} if suites is not None else {}
    (repo / ".claude" / "workbench.json").write_text(json.dumps(cfg))
    (repo / "a.txt").write_text("a\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "base")
    wt = Path(create("ww", start=repo)["path"])
    (wt / "b.txt").write_text("b\n")
    git(wt, "add", "-A")
    git(wt, "commit", "-qm", "work")
    return repo


def test_suites_run_after_merge(tmp_path, monkeypatch):
    repo = setup(tmp_path, ["pwd > one.out", "echo two > two.out"], monkeypatch)
    info = merge_back("ww", start=repo)
    assert info["suites"] == "pass"
    assert (repo / "one.out").read_text().strip() == str(repo.resolve())
    assert (repo / "two.out").exists()


def test_failing_suite_exit_4(tmp_path, monkeypatch, capsys):
    repo = setup(tmp_path, ["seq 1 30; exit 3", "touch never.out"], monkeypatch)
    monkeypatch.chdir(repo)
    rc = main(["--name", "ww"])
    out = capsys.readouterr().out
    assert rc == 4
    assert "suites: FAIL seq 1 30; exit 3 exit 3" in out
    assert "30" in out and "\n  15\n" not in out and "\n  16\n" in out
    assert not (repo / "never.out").exists()
    assert (repo / "b.txt").exists()


def test_no_suites_and_flag(tmp_path, monkeypatch, capsys):
    repo = setup(tmp_path, ["touch ran.out"], monkeypatch)
    monkeypatch.chdir(repo)
    assert main(["--name", "ww", "--no-suites"]) == 0
    assert not (repo / "ran.out").exists()
    capsys.readouterr()
    second = tmp_path / "second"
    second.mkdir()
    repo2 = setup(second, None, monkeypatch)
    monkeypatch.chdir(repo2)
    assert main(["--name", "ww"]) == 0
    assert "suites: none configured" in capsys.readouterr().out
