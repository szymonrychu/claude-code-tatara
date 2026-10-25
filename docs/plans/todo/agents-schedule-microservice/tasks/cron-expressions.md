---
title: cron expressions
status: todo
repo: agents-schedule
value: "a schedule's cron and timezone are validated once and its fire times are computed the same way everywhere"
files: [src/agents_schedule/cron.py, tests/test_cron.py]
verify: "uv run --frozen pytest tests/test_cron.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [scaffold-project-and-cli]
owns: [sched-cron]
uses: []
model: ""
estimate: 5
estimate_by: formula
actual: ""
actual_roles: ""
review: ""
worktree: ""
branch: ""
verified_head: ""
run: ""
provides: []
---

# cron expressions

## Requirement

Add `agents_schedule.cron` (design D4, D5; approvals A2, A3), pure functions over croniter and zoneinfo, no DB:

- `validate_cron(expr) -> str`: strips and collapses whitespace; exactly 5 fields (`^(\S+\s+){4}\S+$`, the tatara-new CRD pattern) and accepted by croniter; macros (`@daily`), seconds and year fields are refused. Raises `CronError(code="invalid_cron", message)` with the reason.
- `validate_timezone(name) -> ZoneInfo`: IANA name via zoneinfo; raises `CronError(code="invalid_timezone")`.
- `next_fires(expr, tz, after, n=3) -> list[datetime]`: the next n fire times strictly after `after`, tz-aware in `tz`.
- `due(expr, tz, stamp, now) -> Due(fire_time: datetime | None, skipped: int)`: tatara-new parity (`TN/internal/controller/projectscan.go:activityDue`): nothing is due while `next(stamp) > now`. Otherwise `fire_time` is the latest fire time in `(stamp, now]` (one catch-up run) and `skipped` counts the earlier fire times in that interval, which are not run. `stamp` is the latest scheduled fire time already recorded or the schedule's `armed_at`.
- DST in the schedule's zone: a wall time that does not exist on the spring-forward day fires once at croniter's resolution, and an ambiguous wall time on the fall-back day fires once, never twice.

## Acceptance conditions

- AC1: a valid 5-field expression is normalised [evidence: test:tests/test_cron.py::test_validate_normalises]
- AC2: 4 or 6 fields, macros and nonsense are refused with invalid_cron [evidence: test:tests/test_cron.py::test_validate_refuses]
- AC3: an unknown timezone is refused with invalid_timezone [evidence: test:tests/test_cron.py::test_timezone_refused]
- AC4: next_fires returns 3 tz-aware times strictly after the given instant [evidence: test:tests/test_cron.py::test_next_fires]
- AC5: after downtime spanning several fire times exactly one is due, the latest, and the rest are counted as skipped [evidence: test:tests/test_cron.py::test_due_collapses_missed_runs]
- AC6: nothing is due before the next fire time [evidence: test:tests/test_cron.py::test_not_due_before_next]
- AC7: fall-back day fires once, spring-forward day does not crash or double fire in Europe/Warsaw [evidence: test:tests/test_cron.py::test_dst_transitions_fire_once]

## Files

- `src/agents_schedule/cron.py`
- `tests/test_cron.py`

## Interfaces

- `agents_schedule.cron:validate_cron(expr: str) -> str`, `validate_timezone(name: str) -> ZoneInfo`, `next_fires(expr: str, tz: ZoneInfo, after: datetime, n: int = 3) -> list[datetime]`, `due(expr: str, tz: ZoneInfo, stamp: datetime, now: datetime) -> Due`, `Due(fire_time: datetime | None, skipped: int)`, `CronError(code: str, message: str)` (part `sched-cron`).

## Expected outcome

The api validates and previews schedules and the scheduler decides firings with the same functions.

## Steps

- Write tests/test_cron.py with the seven named tests (fixed instants, no clock); run it: fails.
- Write cron.py; `uv run --frozen pytest tests/test_cron.py -q`: `7 passed`.
- Lint clean.

## Notes

- croniter 6.2.4 is maintained (released 2026-07-10, probed on PyPI 2026-10-25); cronsim 2.7 was the alternative (my call, design D4).
- All datetimes are tz-aware; compare in UTC, compute in the schedule's zone.
