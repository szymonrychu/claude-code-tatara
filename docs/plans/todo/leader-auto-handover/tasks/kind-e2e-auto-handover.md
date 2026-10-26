---
title: kind e2e auto handover
status: todo
repo: agents-orchestrator
value: compaction and scale-down handovers are proven end to end through the API
files: [tests/e2e/test_e2e_kind.py, e2e/agent-test.scenario.json]
verify: "uv run pytest -q -p no:cacheprovider -m e2e --collect-only tests/e2e/test_e2e_kind.py && uv run ruff check . && uv run ruff format --check ."
depends_on: [orch-wrapper-pin-0-3-0, leadership-auto-handover, scale-down-staying-peer, reconciler-leader-pod-hold, leader-changed-reason]
model: sonnet
review: ""
verified_head: ""
points: 3
expected_minutes: 7
expected_tokens: 996161
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# kind e2e auto handover

## Requirement

Goal G5, verbatim: "the UI, API and stream show automatic handovers with their reason (compaction, scale-down); documented API and API-only e2e test." Goals G1 and G2 end to end against the kind cluster with the pinned wrapper 0.3.0 test image.

Scope:
- `e2e/agent-test.scenario.json`: a new turn whose unique `match` (for example `compact mid turn`) runs `{"text": ...}`, then `{"auto_compact": {"pre_tokens": 150000}}` (the fake claude runs the PreCompact hook, so the wrapper emits `compacting`, then writes the compaction boundary), then a final `{"text": ...}`.
- `tests/e2e/test_e2e_kind.py`, API only (the public api client; kubectl only for pod presence as the existing scale tests do):
  - `test_leader_compaction_hands_over`: a 2-replica hive; after the first election, an untargeted message matching the new turn goes to the leader; the session's events include a `compacting` event of the leader; after that turn ends, the session view shows a different leader at a higher epoch with `leader_reason == "compaction"`, within `LEADER_TIMEOUT` after the turn completed; the next untargeted message is dispatched to the new leader.
  - `test_scale_down_below_leader_hands_over`: a hive of 3 (max 3); make the highest ordinal the leader through `POST /api/v1/sessions/{id}/leader`; `POST /scale {replicas: 2}` answers 202; the leader moves to an agent with a lower ordinal at a higher epoch with `leader_reason == "scale_down"`; the top pod is then gone and the surviving pods keep their uids.
  - Test no longer accurate, to update: `test_scale_refusals` asserts 409 `leader_would_leave` for a 3 to 2 scale with the top ordinal leading while both other agents are ready, which the user's decision now accepts. It keeps its `out_of_range` checks; its leader part moves to `test_scale_down_below_leader_hands_over`. The no-staying-agent refusal is covered by the unit tests of task scale-down-staying-peer (an e2e cannot make every lower agent unready without breaking the pods).
- Every session a test creates is discarded in its teardown (the existing context managers).

Notes: run locally or in PR CI with `mise run test:e2e` (`scripts/e2e.sh`; one test: `E2E_HOLD_FILE`, then `pytest tests/e2e/test_e2e_kind.py::<name>`). The agent-test image is built from the wrapper commit pinned by task orch-wrapper-pin-0-3-0, which must carry the `compacting` event. Reuse `wait_for`, `leader_view`, `wait_leader`, `live_agents`, `scale_to`, `scale_session` and the message helpers already in the file.

## Acceptance conditions

- AC1: the new e2e tests are collected under the e2e marker [evidence: command:uv run pytest -q -p no:cacheprovider -m e2e --collect-only tests/e2e/test_e2e_kind.py]
- AC2: on kind, a leader that compacts mid-turn hands over after its turn with reason `compaction`, and the next untargeted message goes to the new leader [evidence: command:mise run test:e2e]
- AC3: on kind, a scale-down below the leader answers 202, moves leadership to a staying agent with reason `scale_down`, then removes the top pod [evidence: command:mise run test:e2e]
- AC4: the scenario file stays valid JSON with the new compaction turn [evidence: command:python3 -c "import json; d = json.load(open('e2e/agent-test.scenario.json')); assert any(any('auto_compact' in s for s in t['steps']) for t in d['turns'])"]
- AC5: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

## Files

- `tests/e2e/test_e2e_kind.py`
- `e2e/agent-test.scenario.json`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
