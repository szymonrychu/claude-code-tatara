"""Expected minutes and tokens per storypoint, calibrated from done-task actuals.

Rows are plain dicts with int `points`, `actual_minutes` and `actual_tokens` (optionally
`expected_minutes`, `expected_tokens`, `points_actual`); ticket.py collects them from done
tasks. A points bucket with MIN_BUCKET rows uses its median; otherwise, with MIN_REFIT
usable rows overall, the least-squares line over points; otherwise the SEED table.
Stdlib only, Python 3.9 safe.
"""

from __future__ import annotations

import statistics

POINTS = (1, 2, 3, 5, 8, 13)
MIN_BUCKET = 3
MIN_REFIT = 5
# Probe of this machine's transcripts on 2026-10-24: a median task (about 34 min, 2.25M
# tokens) taken as 3 points and scaled linearly (design D15).
SEED = {
    1: (11, 750000),
    2: (23, 1500000),
    3: (34, 2250000),
    5: (57, 3750000),
    8: (91, 6000000),
    13: (147, 9750000),
}
TARGETS = ("actual_minutes", "actual_tokens")


def _solve(a: list, b: list) -> list | None:
    """Solve a x = b by Gauss-Jordan elimination; None when the system is singular."""
    n = len(b)
    m = [row[:] + [b[i]] for i, row in enumerate(a)]
    for c in range(n):
        piv = max(range(c, n), key=lambda r: abs(m[r][c]))
        if abs(m[piv][c]) < 1e-12:
            return None
        m[c], m[piv] = m[piv], m[c]
        for r in range(n):
            if r != c:
                f = m[r][c] / m[c][c]
                m[r] = [m[r][k] - f * m[c][k] for k in range(n + 1)]
    return [m[i][n] / m[i][i] for i in range(n)]


def _int(v) -> bool:
    return isinstance(v, int) and not isinstance(v, bool)


def usable(rows: list) -> list:
    """Rows with points on the scale and both actuals as non-negative ints."""
    return [
        r
        for r in rows
        if r.get("points") in POINTS
        and _int(r.get("points"))
        and all(_int(r.get(k)) and r[k] >= 0 for k in TARGETS)
    ]


def refit(rows: list, target: str) -> tuple[float, float] | None:
    """Least-squares (intercept, slope) of `target` over points; None when singular."""
    pts = usable(rows)
    sx = float(sum(r["points"] for r in pts))
    a = [[float(len(pts)), sx], [sx, float(sum(r["points"] ** 2 for r in pts))]]
    b = [float(sum(r[target] for r in pts)), float(sum(r["points"] * r[target] for r in pts))]
    sol = _solve(a, b)
    return None if sol is None else (sol[0], sol[1])


def mdape(pairs: list) -> float | None:
    """Median absolute percentage error of (predicted, actual) pairs; zero actuals skipped."""
    errs = [abs(pred - act) / act for pred, act in pairs if act]
    return statistics.median(errs) if errs else None


def _estimate(points: int, rows: list) -> tuple[int, int, str, int]:
    if points not in POINTS:
        raise ValueError(f"points must be one of {POINTS}, got {points!r}")
    pts = usable(rows)
    bucket = [r for r in pts if r["points"] == points]
    if len(bucket) >= MIN_BUCKET:
        m, t = (round(statistics.median(r[k] for r in bucket)) for k in TARGETS)
        return m, t, "history", len(bucket)
    if len(pts) >= MIN_REFIT:
        fits = [refit(pts, k) for k in TARGETS]
        if None not in fits:
            m, t = (max(1, round(a + s * points)) for a, s in fits)
            return m, t, "refit", len(bucket)
    m, t = SEED[points]
    return m, t, "seed", len(bucket)


def expected(points: int, rows: list) -> tuple[int, int]:
    """Expected (minutes, tokens) for a task of `points` storypoints."""
    m, t, _, _ = _estimate(points, rows)
    return m, t


def bucket_table(rows: list) -> dict:
    """Per points value: expected minutes and tokens, bucket size n, and their source."""
    table = {}
    for p in POINTS:
        m, t, source, n = _estimate(p, rows)
        table[p] = {"minutes": m, "tokens": t, "n": n, "source": source}
    return table
