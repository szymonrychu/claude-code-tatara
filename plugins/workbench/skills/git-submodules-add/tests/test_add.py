import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_lib"))

import add  # noqa: E402
import common  # noqa: E402


def _run(cmd, cwd):
    subprocess.run(cmd, cwd=cwd, check=True, capture_output=True, text=True)


@pytest.fixture
def bare_repo_on_develop(tmp_path):
    bare = tmp_path / "remote.git"
    _run(["git", "init", "-q", "--bare", str(bare)], cwd=tmp_path)

    work = tmp_path / "work"
    _run(["git", "init", "-q", "-b", "develop", str(work)], cwd=tmp_path)
    _run(["git", "config", "user.email", "test@test.local"], cwd=work)
    _run(["git", "config", "user.name", "Test"], cwd=work)
    (work / "README.md").write_text("hello\n")
    _run(["git", "add", "README.md"], cwd=work)
    _run(["git", "commit", "-q", "-m", "init"], cwd=work)
    _run(["git", "remote", "add", "origin", str(bare)], cwd=work)
    _run(["git", "push", "-q", "origin", "develop"], cwd=work)

    _run(["git", "symbolic-ref", "HEAD", "refs/heads/develop"], cwd=bare)
    return bare


@pytest.fixture
def workbench(tmp_path, monkeypatch):
    root = tmp_path / "workbench"
    root.mkdir()
    _run(["git", "init", "-q", str(root)], cwd=tmp_path)
    (root / ".gitmodules").write_text("")
    (root / "code").mkdir()
    monkeypatch.chdir(root)
    # local bare repos stand in for remotes in tests; git blocks recursive
    # file:// transport (submodule add) by default since CVE-2022-39253
    monkeypatch.setenv("GIT_ALLOW_PROTOCOL", "file")
    return root


def test_default_branch_detects_non_main(bare_repo_on_develop):
    assert add.default_branch(str(bare_repo_on_develop)) == "develop"


def test_default_branch_failure_on_missing_repo(tmp_path):
    with pytest.raises(common.RepoError):
        add.default_branch(str(tmp_path / "nope.git"))


@pytest.mark.parametrize(
    "url,expected",
    [
        ("https://github.com/org/repo.git", "repo"),
        ("https://github.com/org/repo", "repo"),
        ("git@github.com:org/repo.git", "repo"),
        ("git@github.com:org/repo", "repo"),
        ("ssh://git@github.com/org/repo.git", "repo"),
        ("https://github.com/org/repo.git/", "repo"),
    ],
)
def test_submodule_name_derivation(url, expected):
    assert add.submodule_name(url) == expected


def test_submodule_name_garbage_raises():
    with pytest.raises(common.RepoError):
        add.submodule_name("///")


def test_process_url_skips_when_path_already_exists(workbench):
    (workbench / "code" / "repo").mkdir()
    report = common.Report()
    add.process_url("https://example.com/org/repo.git", workbench, report)
    rendered = report.render()
    assert "skipped" in rendered
    assert "repo" in rendered
    assert report.exit_code == 0


def test_process_url_skips_when_already_a_submodule(workbench):
    (workbench / ".gitmodules").write_text(
        '[submodule "repo"]\n\tpath = code/repo\n\turl = https://example.com/org/repo.git\n'
    )
    report = common.Report()
    add.process_url("https://example.com/org/repo.git", workbench, report)
    assert "skipped" in report.render()


def test_process_url_adds_submodule(workbench, bare_repo_on_develop):
    report = common.Report()
    add.process_url(str(bare_repo_on_develop), workbench, report)
    rendered = report.render()
    assert "added" in rendered
    assert "develop" in rendered
    assert report.exit_code == 0
    assert (workbench / "code" / "remote.git").exists() or (workbench / "code" / "remote").exists()


def test_process_url_failure_on_garbage_url(workbench, tmp_path):
    report = common.Report()
    missing = tmp_path / "does-not-exist-xyz.git"
    add.process_url(str(missing), workbench, report)
    assert "failed" in report.render()
    assert report.exit_code == 1


def test_main_aggregates_across_urls_and_exit_code(workbench, bare_repo_on_develop, tmp_path):
    (workbench / "code" / "already-there").mkdir()
    (workbench / ".gitmodules").write_text(
        '[submodule "already-there"]\n\tpath = code/already-there\n'
        "\turl = https://example.com/org/already-there.git\n"
    )
    missing = tmp_path / "nope-xyz.git"
    with pytest.raises(SystemExit) as exc_info:
        add.main(
            [
                "https://example.com/org/already-there.git",
                str(bare_repo_on_develop),
                str(missing),
            ]
        )
    assert exc_info.value.code == 1


def test_main_all_ok_exit_zero(workbench, bare_repo_on_develop):
    with pytest.raises(SystemExit) as exc_info:
        add.main([str(bare_repo_on_develop)])
    assert exc_info.value.code == 0
