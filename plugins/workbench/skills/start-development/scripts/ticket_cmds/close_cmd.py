"""ticket.py close: land the epic's integration branch on main, tested, in a fixed order.

Meta mode: tasks commit directly on <epic>, so there is no per-task landing gate. merge.py
rebases <epic> onto <base> in the integration tree, runs --verify on the rebased tip there and
fast-forwards <base> in the main checkout only when it passed; --verify then runs on <base>
itself. close.json records the result and main's pre-fast-forward SHA. Component mode moves
nothing; the epic closes through the phase 6 MR.
"""

import datetime
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VERIFY_EXIT = 4
CLOSE_JSON = "close.json"


def _recorded(epic_dir: Path) -> dict | None:
    p = epic_dir / CLOSE_JSON
    return json.loads(p.read_text()) if p.is_file() else None


def _write(epic_dir: Path, rec: dict, t, root: Path) -> None:
    path = epic_dir / CLOSE_JSON
    path.write_text(json.dumps(rec, indent=2) + "\n")
    t.commit_ticket_change(epic_dir.name, "close", [path], root)
    print(json.dumps(rec, indent=2))


def run(a, t) -> int:
    root = Path(a.root)
    t.require_main_checkout(root)
    epic_dir = t.resolve_epic(a.epic, root)
    name = epic_dir.name
    wb, mm = t._workbench(root), t._merge()
    prior = _recorded(epic_dir)
    done_before = prior and prior.get("mainVerify", {}).get("passed")
    if done_before and (not t._branch_exists(wb, name) or mm.merged_into(wb, name, a.base)):
        print(json.dumps(prior, indent=2))
        return 0

    t.review_gate(epic_dir, "close")
    component = any(repo for repo, _ in t._integration_plan(root, epic_dir))
    if not component and not t._branch_exists(wb, name):
        raise t.TicketError(f"epic {name!r} has no integration branch {name!r} to close")
    if component:
        print(f"component mode: close through the phase 6 MR from {name}")
        return 0

    try:
        res = mm.merge_back(
            name=name, base=a.base, keep=True, suites=False, verify=a.verify, start=wb
        )
    except mm.WorktreeError as e:
        raise t.TicketError(str(e)) from e
    ver = res["verification"]
    # a rerun after a failed main verify: <epic> is already in <base>, so merge_back verified <base>
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
        "epic": name,
        "base": a.base,
        "baseBefore": before,
        "baseAfter": prior["baseAfter"] if rerun else res["baseAfter"],
        "epicTip": t._git(wb, "rev-parse", name).stdout.strip(),
        "integrationVerify": prior["integrationVerify"]
        if rerun
        else {"command": a.verify, "passed": True},
        "mainVerify": {"command": a.verify, "passed": passed, "tail": tail},
        "at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
    }
    _write(epic_dir, rec, t, root)
    if not passed:
        print(
            f"ticket.py: verify failed on {a.base!r} after the fast-forward; {a.base!r} was at "
            f"{before} before the close",
            file=sys.stderr,
        )
        return VERIFY_EXIT
    print(f"next: ticket.py move {name} done")
    return 0


def register(sub, t) -> None:
    sp = sub.add_parser(
        "close",
        help="rebase the epic onto base, verify it there, fast-forward base, verify base",
    )
    sp.set_defaults(fn=lambda a: run(a, t))
    sp.add_argument("epic")
    sp.add_argument("--verify", required=True, help="the repo's full suite and lint command")
    sp.add_argument("--base", default="main")
