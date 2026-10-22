---
title: "ruff E501 errors in scripts/tests/test_secret_scanning.py (e.g. line 193) make `mise run lint` root fail after merging the epic branch"
status: done
repo: workbench
value: "owned by the gitlink-free secrets scan task; lint:root fails until fixed"
files: ["scripts/tests/test_secret_scanning.py:193"]
verify: ""
depends_on: []
owns: []
uses: []
model: ""
estimate: ""
estimate_by: ""
actual: ""
actual_roles: ""
review: ""
worktree: /Users/szymonri/Documents/workbench/.claude/worktrees/init-leaves-a-green-tree-ruff-e501-errors-in-scripts
branch: init-leaves-a-green-tree-ruff-e501-errors-in-scripts
verified_head: 5619cda9d76f90d8717064e2dddaac772bfe5bdd
run: init-leaves-a-green-tree
provides: []
acs_for_audit: []
process_gaps: []
---

# ruff E501 errors in scripts/tests/test_secret_scanning.py (e.g. line 193) make `mise run lint` root fail after merging the epic branch

## Requirement

ruff E501 errors in scripts/tests/test_secret_scanning.py (e.g. line 193) make `mise run lint` root fail after merging the epic branch

Where: scripts/tests/test_secret_scanning.py:193

Why: owned by the gitlink-free secrets scan task; lint:root fails until fixed

## Acceptance conditions

- AC1: ruff E501 errors in scripts/tests/test_secret_scanning.py (e.g. line 193) make `mise run lint` root fail after merging the epic branch at scripts/tests/test_secret_scanning.py:193 is resolved [evidence: judgement]

## Files

- `scripts/tests/test_secret_scanning.py:193`

## Interfaces

Keep the interfaces around scripts/tests/test_secret_scanning.py:193 unchanged unless resolving it requires otherwise: ruff E501 errors in scripts/tests/test_secret_scanning.py (e.g. line 193) make `mise run lint` root fail after merging the epic branch.

## Expected outcome

ruff E501 errors in scripts/tests/test_secret_scanning.py (e.g. line 193) make `mise run lint` root fail after merging the epic branch at scripts/tests/test_secret_scanning.py:193 is resolved, and owned by the gitlink-free secrets scan task; lint:root fails until fixed no longer applies.

## Steps

1. Write a failing test that shows: ruff E501 errors in scripts/tests/test_secret_scanning.py (e.g. line 193) make `mise run lint` root fail after merging the epic branch.
2. Fix it at scripts/tests/test_secret_scanning.py:193.
3. Run the task verify command and confirm it passes.

## Ruling

- 2026-10-22 accepted: e2e-init-green: verifier timed out (540s deadline vs 48-min file); hand-verified on 27d001e: 'mise exec -- pytest scripts/tests/e2e/test_instantiate.py -q' -> 7 passed in 2867.48s. ruff-e501: no change needed, the wrap landed in ce694a7; no targeted tests apply (pure formatting).

## Notes

Discovered in task `init-writes-allow-entries` during run `init-leaves-a-green-tree`.

