---
title: kind e2e scaling
status: todo
repo: agent-orchestrator
value: CI proves on a real cluster that agents join and leave without restarting the others
files: [tests/e2e/test_e2e_kind.py, e2e/values-kind.yaml]
verify: "uv run pytest -q -p no:cacheprovider -m e2e --collect-only tests/e2e/test_e2e_kind.py && uv run ruff check . && uv run ruff format --check ."
depends_on: [public-scale-route, agent-scale-route, scale-tool-allow, scale-down-drain]
owns: []
uses: [orch-cluster-scale-api, orch-agent-scale-api, scale-drain-status]
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

# kind e2e scaling

## Requirement

Prove dynamic join and leave, the scale routes and the static switch on kind through the API alone (design D1-D4; user S1, S2, S3, Q2, Q4, Q7, X2). In `tests/e2e/test_e2e_kind.py` (marker `e2e`, `mise run test:e2e`, PR CI `e2e` job) add, using `/api/v1` over the port-forward, `kubectl` only for pod uids and annotations, and `kubectl exec` into agent pods for `/agent/v1` (the foundation D1 pattern; the fake claude cannot call MCP tools):
- `test_scale_up_and_down_keeps_surviving_pods`: a cluster `{replicas: 1, max_replicas: 3}`; record pod uids and the config-hash annotation; `POST .../scale {replicas: 3}` is 202; three agents become ready; pod-0 keeps its uid and the hash annotation is unchanged; agent-0's `/agent/v1/me` lists three members and the leader is unchanged (a joining agent never leads, Q2); `POST .../scale {replicas: 2}`: agent-2's pod is gone, its AgentView is `gone`, pods 0 and 1 keep their uids, `/agent/v1/me` lists two members.
- `test_scale_refusals`: `replicas` 0 and 4 are 422 `out_of_range`; a static cluster `{replicas: 2, max_replicas: 2, static: true}` is 409 `static_cluster`; after `POST .../leader` makes agent-2 leader (hive route) a scale to 2 is 409 `leader_would_leave`.
- `test_agent_scale_leader_only`: from the leader pod `POST $ORCH_AGENT_URL/agent/v1/scale` with `$ORCH_AGENT_TOKEN` is 202; from another agent pod it is 403 `not_leader`.
- `test_static_single_pod_is_alone`: `{replicas: 1, max_replicas: 1, static: true}`: the pod's rendered any-mcp config has no scale or hive tools in the orchestrator entry's allow list and the rendered ccw config has peers disabled.
- When the scripted fake claude can hold a turn open (check `e2e/agent-test.scenario.json`), `test_scale_down_waits_for_busy_agent`: a turn targeted at the top agent is still running when the scale-down is posted, the pod stays until the turn is sent, then goes; otherwise the drain is pinned by the reconciler unit tests and this is stated in the task result.
Every cluster a test creates is deleted in its teardown; raise `ORCH_MAX_CLUSTERS` in `e2e/values-kind.yaml` only if needed.

## Acceptance conditions

- AC1: the new e2e tests are collected under the e2e marker [evidence: command:uv run pytest -q -p no:cacheprovider -m e2e --collect-only tests/e2e/test_e2e_kind.py]
- AC2: scale up and down keeps surviving pod uids and the config hash, and members join and leave in /agent/v1/me with the leader unchanged [evidence: judgement:tests/e2e/test_e2e_kind.py::test_scale_up_and_down_keeps_surviving_pods reviewed; executed by the PR CI e2e job]
- AC3: out_of_range, static_cluster, leader_would_leave and agent-route not_leader are asserted through the API only [evidence: judgement:tests/e2e/test_e2e_kind.py refusal and leader-only tests reviewed; executed by the PR CI e2e job]
- AC4: a static single-pod cluster has no scale or hive tools and peers off [evidence: judgement:tests/e2e/test_e2e_kind.py::test_static_single_pod_is_alone reviewed; executed by the PR CI e2e job]
- AC5: every cluster an e2e test creates is deleted in its teardown [evidence: judgement:tests/e2e/test_e2e_kind.py teardown reviewed]
- AC6: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

## Files

- `tests/e2e/test_e2e_kind.py`
- `e2e/values-kind.yaml`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
