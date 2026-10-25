"""ticket.py amend: record a mid-epic scope change on a task and re-validate the epic."""

import datetime
from pathlib import Path


def register(sub, t):
    sp = sub.add_parser("amend", help="replace a task's Requirement/AC and note why")
    sp.set_defaults(fn=lambda a: run(a, t))
    sp.add_argument("epic")
    sp.add_argument("task")
    sp.add_argument("--requirement-file", required=True)
    sp.add_argument("--ac-file")
    sp.add_argument("--reason", required=True)


def run(a, t) -> int:
    root = Path(a.root)
    t.require_main_checkout(root)
    epic_dir = t.resolve_epic(a.epic, root)
    if t._phase_of(epic_dir) == "done":
        raise t.TicketError(f"epic {epic_dir.name!r} is done; amend needs an open epic")
    path = epic_dir / "tasks" / f"{a.task}.md"
    if not path.is_file():
        raise t.TicketError(f"epic {epic_dir.name!r} has no task {a.task!r}")
    doc = t._read_doc(path)
    if doc.meta.get("status") == "done":
        raise t.TicketError(f"task {a.task!r} is done; amend needs an open task")
    original = path.read_text()
    body = t._section_replace(doc.body, "Requirement", t._read(a.requirement_file))
    if a.ac_file:
        ac = t._read(a.ac_file)
        t._parse_ac(ac, a.task)
        body = t._section_replace(body, "Acceptance conditions", ac)
    note = f"- {datetime.date.today().isoformat()} amended: {a.reason.strip()}"
    body = t._append_to_section(body, "Notes", note)
    path.write_text(t.dump(t.Doc(dict(doc.meta), body)))
    try:
        t.derive_tasks(epic_dir, only=[a.task])
        problems = "\n".join(f"ticket.py: lint: {p}" for p in t.lint_problems(root, epic_dir.name))
    except t.TicketError as e:
        problems = str(e)
    if problems:
        path.write_text(original)
        print(problems)
        return 1
    t.commit_ticket_change(epic_dir.name, f"amend {a.task}", [path], root)
    print(f"amended {a.task}")
    return 0
