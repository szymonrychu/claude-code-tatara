---
title: bench run record
status: todo
repo: agent-orchestrator
value: the measured hive result is on record
files: [MEMORY.md]
verify: "uv run pytest tests/test_bench.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [helmfile-apply-smoke]
owns: []
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

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
