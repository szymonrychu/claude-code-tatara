"""ticket.py roadmap: the epic graph, which epics can run now, one status line per epic (D4).

An epic is runnable when it is in todo, its blockers are all done (ticket.resolve_blocker) and its
open tasks' files are disjoint from the open tasks of every in-progress epic, after the repo's
overlapIgnore. Runnable epics that overlap each other are all listed with `overlaps`; the
`runnable:` line keeps the first of each overlapping group by slug order.
"""

import importlib.util
import json
from pathlib import Path

_T = None
_CACHE = {}


def _load(name: str, path: Path):
    if name not in _CACHE:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _CACHE[name] = mod
    return _CACHE[name]


def _edges(root: Path) -> list:
    """[epic, blocker] pairs from each epic's `blockers`, resolved with ticket.resolve_blocker."""
    epics = _T._epics(root)
    return [
        [s, found.slug]
        for s in sorted(epics)
        for b in epics[s].meta.get("blockers", [])
        if (found := _T.resolve_blocker(b, epics))
    ]


def _wb():
    return _load(
        "workbench_lib", Path(__file__).resolve().parents[4] / "scripts" / "lib" / "workbench.py"
    )


def _open_files(root: Path, epic: str, tickets: list, ignore_for) -> dict:
    """{file: repo} of the epic's tasks that are neither done nor merged into main, minus
    ignored files."""
    out = {}
    for t in tickets:
        if t.kind != "task" or t.epic != epic or t.meta.get("status") == "done":
            continue
        left = [f for f in t.meta.get("files", []) if not ignore_for(t.meta.get("repo", ""), f)]
        for f in _T._counting_overlaps(root, t, left) if left else []:
            out[f] = t.meta.get("repo", "")
    return out


def build(root) -> dict:
    root = Path(root)
    edges = _edges(root)
    wb = _wb()
    epics = _T._epics(root)
    tickets = _T.scan(root)
    configs = {}

    def ignore_for(repo, f):
        if repo not in configs:
            configs[repo] = wb.config_for_repo(root, repo)["overlapIgnore"]
        return wb.overlap_ignored(f, configs[repo])

    files = {s: _open_files(root, s, tickets, ignore_for) for s in epics}
    deps = {s: [] for s in epics}
    for a, b in edges:
        deps[a].append(b)

    def clash(a, b):
        shared = sorted(set(files[a]) & set(files[b]))
        return shared[0] if shared else None

    rows = []
    for s, e in sorted(epics.items()):
        if e.phase not in ("todo", "in-progress"):
            continue
        mine = [t for t in tickets if t.kind == "task" and t.epic == s]
        done = sum(1 for t in mine if t.meta.get("status") == "done")
        raw = list(e.meta.get("blockers", []))
        unresolved = [b for b in raw if _T.resolve_blocker(b, epics) is None]
        waiting = sorted({b for b in deps[s] if epics[b].phase != "done"} | set(unresolved))
        rows.append(
            {
                "epic": s,
                "phase": e.phase,
                "stage": e.meta.get("stage", "") if e.phase == "in-progress" else "",
                "done": done,
                "total": len(mine),
                "blockers": deps[s] + unresolved,
                "state": "",
                "_wait": waiting,
            }
        )
    by = {r["epic"]: r for r in rows}
    running = [r["epic"] for r in rows if r["phase"] == "in-progress"]
    ready = []
    for r in rows:
        s = r["epic"]
        if r["phase"] == "in-progress":
            r["state"] = "running"
        elif r["_wait"]:
            r["state"] = "waiting on " + ", ".join(r["_wait"])
        else:
            hit = next(((o, clash(s, o)) for o in running if clash(s, o)), None)
            if hit:
                r["state"] = f"overlaps {hit[0]}: {hit[1]}"
            else:
                ready.append(s)
    runnable = []
    for s in ready:
        hit = next(((o, clash(s, o)) for o in ready if o != s and clash(s, o)), None)
        by[s]["state"] = f"overlaps {hit[0]}: {hit[1]}" if hit else "runnable"
        if not any(clash(s, o) for o in runnable):
            runnable.append(s)
    for r in rows:
        del r["_wait"]
    return {"epics": rows, "edges": edges, "runnable": runnable}


def cmd_roadmap(a) -> int:
    data = build(a.root)
    if a.json:
        print(json.dumps(data, indent=2))
        return 0
    for r in data["epics"]:
        phase = r["phase"] + (f"/{r['stage']}" if r["stage"] else "")
        print(
            f"{r['epic']} {phase} {r['done']}/{r['total']} tasks "
            f"blockers={','.join(r['blockers'])} {r['state']}"
        )
    live = {r["epic"] for r in data["epics"]}
    for x, y in data["edges"]:
        if x in live:
            print(f"{x} <- {y}")
    print("runnable: " + ", ".join(data["runnable"]))
    return 0


def register(sub, t) -> None:
    global _T
    _T = t
    sp = sub.add_parser("roadmap")
    sp.set_defaults(fn=cmd_roadmap)
    sp.add_argument("--json", action="store_true", help="print the same data as one JSON object")
