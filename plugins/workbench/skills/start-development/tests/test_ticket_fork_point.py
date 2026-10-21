"""apply-run persists each task's fork point; derive_tasks exports it."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_ticket_apply_run_fixes as fx  # noqa: E402
from test_ticket_run import meta_of, ticket  # noqa: E402

repo = fx.repo
root = fx.root
apply = fx.apply
body_of = fx.body_of
setup = fx.setup


def ret(task_extra=None, landed=None):
    t = {"id": "t-a", "branch": "b", "clean": True, "verified": True}
    t["verification"] = {"head": "h1"}
    t.update(task_extra or {})
    r = {"run": "r1", "tasks": [t]}
    if landed is not None:
        r["landed"] = landed
    return r


def test_fork_point_from_task_entry(repo, root):
    ep = setup(repo, root, "t-a")
    apply(repo, root, ep, ret({"forkPoint": "aaa111"}))
    assert meta_of(root, ep, "t-a")["fork_point"] == "aaa111"


def test_apply_run_records_fork_point(repo, root):
    ep = setup(repo, root, "t-a")
    apply(repo, root, ep, ret(landed=[{"id": "t-a", "forkPoint": "bbb222", "head": "h1"}]))
    assert meta_of(root, ep, "t-a")["fork_point"] == "bbb222"


def test_task_entry_wins_over_landed(repo, root):
    ep = setup(repo, root, "t-a")
    apply(repo, root, ep, ret({"forkPoint": "aaa111"}, [{"id": "t-a", "forkPoint": "bbb222"}]))
    assert meta_of(root, ep, "t-a")["fork_point"] == "aaa111"


def test_apply_run_keeps_fork_point_when_absent(repo, root):
    ep = setup(repo, root, "t-a")
    apply(repo, root, ep, ret({"forkPoint": "aaa111"}))
    apply(repo, root, ep, ret())
    assert meta_of(root, ep, "t-a")["fork_point"] == "aaa111"


def test_apply_twice_is_idempotent(repo, root):
    ep = setup(repo, root, "t-a")
    apply(repo, root, ep, ret({"forkPoint": "aaa111"}))
    before = body_of(root, ep, "t-a")
    apply(repo, root, ep, ret({"forkPoint": "aaa111"}))
    assert body_of(root, ep, "t-a") == before


def test_derive_tasks_exports_fork_point(repo, root):
    ep = setup(repo, root, "t-a")
    d = root / "in-progress" / ep
    assert ticket.derive_tasks(d)[0]["forkPoint"] == ""
    apply(repo, root, ep, ret({"forkPoint": "aaa111"}))
    assert ticket.derive_tasks(d)[0]["forkPoint"] == "aaa111"


def test_args_carry_fork_point(repo, root):
    from ticket_cmds.args import build_args

    ep = setup(repo, root, "t-a", "t-b")
    d = root / "in-progress" / ep
    apply(repo, root, ep, ret({"forkPoint": "aaa111", "verified": False, "clean": False}))
    tasks = {x["id"]: x for x in build_args(d)["tasks"]}
    assert tasks["t-a"]["forkPoint"] == "aaa111"
    assert tasks["t-b"]["forkPoint"] == ""
