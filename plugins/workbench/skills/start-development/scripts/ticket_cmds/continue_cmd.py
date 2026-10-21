"""ticket.py continue: accept-and-continue after a run, as one command (D10).

Composes apply-run, rule, worktrees --refresh, facts and args; nothing is re-implemented
here. The merge is done by the agent: when an accepted task that a still-open task depends
on has no merge yet, continue prints `MERGE <task> --name <epic>--<task> --repo <repo>`
lines and exits 2 before writing args. Steps 1 and 2 are idempotent, so rerunning after the
merge repeats them safely.
"""

import argparse
import importlib.util
import json
import sys
import tempfile
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
MERGE_EXIT = 2


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules.setdefault(name, mod)
    spec.loader.exec_module(mod)
    return mod


def _heartbeat():
    return _load(
        "heartbeat_continue", PLUGIN_ROOT / "skills" / "heartbeat" / "scripts" / "heartbeat.py"
    )


def _sibling(stem: str):
    return _load(f"ticket_cmds_continue_{stem}", HERE / f"{stem}.py")


def _last_return(a, t):
    """(return dict, run dir or None) from --return or --run; (None, None) with neither."""
    if a.run_return:
        p = Path(a.run_return)
        if not p.is_file():
            raise t.TicketError(f"return file not found: {p}")
        return json.loads(p.read_text()), None
    if not a.run:
        return None, None
    rec, journal = _heartbeat().run_paths(a.run)
    if rec is None:
        raise t.TicketError(f"run {a.run} has no record under the projects dir")
    data = json.loads(Path(rec).read_text())
    if data.get("status") != "completed" or not isinstance(data.get("result"), dict):
        raise t.TicketError(
            f"run {a.run} ended {data.get('status', 'unknown')} with no return to apply"
        )
    return data["result"], (journal.parent if journal else None)


def _verified(ret, files, accept, t):
    """Fail on the first accepted task that has no verified head, before anything is written."""
    heads = {
        str(x.get("id")): (x.get("verification") or {}).get("head")
        for x in (ret or {}).get("tasks", [])
    }
    for task in accept:
        if not (heads.get(task) or t._read_doc(files[task]).meta.get("verified_head")):
            raise t.TicketError(
                f"cannot accept {task!r}: unverified (no verified head); a ruling cannot "
                "stand in for verification"
            )


def _apply(a, t, root, ret, run_dir):
    if ret is None:
        return
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "return.json"
        p.write_text(json.dumps(ret))
        t.cmd_apply_run(
            argparse.Namespace(
                root=str(root),
                epic=a.epic,
                run_return=str(p),
                run_dir=str(run_dir) if run_dir else None,
            )
        )


def _rule(epic_dir, files, accept, reason, t, root):
    rule = _sibling("rule")
    today = rule.datetime.datetime.now(rule.datetime.timezone.utc).strftime("%Y-%m-%d")
    seen = {(x["task"], x.get("reason")) for x in rule.read_rulings(epic_dir) if x.get("accept")}
    changed: list[Path] = []
    for task in accept:
        doc = t._read_doc(files[task])
        recorded = (task, reason) in seen
        line = f"- {today} accepted: {reason}"
        body = doc.body if recorded or line in doc.body else rule._ruling_body(t, doc.body, line)
        t._write_task(files[task], t.Doc(doc.meta, body), changed, status="done")
        if not recorded:
            rule.write_ruling(epic_dir, task, True, reason)
            changed.append(epic_dir / rule.RULINGS)
        print(f"{task}: accepted")
    if changed:
        t.commit_ticket_change(epic_dir.name, "continue", sorted(set(changed)), root)


def _merge_gate(epic_dir, accept, base, t, root) -> list[str]:
    """MERGE lines for done tasks an open task depends on whose branch is not in base."""
    metas = {p.stem: t._read_doc(p).meta for p in t._task_files(epic_dir)}
    open_ids = {k for k, m in metas.items() if m.get("status") != "done"}
    needed = {d for x in t.derive_tasks(epic_dir) if x["id"] in open_ids for d in x["dependsOn"]}
    lines = []
    for task in sorted(needed):
        m = metas.get(task)
        if not m or m.get("status") != "done":
            continue
        if not t._task_merged(
            t._task_src(root, m), m.get("branch", ""), m.get("verified_head", ""), base
        ):
            lines.append(f"MERGE {task} --name {epic_dir.name}--{task} --repo {m.get('repo', '')}")
    return lines


def _refresh_facts(root: Path, t) -> None:
    out = root / "facts.md"
    if out.is_file():
        facts = _sibling("facts")
        facts._T = t
        out.write_text(facts.build(root))


def run(a, t) -> int:
    root = Path(a.root)
    t.require_main_checkout(root)
    epic_dir = t.resolve_epic(a.epic, root)
    accept = t._csv(a.accept)
    if accept and not (a.reason or "").strip():
        raise t.TicketError("continue --accept needs a non-empty --reason")
    files = {p.stem: p for p in t._task_files(epic_dir)}
    unknown = sorted(set(accept) - set(files))
    if unknown:
        raise t.TicketError(f"unknown task(s) in {epic_dir.name!r}: {', '.join(unknown)}")
    if a.run and a.run_return:
        raise t.TicketError("continue takes --run or --return, not both")
    ret, run_dir = _last_return(a, t)
    _verified(ret, files, accept, t)
    _apply(a, t, root, ret, run_dir)
    _rule(epic_dir, files, accept, a.reason, t, root)
    gate = _merge_gate(epic_dir, accept, a.base, t, root)
    if gate:
        print("\n".join(gate))
        print("merge the tasks above (worktree-merger), then rerun continue", file=sys.stderr)
        return MERGE_EXIT
    t.cmd_worktrees(argparse.Namespace(root=str(root), epic=a.epic, base=a.base, refresh=True))
    _refresh_facts(root, t)
    script = _sibling("args").write_args_and_copy(epic_dir, a.out_dir, a.context_pack, t)
    print("arm the heartbeat once the run starts: heartbeat.py --run <runId>")
    print(script)
    return 0


def register(sub, t) -> None:
    sp = sub.add_parser(
        "continue",
        help="apply the last return, record rulings, refresh, and write the next run's args",
    )
    sp.set_defaults(fn=lambda a: run(a, t))
    sp.add_argument("epic")
    sp.add_argument("--out-dir", required=True)
    sp.add_argument("--accept", default="", help="comma-separated task ids to accept")
    sp.add_argument("--reason", default="")
    sp.add_argument("--run", default=None, help="run id: its record supplies the return")
    sp.add_argument("--return", dest="run_return", default=None, help="return.json to apply")
    sp.add_argument("--context-pack", default=None)
    sp.add_argument("--base", default="main")
