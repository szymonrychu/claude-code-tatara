"""ticket.py retro: write RETRO.md's measured half at epic close, or print earlier retros.

`retro <epic>` (main checkout; the epic in-progress or done) writes the Tasks table in delivery
order (the `chore(ticket): <epic> task <slug> done` commits, oldest first; tasks never marked
done follow by the committer date of their `verified_head`, then in dependency order), its
totals line and the Deltas section between the generated markers of templates/retro.md, keeps
everything outside them on a rerun and commits exactly RETRO.md. Values come from the task
frontmatter; empty actuals fall back to the epic's `.logs/agents` records, read once per epic
(backfilled once from the harness transcripts when a task has none) and a missing `points` to
a Notes line `Estimate: <n> points`. A value none of them gives reads `not recorded`, never a
guess. Task files are never written.

`retro --history [--limit N]` prints the Retro and Improvements sections of the N most recently
done epics that have a RETRO.md, as JSON.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import agent_usage  # scripts/lib, on sys.path through ticket.py
import calibration

FILE = "RETRO.md"
BEGIN, END = "<!-- retro:generated:begin -->", "<!-- retro:generated:end -->"
NR = "not recorded"
NOTES_POINTS = re.compile(r"^\W*Estimate: ([0-9]+) points?\b", re.M)
COLUMNS = (
    ("points", "Points (estimate)"),
    ("points_actual", "Points (post-delivery)"),
    ("expected_minutes", "Minutes (expected)"),
    ("actual_minutes", "Minutes (actual)"),
    ("expected_tokens", "Tokens (expected)"),
    ("actual_tokens", "Tokens (actual)"),
)
METRICS = (
    ("points", "points", "points_actual"),
    ("minutes", "expected_minutes", "actual_minutes"),
    ("tokens", "expected_tokens", "actual_tokens"),
)


def register(sub, t) -> None:
    sp = sub.add_parser("retro", help="write RETRO.md's Tasks and Deltas, or print past retros")
    sp.set_defaults(fn=lambda a: run(a, t))
    sp.add_argument("epic", nargs="?")
    sp.add_argument(
        "--history",
        action="store_true",
        help="print the Retro and Improvements of recent done epics as JSON",
    )
    sp.add_argument("--limit", type=int, help="with --history: how many epics (default 5)")
    sp.add_argument(
        "--logs", help="the logs dir holding agents/ (default: the main checkout's .logs)"
    )
    sp.add_argument(
        "--transcripts",
        help="harness subagent transcripts to backfill from when a task has no record "
        "(default: the project's dir under the harness home)",
    )


def run(a, t) -> int:
    if a.history:
        if a.epic:
            raise t.TicketError("retro: --history takes no epic")
        limit = 5 if a.limit is None else a.limit
        if limit < 1:
            raise t.TicketError("retro: --limit must be at least 1")
        print(json.dumps(_history(t, Path(a.root), limit), indent=2))
        return 0
    if not a.epic:
        raise t.TicketError("retro: name an epic, or pass --history")
    if a.limit is not None:
        raise t.TicketError("retro: --limit goes with --history")
    return _write(a, t)


# ---------------------------------------------------------------- the measured half


def _git_lines(t, root: Path, *args: str) -> list[str]:
    r = t._git(t._existing(root), *args)
    return r.stdout.splitlines() if r.returncode == 0 else []


SHA = re.compile(r"[0-9a-f]{4,40}")


def _commit_time(t, root: Path, sha) -> int | None:
    """Committer time of `sha`; None when it is not a sha or names no commit here."""
    if not isinstance(sha, str) or not SHA.fullmatch(sha):
        return None
    r = t._git(t._existing(root), "show", "-s", "--format=%ct", f"{sha}^{{commit}}")
    out = r.stdout.strip()
    return int(out) if r.returncode == 0 and out.isdigit() else None


def _delivery_order(
    t, root: Path, epic: str, slugs: list[str], deps: dict, heads: dict | None = None
) -> list[str]:
    """Slugs by their last `task <slug> done` commit, oldest first; then those whose
    `verified_head` is a commit here, by its committer date; then the rest by deps."""
    done = re.compile(rf"^chore\(ticket\): {re.escape(epic)} task (\S+) done$")
    log = _git_lines(
        t, root, "log", "--reverse", "--format=%s", "--fixed-strings",
        f"--grep=chore(ticket): {epic} task ",
    )  # fmt: skip
    when: dict[str, int] = {}
    for i, subject in enumerate(log):
        m = done.match(subject)
        if m and m.group(1) in slugs:
            when[m.group(1)] = i
    delivered = sorted(when, key=when.__getitem__)
    ordered = [s for s in t.dependency_order(deps) if s not in when]
    dated = {s: _commit_time(t, root, (heads or {}).get(s)) for s in ordered}
    verified = sorted((s for s in ordered if dated[s] is not None), key=dated.__getitem__)
    return delivered + verified + [s for s in ordered if dated[s] is None]


def _estimate_points(t, meta: dict, body: str, slug: str) -> int | None:
    points = t._points(meta.get("points"), slug, "points")
    if points is not None:
        return points
    m = NOTES_POINTS.search(t._sections(body).get("Notes", ""))
    return int(m.group(1)) if m else None


def _rows(
    a, t, root: Path, epic_dir: Path, backfill: bool = True, docs: dict | None = None
) -> list[dict]:
    """One dict per task in delivery order: title and the six measured values (None = unknown).
    `backfill=False` only reads the existing records (the read-only `deltas`); `docs` maps a
    task path to the Doc to read instead of the file (migrate's new values before writing)."""
    tasks = {}
    for path in t._task_files(epic_dir):
        doc = (docs or {}).get(path) or t._read_doc(path)
        meta, slug = doc.meta, path.stem
        row = {"slug": slug, "title": meta.get("title") or slug, "deps": meta.get("depends_on", [])}
        row["head"] = meta.get("verified_head")
        row["points"] = _estimate_points(t, meta, doc.body, slug)
        row["points_actual"] = t._points(meta.get("points_actual"), slug, "points_actual")
        for key in t.COUNT_KEYS:
            row[key] = t._count(meta.get(key), slug, key)
        tasks[slug] = row
    _fill_from_records(a, t, root, epic_dir.name, tasks, backfill)
    deps = {s: list(r["deps"]) for s, r in tasks.items()}
    heads = {s: r["head"] for s, r in tasks.items()}
    order = _delivery_order(t, root, epic_dir.name, list(tasks), deps, heads)
    return [tasks[s] for s in order]


def _fill_from_records(a, t, root: Path, epic: str, tasks: dict, backfill: bool = True) -> None:
    """Empty actual minutes and tokens from the task's `.logs/agents` records."""
    wanting = [r for r in tasks.values() if None in (r["actual_minutes"], r["actual_tokens"])]
    logs = Path(a.logs) if a.logs else t.workbench.logs_dir(root)
    if not wanting or logs is None:
        return
    main = t.workbench.main_checkout(root)
    transcripts = a.transcripts or (main and agent_usage.default_transcripts_dir(main))
    found = agent_usage.records_by_task(
        epic, logs, transcripts, backfill, tasks=[r["slug"] for r in wanting]
    )
    for row in wanting:
        if row["slug"] not in found:
            continue
        sums = agent_usage.aggregate(found[row["slug"]])
        if row["actual_minutes"] is None:
            row["actual_minutes"] = sums["minutes"]
        if row["actual_tokens"] is None:
            row["actual_tokens"] = sums["tokens"]


def _cell(value) -> str:
    return NR if value is None else str(value)


def _total(values: list) -> str:
    known = [v for v in values if v is not None]
    if not known:
        return NR
    total = str(sum(known))
    return total if len(known) == len(values) else f"{total} ({len(known)} of {len(values)} tasks)"


def _table(header: list[str], rows: list[list[str]]) -> str:
    lines = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    lines += ["| " + " | ".join(c.replace("|", "\\|") for c in row) + " |" for row in rows]
    return "\n".join(lines)


def _ratio(expected, actual) -> str:
    if expected is None or actual is None:
        return NR
    return f"{actual / expected:.2f}" if expected else "undefined (expected 0)"


def _difference(estimate, actual) -> str:
    if estimate is None or actual is None:
        return NR
    return f"{actual - estimate:+d}" if actual != estimate else "0"


def _generated(rows: list[dict]) -> str:
    tasks = [[r["title"], *(_cell(r[k]) for k, _ in COLUMNS)] for r in rows]
    tasks.append(["Total", *(_total([r[k] for r in rows]) for k, _ in COLUMNS)])
    deltas = [
        [
            r["title"],
            _difference(r["points"], r["points_actual"]),
            _ratio(r["expected_minutes"], r["actual_minutes"]),
            _ratio(r["expected_tokens"], r["actual_tokens"]),
        ]
        for r in rows
    ]
    mdapes = []
    for name, est, act in METRICS:
        pairs = [(r[est], r[act]) for r in rows if None not in (r[est], r[act])]
        m = calibration.mdape(pairs)
        mdapes.append(f"- MdAPE {name}: {NR if m is None else f'{m * 100:.1f}%'}")
    header = ["Task", *(label for _, label in COLUMNS)]
    deltas_header = [
        "Task",
        "Points (post-delivery - estimate)",
        "Minutes (actual / expected)",
        "Tokens (actual / expected)",
    ]
    return "\n".join(
        [
            BEGIN,
            "## Tasks",
            "",
            "Delivery order; written by `ticket.py retro`.",
            "",
            _table(header, tasks),
            "",
            "## Deltas",
            "",
            _table(deltas_header, deltas),
            "",
            *mdapes,
            END,
        ]
    )


def _splice(t, text: str, generated: str, path: Path) -> str:
    """`text` with the part between the generated markers replaced; refuses without them."""
    start, end = text.find(BEGIN), text.find(END)
    if start < 0 or end < start or text.count(BEGIN) != 1 or text.count(END) != 1:
        raise t.TicketError(
            f"{path} needs exactly one {BEGIN} ... {END} block; restore it, then rerun"
        )
    return text[:start] + generated + text[end + len(END) :]


def _write(a, t) -> int:
    root = Path(a.root)
    t.require_main_checkout(root)
    epic_dir = t.resolve_epic(a.epic, root)
    phase = t._phase_of(epic_dir)
    if phase not in ("in-progress", "done"):
        raise t.TicketError(f"epic {epic_dir.name!r} is {phase}; retro needs in-progress or done")
    path = epic_dir / FILE
    generated = _generated(_rows(a, t, root, epic_dir))
    if path.is_file():
        old = path.read_text()
        text = _splice(t, old, generated, path)
    else:
        title = t._read_doc(epic_dir / "README.md").meta.get("title") or epic_dir.name
        template = (t.TEMPLATES / "retro.md").read_text().replace("<Topic>", title, 1)
        old, text = None, _splice(t, template, generated, path)
    if text != old:
        path.write_text(text)
    status = t._git(t._existing(root), "status", "--porcelain", "--", str(path))
    if status.returncode != 0 or status.stdout.strip():
        t.commit_ticket_change(epic_dir.name, "retro", [path], root)
    print(path)
    return 0


# ---------------------------------------------------------------- history


def _done_order(t, root: Path) -> dict[str, int]:
    """Done epic slug -> rank of its latest `move done` commit, 0 the most recent."""
    move = re.compile(r"^chore\(ticket\): (\S+) move done$")
    log = _git_lines(t, root, "log", "--format=%s", "--fixed-strings", "--grep= move done")
    rank: dict[str, int] = {}
    for i, subject in enumerate(log):
        m = move.match(subject)
        if m:
            rank.setdefault(m.group(1), i)
    return rank


def _history(t, root: Path, limit: int) -> list[dict]:
    base = root / "done"
    epics = sorted(d.name for d in base.iterdir() if (d / FILE).is_file()) if base.is_dir() else []
    rank = _done_order(t, root)
    # epics without a `move done` commit sort after the ranked ones, in slug order
    epics.sort(key=lambda e: (e not in rank, rank.get(e, 0)))
    out = []
    for name in epics[:limit]:
        sections = t._sections((base / name / FILE).read_text())
        out.append(
            {
                "epic": name,
                "retro": sections.get("Retro", ""),
                "improvements": sections.get("Improvements", ""),
            }
        )
    return out
