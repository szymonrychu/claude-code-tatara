import os
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import common  # noqa: E402

GITMODULES = """[submodule "foo"]
\tpath = code/foo
\turl = https://example.com/foo.git
\tbranch = develop
[submodule "bar"]
\tpath = code/bar
\turl = https://example.com/bar.git
"""


@pytest.fixture
def workbench(tmp_path, monkeypatch):
    root = tmp_path / "workbench"
    root.mkdir()
    (root / ".gitmodules").write_text(GITMODULES)
    code_dir = root / "code"
    code_dir.mkdir()
    foo = code_dir / "foo"
    foo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=foo, check=True)
    (code_dir / "bar").mkdir()
    monkeypatch.chdir(root)
    return root


def test_repo_root_found(workbench):
    assert common.repo_root() == workbench


def test_repo_root_found_from_subdir(workbench, monkeypatch):
    sub = workbench / "code" / "foo"
    monkeypatch.chdir(sub)
    assert common.repo_root() == workbench


def test_repo_root_raises_when_missing(tmp_path, monkeypatch):
    empty = tmp_path / "empty"
    empty.mkdir()
    monkeypatch.chdir(empty)
    # isolate the script-location fallback too, else it finds this real repo
    monkeypatch.setattr(common, "__file__", str(tmp_path / "fake_pkg" / "common.py"))
    with pytest.raises(common.RepoError):
        common.repo_root()


def test_repo_root_found_via_script_location_fallback(workbench, tmp_path, monkeypatch):
    unrelated = tmp_path / "unrelated"
    unrelated.mkdir()
    monkeypatch.chdir(unrelated)
    monkeypatch.setattr(common, "__file__", str(workbench / "tools" / "common.py"))
    assert common.repo_root() == workbench


def test_all_repos_from_gitmodules(workbench):
    assert common.all_repos() == ["foo", "bar"]


def test_all_repos_fallback_to_dirs(tmp_path, monkeypatch):
    root = tmp_path / "wb2"
    root.mkdir()
    (root / ".gitmodules").write_text("")
    code_dir = root / "code"
    code_dir.mkdir()
    (code_dir / "alpha").mkdir()
    (code_dir / "beta").mkdir()
    monkeypatch.chdir(root)
    assert common.all_repos() == ["alpha", "beta"]


def test_resolve_repo_ok(workbench):
    assert common.resolve_repo("foo") == workbench / "code" / "foo"


def test_resolve_repo_unknown_raises(workbench):
    with pytest.raises(common.RepoError):
        common.resolve_repo("nope")


def test_tracked_branch_explicit(workbench):
    assert common.tracked_branch("foo") == "develop"


def test_tracked_branch_default(workbench):
    assert common.tracked_branch("bar") == "main"


def test_worktree_path(workbench):
    expected = workbench / ".claude" / "worktrees" / "my-branch" / "foo"
    assert common.worktree_path("my-branch", "foo") == expected


def test_run_success(workbench):
    result = common.run(
        ["git", "rev-parse", "--is-inside-work-tree"], cwd=workbench / "code" / "foo"
    )
    assert result.returncode == 0
    assert result.stdout.strip() == "true"


def test_run_check_raises_on_failure(workbench):
    with pytest.raises(subprocess.CalledProcessError):
        common.run(
            [
                "git",
                "config",
                "-f",
                str(workbench / ".gitmodules"),
                "--get",
                "no.such.key",
            ]
        )


def test_run_check_false_no_raise(workbench):
    result = common.run(
        ["git", "config", "-f", str(workbench / ".gitmodules"), "--get", "no.such.key"],
        check=False,
    )
    assert result.returncode != 0


def test_gh_json_via_path_shim(workbench, tmp_path, monkeypatch):
    shim_dir = tmp_path / "bin"
    shim_dir.mkdir()
    gh_shim = shim_dir / "gh"
    gh_shim.write_text('#!/bin/sh\necho \'{"number": 42, "url": "https://example.com/pr/42"}\'\n')
    gh_shim.chmod(0o755)
    monkeypatch.setenv("PATH", f"{shim_dir}:{os.environ['PATH']}")
    data = common.gh_json(["pr", "view", "1", "--json", "number,url"])
    assert data == {"number": 42, "url": "https://example.com/pr/42"}


def test_report_render_and_exit_code_ok():
    report = common.Report()
    report.add("foo", "ok", "up to date")
    report.add("bar", "skipped", "no changes")
    assert "foo" in report.render()
    assert "bar" in report.render()
    assert report.exit_code == 0


def test_report_exit_code_failed():
    report = common.Report()
    report.add("foo", "ok", "up to date")
    report.add("bar", "failed", "non-fast-forward")
    assert report.exit_code == 1


def test_report_print_and_exit(capsys):
    report = common.Report()
    report.add("foo", "failed", "boom")
    with pytest.raises(SystemExit) as exc_info:
        report.print_and_exit()
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "foo" in captured.out
    assert "boom" in captured.out


def test_parse_repos_comma_string():
    assert common.parse_repos("foo, bar,baz") == ["foo", "bar", "baz"]


def test_parse_repos_list():
    assert common.parse_repos(["foo", "bar,baz", "foo"]) == ["foo", "bar", "baz"]


def test_parse_repos_dedupes_preserving_order():
    assert common.parse_repos("foo,bar,foo,baz,bar") == ["foo", "bar", "baz"]


# Shared with test_common.bats: text, max (None = default 60), expected slug.
SLUG_CASES = [
    ("Keycloak OIDC & PKCE!!", None, "keycloak-oidc-pkce"),
    ("  --Hello World--  ", None, "hello-world"),
    ("a   b\t\tc", None, "a-b-c"),
    ("one,two;three.four", None, "one-two-three-four"),
    ("MiXeD CaSe 42", None, "mixed-case-42"),
    ("Zażółć gęślą Jaźń", None, "za-g-l-ja"),
    ("!!!", None, ""),
    ("word " * 14, None, "word-" * 11 + "word"),
    ("abcdefg hij", 8, "abcdefg"),
    ("abcdefgh ij", 9, "abcdefgh"),
    ("Epic title that is rather long indeed", 28, "epic-title-that-is-rather-lo"),
    ("x" * 70, 28, "x" * 28),
]


@pytest.mark.parametrize("text,max_len,expected", SLUG_CASES)
def test_slugify_table(text, max_len, expected):
    got = common.slugify(text) if max_len is None else common.slugify(text, max_len)
    assert got == expected


@pytest.mark.parametrize("text,max_len,expected", SLUG_CASES)
def test_slugify_matches_shell(text, max_len, expected):
    lib = Path(__file__).resolve().parents[1] / "common.sh"
    args = ['"$1"'] if max_len is None else ['"$1"', '"$2"']
    cmd = f'source "{lib}"; slugify {" ".join(args)}'
    argv = ["bash", "-c", cmd, "_", text] + ([] if max_len is None else [str(max_len)])
    out = subprocess.run(argv, capture_output=True, text=True, check=True).stdout
    assert (
        out.rstrip("\n")
        == expected
        == (common.slugify(text) if max_len is None else common.slugify(text, max_len))
    )
