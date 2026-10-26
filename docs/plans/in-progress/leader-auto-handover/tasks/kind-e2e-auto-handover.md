---
title: kind e2e auto handover
status: done
repo: agents-orchestrator
value: compaction and scale-down handovers are proven end to end through the API
files: [tests/e2e/test_e2e_kind.py, e2e/agent-test.scenario.json]
verify: "uv run pytest -q -p no:cacheprovider -m e2e --collect-only tests/e2e/test_e2e_kind.py && uv run ruff check . && uv run ruff format --check ."
depends_on: [orch-wrapper-pin-0-3-0, leadership-auto-handover, scale-down-staying-peer, reconciler-leader-pod-hold, leader-changed-reason, claim-hold-and-handover-wake]
model: sonnet
review: ""
verified_head: d56162d0a7d5a1fb2419d74301598fe054a17a09
points: 3
expected_minutes: 7
expected_tokens: 996161
points_actual: 3
actual_minutes: 21
actual_tokens: 795251
actual_roles: "impl 20, review 1"
actual_role_tokens: "impl 706561, review 88690"
---

# kind e2e auto handover

## Requirement

Goal G5, verbatim: "the UI, API and stream show automatic handovers with their reason (compaction, scale-down); documented API and API-only e2e test." Goals G1 and G2 end to end against the kind cluster with the pinned wrapper 0.3.0 test image.

Scope:
- `e2e/agent-test.scenario.json`: a new turn whose unique `match` (for example `compact mid turn`) runs `{"text": ...}`, then `{"auto_compact": {"pre_tokens": 150000}}` (the fake claude runs the PreCompact hook, so the wrapper emits `compacting`, then writes the compaction boundary), then a final `{"text": ...}`.
- `tests/e2e/test_e2e_kind.py`, API only (the public api client; kubectl only for pod presence as the existing scale tests do):
  - `test_leader_compaction_hands_over`: a 2-replica hive; after the first election, an untargeted message matching the new turn goes to the leader; the session's events include a `compacting` event of the leader; after that turn ends, the session view shows a different leader at a higher epoch with `leader_reason == "compaction"`, within `LEADER_TIMEOUT` after the turn completed; only after the view shows the new leader does the test send the next untargeted message, and that message is dispatched to the new leader (its `agent_id`).
  - `test_scale_down_below_leader_hands_over`: a hive of 3 (max 3); make the highest ordinal the leader through `POST /api/v1/sessions/{id}/leader`; `POST /scale {replicas: 2}` answers 202; the leader moves to an agent with a lower ordinal at a higher epoch with `leader_reason == "scale_down"`; the top pod is then gone and the surviving pods keep their uids.
  - Test no longer accurate, to update: `test_scale_refusals` asserts 409 `leader_would_leave` for a 3 to 2 scale with the top ordinal leading while both other agents are ready, which the user's decision now accepts. It keeps its `out_of_range` checks; its leader part moves to `test_scale_down_below_leader_hands_over`. The no-staying-agent refusal is covered by the unit tests of task scale-down-staying-peer (an e2e cannot make every lower agent unready without breaking the pods).
- Every session a test creates is discarded in its teardown (the existing context managers).

Notes: run locally or in PR CI with `mise run test:e2e` (`scripts/e2e.sh`; one test: `E2E_HOLD_FILE`, then `pytest tests/e2e/test_e2e_kind.py::<name>`). The agent-test image is built from the wrapper commit pinned by task orch-wrapper-pin-0-3-0, which must carry the `compacting` event. Reuse `wait_for`, `leader_view`, `wait_leader`, `live_agents`, `scale_to`, `scale_session` and the message helpers already in the file.

## Acceptance conditions

- AC1: the new e2e tests are collected under the e2e marker [evidence: command:uv run pytest -q -p no:cacheprovider -m e2e --collect-only tests/e2e/test_e2e_kind.py]
- AC2: on kind, a leader that compacts mid-turn hands over after its turn with reason `compaction`; the test sends its next untargeted message only after the session view shows the new leader, and that message is dispatched to the new leader [evidence: command:mise run test:e2e]
- AC3: on kind, a scale-down below the leader answers 202, moves leadership to a staying agent with reason `scale_down`, then removes the top pod [evidence: command:mise run test:e2e]
- AC4: the scenario file stays valid JSON with the new compaction turn [evidence: command:python3 -c "import json; d = json.load(open('e2e/agent-test.scenario.json')); assert any(any('auto_compact' in s for s in t['steps']) for t in d['turns'])"]
- AC5: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

## Files

- `tests/e2e/test_e2e_kind.py`
- `e2e/agent-test.scenario.json`

## Interfaces

See the Requirement and the acceptance conditions above.

## Expected outcome

See the Requirement and the acceptance conditions above.

## Steps

- Add the scenario turn and the two e2e tests, move the leader part out of `test_scale_refusals`; run `uv run pytest -q -p no:cacheprovider -m e2e --collect-only tests/e2e/test_e2e_kind.py`: the new tests are collected.
- Run `mise run test:e2e` (kind; or the PR CI e2e job): the new tests pass with the pinned wrapper image.
- Run the task's verify command: passes.

## Notes

See the Requirement and the acceptance conditions above.

- 2026-10-26 amended: interrogate 2026-10-26 (fable, opus, sonnet): finding 1 (send only after the new leader shows)

- 2026-10-26 done
