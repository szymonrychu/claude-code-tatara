"""ticket.py deltas: how far the estimates were off, and the table the next estimate uses.

`deltas <epic>` prints, per task in delivery order, estimate against actual for points
(`points` vs `points_actual`), minutes (`expected_minutes` vs `actual_minutes`) and tokens
(`expected_tokens` vs `actual_tokens`) with the difference (actual - estimate) and the ratio
(actual / estimate), then the MdAPE per metric. The rows are retro's (`retro._rows`), reading
the existing `.logs/agents` records but never backfilling them. `deltas --all` does that for
every done epic and adds the MdAPE over all of them. `deltas --buckets` prints
`calibration.bucket_table` over `ticket.calibration_rows`, the rows `new-task` uses.
`--json` prints any mode as JSON. Read-only: no file is written and nothing is committed.
"""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import calibration  # scripts/lib, on sys.path through ticket.py

from ticket_cmds import retro

METRICS = retro.METRICS  # (name, estimate key, actual key) for points, minutes, tokens
LABELS = {
    "points": ("Points", "estimate"),
    "minutes": ("Minutes", "expected"),
    "tokens": ("Tokens", "expected"),
}


def register(sub, t) -> None:
    sp = sub.add_parser("deltas", help="estimate against actual per task, and the bucket table")
    sp.set_defaults(fn=lambda a: run(a, t))
    sp.add_argument("epic", nargs="?")
    sp.add_argument("--all", action="store_true", help="every done epic")
    sp.add_argument(
        "--buckets", action="store_true", help="the per-points table new-task estimates from"
    )
    sp.add_argument("--json", action="store_true", help="machine-readable output")
    sp.add_argument(
        "--logs", help="the logs dir holding agents/ (default: the main checkout's .logs)"
    )


def run(a, t) -> int:
    if a.epic and a.all:
        raise t.TicketError("deltas: name an epic or pass --all, not both")
    if not (a.epic or a.all or a.buckets):
        raise t.TicketError("deltas: name an epic, or pass --all or --buckets")
    root = Path(a.root)
    out: dict = {}
    if a.epic:
        out = _report(a, t, root, t.resolve_epic(a.epic, root))
    elif a.all:
        base = root / "done"
        dirs = sorted(d for d in base.iterdir() if d.is_dir()) if base.is_dir() else []
        epics = [_report(a, t, root, d) for d in dirs]
        out = {"epics": epics, "mdape": _mdape([r for e in epics for r in e["rows"]])}
    if a.buckets:
        table = calibration.bucket_table(t.calibration_rows(root))
        out = {**out, "buckets": table} if out else table
    print(json.dumps(out, indent=2) if a.json else _text(a, out))
    return 0


# ---------------------------------------------------------------- rows


def _logs(a, t, root: Path) -> str | None:
    """The logs dir to read records from, never created (workbench.logs_dir would mkdir it)."""
    if a.logs:
        return a.logs
    found = t.workbench.existing_logs_dir(root)
    return str(found) if found else None


def _metric(estimate, actual) -> dict:
    known = None not in (estimate, actual)
    return {
        "estimate": estimate,
        "actual": actual,
        "difference": actual - estimate if known else None,
        "ratio": actual / estimate if known and estimate else None,
    }


def _report(a, t, root: Path, epic_dir: Path) -> dict:
    ns = SimpleNamespace(logs=_logs(a, t, root), transcripts=None)
    rows = []
    for r in retro._rows(ns, t, root, epic_dir, backfill=False):
        row = {"slug": r["slug"], "title": r["title"]}
        row.update({name: _metric(r[est], r[act]) for name, est, act in METRICS})
        rows.append(row)
    return {"epic": epic_dir.name, "rows": rows, "mdape": _mdape(rows)}


def _mdape(rows: list[dict]) -> dict:
    out = {}
    for name, _, _ in METRICS:
        pairs = [(r[name]["estimate"], r[name]["actual"]) for r in rows]
        out[name] = calibration.mdape([p for p in pairs if None not in p])
    return out


# ---------------------------------------------------------------- text


def _percent(value) -> str:
    return retro.NR if value is None else f"{value * 100:.1f}%"


def _epic_text(report: dict, heading: str) -> list[str]:
    header = ["Task"]
    for name, _, _ in METRICS:
        label, estimate = LABELS[name]
        header += [f"{label} ({estimate})", f"{label} (actual)"]
        header += [f"{label} (difference)", f"{label} (ratio)"]
    cells = []
    for row in report["rows"]:
        line = [row["title"]]
        for name, _, _ in METRICS:
            m = row[name]
            line += [retro._cell(m["estimate"]), retro._cell(m["actual"])]
            line += [retro._difference(m["estimate"], m["actual"])]
            line += [retro._ratio(m["estimate"], m["actual"])]
        cells.append(line)
    return [f"## {heading}", "", retro._table(header, cells), "", *_mdape_text(report["mdape"])]


def _mdape_text(mdape: dict) -> list[str]:
    return [f"- MdAPE {name}: {_percent(mdape[name])}" for name, _, _ in METRICS]


def _buckets_text(table: dict) -> list[str]:
    cells = [
        [str(p), str(b["minutes"]), str(b["tokens"]), str(b["n"]), b["source"]]
        for p, b in table.items()
    ]
    return ["## Buckets", "", retro._table(["Points", "Minutes", "Tokens", "n", "Source"], cells)]


def _text(a, out: dict) -> str:
    parts: list[list[str]] = []
    if a.epic:
        parts.append(_epic_text(out, out["epic"]))
    elif a.all:
        parts += [_epic_text(e, e["epic"]) for e in out["epics"]]
        parts.append(["## All done epics", "", *_mdape_text(out["mdape"])])
    if a.buckets:
        parts.append(_buckets_text(out["buckets"] if (a.epic or a.all) else out))
    return "\n\n".join("\n".join(p) for p in parts)
