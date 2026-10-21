"""pullrequests-watch on GitLab: review discussions and new review notes, ported
from the retired GitLab watch tests with the same assertions, onto
scm.GitLab.discussions / unresolved_reviews / new_review_notes."""

import os
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_lib"))

import common  # noqa: E402
import scm  # noqa: E402
import watch  # noqa: E402


def _gl(repo="repo1", slug="acme/repo1"):
    return scm.GitLab(repo, "gitlab.com", slug)


def _install(shim_dir, name, text):
    shim_dir.mkdir(exist_ok=True)
    path = shim_dir / name
    path.write_text(text)
    path.chmod(0o755)
    return path


GLAB_SHIM = textwrap.dedent(
    """\
    #!/usr/bin/env python3
    import json
    import re
    import sys

    MRS = {
        "201": {
            "iid": 201,
            "state": "opened",
            "has_conflicts": False,
            "detailed_merge_status": "mergeable",
            "web_url": "https://gitlab.com/acme/repo1/-/merge_requests/201",
            "head_pipeline": {"id": 9001, "status": "success"},
        },
        "202": {
            "iid": 202,
            "state": "opened",
            "has_conflicts": False,
            "detailed_merge_status": "ci_still_running",
            "web_url": "https://gitlab.com/acme/repo1/-/merge_requests/202",
            "head_pipeline": {"id": 9002, "status": "failed"},
        },
    }

    JOBS = {"9002": [{"id": 1, "name": "ci/lint", "status": "failed"}]}

    LOGS = {"1": "\\n".join(f"log line {i}" for i in range(1, 151))}

    DISCUSSIONS = {
        "202": [
            {
                "id": "d1",
                "notes": [
                    {"id": 301, "system": True, "body": "changed the description"},
                    {
                        "id": 302,
                        "system": False,
                        "body": "Please fix this line",
                        "resolvable": True,
                        "resolved": False,
                        "author": {"username": "reviewbot"},
                    },
                ],
            },
            {
                "id": "d2",
                "notes": [
                    {
                        "id": 303,
                        "system": False,
                        "body": "LGTM now",
                        "resolvable": True,
                        "resolved": True,
                        "author": {"username": "reviewbot"},
                    }
                ],
            },
        ],
    }


    def main():
        argv = sys.argv[1:]
        if argv[0] != "api":
            sys.stderr.write(f"unhandled glab args: {argv}\\n")
            sys.exit(1)
        path = argv[1]

        m = re.match(r"^projects/(?P<enc>[^/]+)/merge_requests/(?P<iid>\\d+)$", path)
        if m:
            iid = m.group("iid")
            if iid not in MRS:
                sys.stderr.write("404 Project Not Found\\n")
                sys.exit(1)
            print(json.dumps(MRS[iid]))
            return

        m = re.match(
            r"^projects/(?P<enc>[^/]+)/merge_requests/(?P<iid>\\d+)/discussions"
            r"\\?per_page=100$",
            path,
        )
        if m:
            print(json.dumps(DISCUSSIONS.get(m.group("iid"), [])))
            return

        m = re.match(r"^projects/(?P<enc>[^/]+)/pipelines/(?P<pid>\\d+)/jobs$", path)
        if m:
            print(json.dumps(JOBS.get(m.group("pid"), [])))
            return

        m = re.match(r"^projects/(?P<enc>[^/]+)/jobs/(?P<jid>\\d+)/trace$", path)
        if m:
            sys.stdout.write(LOGS.get(m.group("jid"), ""))
            return

        sys.stderr.write(f"unhandled glab api path: {path}\\n")
        sys.exit(1)


    if __name__ == "__main__":
        main()
    """
)

GLAB_WATCH_SHIM = textwrap.dedent(
    """\
    #!/usr/bin/env python3
    import json
    import pathlib
    import re
    import sys

    COUNTER = pathlib.Path(__file__).with_name("calls.txt")
    LAST_TICK = pathlib.Path(__file__).with_name("last_tick.txt")

    def _tick():
        n = int(COUNTER.read_text()) if COUNTER.exists() else 0
        COUNTER.write_text(str(n + 1))
        LAST_TICK.write_text(str(n))
        return n

    def _peek_tick():
        return int(LAST_TICK.read_text()) if LAST_TICK.exists() else 0

    # 301: none -> pending -> passed (with a review from tick 1) ;
    # 303: never launches (always none) ; 304: always pending (timeout)
    def pipeline_for(iid, tick):
        if iid == "301":
            if tick == 0:
                return None
            if tick == 1:
                return {"id": 1, "status": "running"}
            return {"id": 1, "status": "success"}
        if iid == "303":
            return None
        if iid == "304":
            return {"id": 4, "status": "running"}
        return None

    def discussions_for(iid, tick):
        if iid == "301" and tick >= 1:
            return [
                {
                    "id": "d-review",
                    "notes": [
                        {
                            "id": 9101,
                            "body": "Please add a test for this branch",
                            "system": False,
                            "resolvable": True,
                            "resolved": False,
                            "author": {"username": "reviewbot"},
                        },
                        {
                            "id": 9102,
                            "body": "changed the description",
                            "system": True,
                            "resolvable": False,
                            "resolved": False,
                        },
                    ],
                }
            ]
        return []

    def main():
        argv = sys.argv[1:]
        if argv[0] != "api":
            sys.stderr.write(f"unhandled glab args: {argv}\\n")
            sys.exit(1)
        path = argv[1]

        m = re.match(r"^projects/(?P<enc>[^/]+)/merge_requests/(?P<iid>\\d+)$", path)
        if m:
            iid = m.group("iid")
            tick = _tick()
            print(json.dumps({
                "iid": int(iid),
                "state": "opened",
                "has_conflicts": False,
                "detailed_merge_status": "mergeable",
                "web_url": f"https://gitlab.com/acme/repo1/-/merge_requests/{iid}",
                "head_pipeline": pipeline_for(iid, tick),
            }))
            return

        m = re.match(
            r"^projects/(?P<enc>[^/]+)/merge_requests/(?P<iid>\\d+)/discussions"
            r"\\?per_page=100$",
            path,
        )
        if m:
            print(json.dumps(discussions_for(m.group("iid"), _peek_tick())))
            return

        sys.stderr.write(f"unhandled glab api path: {path}\\n")
        sys.exit(1)

    if __name__ == "__main__":
        main()
    """
)


@pytest.fixture(autouse=True)
def _no_host_map(monkeypatch):
    monkeypatch.delenv(scm.HOSTS_ENV, raising=False)


@pytest.fixture
def glab_shim(tmp_path, monkeypatch):
    glab_path = _install(tmp_path / "bin", "glab", GLAB_SHIM)
    monkeypatch.setenv("PATH", f"{glab_path.parent}:{os.environ['PATH']}")
    return glab_path


@pytest.fixture
def glab_watch_shim(tmp_path, monkeypatch):
    glab_path = _install(tmp_path / "wbin", "glab", GLAB_WATCH_SHIM)
    monkeypatch.setenv("PATH", f"{glab_path.parent}:{os.environ['PATH']}")
    return glab_path


@pytest.fixture
def fake_clock(monkeypatch):
    state = {"t": 0.0}
    monkeypatch.setattr(watch, "_now", lambda: state["t"])
    monkeypatch.setattr(watch, "_sleep", lambda s: state.__setitem__("t", state["t"] + s))
    return state


@pytest.fixture
def workbench(tmp_path, monkeypatch):
    root = tmp_path / "workbench"
    repo = root / "code" / "repo1"
    repo.mkdir(parents=True)
    for cmd in (
        ["git", "init", "-q", "-b", "main"],
        ["git", "remote", "add", "origin", "git@gitlab.com:acme/repo1.git"],
    ):
        subprocess.run(cmd, cwd=repo, check=True, capture_output=True)
    (root / ".gitmodules").write_text(
        '[submodule "repo1"]\n\tpath = code/repo1\n\turl = git@gitlab.com:acme/repo1.git\n'
    )
    monkeypatch.chdir(root)
    return root


# -- review-comment helpers --


def test_count_unresolved_reviews_counts_discussions_with_unresolved_notes():
    discussions = [
        {"notes": [{"resolvable": True, "resolved": False}]},
        {"notes": [{"resolvable": True, "resolved": True}]},
        {"notes": [{"resolvable": False, "resolved": False}]},
    ]
    assert scm.GitLab.count_unresolved(discussions) == 1


def test_count_unresolved_reviews_counts_one_per_discussion_not_per_note():
    discussions = [
        {
            "notes": [
                {"resolvable": True, "resolved": False},
                {"resolvable": True, "resolved": False},
            ]
        }
    ]
    assert scm.GitLab.count_unresolved(discussions) == 1


def test_count_unresolved_reviews_empty_is_zero():
    assert scm.GitLab.count_unresolved([]) == 0


def test_count_unresolved_reviews_ignores_system_notes():
    # A system note must never count as review feedback, even if GitLab were to
    # mark it resolvable/unresolved.
    discussions = [{"notes": [{"id": 1, "system": True, "resolvable": True, "resolved": False}]}]
    assert scm.GitLab.count_unresolved(discussions) == 0


def test_unresolved_reviews_fetches_the_mr_discussions(glab_shim):
    assert _gl().unresolved_reviews(202) == 1
    assert _gl().unresolved_reviews(201) == 0


def test_discussions_degrades_to_empty_on_api_error(monkeypatch):
    # Reviews are informational: a failing discussions endpoint must not sink an
    # otherwise-valid poll.
    adapter = _gl()

    def boom(_args):
        raise common.RepoError("404 Not Found")

    monkeypatch.setattr(adapter, "json", boom)
    assert adapter.discussions(201) == []


def test_poll_survives_discussions_failure(glab_shim, monkeypatch):
    # MR endpoint OK + discussions endpoint failing => still report CI/mergeability
    # rather than sinking the whole target as failed.
    adapter = _gl()
    real_json = adapter.json

    def flaky(args):
        if "discussions" in args[-1]:
            raise common.RepoError("500 Internal Server Error")
        return real_json(args)

    monkeypatch.setattr(adapter, "json", flaky)
    poll = adapter.poll(201)
    assert poll["checks"] == "passed"
    assert poll["mergeable"] == "mergeable"
    assert poll["reviews"] == 0
    assert poll["discussions"] == []


def test_poll_includes_discussions_and_reviews_count(glab_shim):
    poll = _gl().poll(202)
    assert poll["reviews"] == 1
    assert len(poll["discussions"]) == 2


def test_new_review_notes_skips_system_notes(glab_shim):
    seen = set()
    new = _gl().new_review_notes(202, seen)
    assert [n["id"] for n in new] == [302, 303]
    assert seen == {302, 303}


def test_new_review_notes_skips_system_notes_in_given_discussions():
    discussions = [
        {"notes": [{"id": 1, "system": True, "body": "changed the description"}]},
        {"notes": [{"id": 2, "system": False, "body": "please fix"}]},
    ]
    seen = set()
    new = _gl().new_review_notes(1, seen, discussions)
    assert [n["id"] for n in new] == [2]
    assert seen == {2}


def test_new_review_notes_does_not_repeat_seen_ids():
    discussions = [{"notes": [{"id": 2, "system": False, "body": "please fix"}]}]
    seen = {2}
    assert _gl().new_review_notes(1, seen, discussions) == []


def test_new_review_notes_empty_discussions_is_empty():
    assert _gl().new_review_notes(1, set(), []) == []


def test_format_new_note_includes_repo_iid_author_body():
    note = {"author": {"username": "reviewbot"}, "body": "Please fix this line"}
    line = _gl().format_new_note(202, note)
    assert line.startswith("[repo1 !202] new review comment from reviewbot: ")
    assert "Please fix this line" in line


def test_format_new_note_truncates_long_body():
    note = {"author": {"username": "reviewbot"}, "body": "x" * 300}
    line = _gl().format_new_note(202, note)
    assert "..." in line
    assert len(line) < 300 + 50


def test_format_new_note_missing_author_defaults_to_unknown():
    assert "unknown" in _gl().format_new_note(202, {"body": "hi"})


# -- build_detail --


def test_gitlab_detail_has_reviews_count(glab_shim):
    adapter = _gl()
    ok, detail = watch.build_detail(adapter, 202, adapter.poll(202))
    assert "mergeable=blocked reviews=1 unresolved url=" in detail
    assert "1 unresolved review discussion" in detail
    assert "1 unresolved review discussions" not in detail


def test_gitlab_review_reason_plural(glab_shim):
    adapter = _gl()
    poll = adapter.poll(201)
    poll["reviews"] = 2
    ok, detail = watch.build_detail(adapter, 201, poll)
    assert "2 unresolved review discussions" in detail
    poll["reviews"] = 1
    ok, detail = watch.build_detail(adapter, 201, poll)
    assert "1 unresolved review discussion" in detail
    assert "1 unresolved review discussions" not in detail


def test_gitlab_reviews_do_not_flip_ok(glab_shim):
    adapter = _gl()
    poll = adapter.poll(201)
    poll["reviews"] = 3
    ok, detail = watch.build_detail(adapter, 201, poll)
    assert ok is True
    assert "reviews=3 unresolved" in detail
    assert "3 unresolved review discussions" in detail


def test_build_detail_zero_reviews_has_no_reason(glab_shim):
    adapter = _gl()
    ok, detail = watch.build_detail(adapter, 201, adapter.poll(201))
    assert "reviews=0 unresolved" in detail
    assert "unresolved review discussion" not in detail


def test_main_no_wait_snapshot_carries_reviews(workbench, glab_shim, capsys):
    with pytest.raises(SystemExit):
        watch.main(["--no-wait", "--prs", "repo1#202"])
    assert "reviews=1 unresolved" in capsys.readouterr().out


# -- watch loop --


def test_gitlab_new_notes_streamed_once(fake_clock, glab_watch_shim, capsys):
    report = common.Report()
    watch.watch_targets([("repo1", _gl(), 301)], report, interval=10, timeout=1200, grace=30)
    captured = capsys.readouterr()
    assert captured.out.count("Please add a test for this branch") == 1
    assert "[repo1 !301] new review comment from reviewbot" in captured.out
    assert "changed the description" not in captured.out
    rendered = report.render()
    assert "reviews=1 unresolved" in rendered
    assert "1 unresolved review discussion" in rendered


def test_watch_zero_reviews_when_no_discussions(fake_clock, glab_watch_shim, capsys):
    report = common.Report()
    watch.watch_targets([("repo1", _gl(), 303)], report, interval=10, timeout=1200, grace=30)
    captured = capsys.readouterr()
    assert "new review comment" not in captured.out
    assert "reviews=0 unresolved" in report.render()


def test_watch_timeout_keeps_reviews(fake_clock, glab_watch_shim):
    report = common.Report()
    watch.watch_targets([("repo1", _gl(), 304)], report, interval=10, timeout=40, grace=30)
    rendered = report.render()
    assert "timed out after" in rendered
    assert "reviews=0 unresolved" in rendered
    assert report.exit_code == 1
