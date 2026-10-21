"""ticket.py graph --todo: the epic blocker graph and its contract-order checks (D8).

epic_graph is the one blocker graph; edges come from each epic's `blockers`, resolved with
ticket.resolve_blocker. graph --todo reports blocker cycles and contract owners scheduled
after (or not before) their consumers.
"""

import sys
from pathlib import Path

_T = None
OPEN = ("todo", "in-progress")


def _contracts():
    # contract.py is a sibling command module; load its reader once.
    if "ticket_cmds.contract" in sys.modules:
        return sys.modules["ticket_cmds.contract"].load_contracts
    import importlib.util

    path = Path(__file__).with_name("contract.py")
    spec = importlib.util.spec_from_file_location("ticket_cmds._contract_reader", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.load_contracts


def _find_cycles(slugs: list, deps: dict) -> list:
    """Each distinct cycle once, as a closed path [a, b, a], rotated to start at its least slug."""
    seen, cycles, stack, on = set(), [], [], set()

    def visit(n):
        if n in on:
            cyc = stack[stack.index(n) :]
            i = cyc.index(min(cyc))
            cyc = cyc[i:] + cyc[:i]
            if cyc + [cyc[0]] not in cycles:
                cycles.append(cyc + [cyc[0]])
            return
        if n in seen:
            return
        seen.add(n)
        on.add(n)
        stack.append(n)
        for m in sorted(deps.get(n, ())):
            visit(m)
        stack.pop()
        on.discard(n)

    for n in sorted(slugs):
        visit(n)
    return cycles


def epic_graph(root) -> dict:
    """{epics: {slug: phase}, edges: [[epic, blocker]], cycles: [[a, b, a]], runnable: [slug]}.

    An edge [a, b] means epic a is blocked by epic b. Blockers that name no epic are ignored
    for edges and cycles, but keep a todo epic from being runnable."""
    epics = _T._epics(Path(root))
    deps = {s: [] for s in epics}
    unresolved = set()
    for s, e in epics.items():
        for b in e.meta.get("blockers", []):
            found = _T.resolve_blocker(b, epics)
            if found:
                deps[s].append(found.slug)
            else:
                unresolved.add(s)
    edges = [[s, b] for s in sorted(deps) for b in deps[s]]
    runnable = sorted(
        s
        for s, e in epics.items()
        if e.phase == "todo"
        and s not in unresolved
        and all(epics[b].phase == "done" for b in deps[s])
    )
    return {
        "epics": {s: e.phase for s, e in epics.items()},
        "edges": edges,
        "cycles": _find_cycles(list(epics), deps),
        "runnable": runnable,
    }


def _closure(start: str, deps: dict) -> set:
    out, todo = set(), [start]
    while todo:
        for m in deps.get(todo.pop(), ()):
            if m not in out:
                out.add(m)
                todo.append(m)
    return out


def graph_problems(root) -> list:
    g = epic_graph(root)
    phase = g["epics"]
    live = {s for s, p in phase.items() if p in OPEN}
    deps = {s: [] for s in phase}
    for a, b in g["edges"]:
        deps[a].append(b)
    problems = [f"cycle: {' -> '.join(c)}" for c in g["cycles"] if all(n in live for n in c)]
    uses = {}
    for t in _T.scan(Path(root)):
        if t.kind == "task":
            for n in t.meta.get("uses", []):
                uses.setdefault(n, set()).add(t.epic)
    for c in _contracts()(root):
        owner = c["owner"]
        if owner not in live:
            continue
        consumers = sorted(
            (set(c.get("consumers", [])) | uses.get(c["name"], set())) & live - {owner}
        )
        for k in consumers:
            if k in _closure(owner, deps):
                problems.append(f"contract {c['name']}: owner {owner} comes after consumer {k}")
            elif owner not in _closure(k, deps):
                problems.append(
                    f"contract {c['name']}: consumer {k} is not blocked by owner {owner}"
                )
    return problems


def cmd_graph(a) -> int:
    if not a.todo:
        raise _T.TicketError("graph needs --todo")
    problems = graph_problems(a.root)
    for p in problems:
        print(p)
    if not problems:
        print("graph: ok")
    return 1 if problems else 0


def register(sub, t) -> None:
    global _T
    _T = t
    sp = sub.add_parser("graph")
    sp.set_defaults(fn=cmd_graph)
    sp.add_argument(
        "--todo",
        action="store_true",
        help="check todo and in-progress epics: blocker cycles, contract order",
    )
