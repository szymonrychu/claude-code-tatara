import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
LIB_DIR = Path(__file__).resolve().parents[2] / "_lib"
sys.path.insert(0, str(SCRIPTS_DIR))
sys.path.insert(0, str(LIB_DIR))

import scm  # noqa: E402
import update  # noqa: E402

GH_SHIM = """#!/usr/bin/env python3
import json
import os
import sys

argv = sys.argv[1:]
with open(os.environ["GH_STUB_LOG"], "a") as f:
    f.write(json.dumps(argv) + "\\n")


def flag(name):
    if name in argv:
        return argv[argv.index(name) + 1]
    return None


if argv[:2] == ["pr", "list"]:
    existing = json.loads(os.environ.get("GH_STUB_EXISTING", "{}"))
    entry = existing.get(flag("-R"))
    print(json.dumps([entry] if entry else []))
elif argv[:2] == ["pr", "create"]:
    urls = json.loads(os.environ.get("GH_STUB_CREATE_URLS", "{}"))
    print(urls[flag("-R")])
elif argv[:2] == ["pr", "edit"]:
    pass
elif argv[:2] == ["pr", "view"]:
    labels = json.loads(os.environ.get("GH_STUB_LABELS", "{}"))
    target = argv[2] if len(argv) > 2 else None
    names = labels.get(target, [])
    print(json.dumps({"labels": [{"name": n} for n in names]}))
elif argv[:2] == ["label", "create"]:
    pass
else:
    sys.exit(1)
"""


def _init_repo(path, origin_url):
    path.mkdir(parents=True)
    subprocess.run(["git", "init", "-q"], cwd=path, check=True)
    subprocess.run(["git", "remote", "add", "origin", origin_url], cwd=path, check=True)


@pytest.fixture
def workbench(tmp_path, monkeypatch):
    root = tmp_path / "workbench"
    root.mkdir()
    (root / ".gitmodules").write_text(
        '[submodule "repo-ssh"]\n'
        "\tpath = code/repo-ssh\n"
        "\turl = git@github.com:acme/repo-ssh.git\n"
        "\tbranch = main\n"
        '[submodule "repo-https"]\n'
        "\tpath = code/repo-https\n"
        "\turl = https://github.com/acme/repo-https.git\n"
        "\tbranch = main\n"
    )
    code_dir = root / "code"
    code_dir.mkdir()
    _init_repo(code_dir / "repo-ssh", "git@github.com:acme/repo-ssh.git")
    _init_repo(code_dir / "repo-https", "https://github.com/acme/repo-https.git")
    monkeypatch.chdir(root)
    return root


@pytest.fixture
def gh_stub(tmp_path, monkeypatch):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    gh_path = bin_dir / "gh"
    gh_path.write_text(GH_SHIM)
    gh_path.chmod(0o755)

    log_path = tmp_path / "gh_calls.log"
    monkeypatch.setenv("GH_STUB_LOG", str(log_path))
    monkeypatch.setenv("PATH", f"{bin_dir}:{__import__('os').environ['PATH']}")

    def read_calls():
        if not log_path.exists():
            return []
        return [json.loads(line) for line in log_path.read_text().splitlines() if line]

    return read_calls


def test_repo_slug_parses_ssh_url():
    assert scm.slug_from_url("git@github.com:acme/repo-ssh.git") == "acme/repo-ssh"


def test_repo_slug_parses_https_url():
    assert scm.slug_from_url("https://github.com/acme/repo-https.git") == "acme/repo-https"


def test_repo_slug_parses_https_url_without_git_suffix():
    assert scm.slug_from_url("https://github.com/acme/repo-https") == "acme/repo-https"


def test_create_and_edit_branching(workbench, gh_stub, monkeypatch, capsys):
    monkeypatch.setenv(
        "GH_STUB_EXISTING",
        json.dumps(
            {
                "acme/repo-https": {
                    "number": 7,
                    "url": "https://github.com/acme/repo-https/pull/7",
                },
            }
        ),
    )
    monkeypatch.setenv(
        "GH_STUB_CREATE_URLS",
        json.dumps(
            {
                "acme/repo-ssh": "https://github.com/acme/repo-ssh/pull/99",
            }
        ),
    )

    with pytest.raises(SystemExit) as exc:
        update.main(
            [
                "--branch",
                "feature/x",
                "--repos",
                "repo-ssh,repo-https",
                "--body",
                "repo-ssh=Add feature X\n\nDetails here.",
                "--body",
                "repo-https=Add feature X support\n\nMore details.",
            ]
        )

    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "repo-ssh" in out
    assert "created" in out
    assert "https://github.com/acme/repo-ssh/pull/99" in out
    assert "repo-https" in out
    assert "updated" in out
    assert "https://github.com/acme/repo-https/pull/7" in out

    calls = gh_stub()
    create_calls = [c for c in calls if c[:2] == ["pr", "create"]]
    assert len(create_calls) == 1
    assert "-R" in create_calls[0]
    assert create_calls[0][create_calls[0].index("-R") + 1] == "acme/repo-ssh"
    assert "--title" in create_calls[0]
    assert create_calls[0][create_calls[0].index("--title") + 1] == "Add feature X"

    list_calls = [c for c in calls if c[:2] == ["pr", "list"]]
    assert len(list_calls) == 2


def test_pass_two_cross_links_siblings_and_omits_self(workbench, gh_stub, monkeypatch):
    monkeypatch.setenv("GH_STUB_EXISTING", json.dumps({}))
    monkeypatch.setenv(
        "GH_STUB_CREATE_URLS",
        json.dumps(
            {
                "acme/repo-ssh": "https://github.com/acme/repo-ssh/pull/1",
                "acme/repo-https": "https://github.com/acme/repo-https/pull/2",
            }
        ),
    )

    with pytest.raises(SystemExit) as exc:
        update.main(
            [
                "--branch",
                "feature/y",
                "--repos",
                "repo-ssh,repo-https",
                "--body",
                "repo-ssh=Body for ssh repo",
                "--body",
                "repo-https=Body for https repo",
            ]
        )
    assert exc.value.code == 0

    calls = gh_stub()
    edit_calls = [c for c in calls if c[:2] == ["pr", "edit"]]
    # pass 2 issues one edit per repo (pass 1 only edits pre-existing PRs; both here are new)
    assert len(edit_calls) == 2

    def body_for(url):
        for c in edit_calls:
            if c[2] == url.rsplit("/", 1)[1]:
                return c[c.index("--body") + 1]
        raise AssertionError(f"no edit call for {url}")

    ssh_body = body_for("https://github.com/acme/repo-ssh/pull/1")
    https_body = body_for("https://github.com/acme/repo-https/pull/2")

    assert "Complementary PRs" in ssh_body
    assert "https://github.com/acme/repo-https/pull/2" in ssh_body
    assert "https://github.com/acme/repo-ssh/pull/1" not in ssh_body

    assert "Complementary PRs" in https_body
    assert "https://github.com/acme/repo-ssh/pull/1" in https_body
    assert "https://github.com/acme/repo-https/pull/2" not in https_body


def test_aggregate_report_and_exit_code_with_unknown_repo(workbench, gh_stub, monkeypatch, capsys):
    monkeypatch.setenv("GH_STUB_EXISTING", json.dumps({}))
    monkeypatch.setenv(
        "GH_STUB_CREATE_URLS",
        json.dumps(
            {
                "acme/repo-ssh": "https://github.com/acme/repo-ssh/pull/5",
            }
        ),
    )

    with pytest.raises(SystemExit) as exc:
        update.main(
            [
                "--branch",
                "feature/z",
                "--repos",
                "repo-ssh,nope",
                "--body",
                "repo-ssh=Body for ssh repo",
                "--body",
                "nope=Body for missing repo",
            ]
        )

    assert exc.value.code == 1
    out = capsys.readouterr().out
    assert "repo-ssh" in out
    assert "created" in out
    assert "nope" in out
    assert "failed" in out

    calls = gh_stub()
    assert not any(c[:2] == ["pr", "list"] and "nope" in json.dumps(c) for c in calls)


def test_missing_body_is_reported_as_failure(workbench, gh_stub, monkeypatch, capsys):
    monkeypatch.setenv("GH_STUB_EXISTING", json.dumps({}))
    monkeypatch.setenv("GH_STUB_CREATE_URLS", json.dumps({}))

    with pytest.raises(SystemExit) as exc:
        update.main(
            [
                "--branch",
                "feature/w",
                "--repos",
                "repo-ssh",
            ]
        )

    assert exc.value.code == 1
    out = capsys.readouterr().out
    assert "repo-ssh" in out
    assert "failed" in out


def test_semver_applies_when_absent(workbench, gh_stub, monkeypatch, capsys):
    monkeypatch.setenv("GH_STUB_EXISTING", json.dumps({}))
    monkeypatch.setenv(
        "GH_STUB_CREATE_URLS",
        json.dumps({"acme/repo-ssh": "https://github.com/acme/repo-ssh/pull/10"}),
    )
    monkeypatch.setenv("GH_STUB_LABELS", json.dumps({}))

    with pytest.raises(SystemExit) as exc:
        update.main(
            [
                "--branch",
                "feature/semver",
                "--repos",
                "repo-ssh",
                "--body",
                "repo-ssh=Add feature",
                "--semver",
                "repo-ssh=patch",
            ]
        )
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "semver:patch applied" in out

    calls = gh_stub()
    label_create = [c for c in calls if c[:2] == ["label", "create"]]
    assert len(label_create) == 1
    assert label_create[0][2] == "semver:patch"

    add_label_calls = [c for c in calls if c[:2] == ["pr", "edit"] and "--add-label" in c]
    assert len(add_label_calls) == 1
    assert add_label_calls[0][add_label_calls[0].index("--add-label") + 1] == "semver:patch"


def test_semver_skipped_when_already_present(workbench, gh_stub, monkeypatch, capsys):
    monkeypatch.setenv("GH_STUB_EXISTING", json.dumps({}))
    monkeypatch.setenv(
        "GH_STUB_CREATE_URLS",
        json.dumps({"acme/repo-ssh": "https://github.com/acme/repo-ssh/pull/11"}),
    )
    monkeypatch.setenv(
        "GH_STUB_LABELS",
        json.dumps({"11": ["semver:major"]}),
    )

    with pytest.raises(SystemExit) as exc:
        update.main(
            [
                "--branch",
                "feature/semver",
                "--repos",
                "repo-ssh",
                "--body",
                "repo-ssh=Add feature",
                "--semver",
                "repo-ssh=patch",
            ]
        )
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "semver skipped (has semver:major)" in out

    calls = gh_stub()
    assert not any(c[:2] == ["label", "create"] for c in calls)
    assert not any(c[:2] == ["pr", "edit"] and "--add-label" in c for c in calls)


def test_semver_invalid_level_is_per_repo_failure(workbench, gh_stub, monkeypatch, capsys):
    monkeypatch.setenv("GH_STUB_EXISTING", json.dumps({}))
    monkeypatch.setenv(
        "GH_STUB_CREATE_URLS",
        json.dumps({"acme/repo-ssh": "https://github.com/acme/repo-ssh/pull/12"}),
    )
    monkeypatch.setenv("GH_STUB_LABELS", json.dumps({}))

    with pytest.raises(SystemExit) as exc:
        update.main(
            [
                "--branch",
                "feature/semver",
                "--repos",
                "repo-ssh",
                "--body",
                "repo-ssh=Add feature",
                "--semver",
                "repo-ssh=bogus",
            ]
        )
    assert exc.value.code == 1
    out = capsys.readouterr().out
    assert "semver failed (invalid level: bogus)" in out
    # the PR itself still succeeded despite the semver failure
    assert "created" in out
    assert "https://github.com/acme/repo-ssh/pull/12" in out

    calls = gh_stub()
    assert not any(c[:2] == ["label", "create"] for c in calls)
    assert not any(c[:2] == ["pr", "view"] for c in calls)


def test_semver_missing_is_noop(workbench, gh_stub, monkeypatch, capsys):
    monkeypatch.setenv("GH_STUB_EXISTING", json.dumps({}))
    monkeypatch.setenv(
        "GH_STUB_CREATE_URLS",
        json.dumps({"acme/repo-ssh": "https://github.com/acme/repo-ssh/pull/13"}),
    )

    with pytest.raises(SystemExit) as exc:
        update.main(
            [
                "--branch",
                "feature/semver",
                "--repos",
                "repo-ssh",
                "--body",
                "repo-ssh=Add feature",
            ]
        )
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "| -" in out

    calls = gh_stub()
    assert not any(c[:2] == ["pr", "view"] for c in calls)
    assert not any(c[:2] == ["label", "create"] for c in calls)


def test_semver_creates_label_if_missing(workbench, gh_stub, monkeypatch):
    monkeypatch.setenv("GH_STUB_EXISTING", json.dumps({}))
    monkeypatch.setenv(
        "GH_STUB_CREATE_URLS",
        json.dumps({"acme/repo-ssh": "https://github.com/acme/repo-ssh/pull/14"}),
    )
    monkeypatch.setenv("GH_STUB_LABELS", json.dumps({}))

    with pytest.raises(SystemExit) as exc:
        update.main(
            [
                "--branch",
                "feature/semver",
                "--repos",
                "repo-ssh",
                "--body",
                "repo-ssh=Add feature",
                "--semver",
                "repo-ssh=major",
            ]
        )
    assert exc.value.code == 0

    calls = gh_stub()
    label_create = [c for c in calls if c[:2] == ["label", "create"]]
    assert len(label_create) == 1
    call = label_create[0]
    assert call[2] == "semver:major"
    assert "-R" in call
    assert call[call.index("-R") + 1] == "acme/repo-ssh"
    assert "--force" in call
    assert "--color" in call


def test_semver_failure_does_not_abort_other_repos(workbench, gh_stub, monkeypatch, capsys):
    monkeypatch.setenv("GH_STUB_EXISTING", json.dumps({}))
    monkeypatch.setenv(
        "GH_STUB_CREATE_URLS",
        json.dumps(
            {
                "acme/repo-ssh": "https://github.com/acme/repo-ssh/pull/20",
                "acme/repo-https": "https://github.com/acme/repo-https/pull/21",
            }
        ),
    )
    monkeypatch.setenv("GH_STUB_LABELS", json.dumps({}))

    with pytest.raises(SystemExit) as exc:
        update.main(
            [
                "--branch",
                "feature/semver",
                "--repos",
                "repo-ssh,repo-https",
                "--body",
                "repo-ssh=Body ssh",
                "--body",
                "repo-https=Body https",
                "--semver",
                "repo-ssh=bogus",
                "--semver",
                "repo-https=minor",
            ]
        )
    assert exc.value.code == 1
    out = capsys.readouterr().out
    assert "semver failed (invalid level: bogus)" in out
    assert "semver:minor applied" in out

    calls = gh_stub()
    label_create = [c for c in calls if c[:2] == ["label", "create"]]
    assert len(label_create) == 1
    assert label_create[0][2] == "semver:minor"


def test_mixed_hosts_one_run(mixed_workbench, mixed_stubs, run_mixed, capsys):
    code = run_mixed(
        "--branch",
        "feature/m",
        "--repos",
        "gh-repo,gl-repo",
        "--body",
        "gh-repo=GH body",
        "--body",
        "gl-repo=GL body",
        "--semver",
        "gh-repo=minor",
        "--semver",
        "gl-repo=patch",
    )
    assert code == 0
    out = capsys.readouterr().out
    assert "https://github.com/acme/gh-repo/pull/5 | semver:minor applied" in out
    assert "https://gitlab.com/acme/gl-repo/-/merge_requests/8 | semver:patch applied" in out

    calls = mixed_stubs()
    gh_edit = [c for c in calls if c[:3] == ["gh", "pr", "edit"] and "--body" in c]
    gl_put = [
        c
        for c in calls
        if c[0] == "glab" and "PUT" in c and any(a.startswith("description=") for a in c)
    ]
    gh_body = gh_edit[0][gh_edit[0].index("--body") + 1]
    gl_body = [a for a in gl_put[0] if a.startswith("description=")][0]
    assert "## Complementary PRs" in gh_body
    assert "https://gitlab.com/acme/gl-repo/-/merge_requests/8" in gh_body
    assert "## Complementary MRs" in gl_body
    assert "https://github.com/acme/gh-repo/pull/5" in gl_body
