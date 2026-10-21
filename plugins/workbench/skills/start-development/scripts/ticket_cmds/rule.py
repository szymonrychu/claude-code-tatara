"""ticket.py rule: record orchestrator rulings in task files and <epic dir>/rulings.json.

write_ruling and read_rulings are the one writer and reader of rulings.json; `continue`
and plan-execute's mid-run read reuse them (D1, D10).
"""

import datetime
import json
import re
from pathlib import Path

RULINGS = "rulings.json"


def read_rulings(epic_dir) -> list:
    """The rulings recorded for the epic, oldest first; [] when none."""
    p = Path(epic_dir) / RULINGS
    if not p.is_file():
        return []
    data = json.loads(p.read_text())
    if not isinstance(data, list):
        raise ValueError(f"{p}: expected a JSON array")
    return data


def write_ruling(epic_dir, task: str, accept: bool, reason: str) -> None:
    """Append {task, accept, reason, at} to the epic's rulings.json."""
    at = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    entries = read_rulings(epic_dir)
    entries.append({"task": task, "accept": bool(accept), "reason": reason, "at": at})
    (Path(epic_dir) / RULINGS).write_text(json.dumps(entries, indent=2) + "\n")


def _ruling_body(t, body: str, line: str) -> str:
    if re.search(r"^## Ruling\s*$", body, re.M):
        return t._append_to_section(body, "Ruling", line)
    notes = re.search(r"^## Notes\s*$", body, re.M)
    block = f"## Ruling\n\n{line}\n\n"
    if not notes:
        return body.rstrip("\n") + "\n\n" + block.rstrip("\n") + "\n"
    return body[: notes.start()] + block + body[notes.start() :]


def run(a, t) -> int:
    root = Path(a.root)
    t.require_main_checkout(root)
    epic_dir = t.resolve_epic(a.epic, root)
    accept = t._csv(a.accept)
    reject = t._csv(a.reject)
    if not accept and not reject:
        raise t.TicketError("rule needs --accept and/or --reject task ids")
    if not a.reason.strip():
        raise t.TicketError("rule needs a non-empty --reason")
    files = {p.stem: p for p in t._task_files(epic_dir)}
    unknown = sorted((set(accept) | set(reject)) - set(files))
    if unknown:
        raise t.TicketError(f"unknown task(s) in {epic_dir.name!r}: {', '.join(unknown)}")
    both = sorted(set(accept) & set(reject))
    if both:
        raise t.TicketError(f"task(s) both accepted and rejected: {', '.join(both)}")
    today = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    changed: list[Path] = []
    for task, ok in [(x, True) for x in accept] + [(x, False) for x in reject]:
        doc = t._read_doc(files[task])
        line = f"- {today} {'accepted' if ok else 'rejected'}: {a.reason}"
        t._write_task(files[task], t.Doc(doc.meta, _ruling_body(t, doc.body, line)), changed)
        write_ruling(epic_dir, task, ok, a.reason)
        print(f"{task}: {'accepted' if ok else 'rejected'}")
    t.commit_ticket_change(epic_dir.name, "rule", changed + [epic_dir / RULINGS], root)
    return 0


def register(sub, t) -> None:
    sp = sub.add_parser("rule", help="record orchestrator rulings on task findings")
    sp.set_defaults(fn=lambda a: run(a, t))
    sp.add_argument("epic")
    sp.add_argument("--accept", default="", help="comma-separated task ids")
    sp.add_argument("--reject", default="", help="comma-separated task ids")
    sp.add_argument("--reason", required=True)
