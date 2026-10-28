---
title: orch e2e rollout mid turn
status: in-progress
repo: agents-orchestrator
value: a deploy that rolls agents mid-turn is proven safe end to end on every PR
files: [tests/e2e/test_e2e_kind.py, e2e/agent-test.scenario.json, scripts/e2e.sh, e2e/values-kind.yaml]
verify: "uv run pytest -q -p no:cacheprovider -m e2e --collect-only tests/e2e/test_e2e_kind.py && uv run ruff check . && uv run ruff format --check ."
depends_on: [orch-wrapper-pin-patch, orch-rollout-replacer, orch-ingester-reattach, orch-e2e-main-failure, orch-default-continue-prompt, orch-dead-agent-ineligible]
model: sonnet
review: ""
verified_head: ""
points: 5
expected_minutes: 8
expected_tokens: 1828146
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# orch e2e rollout mid turn

## Requirement

Design D11, user decision verbatim: "Regression e2e (kind, tests/e2e/test_e2e_kind.py): roll the agent image (helm upgrade to a second tag of the same image) while a slow turn runs; assert the busy pod is not replaced until idle, the leader rolls last, the wrapper session id is unchanged, the interrupted/queued messages are delivered and the agent never stays dead. Lengthen the fake "slow" turn as needed."

Design D11 (my call), verbatim: "A new scenario turn (its own match text) holds the long turn, so the 4 s "slow" turn other tests rely on is unchanged. For "interrupted" messages the test also deletes one busy pod by hand (a crash, accepted under D1): it returns on the new template, its wrapper session id is unchanged and its interrupted turn completes through the D5 continuation."

Goal G9, verbatim: "A kind e2e rolls the agent image while a turn is running and proves no busy pod is replaced, the turn continues, and queued messages are delivered."

Scope (agents-orchestrator):
- `e2e/agent-test.scenario.json`: a long turn (its own match text, long enough to span the roll) and a turn matching the rendered default continue prompt so a continued turn completes.
- `scripts/e2e.sh`: also tags and loads the agent-test image under a second tag; `e2e/values-kind.yaml`: `ORCH_AGENT_IMAGES` allows both tags.
- `tests/e2e/test_e2e_kind.py`, API only plus kubectl for pod uids and revisions: a 2-replica hive; a long turn runs on the non-leader; `helm upgrade --reuse-values --set agentImage=<second tag>`; assert: the busy pod keeps its uid until its turn completed, then is replaced; the leader's pod is replaced last and after the leader moved; every agent's wrapper session id (events API `wrapper_session_id`) is unchanged; messages posted during the roll reach `sent` with completed turns and none is `failed`; no agent stays `dead` past a deadline; then a busy pod deleted by hand returns on the new revision with the same wrapper session id and its interrupted turn completes. Every session is discarded in teardown; the release is upgraded back to the first tag.

Steps: scenario and script first; then the test; `uv run pytest -q -p no:cacheprovider -m e2e --collect-only tests/e2e/test_e2e_kind.py`; the PR CI e2e job passes.

Notes: run with `mise run test:e2e` (kind; or the PR CI e2e job; `E2E_HOLD_FILE` for one test). Reuse `wait_for`, `pods_of`, `scale_session`, the message helpers and `test_scale_down_waits_for_busy_agent` (mid-turn pattern). Needs the pinned wrapper with the continuation (task orch-wrapper-pin-patch) and the replacer, re-attach and default prompt tasks.


Amendment 2026-10-28 (supervisor, design D1 transition bullet): the test also proves the RollingUpdate-to-OnDelete transition on a real API server: with a busy agent, `kubectl patch` its StatefulSet to `updateStrategy: {type: RollingUpdate}` (strategy only, as a StatefulSet created by the previous release has it, partition defaulted), then trigger a template change (`helm upgrade ... --set agentImage=<second tag>`); assert the orchestrator's apply succeeds (no reconciler apply error in its logs or session status), the StatefulSet ends `type: OnDelete` without `rollingUpdate`, and the busy pod keeps its uid until its turn completed (the controller rolled nothing).

## Acceptance conditions

- AC1: the new e2e tests are collected under the e2e marker [evidence: command:uv run pytest -q -p no:cacheprovider -m e2e --collect-only tests/e2e/test_e2e_kind.py]
- AC2: on kind, a helm upgrade to a second agent image tag does not replace the busy pod until its turn completed [evidence: command:mise run test:e2e]
- AC3: on kind, the leader's pod is replaced last, after leadership moved [evidence: command:mise run test:e2e]
- AC4: on kind, every agent keeps its wrapper session id across the roll and no agent stays dead [evidence: command:mise run test:e2e]
- AC5: on kind, messages posted during the roll are delivered and none fails [evidence: command:mise run test:e2e]
- AC6: on kind, a busy pod deleted by hand returns on the new revision with the same wrapper session id and its interrupted turn completes [evidence: command:mise run test:e2e]
- AC7: the scenario stays valid JSON and keeps the 4 s slow turn [evidence: command:python3 -c "import json; d = json.load(open('e2e/agent-test.scenario.json')); t = [x for x in d['turns'] if x['match'] == 'slow'][0]; assert {'sleep': 4} in t['steps'] and len(d['turns']) >= 5"]
- AC9: on kind, a StatefulSet left on RollingUpdate is switched to OnDelete by a template-changing apply without the controller replacing the busy pod [evidence: command:mise run test:e2e]
- AC8: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

## Files

- `tests/e2e/test_e2e_kind.py`
- `e2e/agent-test.scenario.json`
- `scripts/e2e.sh`
- `e2e/values-kind.yaml`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

- Red: write the tests the requirement and acceptance conditions name (or, for a release/deploy/CI step, the check the evidence names); run `"uv run pytest -q -p no:cacheprovider -m e2e --collect-only tests/e2e/test_e2e_kind.py && uv run ruff check . && uv run ruff format --check ."` and see them fail for the expected reason.
- Green: implement the requirement exactly as written; run `"uv run pytest -q -p no:cacheprovider -m e2e --collect-only tests/e2e/test_e2e_kind.py && uv run ruff check . && uv run ruff format --check ."` and expect every check to pass, quoting the summary line.
- Refactor with the verify still green; update MEMORY.md with a dated entry for any non-obvious decision.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.

- 2026-10-28 amended: D1 transition amendment: prove RollingUpdate->OnDelete switch on a real API server
