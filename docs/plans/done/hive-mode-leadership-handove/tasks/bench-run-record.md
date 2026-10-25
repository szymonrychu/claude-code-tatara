---
title: bench run record
status: done
repo: agent-orchestrator
value: the measured hive result is on record
files: [MEMORY.md]
verify: "uv run pytest tests/test_bench.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [helmfile-apply-smoke]
model: ""
review: ""
verified_head: 341fa68f3a58cab7b7897e277b3500368da18e97
points: 1
expected_minutes: 5
expected_tokens: 750000
points_actual: ""
actual_minutes: 14
actual_tokens: 812648
actual_roles: "impl 13, review 1"
actual_role_tokens: "impl 673239, review 139409"
---

# bench run record

## Requirement

Record the speed-up result (Q12). Against the deployed release, run `orch bench examples/bench.yaml` with arms single, rr3, rr3-peers and hive3 (every multi-replica arm is a hive now). Record in MEMORY.md, dated: per-arm median wall time, failed turns, tokens, verify pass rate and final leader epoch, the token multiple versus single, and the verdict on "3 agents faster than 1". No switch follows from the result either way (Q12); the record is the deliverable.

## Acceptance conditions

- AC1: MEMORY.md has the dated bench entry with every arm including hive3 [evidence: command:grep -q "hive3" MEMORY.md]
- AC2: the entry states wall time, failed turns, tokens, verify pass rate, the token multiple and the verdict per arm [evidence: judgement:]
- AC3: bench tests and lint pass [evidence: command:uv run pytest tests/test_bench.py -q && uv run ruff check . && uv run ruff format --check .]

## Files

- `MEMORY.md`

## Interfaces

- Uses `orch bench` and `examples/bench.yaml` from bench-hive-arm against the deployed API.

## Expected outcome

MEMORY.md holds the measured result of hive versus single.

## Steps

- Run `uv run orch bench examples/bench.yaml` against the deployed API; read the report.
- Write the MEMORY entry; run the verify command: passes.

## Notes

- The bench talks only to `/api/v1`; it needs an allowed source address (port-forward as in agents-helmfile smoke).
