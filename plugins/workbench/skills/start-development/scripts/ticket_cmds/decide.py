"""ticket.py decide: record a gate answer as a design decision and an approvals.json entry."""

import json
import re
from pathlib import Path


def register(sub, t):
    sp = sub.add_parser("decide", help="record a user decision in design.md and approvals.json")
    sp.set_defaults(fn=lambda a: run(a, t))
    sp.add_argument("epic")
    sp.add_argument("approval_id")
    sp.add_argument("text")
    sp.add_argument(
        "--tasks", required=True, help="comma-separated task slugs the decision lands in"
    )
    sp.add_argument(
        "--title", default=None, help="short decision title (default: first 60 chars of text)"
    )


def _section_span(md: str, name: str, t) -> tuple[int, int]:
    m = re.search(rf"^## {re.escape(name)}\s*$", md, re.M)
    if not m:
        raise t.TicketError(f"design.md has no ## {name} section")
    nxt = re.search(r"^## ", md[m.end() :], re.M)
    return m.end(), (m.end() + nxt.start() if nxt else len(md))


def _add_decision(md: str, n: int, title: str, text: str, tasks: list[str], t) -> str:
    block = f"### D{n}: {title}\n{text} (user decision)\n"
    s, e = _section_span(md, "Decisions", t)
    md = md[:s] + md[s:e].rstrip("\n") + "\n\n" + block + ("\n" + md[e:] if md[e:] else "")
    s, e = _section_span(md, "Decision coverage", t)
    body = md[s:e]
    row = f"| D{n} {title} | {', '.join(tasks)} |"
    lines = body.split("\n")
    last = max((i for i, ln in enumerate(lines) if ln.strip().startswith("|")), default=None)
    if last is None:
        lines = body.rstrip("\n").split("\n") + ["", "| Decision | Tasks |", "|---|---|", row, ""]
    else:
        lines.insert(last + 1, row)
    return md[:s] + "\n".join(lines) + md[e:]


def _lint(epic_dir: Path, root: Path, t) -> tuple[int, str]:
    problems = t.lint_problems(root, epic_dir.name)
    return (1 if problems else 0), "\n".join(f"ticket.py: lint: {p}" for p in problems)


def run(a, t) -> int:
    root = Path(a.root)
    t.require_main_checkout(root)
    epic_dir = t.resolve_epic(a.epic, root)
    if t._phase_of(epic_dir) == "done":
        raise t.TicketError(f"epic {epic_dir.name!r} is done; decide needs todo or in-progress")
    design_path, ledger_path = epic_dir / "design.md", epic_dir / "approvals.json"
    if not design_path.is_file():
        raise t.TicketError(f"epic {epic_dir.name!r} has no design.md")
    tasks = [x.strip() for x in a.tasks.split(",") if x.strip()]
    if not tasks:
        raise t.TicketError("--tasks names no task")
    known = {p.stem for p in t._task_files(epic_dir)}
    unknown = [x for x in tasks if x not in known]
    if unknown:
        raise t.TicketError(f"unknown task(s) {', '.join(unknown)} in epic {epic_dir.name!r}")
    ledger_before = ledger_path.read_text() if ledger_path.is_file() else None
    ledger = json.loads(ledger_before) if ledger_before else []
    design_before = design_path.read_text()

    n = max((int(m) for m in re.findall(r"^### D(\d+):", design_before, re.M)), default=0) + 1
    did = f"D{n}"
    title = (a.title or a.text).strip()
    title = title if a.title else title[:60].strip()
    entry = next((e for e in ledger if e.get("id") == a.approval_id), None)
    if entry is None:
        ledger.append(
            {
                "id": a.approval_id,
                "text": a.text,
                "decisions": [did],
                "tasks": tasks,
                "status": "approved",
            }
        )
    else:
        entry["decisions"] = [*entry.get("decisions", []), did]
        entry["tasks"] = sorted({*entry.get("tasks", []), *tasks})

    design_path.write_text(_add_decision(design_before, n, title, a.text.strip(), tasks, t))
    ledger_path.write_text(json.dumps(ledger, indent=2, ensure_ascii=False) + "\n")
    code, out = _lint(epic_dir, root, t)
    if code != 0:
        design_path.write_text(design_before)
        if ledger_before is None:
            ledger_path.unlink()
        else:
            ledger_path.write_text(ledger_before)
        print(out)
        print(f"ticket.py: decide {a.approval_id} rolled back: lint failed")
        return 1
    t.commit_ticket_change(
        epic_dir.name, f"decide {a.approval_id}", [design_path, ledger_path], root
    )
    print(f"{did} recorded for {a.approval_id}")
    return 0
