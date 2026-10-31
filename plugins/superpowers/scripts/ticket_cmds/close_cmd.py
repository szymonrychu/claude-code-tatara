"""ticket.py close: land the plan branch on main, tested, in a fixed order, then move the plan
to done.

Meta mode: merge.py rebases <plan> onto <base> in the plan tree, runs --verify on the rebased
tip there and fast-forwards <base> in the main checkout only when it passed; --verify then runs
on <base> itself. close.json records the result and main's pre-fast-forward SHA. On a pass the
plan dir moves to done and close.json, retro.md and the move are committed together, then the
plan's tree and branch are swept. Component mode moves nothing; the plan closes through its MR,
then `ticket.py move <plan> done`.
"""

import datetime
import json
import sys
from pathlib import Path

VERIFY_EXIT = 4
CLOSE_JSON = "close.json"


def _recorded(plan_dir: Path) -> dict | None:
    p = plan_dir / CLOSE_JSON
    return json.loads(p.read_text()) if p.is_file() else None


def _write(plan_dir: Path, rec: dict) -> bool:
    """Write close.json; True when its content changed."""
    path = plan_dir / CLOSE_JSON
    text = json.dumps(rec, indent=2) + "\n"
    changed = not path.is_file() or path.read_text() != text
    path.write_text(text)
    print(json.dumps(rec, indent=2))
    return changed


def run(a, t) -> int:
    root = Path(a.root)
    t.require_main_checkout(root)
    plan_dir = t.resolve_plan(a.plan, root)
    name = plan_dir.name
    prior = _recorded(plan_dir)
    if t.phase_of(plan_dir) == "done" and prior and prior.get("mainVerify", {}).get("passed"):
        print(json.dumps(prior, indent=2))
        return 0

    t.retro_gate(plan_dir, "close")
    if any(repo for repo, _ in t.tree_layout(root, plan_dir)):
        print(f"component mode: {name} closes through its MR; then run ticket.py move {name} done")
        return 0
    wb, mm = t._workbench(root), t._merge()
    if not t._branch_exists(wb, name):
        raise t.TicketError(f"plan {name!r} has no branch {name!r} to close")

    try:
        res = mm.merge_back(
            name=name, base=a.base, keep=True, suites=False, verify=a.verify, start=wb
        )
    except mm.WorktreeError as e:
        raise t.TicketError(str(e)) from e
    ver = res["verification"]
    # a rerun after a failed main verify: <plan> is already in <base>, so merge_back verified <base>
    rerun = bool(prior) and res.get("contained", False)
    if not ver["passed"] and not rerun:
        print("\n".join(ver["tail"]), file=sys.stderr)
        print(
            f"ticket.py: verify failed on the rebased {name!r} tip; {a.base!r} did not move "
            f"(still at {res['baseBefore']})",
            file=sys.stderr,
        )
        return VERIFY_EXIT
    # a rerun after a failed main verify keeps the commit main was at before the first close
    before = prior["baseBefore"] if rerun else res["baseBefore"]
    if rerun:
        passed, tail = ver["passed"], ver["tail"]
    else:
        passed, tail = mm._run_verify(a.verify, mm.target_tree(wb, a.base))
    rec = {
        "plan": name,
        "base": a.base,
        "baseBefore": before,
        "baseAfter": prior["baseAfter"] if rerun else res["baseAfter"],
        "planTip": t._git(wb, "rev-parse", name).stdout.strip(),
        "integrationVerify": prior["integrationVerify"]
        if rerun
        else {"command": a.verify, "passed": True},
        "mainVerify": {"command": a.verify, "passed": passed, "tail": tail},
        "at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
    }
    changed = _write(plan_dir, rec)
    if not passed:
        if changed:
            t.commit_ticket_change(name, "close verify failed", [plan_dir / CLOSE_JSON], root)
        print(
            f"ticket.py: verify failed on {a.base!r} after the fast-forward; {a.base!r} was at "
            f"{before} before the close",
            file=sys.stderr,
        )
        return VERIFY_EXIT
    return t.finish(root, plan_dir, "close", a.base)


def register(sub, t) -> None:
    sp = sub.add_parser(
        "close",
        help="rebase the plan onto base, verify it there, fast-forward base, verify base, "
        "move the plan to done",
    )
    sp.set_defaults(fn=lambda a: run(a, t))
    sp.add_argument("plan")
    sp.add_argument("--verify", required=True, help="the repo's full suite and lint command")
    sp.add_argument("--base", default="main")
