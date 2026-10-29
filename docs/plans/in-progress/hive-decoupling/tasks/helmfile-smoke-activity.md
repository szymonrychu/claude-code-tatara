---
title: helmfile smoke activity
status: in-progress
repo: agents-helmfile
value: the live smoke proves the activity route and tool on every deploy
files: [scripts/smoke.sh, tests/test_smoke_script.py]
verify: "uv run --frozen pytest -q -p no:cacheprovider tests/test_smoke_script.py && mise run lint"
depends_on: [orch-hive-tools-activity]
model: sonnet
review: ""
verified_head: ""
points: 3
expected_minutes: 6
expected_tokens: 936557
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# helmfile smoke activity

## Requirement

README Goal G5, verbatim: "Released and deployed: any-mcp-tatara-plugins next minor tag, orchestrator pins, agents-helmfile bump, apply, a smoke covering the activity route and tool, and a live handoff proof."

Design D11, verbatim: "the agents-helmfile smoke grows: step 4a also requires `orchestrator_activity` in `--list-tools` (parsed as JSON), and a step 6a calls `GET /agent/v1/activity` from the agent pod with its own env and requires 200 with a `lines` array."

Scope (agents-helmfile):
- `scripts/smoke.sh`: step 4a requires `orchestrator_activity` in the `--list-tools` JSON array (jq, like the existing `orchestrator_sessions_list` check); new step 6a after step 6: from the hive pod, with its own `ORCH_AGENT_URL`, `ORCH_AGENT_TOKEN`, `ORCH_SESSION_ID`, `GET /agent/v1/activity?limit=5` must answer 200 with a JSON object whose `lines` is an array (python3 in the pod prints the status and `isinstance(body.get("lines"), list)`; nothing else printed); header comment updated. Any wait added has its own deadline.
- `tests/test_smoke_script.py`: the fake kubectl answers the activity call with the real route shape `{"lines": [{"id": 1, "agent": "agent-x-0", "text": "agent-x-0 ran: true (ok)", "ts": "2026-10-27T00:00:00+00:00"}]}` as rendered status lines; the fake `--list-tools` output gains `orchestrator_activity` in its JSON array; the new tests below.
- The smoke runs against the deployed release only after helmfile-deploy-pin's apply; the step is in the same agents-helmfile PR as the pin.

## Acceptance conditions

- ac1: step 6a calls /agent/v1/activity inside the hive pod with the pod's own env and passes on 200 with a lines array [evidence: test:tests/test_smoke_script.py::test_agent_activity_check_runs_in_pod_with_its_own_env]
- ac2: step 6a fails the smoke on a non-200 answer or a body without a lines array [evidence: test:tests/test_smoke_script.py::test_agent_activity_check_fails_without_lines]
- ac3: step 4a fails the smoke when --list-tools lists no orchestrator_activity [evidence: test:tests/test_smoke_script.py::test_plugin_tools_require_activity]
- ac4: every new wait has its own deadline and the fakes answer the real route and --list-tools JSON shapes [evidence: judgement:reviewer checks each timeout in the smoke diff and compares the fakes with the route contract in agents-orchestrator README Agent API]
- ac5: the smoke script tests and lint pass [evidence: command:uv run --frozen pytest -q -p no:cacheprovider tests/test_smoke_script.py && mise run lint]

## Files

- `scripts/smoke.sh`
- `tests/test_smoke_script.py`

## Interfaces

- Smoke step 4a: `jq -e 'any(.[]?; .name == "orchestrator_activity")'` over `--list-tools`; step 6a: in-pod python prints `<status> <has_lines>`.

## Expected outcome

Every `mise run smoke` proves the activity route from an agent pod and the tool in the plugin listing.

## Steps

- Red: the tests of ac1-ac3 in `tests/test_smoke_script.py` with the fake kubectl; run `uv run --frozen pytest -q -p no:cacheprovider tests/test_smoke_script.py`: they fail.
- Green: `scripts/smoke.sh` steps 4a and 6a and the header comment; run the task's verify: passes. Quote the summary line.

## Notes

- Mirror the step 6 `/agent/v1/me` check (`smoke.sh:346-356`) and its tests `test_agent_me_check_*` (`tests/test_smoke_script.py:950-964`).
- Recurring retro: fakes must answer the real output shapes; each wait gets its own deadline.
