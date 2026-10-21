"""apply-run writes statuses that match what happened; discovered tasks export."""

import datetime
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_ticket_run as base  # noqa: E402
from test_ticket_run import cli, commit_all, meta_of, mk_epic, mk_task  # noqa: E402

ticket = base.ticket
git = base.git


@pytest.fixture
def repo(tmp_path):
    r = tmp_path / "proj"
    r.mkdir()
    git(r, "init", "-b", "main")
    git(r, "config", "user.email", "t@t")
    git(r, "config", "user.name", "t")
    (r / "a.py").write_text("x = 1\n")
    git(r, "add", ".")
    git(r, "commit", "-m", "init")
    return r


@pytest.fixture
def root(repo):
    return repo / "docs" / "plans"


def setup(repo, root, *names):
    ep = mk_epic(root)
    for t in names:
        mk_task(root, ep, t)
    commit_all(repo)
    assert cli("move", ep, "in-progress", "--root", root).returncode == 0
    return ep


def apply(repo, root, ep, ret):
    rj = repo / "return.json"
    rj.write_text(json.dumps(ret))
    r = cli("apply-run", ep, rj, "--root", root)
    assert r.returncode == 0, r.stderr
    return r


def body_of(root, ep, slug):
    return (root / "in-progress" / ep / "tasks" / f"{slug}.md").read_text()


def test_process_only_gate_repeat_is_done(repo, root):
    ep = setup(repo, root, "t-proc")
    apply(
        repo,
        root,
        ep,
        {
            "run": "r1",
            "tasks": [
                {
                    "id": "t-proc",
                    "branch": "b",
                    "clean": False,
                    "processOnly": True,
                    "verified": True,
                    "verification": {"head": "def456"},
                    "stopped": "gate-repeat",
                }
            ],
            "escalated": [{"id": "t-proc", "reason": "gate-repeat", "findings": []}],
        },
    )
    assert meta_of(root, ep, "t-proc")["status"] == "done"


def test_unverified_process_only_is_not_done(repo, root):
    ep = setup(repo, root, "t-proc")
    apply(
        repo,
        root,
        ep,
        {
            "run": "r1",
            "tasks": [
                {
                    "id": "t-proc",
                    "clean": False,
                    "processOnly": True,
                    "verified": False,
                    "verification": None,
                    "stopped": "gate-repeat",
                }
            ],
        },
    )
    assert meta_of(root, ep, "t-proc")["status"] == "in-progress"


def test_dependency_failed_stays_todo_with_note(repo, root):
    ep = setup(repo, root, "t-dep", "t-wait", "t-other")
    apply(
        repo,
        root,
        ep,
        {
            "run": "r2",
            "tasks": [
                {
                    "id": "t-wait",
                    "clean": False,
                    "verified": False,
                    "verification": None,
                    "stopped": "dependency-failed",
                    "impl": None,
                },
                {
                    "id": "t-other",
                    "clean": False,
                    "verified": True,
                    "verification": {"head": "1"},
                    "stopped": "round-cap",
                },
            ],
            "escalated": [
                {
                    "id": "t-wait",
                    "reason": "dependency-failed",
                    "waitingOn": ["t-dep"],
                    "findings": [],
                },
                {"id": "t-other", "reason": "round-cap", "findings": []},
            ],
        },
    )
    assert meta_of(root, ep, "t-wait")["status"] == "todo"
    today = datetime.date.today().isoformat()
    assert f"- {today} run r2: dependency-failed on t-dep" in body_of(root, ep, "t-wait")
    assert meta_of(root, ep, "t-other")["status"] == "escalated"
    assert "dependency-failed on" not in body_of(root, ep, "t-other")
    # re-apply does not duplicate the line
    apply(
        repo,
        root,
        ep,
        {
            "run": "r2",
            "tasks": [
                {"id": "t-wait", "clean": False, "verified": False, "stopped": "dependency-failed"}
            ],
            "escalated": [
                {
                    "id": "t-wait",
                    "reason": "dependency-failed",
                    "waitingOn": ["t-dep"],
                    "findings": [],
                }
            ],
        },
    )
    assert body_of(root, ep, "t-wait").count("dependency-failed on t-dep") == 1


def test_real_escalation_stays_escalated(repo, root):
    ep = setup(repo, root, "t-mix")
    apply(
        repo,
        root,
        ep,
        {
            "run": "r3",
            "tasks": [{"id": "t-mix", "clean": False, "verified": False, "stopped": "round-cap"}],
            "escalated": [
                {"id": "t-mix", "reason": "dependency-failed", "findings": []},
                {"id": "t-mix", "reason": "round-cap", "findings": []},
            ],
        },
    )
    assert meta_of(root, ep, "t-mix")["status"] == "escalated"


def test_discovered_task_exports(repo, root):
    ep = setup(repo, root, "t-src")
    apply(
        repo,
        root,
        ep,
        {
            "run": "r4",
            "tasks": [
                {"id": "t-src", "clean": True, "verified": True, "verification": {"head": "1"}}
            ],
            "discovered": [
                {
                    "taskId": "t-src",
                    "what": "Fix the flaky parser",
                    "where": "lib/parser.py",
                    "why": "outside my files",
                }
            ],
        },
    )
    body = body_of(root, ep, "fix-the-flaky-parser")
    secs = ticket._sections(body)
    assert "Fix the flaky parser" in secs["Requirement"]
    assert "lib/parser.py" in secs["Requirement"] and "outside my files" in secs["Requirement"]
    assert (
        secs["Acceptance conditions"].strip()
        == "- AC1: Fix the flaky parser at lib/parser.py is resolved [evidence: judgement]"
    )
    for name in ("Interfaces", "Expected outcome", "Steps", "Notes"):
        assert secs[name].strip(), name
    assert "Fix the flaky parser" in secs["Interfaces"] + secs["Expected outcome"]
    r = cli("tasks", ep, "--root", root)
    assert r.returncode == 0, r.stderr
    t = {x["id"]: x for x in json.loads(r.stdout)}["fix-the-flaky-parser"]
    assert t["ac"][0]["evidence"]["kind"] == "judgement"


def test_discovered_task_has_no_template_text(repo, root):
    ep = setup(repo, root, "t-src")
    apply(
        repo,
        root,
        ep,
        {
            "run": "r5",
            "tasks": [
                {"id": "t-src", "clean": True, "verified": True, "verification": {"head": "1"}}
            ],
            "discovered": [
                {
                    "taskId": "t-src",
                    "what": "Fix the flaky parser",
                    "where": "lib/parser.py",
                    "why": "outside my files",
                }
            ],
        },
    )
    body = body_of(root, ep, "fix-the-flaky-parser")
    secs = ticket._sections(body)
    guidance = ticket._template_sections()
    for name in ("Interfaces", "Expected outcome", "Steps", "Notes"):
        assert secs[name].strip() != guidance[name].strip(), name
        assert guidance[name].strip() not in body, name
    for text in (
        "Signatures, schemas and contracts",
        "What is true and observable",
        "Test first. One step per bullet",
        "Context the implementer needs",
    ):
        assert text not in body, text
    assert "{{" not in body
