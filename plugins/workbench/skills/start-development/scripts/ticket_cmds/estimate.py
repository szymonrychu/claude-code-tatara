"""ticket.py estimate: recompute task minutes from the formula and refresh the epic Time line."""

import json
from pathlib import Path


def register(sub, t):
    sp = sub.add_parser("estimate", help="formula task minutes and the epic Time line")
    sp.set_defaults(fn=lambda a: run(a, t))
    sp.add_argument("epic")
    sp.add_argument("--json", action="store_true", help="print the epic_estimate dict")


def run(a, t) -> int:
    root = Path(a.root)
    t.require_main_checkout(root)
    epic_dir = t.resolve_epic(a.epic, root)
    if t._phase_of(epic_dir) == "done":
        raise t.TicketError(f"epic {epic_dir.name!r} is in done; its tasks are closed")
    changed: list[Path] = []
    for path in t._task_files(epic_dir):
        doc = t._read_doc(path)
        if doc.meta.get("estimate_by") == "override":
            continue
        minutes = t.formula_minutes(
            root, doc.meta.get("repo", ""), doc.meta.get("files") or [], doc.meta.get("verify", "")
        )
        t._write_task(path, doc, changed, estimate=str(minutes), estimate_by="formula")
    if (epic_dir / "README.md").is_file():
        readme, moved = t.update_time_section(epic_dir)
        if moved:
            changed.append(readme)
    if changed:
        t.commit_ticket_change(epic_dir.name, "estimate", changed, root)
    est = t.estimator.epic_estimate(t.epic_rows(epic_dir))
    if a.json:
        print(json.dumps(est, indent=2))
        return 0
    print(t.time_summary(epic_dir))
    print("Longest path: " + ", ".join(f"{r['id']} ({r['minutes']} min)" for r in est["longest"]))
    return 0
