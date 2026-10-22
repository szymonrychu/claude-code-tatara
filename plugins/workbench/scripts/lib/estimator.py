#!/usr/bin/env python3
"""Agent-time estimator: task minutes from files and verify kind, epic wall time, refit.

Every number comes from estimator.json beside this module. Stdlib only.
"""

import argparse
import importlib.util
import json
import math
import re
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_PATH = HERE / "estimator.json"
TICKET = HERE.parents[1] / "skills" / "start-development" / "scripts" / "ticket.py"


def load(path=None) -> dict:
    return json.loads(Path(path or DEFAULT_PATH).read_text())


def _norm(s: str) -> str:
    return " ".join(s.split())


def full_suite(cmd: str, suites=(), params=None) -> bool:
    """True when any &&-, ||- or ;-separated part of cmd is a whole-suite run."""
    pats = [re.compile(p) for p in (params or load())["fullSuitePatterns"]]
    known = {_norm(s) for s in suites}
    for part in re.split(r"&&|\|\||;", cmd or ""):
        part = _norm(part)
        if not part or re.match(r"^cd( |$)", part):
            continue
        if part in known or any(p.search(part) for p in pats):
            return True
    return False


def task_minutes(files: int, verify: str, suites=(), params=None) -> int:
    p = params or load()["task"]
    factor = p["fullSuiteFactor"] if full_suite(verify, suites) else 1
    return max(1, round(p["intercept"] * (files + 1) ** p["exponent"] * factor))


def parallelism(open_tasks: int, params=None) -> float:
    par = (params or load()["epic"])["parallelism"]
    lo, hi = par["low"], par["high"]
    if open_tasks <= lo["tasks"]:
        return round(lo["p"], 1)
    if open_tasks >= hi["tasks"]:
        return round(hi["p"], 1)
    frac = (open_tasks - lo["tasks"]) / (hi["tasks"] - lo["tasks"])
    return round(lo["p"] + frac * (hi["p"] - lo["p"]), 1)


def epic_estimate(tasks: list, params=None) -> dict:
    epic = params or load()["epic"]
    by_id = {t["id"]: t for t in tasks}
    best: dict = {}

    def path_to(tid: str, seen=()):
        if tid in best:
            return best[tid]
        t = by_id[tid]
        deps = [d for d in t.get("depends_on") or [] if d in by_id and d not in seen]
        sub = max((path_to(d, seen + (tid,)) for d in deps), key=lambda r: r[0], default=(0, []))
        best[tid] = (sub[0] + t["minutes"], sub[1] + [tid])
        return best[tid]

    cp, path = max((path_to(t) for t in by_id), key=lambda r: r[0], default=(0, []))
    total = sum(t["minutes"] for t in tasks)
    open_n = sum(1 for t in tasks if t.get("status") != "done")
    p = parallelism(open_n, epic)
    run_wall = max(cp, total / p)
    longest = sorted(
        ({"id": i, "minutes": by_id[i]["minutes"]} for i in path), key=lambda r: -r["minutes"]
    )[:3]
    return {
        "sum": total,
        "remaining": sum(t["minutes"] for t in tasks if t.get("status") != "done"),
        "cp": cp,
        "path": path,
        "p": p,
        "runWall": run_wall,
        "epicWall": epic["k"] * run_wall,
        "longest": longest,
    }


def _solve(a: list, b: list) -> list:
    n = len(b)
    m = [row[:] + [b[i]] for i, row in enumerate(a)]
    for c in range(n):
        piv = max(range(c, n), key=lambda r: abs(m[r][c]))
        if abs(m[piv][c]) < 1e-12:
            raise ValueError("refit: singular system (need varied files and both suite kinds)")
        m[c], m[piv] = m[piv], m[c]
        for r in range(n):
            if r != c:
                f = m[r][c] / m[c][c]
                m[r] = [x - f * y for x, y in zip(m[r], m[c], strict=True)]
    return [m[i][n] / m[i][i] for i in range(n)]


def refit(rows: list) -> dict:
    xs = [[1.0, math.log(r["files"] + 1), float(r["full"])] for r in rows]
    ys = [math.log(max(r["minutes"], 1)) for r in rows]
    a = [[sum(x[i] * x[j] for x in xs) for j in range(3)] for i in range(3)]
    b = [sum(x[i] * y for x, y in zip(xs, ys, strict=True)) for i in range(3)]
    b0, b1, b2 = _solve(a, b)
    return {
        "intercept": round(math.exp(b0), 3),
        "exponent": round(b1, 3),
        "fullSuiteFactor": round(math.exp(b2), 3),
    }


def mdape(rows: list, params: dict) -> float:
    errs = []
    for r in rows:
        pred = max(
            1,
            round(
                params["intercept"]
                * (r["files"] + 1) ** params["exponent"]
                * (params["fullSuiteFactor"] if r["full"] else 1)
            ),
        )
        errs.append(abs(pred - r["minutes"]) / r["minutes"])
    return statistics.median(errs)


def _ticket():
    spec = importlib.util.spec_from_file_location("ticket_estimator", TICKET)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["ticket_estimator"] = mod
    spec.loader.exec_module(mod)
    return mod


def rows_from_plans(root: Path, params: dict) -> list:
    t = _ticket()
    rows = []
    for phase in ("done", "in-progress"):
        for f in sorted((root / phase).glob("*/tasks/*.md")):
            meta = t.load(f.read_text(), f).meta
            try:
                actual = float(meta.get("actual") or 0)
            except ValueError:
                continue
            if actual > 0:
                rows.append(
                    {
                        "task": f.stem,
                        "files": len(meta.get("files") or []),
                        "full": int(full_suite(str(meta.get("verify", "")), params=params)),
                        "minutes": actual,
                    }
                )
    return rows


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    rf = sub.add_parser("refit")
    src = rf.add_mutually_exclusive_group(required=True)
    src.add_argument("--fixture")
    src.add_argument("--plans-root")
    rf.add_argument("--write", action="store_true")
    rf.add_argument(
        "--config", help="estimator.json to read and write (default: beside the module)"
    )
    a = ap.parse_args(argv)
    cfg_path = Path(a.config) if a.config else DEFAULT_PATH
    cfg = load(cfg_path)
    rows = (
        json.loads(Path(a.fixture).read_text())
        if a.fixture
        else rows_from_plans(Path(a.plans_root), cfg)
    )
    if not rows:
        print("refit: no rows with a positive actual", file=sys.stderr)
        return 1
    fit = refit(rows)
    out = {**fit, "mdape": round(mdape(rows, fit), 3), "n": len(rows)}
    if a.write:
        cfg["task"] = fit
        cfg_path.write_text(json.dumps(cfg, indent=2) + "\n")
    print(json.dumps(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
