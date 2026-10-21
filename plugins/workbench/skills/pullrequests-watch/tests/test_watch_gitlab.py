"""pullrequests-watch on GitLab: the retired GitLab watch tests that are
not about review discussions, new review notes, --deploy or --sha, ported onto
the host-agnostic watch over scm.GitLab, plus the local-only repo."""

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


def _run(cmd, cwd):
    subprocess.run(cmd, cwd=cwd, check=True, capture_output=True, text=True)


def _gl(repo="repo1", slug="acme/repo1"):
    return scm.GitLab(repo, "gitlab.com", slug)


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
        "203": {
            "iid": 203,
            "state": "opened",
            "has_conflicts": True,
            "detailed_merge_status": "conflict",
            "web_url": "https://gitlab.com/acme/repo1/-/merge_requests/203",
            "head_pipeline": None,
        },
        "204": {
            "iid": 204,
            "state": "merged",
            "has_conflicts": False,
            "detailed_merge_status": "mergeable",
            "web_url": "https://gitlab.com/acme/repo1/-/merge_requests/204",
            "head_pipeline": {"id": 9004, "status": "success"},
        },
        "205": {
            "iid": 205,
            "state": "closed",
            "has_conflicts": False,
            "detailed_merge_status": "unchecked",
            "web_url": "https://gitlab.com/acme/repo1/-/merge_requests/205",
            "head_pipeline": None,
        },
    }

    JOBS = {"9002": [{"id": 1, "name": "ci/lint", "status": "failed"}]}

    LOGS = {"1": "\\n".join(f"log line {i}" for i in range(1, 151))}


    def main():
        argv = sys.argv[1:]
        if argv[0] != "api":
            sys.stderr.write(f"unhandled glab args: {argv}\\n")
            sys.exit(1)
        path = argv[1]

        m = re.match(
            r"^projects/(?P<enc>[^/]+)/merge_requests\\?source_branch=(?P<branch>[^&]+)&state=opened$",
            path,
        )
        if m:
            branch = m.group("branch")
            if branch == "feature-x":
                print(json.dumps([MRS["201"]]))
            else:
                print(json.dumps([]))
            return

        m = re.match(r"^projects/(?P<enc>[^/]+)/merge_requests/(?P<iid>\\d+)$", path)
        if m:
            iid = m.group("iid")
            if iid not in MRS:
                sys.stderr.write("404 Project Not Found\\n")
                sys.exit(1)
            print(json.dumps(MRS[iid]))
            return

        m = re.match(r"^projects/(?P<enc>[^/]+)/pipelines/(?P<pid>\\d+)/jobs$", path)
        if m:
            pid = m.group("pid")
            print(json.dumps(JOBS.get(pid, [])))
            return

        m = re.match(r"^projects/(?P<enc>[^/]+)/jobs/(?P<jid>\\d+)/trace$", path)
        if m:
            jid = m.group("jid")
            sys.stdout.write(LOGS.get(jid, ""))
            return

        sys.stderr.write(f"unhandled glab api path: {path}\\n")
        sys.exit(1)


    if __name__ == "__main__":
        main()
    """
)


def _install(shim_dir, name, text):
    shim_dir.mkdir(exist_ok=True)
    path = shim_dir / name
    path.write_text(text)
    path.chmod(0o755)
    return path


@pytest.fixture(autouse=True)
def _no_host_map(monkeypatch):
    monkeypatch.delenv(scm.HOSTS_ENV, raising=False)


@pytest.fixture
def glab_shim(tmp_path, monkeypatch):
    glab_path = _install(tmp_path / "bin", "glab", GLAB_SHIM)
    monkeypatch.setenv("PATH", f"{glab_path.parent}:{os.environ['PATH']}")
    return glab_path


def _init_submodule(code_dir, name, origin_url):
    repo = code_dir / name
    repo.mkdir(parents=True)
    _run(["git", "init", "-q", "-b", "main"], repo)
    if origin_url:
        _run(["git", "remote", "add", "origin", origin_url], repo)
    return repo


def _make_workbench(root, repos):
    code_dir = root / "code"
    code_dir.mkdir(parents=True)
    gitmodules = ""
    for name, url in repos.items():
        _init_submodule(code_dir, name, url)
        gitmodules += f'[submodule "{name}"]\n\tpath = code/{name}\n\turl = {url or "./" + name}\n'
    (root / ".gitmodules").write_text(gitmodules)
    return root


@pytest.fixture
def workbench(tmp_path, monkeypatch):
    root = _make_workbench(
        tmp_path / "workbench",
        {
            "repo1": "git@gitlab.com:acme/repo1.git",
            "repo2": "https://gitlab.com/acme/group/repo2.git",
        },
    )
    monkeypatch.chdir(root)
    return root


# -- group/repo url parsing --


@pytest.mark.parametrize(
    "url,expected",
    [
        ("https://gitlab.com/acme/repo1.git", "acme/repo1"),
        ("https://gitlab.com/acme/repo1", "acme/repo1"),
        ("git@gitlab.com:acme/repo1.git", "acme/repo1"),
        ("git@gitlab.com:acme/repo1", "acme/repo1"),
        ("ssh://git@gitlab.com/acme/repo1.git", "acme/repo1"),
        ("https://gitlab.com/acme/repo1.git/", "acme/repo1"),
        ("https://gitlab.com/acme/group/repo2.git", "acme/group/repo2"),
        ("git@gitlab.com:acme/group/sub/repo2.git", "acme/group/sub/repo2"),
    ],
)
def test_owner_repo_from_url(url, expected):
    assert scm.slug_from_url(url) == expected


def test_owner_repo_from_url_garbage_raises():
    with pytest.raises(common.RepoError):
        scm.slug_from_url("not-a-url")


def test_repo_slug_reads_origin(workbench):
    assert scm.adapter_for("repo1").slug == "acme/repo1"
    assert scm.adapter_for("repo2").slug == "acme/group/repo2"


def test_repo_slug_unknown_repo_raises(workbench):
    with pytest.raises(common.RepoError):
        scm.adapter_for("nope")


# -- --prs parsing --


def test_parse_mr_pairs():
    assert watch.parse_pr_pairs("repo1#123,repo2#45") == [
        ("repo1", 123),
        ("repo2", 45),
    ]


def test_parse_mr_pairs_invalid_entry_raises():
    with pytest.raises(common.RepoError):
        watch.parse_pr_pairs("repo1-123")


# -- checks reduction --


def test_reduce_checks_none():
    assert scm.GitLab.reduce_checks(None) == "none"
    assert scm.GitLab.reduce_checks({}) == "none"


def test_reduce_checks_passed():
    assert scm.GitLab.reduce_checks({"status": "success"}) == "passed"
    assert scm.GitLab.reduce_checks({"status": "skipped"}) == "passed"


def test_reduce_checks_pending():
    assert scm.GitLab.reduce_checks({"status": "running"}) == "pending"
    assert scm.GitLab.reduce_checks({"status": "manual"}) == "pending"


def test_reduce_checks_failed():
    assert scm.GitLab.reduce_checks({"status": "failed"}) == "failed"
    assert scm.GitLab.reduce_checks({"status": "canceled"}) == "failed"


# -- end to end scenarios via process_pr / process_branch --


def test_open_checks_passed_mergeable(workbench, glab_shim):
    report = common.Report()
    watch.process_pr("repo1", 201, report)
    rendered = report.render()
    assert "ok" in rendered
    assert "mr !201:" in rendered
    assert "state=OPEN" in rendered
    assert "checks=passed" in rendered
    assert "mergeable=mergeable" in rendered
    assert report.exit_code == 0


def test_open_checks_failed_reports_job_name_and_log_tail(workbench, glab_shim):
    report = common.Report()
    watch.process_pr("repo1", 202, report)
    rendered = report.render()
    assert "failed" in rendered
    assert "checks=failed" in rendered
    assert "ci/lint" in rendered
    assert "log line 150" in rendered
    assert "log line 1\n" not in rendered
    lines_in_detail = rendered.count("log line ")
    assert lines_in_detail <= 100
    assert "not mergeable (detailed_merge_status=ci_still_running)" in rendered
    assert report.exit_code == 1


def test_merge_conflict_reports_conflict_without_file_list(workbench, glab_shim):
    report = common.Report()
    watch.process_pr("repo1", 203, report)
    rendered = report.render()
    assert "failed" in rendered
    assert "merge conflict" in rendered
    assert "detailed_merge_status=conflict" in rendered
    assert "merge conflict in:" not in rendered
    assert report.exit_code == 1


def test_merged_mr_is_ok(workbench, glab_shim):
    report = common.Report()
    watch.process_pr("repo1", 204, report)
    rendered = report.render()
    assert "ok" in rendered
    assert "state=MERGED" in rendered
    assert report.exit_code == 0


def test_closed_mr_is_ok(workbench, glab_shim):
    report = common.Report()
    watch.process_pr("repo1", 205, report)
    rendered = report.render()
    assert "ok" in rendered
    assert "state=CLOSED" in rendered
    assert report.exit_code == 0


def test_unreachable_mr_is_failed(workbench, glab_shim):
    report = common.Report()
    watch.process_pr("repo1", 999, report)
    rendered = report.render()
    assert "failed" in rendered
    assert "mr !999:" in rendered
    assert report.exit_code == 1


def test_process_pr_unknown_repo_is_failed(workbench, glab_shim):
    report = common.Report()
    watch.process_pr("nope", 201, report)
    rendered = report.render()
    assert "failed" in rendered
    assert "nope" in rendered
    assert report.exit_code == 1


def test_process_branch_resolves_mr_for_branch(workbench, glab_shim):
    report = common.Report()
    watch.process_branch("repo1", "feature-x", report)
    rendered = report.render()
    assert "ok" in rendered
    assert "mr !201:" in rendered
    assert "state=OPEN" in rendered
    assert "checks=passed" in rendered


def test_process_branch_no_mr_for_branch_is_failed(workbench, glab_shim):
    report = common.Report()
    watch.process_branch("repo1", "no-such-branch", report)
    rendered = report.render()
    assert "failed" in rendered
    assert "no MR found" in rendered


# -- main() CLI wiring --


def test_main_prs_mode_exit_code(workbench, glab_shim, capsys):
    with pytest.raises(SystemExit) as exc_info:
        watch.main(["--prs", "repo1#201,repo1#202"])
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "repo1" in captured.out
    assert "checks=passed" in captured.out
    assert "checks=failed" in captured.out


def test_main_branch_mode_exit_code(workbench, glab_shim, capsys):
    with pytest.raises(SystemExit) as exc_info:
        watch.main(["--branch", "feature-x", "--repos", "repo1"])
    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "repo1" in captured.out
    assert "checks=passed" in captured.out


def test_main_requires_prs_or_branch_and_repos(workbench, glab_shim):
    with pytest.raises(SystemExit) as exc_info:
        watch.main([])
    assert exc_info.value.code == 2


def test_main_rejects_both_prs_and_branch(workbench, glab_shim):
    with pytest.raises(SystemExit) as exc_info:
        watch.main(["--prs", "repo1#201", "--branch", "feature-x", "--repos", "repo1"])
    assert exc_info.value.code == 2


# -- poll / verdict_for / build_detail --


def test_poll_mr_shapes_state(workbench, glab_shim):
    poll = _gl().poll(201)
    assert poll["state"] == "OPEN"
    assert poll["checks"] == "passed"
    assert poll["mergeable"] == "mergeable"
    assert poll["url"] == "https://gitlab.com/acme/repo1/-/merge_requests/201"


def test_verdict_passed_and_failed():
    passed = {"state": "OPEN", "checks": "passed", "mergeable": "mergeable"}
    failed = {"state": "OPEN", "checks": "failed", "mergeable": "mergeable"}
    assert watch.verdict_for(passed, elapsed=5, grace=30) == "passed"
    assert watch.verdict_for(failed, elapsed=5, grace=30) == "failed"


def test_verdict_conflict_and_merged_and_closed():
    conflict = {"state": "OPEN", "checks": "none", "mergeable": "conflict"}
    merged = {"state": "MERGED", "checks": "passed", "mergeable": "mergeable"}
    closed = {"state": "CLOSED", "checks": "none", "mergeable": "unknown"}
    assert watch.verdict_for(conflict, elapsed=5, grace=30) == "conflict"
    assert watch.verdict_for(merged, elapsed=5, grace=30) == "merged"
    assert watch.verdict_for(closed, elapsed=5, grace=30) == "closed"


def test_verdict_none_before_and_after_grace():
    none_poll = {"state": "OPEN", "checks": "none", "mergeable": "mergeable"}
    assert watch.verdict_for(none_poll, elapsed=10, grace=30) == "pending"
    assert watch.verdict_for(none_poll, elapsed=30, grace=30) == "no-pipeline"


def test_verdict_pending_checks_stay_pending():
    pending = {"state": "OPEN", "checks": "pending", "mergeable": "mergeable"}
    assert watch.verdict_for(pending, elapsed=999, grace=30) == "pending"


def test_build_detail_no_pipeline_reason_and_waited(workbench, glab_shim):
    adapter = _gl()
    poll = adapter.poll(201)
    poll["checks"] = "none"
    ok, detail = watch.build_detail(adapter, 201, poll, waited=30, verdict="no-pipeline")
    assert ok is True
    assert "waited=30" in detail
    assert "no pipeline launched" in detail


def test_build_detail_timeout_is_failed(workbench, glab_shim):
    adapter = _gl()
    poll = adapter.poll(201)
    poll["checks"] = "pending"
    ok, detail = watch.build_detail(adapter, 201, poll, waited=1200, verdict="timeout")
    assert ok is False
    assert "timed out after 1200s" in detail
    assert "checks=pending" in detail


def test_now_and_sleep_are_indirections():
    assert callable(watch._now)
    assert callable(watch._sleep)


GLAB_WATCH_SHIM = textwrap.dedent(
    """\
    #!/usr/bin/env python3
    import json
    import pathlib
    import re
    import sys

    COUNTER = pathlib.Path(__file__).with_name("calls.txt")

    def _tick():
        n = int(COUNTER.read_text()) if COUNTER.exists() else 0
        COUNTER.write_text(str(n + 1))
        return n

    # 301: none -> pending -> passed ; 302: pending -> failed ;
    # 303: never launches (always none) ; 304: always pending (timeout)
    def pipeline_for(iid, tick):
        if iid == "301":
            if tick == 0:
                return None
            if tick == 1:
                return {"id": 1, "status": "running"}
            return {"id": 1, "status": "success"}
        if iid == "302":
            if tick == 0:
                return {"id": 2, "status": "running"}
            return {"id": 2, "status": "failed"}
        if iid == "303":
            return None
        if iid == "304":
            return {"id": 4, "status": "running"}
        return None

    JOBS = {"2": [{"id": 2, "name": "ci/test", "status": "failed"}]}

    LOGS = {"2": "\\n".join(f"boom {i}" for i in range(1, 121))}

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
            data = {
                "iid": int(iid),
                "state": "opened",
                "has_conflicts": False,
                "detailed_merge_status": "mergeable",
                "web_url": f"https://gitlab.com/acme/repo1/-/merge_requests/{iid}",
                "head_pipeline": pipeline_for(iid, tick),
            }
            print(json.dumps(data))
            return

        m = re.match(r"^projects/(?P<enc>[^/]+)/pipelines/(?P<pid>\\d+)/jobs$", path)
        if m:
            pid = m.group("pid")
            print(json.dumps(JOBS.get(pid, [])))
            return

        m = re.match(r"^projects/(?P<enc>[^/]+)/jobs/(?P<jid>\\d+)/trace$", path)
        if m:
            jid = m.group("jid")
            sys.stdout.write(LOGS.get(jid, ""))
            return

        sys.stderr.write(f"unhandled glab api path: {path}\\n")
        sys.exit(1)

    if __name__ == "__main__":
        main()
    """
)


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


# -- watch loop --


def test_watch_reports_success_when_pipeline_passes(fake_clock, glab_watch_shim):
    report = common.Report()
    watch.watch_targets([("repo1", _gl(), 301)], report, interval=10, timeout=1200, grace=30)
    rendered = report.render()
    assert "ok" in rendered
    assert "checks=passed" in rendered
    assert report.exit_code == 0


def test_watch_reports_failure_with_log_tail(fake_clock, glab_watch_shim):
    report = common.Report()
    watch.watch_targets([("repo1", _gl(), 302)], report, interval=10, timeout=1200, grace=30)
    rendered = report.render()
    assert "failed" in rendered
    assert "checks=failed" in rendered
    assert "ci/test" in rendered
    assert "boom 120" in rendered
    assert rendered.count("boom ") <= 100
    assert report.exit_code == 1


def test_watch_no_pipeline_after_grace(fake_clock, glab_watch_shim):
    report = common.Report()
    watch.watch_targets([("repo1", _gl(), 303)], report, interval=10, timeout=1200, grace=30)
    rendered = report.render()
    assert "no pipeline launched" in rendered
    assert "ok" in rendered
    assert report.exit_code == 0


def test_watch_timeout_is_failed(fake_clock, glab_watch_shim):
    report = common.Report()
    watch.watch_targets([("repo1", _gl(), 304)], report, interval=10, timeout=40, grace=30)
    rendered = report.render()
    assert "timed out after" in rendered
    assert "failed" in rendered
    assert report.exit_code == 1


def test_main_no_wait_is_snapshot(workbench, glab_shim, capsys):
    with pytest.raises(SystemExit) as exc_info:
        watch.main(["--no-wait", "--prs", "repo1#201"])
    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "checks=passed" in captured.out
    assert "waited=" not in captured.out


def test_main_default_watches(workbench, glab_watch_shim, fake_clock, capsys):
    with pytest.raises(SystemExit) as exc_info:
        watch.main(["--prs", "repo1#301"])
    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "checks=passed" in captured.out
    assert "waited=" in captured.out


def test_watch_prints_resolved_line_on_resolution(fake_clock, glab_watch_shim, capsys):
    report = common.Report()
    watch.watch_targets([("repo1", _gl(), 301)], report, interval=10, timeout=1200, grace=30)
    captured = capsys.readouterr()
    assert "RESOLVED repo1" in captured.out
    assert "checks=passed" in captured.out
    rendered = report.render()
    assert "repo1" in rendered
    assert "checks=passed" in rendered


def test_resolved_line_shape_gitlab(fake_clock, glab_watch_shim, capsys):
    report = common.Report()
    watch.watch_targets([("repo1", _gl(), 301)], report, interval=10, timeout=1200, grace=30)
    lines = [ln for ln in capsys.readouterr().out.splitlines() if ln.startswith("RESOLVED")]
    assert lines == [
        f"RESOLVED {'repo1':<20} {'ok':<10} mr !301: state=OPEN checks=passed "
        "mergeable=mergeable reviews=0 unresolved "
        "url=https://gitlab.com/acme/repo1/-/merge_requests/301 waited=20"
    ]


GLAB_MULTI_WATCH_SHIM = textwrap.dedent(
    """\
    #!/usr/bin/env python3
    import json
    import pathlib
    import re
    import sys

    COUNTER = pathlib.Path(__file__).with_name("calls.txt")

    def _tick(iid):
        state = {}
        if COUNTER.exists():
            for line in COUNTER.read_text().splitlines():
                k, v = line.split("=")
                state[k] = int(v)
        n = state.get(iid, 0)
        state[iid] = n + 1
        COUNTER.write_text("\\n".join(f"{k}={v}" for k, v in state.items()))
        return n
    # 401: resolves immediately (tick 0 -> success)
    # 402: pending on tick 0, resolves on tick 1 -> success
    def pipeline_for(iid, tick):
        if iid == "401":
            return {"id": 1, "status": "success"}
        if iid == "402":
            if tick == 0:
                return {"id": 2, "status": "running"}
            return {"id": 2, "status": "success"}
        return None
    def main():
        argv = sys.argv[1:]
        if argv[0] != "api":
            sys.stderr.write(f"unhandled glab args: {argv}\\n")
            sys.exit(1)
        path = argv[1]

        m = re.match(r"^projects/(?P<enc>[^/]+)/merge_requests/(?P<iid>\\d+)$", path)
        if m:
            iid = m.group("iid")
            tick = _tick(iid)
            data = {
                "iid": int(iid),
                "state": "opened",
                "has_conflicts": False,
                "detailed_merge_status": "mergeable",
                "web_url": f"https://gitlab.com/acme/repo/-/merge_requests/{iid}",
                "head_pipeline": pipeline_for(iid, tick),
            }
            print(json.dumps(data))
            return

        sys.stderr.write(f"unhandled glab api path: {path}\\n")
        sys.exit(1)

    if __name__ == "__main__":
        main()
    """
)


@pytest.fixture
def glab_multi_watch_shim(tmp_path, monkeypatch):
    glab_path = _install(tmp_path / "mwbin", "glab", GLAB_MULTI_WATCH_SHIM)
    monkeypatch.setenv("PATH", f"{glab_path.parent}:{os.environ['PATH']}")
    return glab_path


def test_watch_resolved_lines_are_edge_triggered_per_target(
    fake_clock, glab_multi_watch_shim, capsys
):
    """Regression test for the batch-completion barrier bug.

    repo1 (iid 401) resolves on the first tick; repo2 (iid 402) is still
    pending and only resolves on the second tick. repo1's RESOLVED line must
    reach stdout as soon as it resolves, not held back until repo2 catches up.
    """
    report = common.Report()
    watch.watch_targets(
        [("repo1", _gl("repo1", "acme/repo1"), 401), ("repo2", _gl("repo2", "acme/repo2"), 402)],
        report,
        interval=10,
        timeout=1200,
        grace=30,
    )
    captured = capsys.readouterr()
    repo1_pos = captured.out.index("RESOLVED repo1")
    repo2_pos = captured.out.index("RESOLVED repo2")
    assert repo1_pos < repo2_pos
    rendered = report.render()
    assert "repo1" in rendered
    assert "repo2" in rendered


# -- a repo with no PR/MR host --


@pytest.fixture
def local_workbench(tmp_path, monkeypatch):
    root = _make_workbench(
        tmp_path / "workbench",
        {
            "repo1": "git@gitlab.com:acme/repo1.git",
            "scratch": None,
            "mirror": "/srv/git/mirror.git",
        },
    )
    monkeypatch.chdir(root)
    return root


def test_local_only_repo_skipped(local_workbench, glab_shim, fake_clock, capsys):
    with pytest.raises(SystemExit) as exc_info:
        watch.main(["--branch", "feature-x", "--repos", "repo1,scratch,mirror"])
    assert exc_info.value.code == 0
    out = capsys.readouterr().out
    resolved = [ln for ln in out.splitlines() if ln.startswith("RESOLVED")]
    assert len(resolved) == 1
    assert "repo1" in resolved[0] and "mr !201: state=OPEN checks=passed" in resolved[0]
    rows = {ln.split()[0]: ln for ln in out.split("REPO ", 1)[1].splitlines()[1:]}
    assert rows["scratch"].split()[1] == "skipped"
    assert "local-only: no PR/MR host for (no origin)" in rows["scratch"]
    assert rows["mirror"].split()[1] == "skipped"
    assert "local-only: no PR/MR host for /srv/git/mirror.git" in rows["mirror"]


def test_local_only_repo_skipped_no_wait(local_workbench, glab_shim, capsys):
    with pytest.raises(SystemExit) as exc_info:
        watch.main(["--no-wait", "--prs", "repo1#201,scratch#1"])
    assert exc_info.value.code == 0
    out = capsys.readouterr().out
    assert "mr !201: state=OPEN checks=passed" in out
    assert "local-only: no PR/MR host for (no origin)" in out
