"""The scm poll ops: resolve_branch, poll, failed_reasons, conflict_files, list_open.

Each op is checked against a fake gh/glab on PATH, with the value vocabularies
the pullrequests-watch and pullrequests-list scripts report on both hosts.
"""

import json
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import common  # noqa: E402
import scm  # noqa: E402

# One shim serves as both gh and glab. It records argv, then answers from the
# first rule in $SHIM_RULES whose "match" tokens all appear in argv (default:
# exit 0, no output).
SHIM = """#!/usr/bin/env python3
import json
import os
import sys

name = os.path.basename(sys.argv[0])
argv = sys.argv[1:]
with open(os.environ["SHIM_LOG"], "a") as f:
    f.write(json.dumps({"cli": name, "argv": argv}) + "\\n")
rules = json.load(open(os.environ["SHIM_RULES"])) if os.environ.get("SHIM_RULES") else []
for rule in rules:
    if rule.get("cli", name) == name and all(t in argv for t in rule.get("match", [])):
        sys.stdout.write(rule.get("stdout", ""))
        sys.stderr.write(rule.get("stderr", ""))
        sys.exit(rule.get("exit", 0))
"""

LOG_150 = "".join(f"line {i}\n" for i in range(1, 151))
TAIL_100 = "\n".join(f"line {i}" for i in range(51, 151))


@pytest.fixture
def shim(tmp_path, monkeypatch):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    for name in ("gh", "glab"):
        path = bin_dir / name
        path.write_text(SHIM)
        path.chmod(0o755)
    log = tmp_path / "shim.jsonl"
    rules = tmp_path / "rules.json"
    monkeypatch.setenv("SHIM_LOG", str(log))
    monkeypatch.setenv("SHIM_RULES", str(rules))
    monkeypatch.setenv("PATH", f"{bin_dir}:{os.environ['PATH']}")

    class Shim:
        def respond(self, *new_rules):
            rules.write_text(json.dumps(list(new_rules)))

        def calls(self):
            if not log.exists():
                return []
            return [json.loads(line) for line in log.read_text().splitlines()]

    s = Shim()
    s.respond()
    return s


# Built after the shim is on PATH; the adapters read the process env per call.
@pytest.fixture
def hosts(shim):
    return (
        scm.GitHub("app", "github.com", "acme/app"),
        scm.GitLab("proj", "gitlab.com", "grp/sub/proj"),
    )


GL_MR = "projects/grp%2Fsub%2Fproj/merge_requests"


def _ok(conclusion="SUCCESS", **extra):
    return {"name": "ok", "status": "COMPLETED", "conclusion": conclusion, **extra}


# --- resolve_branch ---------------------------------------------------------


def test_resolve_branch_both_hosts(shim, hosts):
    github, gitlab = hosts
    shim.respond(
        {"cli": "gh", "match": ["feat/x"], "stdout": json.dumps({"number": 12})},
        {"cli": "glab", "match": [], "stdout": json.dumps([{"iid": 7, "web_url": "u"}])},
    )
    assert github.resolve_branch("feat/x") == 12
    assert gitlab.resolve_branch("feat/x") == 7
    gh_call, gl_call = shim.calls()
    assert gh_call["argv"] == ["pr", "view", "feat/x", "--json", "number", "-R", "acme/app"]
    assert gl_call["argv"] == ["api", f"{GL_MR}?source_branch=feat%2Fx&state=opened"]


def test_resolve_branch_none_raises_naming_branch(shim, hosts):
    github, gitlab = hosts
    shim.respond(
        {"cli": "gh", "stderr": "no pull requests found for branch", "exit": 1},
        {"cli": "glab", "stdout": "[]"},
    )
    with pytest.raises(common.RepoError, match=r"^branch feat/x: no PR found \("):
        github.resolve_branch("feat/x")
    with pytest.raises(common.RepoError, match=r"^branch feat/x: no MR found \("):
        gitlab.resolve_branch("feat/x")


def test_resolve_branch_malformed_answer_raises(shim, hosts):
    github, gitlab = hosts
    shim.respond({"cli": "gh", "stdout": "{}"}, {"cli": "glab", "stdout": "{}"})
    with pytest.raises(common.RepoError, match="branch b: no PR found"):
        github.resolve_branch("b")
    with pytest.raises(common.RepoError, match="branch b: no MR found"):
        gitlab.resolve_branch("b")


# --- poll: GitHub -----------------------------------------------------------


@pytest.mark.parametrize(
    "rollup,checks",
    [
        (None, "none"),
        ([], "none"),
        ([_ok()], "passed"),
        ([_ok("SKIPPED"), _ok("NEUTRAL")], "passed"),
        ([_ok(), _ok("FAILURE")], "failed"),
        ([_ok("CANCELLED")], "failed"),
        ([_ok("TIMED_OUT")], "failed"),
        ([_ok("ACTION_REQUIRED")], "failed"),
        ([_ok("STARTUP_FAILURE")], "failed"),
        ([{"name": "a", "status": "IN_PROGRESS", "conclusion": ""}], "pending"),
        ([{"name": "a", "status": "QUEUED"}], "pending"),
        ([{"context": "ci", "state": "SUCCESS"}], "passed"),
        ([{"context": "ci", "state": "PENDING"}], "pending"),
        ([{"context": "ci", "state": "FAILURE"}], "failed"),
        ([{"context": "ci", "state": "ERROR"}], "failed"),
        ([{"name": "a", "status": "IN_PROGRESS", "conclusion": "SUCCESS"}], "pending"),
        ([{"name": "a"}, _ok("FAILURE")], "failed"),
    ],
)
def test_poll_github_reduces_checks(shim, hosts, rollup, checks):
    github, _ = hosts
    data = {"state": "OPEN", "mergeable": "MERGEABLE", "mergeStateStatus": "CLEAN"}
    data["statusCheckRollup"] = rollup
    shim.respond({"cli": "gh", "stdout": json.dumps(data)})
    assert github.poll(12)["checks"] == checks


@pytest.mark.parametrize(
    "mergeable,status,expected",
    [
        ("MERGEABLE", "CLEAN", "mergeable"),
        ("CONFLICTING", "CLEAN", "conflict"),
        ("MERGEABLE", "DIRTY", "conflict"),
        ("MERGEABLE", "CONFLICTING", "conflict"),
        ("UNKNOWN", "UNKNOWN", "unknown"),
        ("MERGEABLE", "BLOCKED", "blocked"),
        ("MERGEABLE", "BEHIND", "blocked"),
        (None, None, "blocked"),
    ],
)
def test_poll_github_mergeability(shim, hosts, mergeable, status, expected):
    github, _ = hosts
    data = {"state": "OPEN", "url": "u", "statusCheckRollup": []}
    if mergeable is not None:
        data["mergeable"] = mergeable
    if status is not None:
        data["mergeStateStatus"] = status
    shim.respond({"cli": "gh", "stdout": json.dumps(data)})
    poll = github.poll(12)
    assert poll["mergeable"] == expected
    assert poll["merge_detail"] == f"mergeStateStatus={status or 'UNKNOWN'}"


def test_poll_github_normalizes(shim, hosts):
    github, _ = hosts
    rollup = [_ok(), _ok("FAILURE", name="build")]
    data = {
        "state": "OPEN",
        "mergeable": "MERGEABLE",
        "mergeStateStatus": "BLOCKED",
        "url": "https://github.com/acme/app/pull/12",
        "headRefOid": "abc123",
        "statusCheckRollup": rollup,
    }
    threads = {"data": {"repository": {"pullRequest": {"reviewThreads": {
        "pageInfo": {"hasNextPage": False, "endCursor": None},
        "nodes": [{"isResolved": True}],
    }}}}}  # fmt: skip
    shim.respond(
        {"cli": "gh", "match": ["pr", "view", "12"], "stdout": json.dumps(data)},
        {"cli": "gh", "match": ["api", "graphql"], "stdout": json.dumps(threads)},
    )
    assert github.poll(12) == {
        "state": "OPEN",
        "checks": "failed",
        "mergeable": "blocked",
        "merge_detail": "mergeStateStatus=BLOCKED",
        "url": "https://github.com/acme/app/pull/12",
        "head_sha": "abc123",
        "raw": data,
        "reviews": 0,
    }
    call = shim.calls()[0]
    assert call["argv"] == [
        "pr",
        "view",
        "12",
        "--json",
        "state,mergeable,mergeStateStatus,url,statusCheckRollup,headRefOid",
        "-R",
        "acme/app",
    ]


@pytest.mark.parametrize("state", ["OPEN", "MERGED", "CLOSED"])
def test_poll_github_state_passes_through(shim, hosts, state):
    github, _ = hosts
    shim.respond({"cli": "gh", "stdout": json.dumps({"state": state})})
    poll = github.poll(1)
    assert poll["state"] == state
    assert (poll["url"], poll["head_sha"], poll["checks"]) == ("", "", "none")


def test_poll_github_missing_state_is_unknown(shim, hosts):
    github, _ = hosts
    shim.respond({"cli": "gh", "stdout": "{}"})
    assert github.poll(1)["state"] == "UNKNOWN"


def test_poll_github_cli_failure_raises(shim, hosts):
    github, _ = hosts
    shim.respond({"cli": "gh", "stderr": "not found", "exit": 1})
    with pytest.raises(common.RepoError, match="not found"):
        github.poll(1)


# --- poll: GitLab -----------------------------------------------------------


@pytest.mark.parametrize(
    "pipeline,checks",
    [
        (None, "none"),
        ({}, "none"),
        ({"id": 1, "status": "success"}, "passed"),
        ({"id": 1, "status": "skipped"}, "passed"),
        ({"id": 1, "status": "failed"}, "failed"),
        ({"id": 1, "status": "canceled"}, "failed"),
        ({"id": 1, "status": "running"}, "pending"),
        ({"id": 1, "status": "manual"}, "pending"),
        ({"id": 1, "status": "created"}, "pending"),
        ({"id": 1, "status": "something-new"}, "pending"),
    ],
)
def test_poll_gitlab_reduces_pipeline(shim, hosts, pipeline, checks):
    _, gitlab = hosts
    shim.respond(
        {"cli": "glab", "stdout": json.dumps({"state": "opened", "head_pipeline": pipeline})}
    )
    assert gitlab.poll(7)["checks"] == checks


@pytest.mark.parametrize(
    "detailed,conflicts,expected",
    [
        ("mergeable", False, "mergeable"),
        ("conflict", False, "conflict"),
        ("mergeable", True, "conflict"),
        ("checking", False, "unknown"),
        ("unchecked", False, "unknown"),
        ("not_approved", False, "blocked"),
        ("ci_must_pass", False, "blocked"),
        (None, None, "blocked"),
    ],
)
def test_poll_gitlab_mergeability(shim, hosts, detailed, conflicts, expected):
    _, gitlab = hosts
    data = {"state": "opened"}
    if detailed is not None:
        data["detailed_merge_status"] = detailed
    if conflicts is not None:
        data["has_conflicts"] = conflicts
    shim.respond({"cli": "glab", "stdout": json.dumps(data)})
    poll = gitlab.poll(7)
    assert poll["mergeable"] == expected
    assert poll["merge_detail"] == f"detailed_merge_status={detailed or 'unknown'}"


@pytest.mark.parametrize(
    "raw,state",
    [
        ("opened", "OPEN"),
        ("locked", "OPEN"),
        ("merged", "MERGED"),
        ("closed", "CLOSED"),
        ("x", "UNKNOWN"),
    ],
)
def test_poll_gitlab_state_map(shim, hosts, raw, state):
    _, gitlab = hosts
    shim.respond({"cli": "glab", "stdout": json.dumps({"state": raw})})
    assert gitlab.poll(7)["state"] == state


def test_poll_gitlab_normalizes(shim, hosts):
    _, gitlab = hosts
    data = {
        "iid": 7,
        "state": "opened",
        "detailed_merge_status": "not_approved",
        "has_conflicts": False,
        "web_url": "https://gitlab.com/grp/sub/proj/-/merge_requests/7",
        "sha": "def456",
        "head_pipeline": {"id": 77, "status": "running"},
    }
    shim.respond({"cli": "glab", "stdout": json.dumps(data)})
    assert gitlab.poll(7) == {
        "state": "OPEN",
        "checks": "pending",
        "mergeable": "blocked",
        "merge_detail": "detailed_merge_status=not_approved",
        "url": "https://gitlab.com/grp/sub/proj/-/merge_requests/7",
        "head_sha": "def456",
        "raw": data,
        "discussions": [],
        "reviews": 0,
    }
    assert shim.calls()[0]["argv"] == ["api", f"{GL_MR}/7"]


# --- failed_reasons ---------------------------------------------------------


def _gh_failed_poll(github, shim, rollup):
    shim.respond(
        {"cli": "gh", "match": ["run", "view", "555"], "stdout": LOG_150},
        {"cli": "gh", "match": ["run", "view", "666"], "stderr": "log gone", "exit": 1},
        {
            "cli": "gh",
            "match": ["pr", "view"],
            "stdout": json.dumps({"state": "OPEN", "statusCheckRollup": rollup}),
        },
    )
    return github.poll(12)


def _gl_failed_poll(gitlab, shim, jobs, pipeline=None):
    pipeline = pipeline or {"id": 77, "status": "failed"}
    shim.respond(
        {"cli": "glab", "match": ["projects/grp%2Fsub%2Fproj/jobs/9/trace"], "stdout": LOG_150},
        {
            "cli": "glab",
            "match": ["projects/grp%2Fsub%2Fproj/jobs/10/trace"],
            "stderr": "403 Forbidden",
            "exit": 1,
        },
        {
            "cli": "glab",
            "match": ["projects/grp%2Fsub%2Fproj/pipelines/77/jobs"],
            "stdout": json.dumps(jobs),
        },
        {
            "cli": "glab",
            "match": [f"{GL_MR}/7"],
            "stdout": json.dumps({"state": "opened", "head_pipeline": pipeline}),
        },
    )
    return gitlab.poll(7)


def test_failed_reasons_log_tails_both_hosts(shim, hosts):
    github, gitlab = hosts
    rollup = [
        _ok(name="lint"),
        _ok(
            "FAILURE",
            name="build",
            detailsUrl="https://github.com/acme/app/actions/runs/555/job/1",
        ),
    ]
    poll = _gh_failed_poll(github, shim, rollup)
    assert github.failed_reasons(poll) == [f"check 'build' failed:\n{TAIL_100}"]
    assert shim.calls()[-1]["argv"] == [
        "run",
        "view",
        "555",
        "--log-failed",
        "-R",
        "acme/app",
    ]

    jobs = [
        {"id": 8, "name": "lint", "status": "success"},
        {"id": 9, "name": "test", "status": "failed"},
    ]
    poll = _gl_failed_poll(gitlab, shim, jobs)
    assert gitlab.failed_reasons(poll) == [f"job 'test' failed:\n{TAIL_100}"]
    assert [c["argv"] for c in shim.calls()[-2:]] == [
        ["api", "projects/grp%2Fsub%2Fproj/pipelines/77/jobs"],
        ["api", "projects/grp%2Fsub%2Fproj/jobs/9/trace"],
    ]


def test_failed_reasons_short_log_kept_whole(shim, hosts):
    github, _ = hosts
    shim.respond(
        {"cli": "gh", "match": ["run", "view"], "stdout": "a\nb\n"},
        {
            "cli": "gh",
            "match": ["pr", "view"],
            "stdout": json.dumps(
                {
                    "state": "OPEN",
                    "statusCheckRollup": [
                        _ok("FAILURE", name="b", detailsUrl="/actions/runs/1/job/2")
                    ],
                }
            ),
        },
    )
    assert github.failed_reasons(github.poll(12)) == ["check 'b' failed:\na\nb"]


def test_failed_reasons_github_degrades_per_check(shim, hosts):
    github, _ = hosts
    rollup = [
        _ok("FAILURE", name="no-url"),
        {"context": "ext/ci", "state": "ERROR", "detailsUrl": "https://ci.example/1"},
        _ok("CANCELLED", name="gone", detailsUrl="https://github.com/a/b/actions/runs/666"),
        {"status": "COMPLETED", "conclusion": "TIMED_OUT"},
    ]
    poll = _gh_failed_poll(github, shim, rollup)
    assert github.failed_reasons(poll) == [
        "check 'no-url' failed:\nno run id found (detailsUrl=none)",
        "check 'unknown check' failed:\nno run id found (detailsUrl=https://ci.example/1)",
        "check 'gone' failed:\ncould not fetch log for run 666: log gone",
        "check 'unknown check' failed:\nno run id found (detailsUrl=none)",
    ]


def test_failed_reasons_gitlab_degrades_per_job(shim, hosts):
    _, gitlab = hosts
    jobs = [{"id": 10, "status": "failed"}, {"id": 9, "name": "test", "status": "failed"}]
    poll = _gl_failed_poll(gitlab, shim, jobs)
    assert gitlab.failed_reasons(poll) == [
        "job 'unknown job' failed:\ncould not fetch log for job 10: 403 Forbidden",
        f"job 'test' failed:\n{TAIL_100}",
    ]


def test_failed_reasons_gitlab_jobs_fetch_error_raises(shim, hosts):
    _, gitlab = hosts
    poll = _gl_failed_poll(gitlab, shim, [])
    shim.respond({"cli": "glab", "stderr": "500", "exit": 1})
    with pytest.raises(common.RepoError, match="500"):
        gitlab.failed_reasons(poll)


def test_failed_reasons_empty_unless_checks_failed(shim, hosts):
    github, gitlab = hosts
    poll = _gh_failed_poll(github, shim, [_ok()])
    assert github.failed_reasons(poll) == []
    poll = _gl_failed_poll(gitlab, shim, [], pipeline={"id": 77, "status": "success"})
    before = len(shim.calls())
    assert gitlab.failed_reasons(poll) == []
    assert len(shim.calls()) == before


# --- conflict_files ---------------------------------------------------------


def test_conflict_files(shim, hosts):
    github, gitlab = hosts
    files = {"files": [{"path": "a.py"}, {"path": "b/c.md"}, {"additions": 1}]}
    shim.respond({"cli": "gh", "stdout": json.dumps(files)})
    assert github.conflict_files(12) == ["a.py", "b/c.md"]
    assert shim.calls()[-1]["argv"] == ["pr", "view", "12", "--json", "files", "-R", "acme/app"]
    before = len(shim.calls())
    assert gitlab.conflict_files(7) == []
    assert len(shim.calls()) == before


def test_conflict_files_github_error_is_empty(shim, hosts):
    github, _ = hosts
    shim.respond({"cli": "gh", "stderr": "boom", "exit": 1})
    assert github.conflict_files(12) == []


# --- list_open --------------------------------------------------------------


def test_list_open_both_hosts(shim, hosts):
    github, gitlab = hosts
    prs = [
        {
            "number": 3,
            "url": "https://github.com/acme/app/pull/3",
            "title": "newer",
            "body": "fix it",
            "createdAt": "2026-10-03T00:00:00Z",
            "mergeable": "CONFLICTING",
            "mergeStateStatus": "DIRTY",
            "statusCheckRollup": [],
        },
        {
            "number": 1,
            "url": "https://github.com/acme/app/pull/1",
            "title": "older",
            "body": "",
            "createdAt": "2026-10-01T00:00:00Z",
            "mergeable": "MERGEABLE",
            "mergeStateStatus": "CLEAN",
            "statusCheckRollup": [_ok("FAILURE")],
        },
    ]
    mrs = [
        {
            "iid": 4,
            "web_url": "https://gitlab.com/grp/sub/proj/-/merge_requests/4",
            "title": "first",
            "description": "the body",
            "created_at": "2026-09-01T00:00:00Z",
            "detailed_merge_status": "mergeable",
            "has_conflicts": False,
            "head_pipeline": {"id": 1, "status": "canceled"},
        },
        {
            "iid": 5,
            "web_url": "https://gitlab.com/grp/sub/proj/-/merge_requests/5",
            "title": "second",
            "description": None,
            "created_at": "2026-09-02T00:00:00Z",
            "detailed_merge_status": "conflict",
            "has_conflicts": True,
        },
    ]
    shim.respond(
        {"cli": "gh", "stdout": json.dumps(prs)},
        {"cli": "glab", "stdout": json.dumps(mrs)},
    )
    assert github.list_open() == [
        {
            "n": 1,
            "url": "https://github.com/acme/app/pull/1",
            "title": "older",
            "body": "",
            "created": "2026-10-01T00:00:00Z",
            "checks": "failed",
            "mergeable": "mergeable",
            "raw": prs[1],
        },
        {
            "n": 3,
            "url": "https://github.com/acme/app/pull/3",
            "title": "newer",
            "body": "fix it",
            "created": "2026-10-03T00:00:00Z",
            "checks": "none",
            "mergeable": "conflict",
            "raw": prs[0],
        },
    ]
    assert gitlab.list_open() == [
        {
            "n": 4,
            "url": "https://gitlab.com/grp/sub/proj/-/merge_requests/4",
            "title": "first",
            "body": "the body",
            "created": "2026-09-01T00:00:00Z",
            "checks": "failed",
            "mergeable": "mergeable",
            "raw": mrs[0],
        },
        {
            "n": 5,
            "url": "https://gitlab.com/grp/sub/proj/-/merge_requests/5",
            "title": "second",
            "body": "",
            "created": "2026-09-02T00:00:00Z",
            "checks": "none",
            "mergeable": "conflict",
            "raw": mrs[1],
        },
    ]
    gh_call, gl_call = shim.calls()
    assert gh_call["argv"][:4] == ["pr", "list", "--state", "open"]
    fields = gh_call["argv"][gh_call["argv"].index("--json") + 1].split(",")
    assert set(fields) >= {
        "number",
        "url",
        "title",
        "body",
        "createdAt",
        "mergeable",
        "statusCheckRollup",
    }
    assert gh_call["argv"][-2:] == ["-R", "acme/app"]
    assert gl_call["argv"] == [
        "api",
        f"{GL_MR}?state=opened&order_by=created_at&sort=asc&per_page=100",
    ]


def test_list_open_empty_both_hosts(shim, hosts):
    github, gitlab = hosts
    shim.respond({"cli": "gh", "stdout": "[]"}, {"cli": "glab", "stdout": "null"})
    assert github.list_open() == []
    assert gitlab.list_open() == []


def test_list_open_github_lists_more_than_the_default_page(shim, hosts):
    github, _ = hosts
    shim.respond({"cli": "gh", "stdout": "[]"})
    github.list_open()
    argv = shim.calls()[0]["argv"]
    assert int(argv[argv.index("--limit") + 1]) >= 100
