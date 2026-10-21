"""ticket.py questions: the open-questions store across todo epics (D9, M4).

Each epic's design.md carries `## Open questions`: open lines are
`- Q<n>: <question> [recommended: <answer>]`, answered ones `- Q<n>: <question> [answer: <text>]`.
"""

import json
import re
from pathlib import Path

SECTION = "Open questions"
LINE = re.compile(r"^- (Q\d+): (.*?)(?: \[(recommended|answer): (.*)\])?\s*$")
HEAD = re.compile(rf"^## {SECTION}\s*$", re.M)


def _bounds(text: str) -> tuple[int, int] | None:
    """Start and end offsets of the section body (after the heading line)."""
    m = HEAD.search(text)
    if not m:
        return None
    nxt = re.search(r"^## ", text[m.end() :], re.M)
    return m.end(), m.end() + nxt.start() if nxt else len(text)


def _parse(text: str) -> list[dict]:
    b = _bounds(text)
    if not b:
        return []
    out = []
    for ln in text[b[0] : b[1]].splitlines():
        m = LINE.match(ln)
        if m:
            out.append(
                {
                    "id": m.group(1),
                    "question": m.group(2).strip(),
                    "kind": m.group(3),
                    "value": m.group(4),
                    "line": ln,
                }
            )
    return out


def _design(t, root: Path, epic: str) -> Path:
    d = t.find_epic(epic, root)
    if d is None or d.parent.name != "todo":
        raise t.TicketError(f"unknown todo epic {epic!r} under {root}")
    p = d / "design.md"
    if not p.is_file():
        raise t.TicketError(f"epic {epic!r} has no design.md")
    return p


def _commit(t, root: Path, epic: str, path: Path) -> None:
    t.commit_ticket_change(epic, "questions", [path], root)


def _list(t, a, root: Path) -> int:
    rows = []
    for e in sorted(t._epics(root).values(), key=lambda x: x.slug):
        if e.phase != "todo":
            continue
        p = e.path.parent / "design.md"
        if not p.is_file():
            continue
        for q in _parse(p.read_text()):
            if q["kind"] != "answer":
                rows.append(
                    {
                        "epic": e.slug,
                        "id": q["id"],
                        "question": q["question"],
                        "recommended": q["value"],
                    }
                )
    if a.json:
        print(json.dumps(rows, indent=2))
    else:
        for r in rows:
            rec = f" [recommended: {r['recommended']}]" if r["recommended"] else ""
            print(f"{r['epic']} {r['id']}: {r['question']}{rec}")
    return 0


def _add(t, a, root: Path) -> int:
    epic, question = a.add
    t.require_main_checkout(root)
    p = _design(t, root, epic)
    text = p.read_text()
    nums = [int(q["id"][1:]) for q in _parse(text)]
    line = f"- Q{max(nums, default=0) + 1}: {question.strip()}"
    if a.recommended:
        line += f" [recommended: {a.recommended}]"
    b = _bounds(text)
    if b is None:
        text = text.rstrip("\n") + f"\n\n## {SECTION}\n\n{line}\n"
    else:
        head, tail = text[: b[1]].rstrip("\n"), text[b[1] :]
        text = f"{head}\n{line}\n" + (f"\n{tail}" if tail else "")
    p.write_text(text)
    _commit(t, root, epic, p)
    return 0


def _answer(t, a, root: Path) -> int:
    epic, qid, answer = a.answer
    t.require_main_checkout(root)
    p = _design(t, root, epic)
    text = p.read_text()
    hit = next((q for q in _parse(text) if q["id"] == qid), None)
    if hit is None:
        raise t.TicketError(f"epic {epic!r} has no question {qid}")
    new = f"- {qid}: {hit['question']} [answer: {answer.strip()}]"
    p.write_text(text.replace(hit["line"], new, 1))
    _commit(t, root, epic, p)
    return 0


def run(a) -> int:
    from_t = a.t
    root = Path(a.root)
    if a.add and a.answer:
        raise from_t.TicketError("questions: use --add or --answer, not both")
    if a.add:
        return _add(from_t, a, root)
    if a.answer:
        return _answer(from_t, a, root)
    return _list(from_t, a, root)


def register(sub, t):
    sp = sub.add_parser("questions", help="list, add or answer open questions in todo epics")
    sp.set_defaults(fn=run, t=t)
    sp.add_argument("--json", action="store_true")
    sp.add_argument("--add", nargs=2, metavar=("EPIC", "QUESTION"))
    sp.add_argument("--recommended", default=None)
    sp.add_argument("--answer", nargs=3, metavar=("EPIC", "QID", "TEXT"))
