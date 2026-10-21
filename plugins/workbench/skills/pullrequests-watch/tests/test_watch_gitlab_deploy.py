"""pullrequests-watch --deploy and --sha on GitLab: the retired GitLab watch
deploy and sha tests, ported onto the host-agnostic watch over scm.GitLab with the
same assertions."""

import argparse
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


@pytest.fixture(autouse=True)
def _no_host_map(monkeypatch):
    monkeypatch.delenv(scm.HOSTS_ENV, raising=False)


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
    }

    def main():
        argv = sys.argv[1:]
        path = argv[1]
        m = re.match(r"^projects/(?P<enc>[^/]+)/merge_requests/(?P<iid>\\d+)$", path)
        if m and m.group("iid") in MRS:
            print(json.dumps(MRS[m.group("iid")]))
            return
        sys.stderr.write(f"unhandled glab api path: {path}\\n")
        sys.exit(1)

    if __name__ == "__main__":
        main()
    """
)


@pytest.fixture
def glab_shim(tmp_path, monkeypatch):
    shim_dir = tmp_path / "bin"
    shim_dir.mkdir()
    glab_path = shim_dir / "glab"
    glab_path.write_text(GLAB_SHIM)
    glab_path.chmod(0o755)
    monkeypatch.setenv("PATH", f"{shim_dir}:{os.environ['PATH']}")
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


@pytest.fixture
def fake_clock(monkeypatch):
    state = {"t": 0.0}
    monkeypatch.setattr(watch, "_now", lambda: state["t"])
    monkeypatch.setattr(watch, "_sleep", lambda s: state.__setitem__("t", state["t"] + s))
    return state


GLAB_DEPLOY_PR_SHIM = textwrap.dedent(
    """\
    #!/usr/bin/env python3
    import json
    import re
    import sys

    MRS = {
        "401": {
            "iid": 401,
            "state": "merged",
            "target_branch": "main",
            "merge_commit_sha": "deadbeef01deadbeef01deadbeef01deadbeef01",
            "web_url": "https://gitlab.com/acme/repo1/-/merge_requests/401",
        },
        "402": {
            "iid": 402,
            "state": "merged",
            "target_branch": "main",
            "merge_commit_sha": "cafebabe02cafebabe02cafebabe02cafebabe02",
            "web_url": "https://gitlab.com/acme/repo1/-/merge_requests/402",
        },
        "403": {
            "iid": 403,
            "state": "opened",
            "target_branch": "main",
            "merge_commit_sha": None,
            "web_url": "https://gitlab.com/acme/repo1/-/merge_requests/403",
        },
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

        sys.stderr.write(f"unhandled glab api path: {path}\\n")
        sys.exit(1)

    if __name__ == "__main__":
        main()
    """
)


@pytest.fixture
def glab_deploy_pr_shim(tmp_path, monkeypatch):
    shim_dir = tmp_path / "dpbin"
    shim_dir.mkdir()
    glab_path = shim_dir / "glab"
    glab_path.write_text(GLAB_DEPLOY_PR_SHIM)
    glab_path.chmod(0o755)
    monkeypatch.setenv("PATH", f"{shim_dir}:{os.environ['PATH']}")
    return glab_path


GLAB_DEPLOY_POLL_SHIM = textwrap.dedent(
    """\
    #!/usr/bin/env python3
    import json
    import re
    import sys

    PIPELINES = {
        "main|deadbeef01deadbeef01deadbeef01deadbeef01": [
            {"id": 5001, "status": "success", "sha": "deadbeef01deadbeef01deadbeef01deadbeef01",
             "ref": "main", "web_url": "https://gitlab.com/acme/repo1/-/pipelines/5001"},
        ],
        "main|cafebabe02cafebabe02cafebabe02cafebabe02": [
            {"id": 5002, "status": "failed", "sha": "cafebabe02cafebabe02cafebabe02cafebabe02",
             "ref": "main", "web_url": "https://gitlab.com/acme/repo1/-/pipelines/5002"},
        ],
        "main|": [
            {"id": 5003, "status": "success", "sha": "latestsha0latestsha0latestsha0latestsha0",
             "ref": "main", "web_url": "https://gitlab.com/acme/repo1/-/pipelines/5003"},
        ],
    }

    JOBS = {"5002": [{"id": 21, "name": "ci/deploy", "status": "failed"}]}

    LOGS = {"21": "\\n".join(f"deploy log line {i}" for i in range(1, 151))}

    def main():
        argv = sys.argv[1:]
        if argv[0] != "api":
            sys.stderr.write(f"unhandled glab args: {argv}\\n")
            sys.exit(1)
        path = argv[1]

        m = re.match(
            r"^projects/(?P<enc>[^/]+)/pipelines\\?ref=(?P<ref>[^&]+)"
            r"(&sha=(?P<sha>[^&]+))?&per_page=1$",
            path,
        )
        if m:
            key = f"{m.group('ref')}|{m.group('sha') or ''}"
            print(json.dumps(PIPELINES.get(key, [])))
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
def glab_deploy_poll_shim(tmp_path, monkeypatch):
    shim_dir = tmp_path / "dqbin"
    shim_dir.mkdir()
    glab_path = shim_dir / "glab"
    glab_path.write_text(GLAB_DEPLOY_POLL_SHIM)
    glab_path.chmod(0o755)
    monkeypatch.setenv("PATH", f"{shim_dir}:{os.environ['PATH']}")
    return glab_path


GLAB_DEPLOY_SHIM = textwrap.dedent(
    """\
    #!/usr/bin/env python3
    import json
    import re
    import sys

    MRS = {
        "401": {
            "iid": 401, "state": "merged", "target_branch": "main",
            "merge_commit_sha": "deadbeef01deadbeef01deadbeef01deadbeef01",
            "web_url": "https://gitlab.com/acme/repo1/-/merge_requests/401",
        },
        "402": {
            "iid": 402, "state": "merged", "target_branch": "main",
            "merge_commit_sha": "cafebabe02cafebabe02cafebabe02cafebabe02",
            "web_url": "https://gitlab.com/acme/repo1/-/merge_requests/402",
        },
        "403": {
            "iid": 403, "state": "opened", "target_branch": "main",
            "merge_commit_sha": None,
            "web_url": "https://gitlab.com/acme/repo1/-/merge_requests/403",
        },
    }

    PIPELINES = {
        "main|deadbeef01deadbeef01deadbeef01deadbeef01": [
            {"id": 5001, "status": "success", "sha": "deadbeef01deadbeef01deadbeef01deadbeef01",
             "ref": "main", "web_url": "https://gitlab.com/acme/repo1/-/pipelines/5001"},
        ],
        "main|cafebabe02cafebabe02cafebabe02cafebabe02": [
            {"id": 5002, "status": "failed", "sha": "cafebabe02cafebabe02cafebabe02cafebabe02",
             "ref": "main", "web_url": "https://gitlab.com/acme/repo1/-/pipelines/5002"},
        ],
        "main|": [
            {"id": 5003, "status": "success", "sha": "latestsha0latestsha0latestsha0latestsha0",
             "ref": "main", "web_url": "https://gitlab.com/acme/repo1/-/pipelines/5003"},
        ],
    }

    JOBS = {"5002": [{"id": 21, "name": "ci/deploy", "status": "failed"}]}
    LOGS = {"21": "\\n".join(f"deploy log line {i}" for i in range(1, 151))}

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
            r"^projects/(?P<enc>[^/]+)/pipelines\\?ref=(?P<ref>[^&]+)"
            r"(&sha=(?P<sha>[^&]+))?&per_page=1$",
            path,
        )
        if m:
            key = f"{m.group('ref')}|{m.group('sha') or ''}"
            print(json.dumps(PIPELINES.get(key, [])))
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
def glab_deploy_shim(tmp_path, monkeypatch):
    shim_dir = tmp_path / "dbin"
    shim_dir.mkdir()
    glab_path = shim_dir / "glab"
    glab_path.write_text(GLAB_DEPLOY_SHIM)
    glab_path.chmod(0o755)
    monkeypatch.setenv("PATH", f"{shim_dir}:{os.environ['PATH']}")
    return glab_path


GLAB_DEPLOY_WATCH_SHIM = textwrap.dedent(
    """\
    #!/usr/bin/env python3
    import json
    import pathlib
    import re
    import sys

    COUNTER = pathlib.Path(__file__).with_name("calls.txt")

    def _tick(key):
        state = {}
        if COUNTER.exists():
            for line in COUNTER.read_text().splitlines():
                k, v = line.split("=")
                state[k] = int(v)
        n = state.get(key, 0)
        state[key] = n + 1
        COUNTER.write_text("\\n".join(f"{k}={v}" for k, v in state.items()))
        return n

    # aaa1: none -> pending -> success ; bbb2: always none (grace) ;
    # ccc3: always pending (timeout)
    def pipeline_for(sha, tick):
        if sha == "aaa1":
            if tick == 0:
                return []
            if tick == 1:
                return [{"id": 1, "status": "running", "sha": "aaa1", "ref": "main",
                         "web_url": "https://gitlab.com/acme/repo1/-/pipelines/1"}]
            return [{"id": 1, "status": "success", "sha": "aaa1", "ref": "main",
                     "web_url": "https://gitlab.com/acme/repo1/-/pipelines/1"}]
        if sha == "bbb2":
            return []
        if sha == "ccc3":
            return [{"id": 3, "status": "running", "sha": "ccc3", "ref": "main",
                     "web_url": "https://gitlab.com/acme/repo1/-/pipelines/3"}]
        return []

    def main():
        argv = sys.argv[1:]
        if argv[0] != "api":
            sys.stderr.write(f"unhandled glab args: {argv}\\n")
            sys.exit(1)
        path = argv[1]

        m = re.match(
            r"^projects/(?P<enc>[^/]+)/pipelines\\?ref=(?P<ref>[^&]+)"
            r"&sha=(?P<sha>[^&]+)&per_page=1$",
            path,
        )
        if m:
            sha = m.group("sha")
            tick = _tick(sha)
            print(json.dumps(pipeline_for(sha, tick)))
            return

        sys.stderr.write(f"unhandled glab api path: {path}\\n")
        sys.exit(1)

    if __name__ == "__main__":
        main()
    """
)


@pytest.fixture
def glab_deploy_watch_shim(tmp_path, monkeypatch):
    shim_dir = tmp_path / "dwbin"
    shim_dir.mkdir()
    glab_path = shim_dir / "glab"
    glab_path.write_text(GLAB_DEPLOY_WATCH_SHIM)
    glab_path.chmod(0o755)
    monkeypatch.setenv("PATH", f"{shim_dir}:{os.environ['PATH']}")
    return glab_path


# -- --sha parsing --


def test_parse_sha_pairs():
    assert watch.parse_sha_pairs("repo1=deadbeef,repo2=CAFE1234") == {
        "repo1": "deadbeef",
        "repo2": "CAFE1234",
    }


def test_parse_sha_pairs_invalid_entry_raises():
    with pytest.raises(common.RepoError):
        watch.parse_sha_pairs("repo1-deadbeef")


def test_parse_sha_pairs_empty_is_empty_dict():
    assert watch.parse_sha_pairs("") == {}


# -- resolve_deploy --


def test_resolve_deploy_pr_merged_returns_branch_and_sha(workbench, glab_deploy_pr_shim):
    gl = _gl()
    branch, sha = gl.resolve_deploy(401)
    assert gl.project == "acme%2Frepo1"
    assert branch == "main"
    assert sha == "deadbeef01deadbeef01deadbeef01deadbeef01"


def test_resolve_deploy_pr_not_merged_raises_clear_error(workbench, glab_deploy_pr_shim):
    with pytest.raises(common.RepoError, match="not merged yet") as exc_info:
        _gl().resolve_deploy(403)
    assert str(exc_info.value) == (
        "mr !403 not merged yet (no merge_commit_sha) - deploy-watch is a post-merge action"
    )


# -- poll_deploy / verdict_for_deploy --


def test_poll_deploy_sha_pinned_success(workbench, glab_deploy_poll_shim):
    poll = _gl().poll_deploy("main", "deadbeef01deadbeef01deadbeef01deadbeef01")
    assert poll["branch"] == "main"
    assert poll["checks"] == "passed"
    assert poll["pipeline"]["id"] == 5001


def test_poll_deploy_sha_pinned_failed(workbench, glab_deploy_poll_shim):
    poll = _gl().poll_deploy("main", "cafebabe02cafebabe02cafebabe02cafebabe02")
    assert poll["checks"] == "failed"
    assert poll["pipeline"]["id"] == 5002


def test_poll_deploy_latest_no_sha(workbench, glab_deploy_poll_shim):
    poll = _gl().poll_deploy("main")
    assert poll["sha"] is None
    assert poll["checks"] == "passed"
    assert poll["pipeline"]["id"] == 5003


def test_poll_deploy_no_pipeline_yet_is_none_checks(workbench, glab_deploy_poll_shim):
    poll = _gl().poll_deploy("main", "notregisteredsha0000000000000000000000000")
    assert poll["pipeline"] is None
    assert poll["checks"] == "none"


def test_verdict_for_deploy_passed_and_failed():
    passed = {"checks": "passed"}
    failed = {"checks": "failed"}
    assert watch.verdict_for_deploy(passed, elapsed=5, grace=30) == "passed"
    assert watch.verdict_for_deploy(failed, elapsed=5, grace=30) == "failed"


def test_verdict_for_deploy_none_before_and_after_grace():
    none_poll = {"checks": "none"}
    assert watch.verdict_for_deploy(none_poll, elapsed=10, grace=30) == "pending"
    assert watch.verdict_for_deploy(none_poll, elapsed=30, grace=30) == "no-pipeline"


def test_verdict_for_deploy_pending_stays_pending():
    pending = {"checks": "pending"}
    assert watch.verdict_for_deploy(pending, elapsed=999, grace=30) == "pending"


# -- build_deploy_detail --


def test_build_deploy_detail_passed_is_ok(workbench, glab_deploy_poll_shim):
    gl = _gl()
    poll = gl.poll_deploy("main", "deadbeef01deadbeef01deadbeef01deadbeef01")
    ok, detail = watch.build_deploy_detail(gl, poll)
    assert ok is True
    assert "branch=main" in detail
    assert "status=passed" in detail
    assert "pipelines/5001" in detail


def test_build_deploy_detail_failed_reports_job_name_and_log_tail(workbench, glab_deploy_poll_shim):
    gl = _gl()
    poll = gl.poll_deploy("main", "cafebabe02cafebabe02cafebabe02cafebabe02")
    ok, detail = watch.build_deploy_detail(gl, poll)
    assert ok is False
    assert "status=failed" in detail
    assert "ci/deploy" in detail
    assert "deploy log line 150" in detail
    assert "deploy log line 1\n" not in detail
    assert detail.count("deploy log line ") <= 100


def test_build_deploy_detail_no_pipeline_reason_and_waited():
    poll = {"branch": "main", "sha": None, "pipeline": None, "checks": "none"}
    ok, detail = watch.build_deploy_detail(_gl(), poll, waited=30, verdict="no-pipeline")
    assert ok is True
    assert "waited=30" in detail
    assert "no pipeline launched" in detail


def test_build_deploy_detail_timeout_is_failed():
    poll = {"branch": "main", "sha": None, "pipeline": None, "checks": "pending"}
    ok, detail = watch.build_deploy_detail(_gl(), poll, waited=1200, verdict="timeout")
    assert ok is False
    assert "timed out after 1200s" in detail
    assert "status=pending" in detail


# -- process_deploy_pr / process_deploy_branch --


def test_process_deploy_pr_sha_pinned_success(workbench, glab_deploy_shim):
    report = common.Report()
    watch.process_deploy_pr("repo1", 401, report)
    rendered = report.render()
    assert "ok" in rendered
    assert "mr !401 deploy:" in rendered
    assert "branch=main" in rendered
    assert "status=passed" in rendered
    assert report.exit_code == 0


def test_process_deploy_pr_failed_reports_job_name_and_log_tail(workbench, glab_deploy_shim):
    report = common.Report()
    watch.process_deploy_pr("repo1", 402, report)
    rendered = report.render()
    assert "failed" in rendered
    assert "status=failed" in rendered
    assert "ci/deploy" in rendered
    assert "deploy log line 150" in rendered
    assert report.exit_code == 1


def test_process_deploy_pr_not_merged_reports_clearly(workbench, glab_deploy_shim):
    report = common.Report()
    watch.process_deploy_pr("repo1", 403, report)
    rendered = report.render()
    assert "failed" in rendered
    assert "not merged yet" in rendered
    assert report.exit_code == 1


def test_process_deploy_branch_uses_tracked_branch_default(workbench, glab_deploy_shim):
    report = common.Report()
    watch.process_deploy_branch("repo1", None, None, report)
    rendered = report.render()
    assert "deploy: branch=main" in rendered
    assert "status=passed" in rendered


def test_process_deploy_branch_with_sha_pin(workbench, glab_deploy_shim):
    report = common.Report()
    watch.process_deploy_branch("repo1", "main", "cafebabe02cafebabe02cafebabe02cafebabe02", report)
    rendered = report.render()
    assert "failed" in rendered
    assert "status=failed" in rendered


# -- main() CLI wiring --


def test_main_deploy_rejects_sha_for_unknown_repo(workbench, glab_shim):
    with pytest.raises(SystemExit) as exc_info:
        watch.main(["--deploy", "--repos", "repo1", "--sha", "repo2=abc123"])
    assert exc_info.value.code == 2


# -- deploy watch loop --


def test_watch_deploy_reports_success_after_pending(fake_clock, glab_deploy_watch_shim):
    report = common.Report()
    watch.watch_deploy_targets(
        [("repo1", _gl(), "main", "aaa1", "deploy")], report, interval=10, timeout=1200, grace=30
    )
    rendered = report.render()
    assert "ok" in rendered
    assert "status=passed" in rendered
    assert report.exit_code == 0


def test_watch_deploy_no_pipeline_after_grace(fake_clock, glab_deploy_watch_shim):
    report = common.Report()
    watch.watch_deploy_targets(
        [("repo1", _gl(), "main", "bbb2", "deploy")], report, interval=10, timeout=1200, grace=30
    )
    rendered = report.render()
    assert "no pipeline launched" in rendered
    assert "ok" in rendered
    assert report.exit_code == 0


def test_watch_deploy_timeout_is_failed(fake_clock, glab_deploy_watch_shim):
    report = common.Report()
    watch.watch_deploy_targets(
        [("repo1", _gl(), "main", "ccc3", "deploy")], report, interval=10, timeout=40, grace=30
    )
    rendered = report.render()
    assert "timed out after" in rendered
    assert "failed" in rendered
    assert report.exit_code == 1


# -- _deploy_targets_from_args --


def _flat(targets):
    return [(repo, adapter.slug, branch, sha) for repo, adapter, branch, sha, *_ in targets]


def test_deploy_targets_from_args_prs_mode(workbench, glab_deploy_shim):
    report = common.Report()
    args = argparse.Namespace(prs="repo1#401", branch=None, repos=None, sha=None)
    targets = watch._deploy_targets_from_args(args, report)
    assert _flat(targets) == [
        ("repo1", "acme/repo1", "main", "deadbeef01deadbeef01deadbeef01deadbeef01")
    ]


def test_deploy_targets_from_args_repos_mode_default_branch(workbench, glab_deploy_shim):
    report = common.Report()
    args = argparse.Namespace(prs=None, branch=None, repos="repo1", sha=None)
    targets = watch._deploy_targets_from_args(args, report)
    assert _flat(targets) == [("repo1", "acme/repo1", "main", None)]


def test_deploy_targets_from_args_repos_mode_with_sha(workbench, glab_deploy_shim):
    report = common.Report()
    args = argparse.Namespace(prs=None, branch=None, repos="repo1", sha="repo1=cafebabe")
    targets = watch._deploy_targets_from_args(args, report)
    assert _flat(targets) == [("repo1", "acme/repo1", "main", "cafebabe")]


# -- deploy CLI wiring --


def test_main_deploy_prs_no_wait(workbench, glab_deploy_shim, capsys):
    with pytest.raises(SystemExit) as exc_info:
        watch.main(["--prs", "repo1#401", "--deploy", "--no-wait"])
    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "branch=main" in captured.out
    assert "status=passed" in captured.out


def test_main_deploy_prs_not_merged_no_wait_is_failed(workbench, glab_deploy_shim, capsys):
    with pytest.raises(SystemExit) as exc_info:
        watch.main(["--prs", "repo1#403", "--deploy", "--no-wait"])
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "not merged yet" in captured.out


def test_main_deploy_repos_no_wait_default_branch(workbench, glab_deploy_shim, capsys):
    with pytest.raises(SystemExit) as exc_info:
        watch.main(["--repos", "repo1", "--deploy", "--no-wait"])
    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "branch=main" in captured.out


def test_main_deploy_watches_by_default(workbench, glab_deploy_shim, capsys):
    with pytest.raises(SystemExit) as exc_info:
        watch.main(["--prs", "repo1#401", "--deploy"])
    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "waited=" in captured.out
    assert "status=passed" in captured.out
    assert "reviews=" not in captured.out


def test_main_deploy_prs_watch_mode_carries_mr_prefix(workbench, glab_deploy_shim, capsys):
    with pytest.raises(SystemExit):
        watch.main(["--prs", "repo1#401", "--deploy"])
    assert "mr !401 deploy:" in capsys.readouterr().out


def test_main_deploy_repos_watch_mode_has_plain_prefix(workbench, glab_deploy_shim, capsys):
    with pytest.raises(SystemExit):
        watch.main(["--repos", "repo1", "--deploy"])
    out = capsys.readouterr().out
    assert "deploy:" in out
    assert "mr !" not in out


def test_main_deploy_requires_prs_or_repos(workbench, glab_deploy_shim):
    with pytest.raises(SystemExit) as exc_info:
        watch.main(["--deploy"])
    assert exc_info.value.code == 2


def test_main_deploy_sha_without_repos_form_is_rejected(workbench, glab_deploy_shim):
    with pytest.raises(SystemExit) as exc_info:
        watch.main(["--prs", "repo1#401", "--deploy", "--sha", "repo1=deadbeef"])
    assert exc_info.value.code == 2


def test_main_sha_without_deploy_is_rejected(workbench, glab_deploy_shim):
    with pytest.raises(SystemExit) as exc_info:
        watch.main(["--branch", "x", "--repos", "repo1", "--sha", "repo1=deadbeef"])
    assert exc_info.value.code == 2


def test_watch_deploy_prints_resolved_line(fake_clock, glab_deploy_watch_shim, capsys):
    report = common.Report()
    watch.watch_deploy_targets(
        [("repo1", _gl(), "main", "aaa1", "deploy")], report, interval=10, timeout=1200, grace=30
    )
    captured = capsys.readouterr()
    assert "RESOLVED repo1" in captured.out
    assert "status=passed" in captured.out
    rendered = report.render()
    assert "repo1" in rendered
    assert "status=passed" in rendered


# -- acceptance tests named by the task --


def test_gitlab_deploy_prs_uses_merge_commit(workbench, glab_deploy_shim):
    report = common.Report()
    watch.process_deploy_pr("repo1", 401, report)
    rendered = report.render()
    assert "mr !401 deploy:" in rendered
    assert "branch=main" in rendered
    assert "status=passed" in rendered
    assert report.exit_code == 0


def test_gitlab_deploy_unmerged_mr_fails(workbench, glab_deploy_shim):
    report = common.Report()
    watch.process_deploy_pr("repo1", 403, report)
    assert "not merged yet" in report.render()
    assert report.exit_code == 1


def test_gitlab_deploy_branch_mode_and_sha(workbench, glab_deploy_shim):
    default = common.Report()
    watch.process_deploy_branch("repo1", None, None, default)
    assert "deploy: branch=main" in default.render()
    assert "status=passed" in default.render()
    pinned = common.Report()
    watch.process_deploy_branch("repo1", "main", "cafebabe02cafebabe02cafebabe02cafebabe02", pinned)
    assert "status=failed" in pinned.render()
    assert pinned.exit_code == 1


def test_gitlab_deploy_failed_job_tail(workbench, glab_deploy_shim):
    report = common.Report()
    watch.process_deploy_pr("repo1", 402, report)
    rendered = report.render()
    assert "status=failed" in rendered
    assert "ci/deploy" in rendered
    assert "deploy log line 150" in rendered
