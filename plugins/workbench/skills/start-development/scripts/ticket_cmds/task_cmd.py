"""ticket.py task: record a task's outcome (status, verified head, a dated note) and commit it."""

import datetime
from pathlib import Path


def register(sub, t) -> None:
    sp = sub.add_parser("task", help="set a task's status (and verified head), note why, commit")
    sp.set_defaults(fn=lambda a: run(a, t))
    sp.add_argument("epic")
    sp.add_argument("task")
    sp.add_argument("--status", required=True, help=f"one of {', '.join(t.TASK_STATUSES)}")
    sp.add_argument("--verified-head", help="the commit the reviewer verified on")
    sp.add_argument("--note", help="appended under ## Notes as a dated line")


def run(a, t) -> int:
    if a.status not in t.TASK_STATUSES:
        raise t.TicketError(f"status {a.status!r} is not one of {', '.join(t.TASK_STATUSES)}")
    root = Path(a.root)
    t.require_main_checkout(root)
    epic_dir = t.resolve_epic(a.epic, root)
    if t._phase_of(epic_dir) == "done":
        raise t.TicketError(f"epic {epic_dir.name!r} is done; its tasks are closed")
    path = epic_dir / "tasks" / f"{a.task}.md"
    if not path.is_file():
        raise t.TicketError(f"epic {epic_dir.name!r} has no task {a.task!r}")
    doc = t._read_doc(path)
    meta = dict(doc.meta, status=a.status)
    if a.verified_head is not None:
        meta["verified_head"] = a.verified_head
    note = f"- {datetime.date.today().isoformat()} {a.status}"
    if a.note and a.note.strip():
        note += f": {a.note.strip()}"
    path.write_text(t.dump(t.Doc(meta, t._append_to_section(doc.body, "Notes", note))))
    t.commit_ticket_change(epic_dir.name, f"task {a.task} {a.status}", [path], root)
    print(f"{a.task}: {a.status}")
    return 0
