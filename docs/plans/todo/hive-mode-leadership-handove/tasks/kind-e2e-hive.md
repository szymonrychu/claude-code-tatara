---
title: kind e2e hive
status: todo
repo: agent-orchestrator
value: "CI proves on a real cluster that leadership, locks, notes and the alone mode work through the APIs alone"
files: [tests/e2e/test_e2e_kind.py, tests/e2e/conftest.py, e2e/agent-test.scenario.json]
verify: "uv run pytest -q -p no:cacheprovider -m e2e --collect-only tests/e2e/test_e2e_kind.py && uv run ruff check . && uv run ruff format --check ."
depends_on: [render-hive-gating, plugin-config-merge, file-locks-api, hive-state-push-loop, leader-routing, views-leader-stream, chart-agents-service, agent-api-me]
owns: []
uses: [orch-agents-service, orch-plugin-entry, orch-hive-state-note]
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

# kind e2e hive

## Requirement

API-only kind e2e (X2) in `tests/e2e/test_e2e_kind.py` (marker `e2e`, run by `mise run test:e2e` and the PR CI e2e job), reusing the `api` and `cluster` fixtures with bounded waits. Agent-originated calls run through `kubectl exec` into an agent pod with `python3` (urllib) and the pod's own `$ORCH_AGENT_URL` and `$ORCH_AGENT_TOKEN` (the fake claude cannot call MCP tools).

- `test_agent_api_identity` (D1): in a 2-replica cluster, `GET /agent/v1/me` from `agent-<slug>-0` with the token is 200 with the matching pod_name; a non-agent probe pod with the same token gets 403 `forbidden`; the agent pod without the token gets 401; `/api/v1/clusters` on the agents port is 404. `test_in_cluster_pod_refused_by_allowlist` stays unchanged.
- `test_leadership_handover_routes`: the cluster view shows a leader with epoch 1; the leader posts a handover to the other agent (202); the view shows the new leader with epoch 2 within the bound; the next untargeted message runs on the new leader.
- `test_user_make_leader`: `POST /api/v1/clusters/{id}/leader` is 202 and the view follows.
- `test_advisory_locks`: claim from pod 0, list from pod 1 shows it, a claim from pod 1 reports it held, the check webhook from pod 1 returns additional_context naming pod 0, reassign from a member is 403, discard by the leader succeeds.
- `test_hive_notes_delivered`: a scripted Write on agent A (scenario in `e2e/agent-test.scenario.json`) shows up as a `note_received` event naming the path on agent B (cluster events API), and both agents receive a `hive_state` note.
- `test_alone_cluster_has_no_hive_tools`: a 1-replica static cluster's ConfigMap has peers and notes disabled and its any-mcp JSON has no orchestrator entry.
Test-only task: the real run is the PR CI e2e job.

## Acceptance conditions

- AC1: the new e2e tests are collected under the e2e marker [evidence: command:uv run pytest -q -p no:cacheprovider -m e2e --collect-only tests/e2e/test_e2e_kind.py]
- AC2: the tests cover identity, handover routing, user make leader, locks, notes delivery and the alone cluster through the public and agent APIs only [evidence: judgement:tests/e2e/test_e2e_kind.py reviewed against the requirement; executed by the PR CI e2e job]
- AC3: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

## Files

- `tests/e2e/test_e2e_kind.py`
- `tests/e2e/conftest.py`
- `e2e/agent-test.scenario.json`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
