---
title: smoke step7 per-wait deadlines
status: todo
repo: agents-helmfile
value: the scale-below-leader smoke step never fails spuriously on a slow pod-1
files: [scripts/smoke.sh, tests/test_smoke_script.py, MEMORY.md]
verify: "uv run pytest -q tests/test_smoke_script.py && mise run lint"
depends_on: [helmfile-apply-smoke]
model: sonnet
review: ""
verified_head: ""
points: 2
expected_minutes: 5
expected_tokens: 546295
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# smoke step7 per-wait deadlines

## Requirement

Epic review finding (leader-auto-handover review, 2026-10-27, Consider 1), accepted by the hive leader as a task: "smoke step 7 per-wait deadlines + MEMORY line fix (agents-helmfile, sonnet)".

Evidence from the review: in `scripts/smoke.sh` step 7, the agent1 lookup loop and the "leader became pod-1" (make-leader) wait run on the `deadline` set before `scale 2`, which the pod-1 Ready wait already consumed (main 0ed86cf: deadline set at :538, reused at :564 and :577). A slow pod-1 Ready leaves those waits little or no budget, so the smoke can fail spuriously. MEMORY.md:24 claims "each wait gets its own SMOKE_TIMEOUT_S deadline", which is false for these two waits.

Scope:
- `scripts/smoke.sh` step 7: every wait in step 7 (pod-1 appear + Ready, agent1 lookup, make-leader wait including its retries, leader moved to pod-0 with `scale_down`, pod-1 gone) starts its own `SMOKE_TIMEOUT_S` deadline. Read the current main code first; d1c09ff ("wait for agent ready and retry make-leader") changed this region after the epic merge. Failure messages stay as they are.
- `tests/test_smoke_script.py`: a test, written first and seen failing, proving the agent1 lookup and the make-leader wait get their own window after a pod-1 Ready wait that used most of `SMOKE_TIMEOUT_S` (use the existing fake-binary harness).
- `MEMORY.md`: the 2026-10-26 step 7 line stays true (each wait gets its own deadline), with a dated note of this fix.
No other behaviour change.

## Acceptance conditions

- AC1: each step 7 wait starts its own SMOKE_TIMEOUT_S deadline, pinned by a test where pod-1 Ready uses most of the timeout [evidence: command:uv run pytest -q tests/test_smoke_script.py]
- AC2: shellcheck, ruff and gitleaks pass [evidence: command:mise run lint]
- AC3: MEMORY.md records the per-wait deadline fix [evidence: command:grep -q "own SMOKE_TIMEOUT_S deadline" MEMORY.md]

## Files

- `scripts/smoke.sh`
- `tests/test_smoke_script.py`
- `MEMORY.md`

## Interfaces

- `scripts/smoke.sh` step 7 (scale 1 -> 2 -> 1): same log and failure messages, same order of waits; only the deadlines change.
- `tests/test_smoke_script.py` fake-binary harness (fake curl/kubectl) as used by the existing step 7 tests.

## Expected outcome

Every wait in step 7 gets its own `SMOKE_TIMEOUT_S` window; a pod-1 Ready that uses most of the timeout no longer starves the agent lookup or the make-leader wait; MEMORY.md says so truthfully.

## Steps

- Read scripts/smoke.sh step 7 on the current tree, tests/test_smoke_script.py and MEMORY.md in one pass.
- Red: add the test (pod-1 Ready slow, near SMOKE_TIMEOUT_S, then agent lookup / make-leader need time); `uv run pytest -q tests/test_smoke_script.py` fails on the new test only.
- Green: reset `deadline` before each step 7 wait; the same command passes.
- MEMORY.md: dated note of the fix; `grep -q "own SMOKE_TIMEOUT_S deadline" MEMORY.md` exits 0.
- `mise run lint`: exit 0.

## Notes

d1c09ff (after the epic merge) added the agent-ready wait and make-leader retry in this region; build on it. Never run `mise run smoke` or `mise run apply` (live); the orchestrator does that. helmfile-apply-smoke commits its MEMORY.md entry first in the same tree; keep it.
