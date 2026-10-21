"""ticket.py contract add/use/list: the cross-epic contracts registry (D8).

One docs/plans/contracts.json per plans root: a JSON array of
{name, kind, owner, file, consumers, note}. load_contracts is the one reader; every
mutation rewrites only that file.
"""

import json
from pathlib import Path

FILE = "contracts.json"
_T = None


def registry_path(root) -> Path:
    return Path(root) / FILE


def load_contracts(root) -> list:
    p = registry_path(root)
    return json.loads(p.read_text()) if p.is_file() else []


def _save(root, contracts: list) -> Path:
    p = registry_path(root)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(contracts, indent=2) + "\n")
    return p


def _csv(s) -> list:
    return [x.strip() for x in (s or "").split(",") if x.strip()]


def _merge(old: list, new: list) -> list:
    return list(old) + [x for x in new if x not in old]


def _find(contracts: list, name: str):
    return next((c for c in contracts if c["name"] == name), None)


def cmd_add(a) -> int:
    root = Path(a.root)
    _T.require_main_checkout(root)
    contracts = load_contracts(root)
    cur = _find(contracts, a.name)
    if cur and cur["owner"] != a.owner:
        raise _T.TicketError(f"contract {a.name!r} is already registered to {cur['owner']!r}")
    for t in _T.scan(root):
        if t.kind == "task" and t.epic != a.owner and a.name in t.meta.get("owns", []):
            raise _T.TicketError(
                f"contract {a.name!r} is owned by task {t.slug!r} of epic "
                f"{t.epic!r}, not {a.owner!r}"
            )
    consumers = _csv(a.consumers)
    if cur:
        cur.update(kind=a.kind, file=a.file, consumers=_merge(cur["consumers"], consumers))
        if a.note is not None:
            cur["note"] = a.note
    else:
        contracts.append(
            {
                "name": a.name,
                "kind": a.kind,
                "owner": a.owner,
                "file": a.file,
                "consumers": _merge([], consumers),
                "note": a.note or "",
            }
        )
    _T.commit_ticket_change(a.owner, f"contract add {a.name}", [_save(root, contracts)], root)
    return 0


def cmd_use(a) -> int:
    root = Path(a.root)
    _T.require_main_checkout(root)
    contracts = load_contracts(root)
    cur = _find(contracts, a.name)
    if not cur:
        raise _T.TicketError(f"no contract {a.name!r}")
    cur["consumers"] = _merge(cur["consumers"], [a.epic])
    _T.commit_ticket_change(a.epic, f"contract use {a.name}", [_save(root, contracts)], root)
    return 0


def cmd_list(a) -> int:
    contracts = load_contracts(a.root)
    if a.json:
        print(json.dumps(contracts, indent=2))
        return 0
    for c in contracts:
        print(
            f"{c['name']} {c['kind']} owner={c['owner']} file={c['file']} "
            f"consumers={','.join(c['consumers'])}"
        )
    return 0


def register(sub, t) -> None:
    global _T
    _T = t
    sp = sub.add_parser("contract", root=False)
    cs = sp.add_subparsers(dest="contract_cmd", required=True)

    def leaf(name, fn):
        p = cs.add_parser(name)
        p.set_defaults(fn=fn)
        p.add_argument("--root", default=None, help="plans root (default: git top/docs/plans)")
        return p

    p = leaf("add", cmd_add)
    p.add_argument("name")
    p.add_argument("--kind", required=True)
    p.add_argument("--owner", required=True)
    p.add_argument("--file", required=True)
    p.add_argument("--consumers", default="")
    p.add_argument("--note", default=None)
    p = leaf("use", cmd_use)
    p.add_argument("name")
    p.add_argument("--epic", required=True)
    p = leaf("list", cmd_list)
    p.add_argument("--json", action="store_true")
