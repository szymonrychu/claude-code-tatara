"""ticket.py task: record a task's outcome (status, verified head, a dated note) and commit it.

`--status done` also stamps the task's actuals: `points_actual` from `--points-actual`, and
minutes and tokens measured from its agents' `.logs/agents` records (agent_usage), never
guessed: with no record it first backfills the epic's records from the harness transcripts
(`--transcripts`, default the project's dir), and only then notes the gap.
"""

import datetime
from pathlib import Path

import agent_usage  # scripts/lib, on sys.path through ticket.py


def register(sub, t) -> None:
    sp = sub.add_parser("task", help="set a task's status (and verified head), note why, commit")
    sp.set_defaults(fn=lambda a: run(a, t))
    sp.add_argument("epic")
    sp.add_argument("task")
    sp.add_argument("--status", required=True, help=f"one of {', '.join(t.TASK_STATUSES)}")
    sp.add_argument("--verified-head", help="the commit the reviewer verified on")
    sp.add_argument("--note", help="appended under ## Notes as a dated line")
    sp.add_argument(
        "--points-actual",
        help="post-delivery Fibonacci storypoints (the reviewer's pointsActual); "
        "required with --status done, refused otherwise",
    )
    sp.add_argument(
        "--logs", help="the logs dir holding agents/ (default: the main checkout's .logs)"
    )
    sp.add_argument(
        "--transcripts",
        help="harness subagent transcripts to backfill from when the task has no record "
        "(default: the project's dir under the harness home)",
    )


def _actuals(a, t, root: Path, epic: str) -> tuple[dict, list[str]]:
    """Frontmatter for a done task and the extra Notes lines; nothing for any other status."""
    if a.status != "done":
        if a.points_actual is not None:
            raise t.TicketError("--points-actual goes with --status done only")
        return {}, []
    if a.points_actual in (None, ""):
        raise t.TicketError("--status done needs --points-actual N (the reviewer's pointsActual)")
    try:
        points = t._points(a.points_actual, a.task, "points_actual")
    except t.TicketError as e:
        raise t.TicketError(f"--points-actual: {e}") from None
    meta = {"points_actual": str(points)}
    logs = Path(a.logs) if a.logs else t.workbench.logs_dir(root)
    records = agent_usage.read_records(logs, epic, a.task) if logs else []
    if logs and not records:
        transcripts = a.transcripts or agent_usage.default_transcripts_dir(root)
        agent_usage.backfill(transcripts, logs, epic=epic)
        records = agent_usage.read_records(logs, epic, a.task)
    if not records:
        return meta, ["actuals: no agent records"]
    sums = agent_usage.aggregate(records)
    if sums["minutes"] is not None:
        meta["actual_minutes"] = str(sums["minutes"])
    meta["actual_tokens"] = str(sums["tokens"])
    if sums["roles"]:
        meta["actual_roles"] = t._format_roles({r: m for r, (m, _) in sums["roles"].items()})
        meta["actual_role_tokens"] = t._format_roles({r: n for r, (_, n) in sums["roles"].items()})
    return meta, []


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
    actuals, extra_notes = _actuals(a, t, root, epic_dir.name)
    doc = t._read_doc(path)
    meta = dict(doc.meta, status=a.status, **actuals)
    if a.verified_head is not None:
        meta["verified_head"] = a.verified_head
    today = datetime.date.today().isoformat()
    note = f"- {today} {a.status}"
    if a.note and a.note.strip():
        note += f": {a.note.strip()}"
    body = doc.body
    for line in [note] + [f"- {today} {extra}" for extra in extra_notes]:
        body = t._append_to_section(body, "Notes", line)
    path.write_text(t.dump(t.Doc(meta, body)))
    t.commit_ticket_change(epic_dir.name, f"task {a.task} {a.status}", [path], root)
    print(f"{a.task}: {a.status}")
    return 0
