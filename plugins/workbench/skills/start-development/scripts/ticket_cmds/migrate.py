"""ticket.py migrate: map old-scheme task files to the 18 keys of templates/task.md.

`migrate <epic>` or `migrate --all` (every epic under todo, in-progress and done) computes each
task's new frontmatter: the template keys in template order, every other key dropped (the
legacy estimate, estimate_by, actual, worktree, branch, run, provides, owns, uses,
process_gaps, acs_for_audit, fork_point and any stray key), the body unchanged.

- `points`: kept when set (an empty expected value filled from calibration.SEED); else from a
  whole-number legacy `estimate` in minutes (calibration.points_for_minutes, the estimate kept
  as expected_minutes, the bucket's SEED tokens as expected_tokens); else from a Notes line
  `Estimate: N points` with SEED expected values; else all three stay empty.
- Actuals of a task carrying a legacy key: actual_minutes from a whole-number legacy `actual`,
  else from the task's agent records; tokens and roles only from records covering both impl
  and review. A one-role match gives nothing from records and prints `partial:`. Legacy
  actual_roles values are dropped. A task without a legacy key keeps its actuals.

Records come from the epic's `.logs/agents` (agent_usage.records_by_task), backfilled once
per epic from the harness transcripts with the names map, so unmarked transcripts whose
first prompt names one task count too. Every mapped task runs through `_number_problems`
first: any problem refuses the run (exit 1, every problem on stderr, nothing else printed).
`--dry-run` then prints, per task it would change, each changed key with its old and new
value and the dropped keys, each `partial:` line and, per changed done epic, the RETRO.md
generated block computed from the new values. It changes no tracked file.

Without `--dry-run` (main checkout only) it then writes, per changed epic, the task files and,
for a done epic, RETRO.md (created from templates/retro.md when absent, else only its generated
block replaced), its rows read from the new values, and commits exactly those files as
`chore(ticket): <epic> migrate`; an epic with nothing to change gets no commit, so a second run
prints `migrate: nothing to change`. It prints `<epic>: <n> tasks migrated[, RETRO.md]` per
changed epic, then `retro-writer: <epic>` for each done epic whose RETRO.md Retro section is still
the template's. A done epic with no RETRO.md counts as changed even when no task file
changes. A done epic is history: this is the one writer of its task files.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import agent_usage  # scripts/lib, on sys.path through ticket.py
import calibration

from ticket_cmds import retro

WHOLE = re.compile(r"[0-9]+")
BARE_NAME = re.compile(r"[A-Za-z0-9._/-]+")
ACTUALS = ("actual_minutes", "actual_tokens", "actual_roles", "actual_role_tokens")
NAME_KEYS = ("worktree", "branch")


def register(sub, t) -> None:
    sp = sub.add_parser("migrate", help="map old-scheme task files to the template keys")
    sp.set_defaults(fn=lambda a: run(a, t))
    sp.add_argument("epic", nargs="?")
    sp.add_argument("--all", action="store_true", help="every epic under todo, in-progress, done")
    sp.add_argument("--dry-run", action="store_true", help="print the plan, write nothing")
    sp.add_argument(
        "--transcripts",
        help="harness subagent transcripts to backfill records from "
        "(default: the project's dir under the harness home)",
    )
    sp.add_argument(
        "--logs", help="the logs dir holding agents/ (default: the main checkout's .logs)"
    )


def _whole(value) -> int | None:
    return int(value) if isinstance(value, str) and WHOLE.fullmatch(value) else None


def _template_meta(t) -> dict:
    return t._template("task.md").meta


def _is_legacy(t, meta: dict) -> bool:
    return any(key not in _template_meta(t) for key in meta)


def _roles(records: list[dict]) -> set[str]:
    return {agent_usage.role_for(r.get("role"), r.get("agentType")) for r in records} - {""}


def _partial(records: list[dict]) -> str | None:
    """The roles a one-role record set covers (', ' joined), None for none or a full set."""
    roles = _roles(records)
    if not records or {"impl", "review"} <= roles:
        return None
    return ", ".join(sorted(roles)) or "no role"


def _seed(out: dict, points: int | None, only_empty: bool) -> None:
    """expected_minutes and expected_tokens from calibration.SEED[points]; nothing for a
    value off the scale (`_number_problems` then refuses the points)."""
    if points not in calibration.SEED:
        return
    minutes, tokens = calibration.SEED[points]
    for key, seed in (("expected_minutes", minutes), ("expected_tokens", tokens)):
        if not only_empty or out[key] in (None, ""):
            out[key] = str(seed)


def migrate_meta(t, meta: dict, body: str, records: list[dict]) -> dict:
    """The new frontmatter of one task, in template order (pure; no I/O)."""
    template = _template_meta(t)
    out = {key: meta.get(key, default) for key, default in template.items()}
    if out["points"] not in (None, ""):
        _seed(out, _whole(out["points"]), only_empty=True)
    else:
        minutes = _whole(meta.get("estimate"))
        notes = retro.NOTES_POINTS.search(t._sections(body).get("Notes", ""))
        if minutes is not None:
            points = calibration.points_for_minutes(minutes)
            out.update(points=str(points), expected_minutes=str(minutes))
            out["expected_tokens"] = str(calibration.SEED[points][1])
        elif notes:
            out["points"] = notes.group(1)
            _seed(out, int(notes.group(1)), only_empty=False)
    if _is_legacy(t, meta):
        out.update(dict.fromkeys(ACTUALS, ""))
        if records and _partial(records) is None:
            out.update(t.record_actuals(records))
        actual = _whole(meta.get("actual"))
        if actual is not None:
            out["actual_minutes"] = str(actual)
    return out


def _task_name(value, key: str, epic: str, task: str) -> str | None:
    """A legacy worktree basename or branch that names exactly this task, else None."""
    if not isinstance(value, str) or not value:
        return None
    name = Path(value).name if key == "worktree" else value
    if not BARE_NAME.fullmatch(name) or epic not in name or task not in name:
        return None
    return name


def names_map(t, root: Path) -> dict[str, tuple[str, str | None]]:
    """Every name a transcript may use for a task: `<epic>/tasks/<task>.md`, the
    ticket_names entries, and each old task's legacy worktree basename and branch when the
    value is a bare name holding both the epic and the task slug (never HEAD or free text)."""
    names = dict(t.ticket_names(root))
    for ticket in t.scan(root):
        if ticket.kind != "task":
            continue
        owner = (ticket.epic, ticket.slug)
        names.setdefault(f"{ticket.epic}/tasks/{ticket.slug}.md", owner)
        for key in NAME_KEYS:
            name = _task_name(ticket.meta.get(key), key, ticket.epic, ticket.slug)
            if name:
                names.setdefault(name, owner)
    return names


def _epic_dirs(a, t, root: Path) -> list[Path]:
    if a.epic:
        return [t.resolve_epic(a.epic, root)]
    out = []
    for phase in t.PHASES:
        base = root / phase
        out += sorted(d for d in base.iterdir() if d.is_dir()) if base.is_dir() else []
    return out


def _show(value) -> str:
    return "absent" if value is None else json.dumps(value)


def _change_line(label: str, old: dict, new: dict) -> str:
    parts = [f"{k}: {_show(old.get(k))} -> {_show(v)}" for k, v in new.items() if old.get(k) != v]
    dropped = sorted(k for k in old if k not in new)
    if dropped:
        parts.append("drop: " + ", ".join(dropped))
    return f"{label}: " + ("; ".join(parts) or "key order")


def _plan(a, t, root: Path, epic_dir: Path, names: dict, logs, transcripts) -> dict:
    """One epic's mapping: the new Doc per task path, the problems, the output lines."""
    epic = epic_dir.name
    docs = {path: t._read_doc(path) for path in t._task_files(epic_dir)}
    legacy = [p.stem for p, doc in docs.items() if _is_legacy(t, doc.meta)]
    wanting = [
        p.stem for p, doc in docs.items() if "" in (doc.meta.get(k, "") for k in ACTUALS[:2])
    ]
    records = {}
    if logs is not None and docs:
        records = agent_usage.records_by_task(
            epic, logs, transcripts, names=names, tasks=sorted(set(legacy + wanting))
        )
    plan: dict = {"dir": epic_dir, "problems": [], "lines": [], "docs": {}, "all": docs}
    plan["needs_retro"] = t._phase_of(epic_dir) == "done" and not (epic_dir / retro.FILE).is_file()
    partials = []
    for path, doc in docs.items():
        label = f"{epic}/{path.stem}"
        found = records.get(path.stem, []) if path.stem in legacy else []
        new = migrate_meta(t, doc.meta, doc.body, found)
        plan["problems"] += t._number_problems(new, label)
        if _partial(found):
            partials.append(f"partial: {label} ({_partial(found)})")
        new_doc = t.Doc(new, doc.body)
        if t.dump(new_doc) != path.read_text():
            plan["docs"][path] = new_doc
            plan["lines"].append(_change_line(label, doc.meta, new))
    plan["lines"] += partials
    changed = plan["docs"] or plan["needs_retro"]
    if a.dry_run and changed and t._phase_of(epic_dir) == "done" and not plan["problems"]:
        plan["lines"] += _retro_lines(a, t, root, epic_dir, {**docs, **plan["docs"]})
    return plan


def _retro_text(a, t, root: Path, epic_dir: Path, docs: dict) -> tuple[Path, str | None, str]:
    """A done epic's RETRO.md: its path, its current text (None when absent) and the text with
    the generated block computed from `docs` (the new values), as `ticket.py retro` writes it."""
    path = epic_dir / retro.FILE
    generated = retro._generated(retro._rows(a, t, root, epic_dir, backfill=False, docs=docs))
    if path.is_file():
        old = path.read_text()
        return path, old, retro._splice(t, old, generated, path)
    title = t._read_doc(epic_dir / "README.md").meta.get("title") or epic_dir.name
    template = _retro_template(t).replace("<Topic>", title, 1)
    return path, None, retro._splice(t, template, generated, path)


def _retro_template(t) -> str:
    return (t.TEMPLATES / "retro.md").read_text()


def _retro_lines(a, t, root: Path, epic_dir: Path, docs: dict) -> list[str]:
    """The RETRO.md a done epic would get, its rows read from the new values."""
    path, old, text = _retro_text(a, t, root, epic_dir, docs)
    if text == old:
        return []
    generated = text[text.index(retro.BEGIN) : text.index(retro.END) + len(retro.END)]
    return [f"retro: {path} ({'create' if old is None else 'update'})", generated]


def _needs_retro_writer(t, epic_dir: Path) -> bool:
    """A done epic whose RETRO.md Retro section is still the template's."""
    path = epic_dir / retro.FILE
    if t._phase_of(epic_dir) != "done" or not path.is_file():
        return False
    placeholder = t._sections(_retro_template(t)).get("Retro")
    return t._sections(path.read_text()).get("Retro") == placeholder


def _write(a, t, root: Path, plans: list[dict]) -> list[str]:
    """Compute every epic's RETRO.md first (a broken one refuses before any write), then per
    changed epic write its task files and RETRO.md and commit exactly them."""
    writes = []
    for plan in plans:
        epic_dir = plan["dir"]
        if not plan["docs"] and not plan["needs_retro"]:
            continue
        retro_md = None
        if t._phase_of(epic_dir) == "done":
            path, old, text = _retro_text(a, t, root, epic_dir, {**plan["all"], **plan["docs"]})
            retro_md = (path, text) if text != old else None
        writes.append((epic_dir, plan["docs"], retro_md))
    lines = []
    for epic_dir, docs, retro_md in writes:
        paths = list(docs)
        for path, doc in docs.items():
            path.write_text(t.dump(doc))
        if retro_md:
            retro_md[0].write_text(retro_md[1])
            paths.append(retro_md[0])
        t.commit_ticket_change(epic_dir.name, "migrate", paths, root)
        lines.append(
            f"{epic_dir.name}: {len(docs)} tasks migrated" + (", RETRO.md" if retro_md else "")
        )
    return lines


def run(a, t) -> int:
    if bool(a.epic) == bool(a.all):
        raise t.TicketError("migrate: name an epic or pass --all, not both")
    root = Path(a.root)
    if not a.dry_run:
        t.require_main_checkout(root)
    epic_dirs = _epic_dirs(a, t, root)
    names = names_map(t, root)
    logs = Path(a.logs) if a.logs else t.workbench.logs_dir(root)
    main = t.workbench.main_checkout(root)
    transcripts = a.transcripts or (main and agent_usage.default_transcripts_dir(main))
    plans = [_plan(a, t, root, d, names, logs, transcripts) for d in epic_dirs]
    problems = [p for plan in plans for p in plan["problems"]]
    if problems:
        for problem in problems:
            print(f"ticket.py: migrate: {problem}", file=sys.stderr)
        return 1
    if a.dry_run:
        lines = [line for plan in plans for line in plan["lines"]]
    else:
        lines = _write(a, t, root, plans)
    print("\n".join(lines) if lines else "migrate: nothing to change")
    if not a.dry_run:
        for epic_dir in epic_dirs:
            if _needs_retro_writer(t, epic_dir):
                print(f"retro-writer: {epic_dir.name}")
    return 0
