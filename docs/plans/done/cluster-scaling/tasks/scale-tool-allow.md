---
title: scale tool allow
status: done
repo: agent-orchestrator
value: "only scalable clusters offer the scale tool, so static and alone agents never see it"
files: [src/agent_orchestrator/k8s/on_start.py, tests/test_render.py]
verify: "uv run --frozen pytest -q tests/test_render.py && uv run ruff check . && uv run ruff format --check ."
depends_on: []
model: ""
review: ""
verified_head: 69a3929c7b56c667ac316fb2ffda47fa62ae4b10
points: 1
expected_minutes: 5
expected_tokens: 750000
points_actual: ""
actual_minutes: 2
actual_tokens: 431039
actual_roles: "impl 1, review 1"
actual_role_tokens: "impl 214326, review 216713"
---

# scale tool allow

## Requirement

Expose the scale tool only on scalable clusters (design D4; user S3, Q7, X1; foundation D2). In `src/agent_orchestrator/k8s/on_start.py`, where hive-mode-leadership-handove F3 renders the merged `orchestrator` any-mcp plugin entry and its `allow` list, include the scale tool (`scale`, as F3 names tools in `allow`) if and only if `spec.scalable` (hive and not static). Alone clusters (`max_replicas == 1`, so a static single pod) and static multi-pod clusters render no scale tool; a scalable cluster renders it at any current `replicas`, including 1. The rendered ConfigMap (and so the pod-template hash) must not depend on `spec.replicas`: the hive hash-invariant test stays green and a new test proves the allow list is identical for the same spec at replicas 1 and at max_replicas.

## Acceptance conditions

- AC1: the scale tool is in the orchestrator entry's allow list only when the cluster is scalable, for alone, static multi-pod, scalable at 1 and scalable at max specs [evidence: test:tests/test_render.py::test_scale_tool_allowed_only_when_scalable]
- AC2: the allow list and on-start script are identical for one spec rendered at replicas 1 and at max_replicas [evidence: test:tests/test_render.py::test_scale_allow_independent_of_replicas]
- AC3: the hive hash invariant stays green [evidence: test:tests/test_render.py::test_runtime_fields_change_only_statefulset_replicas]
- AC4: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

## Files

- `src/agent_orchestrator/k8s/on_start.py`
- `tests/test_render.py`

## Interfaces

- Changes the `allow` list of the `orchestrator` plugin entry rendered in `src/agent_orchestrator/k8s/on_start.py` by hive F3 (foundation D2: init tools always, hive tools when `hive`, `scale` when `scalable`).
- Keeps `tests/test_render.py::test_runtime_fields_change_only_statefulset_replicas` (hive hash invariant) green.

## Expected outcome

Agents of scalable clusters load `orchestrator_scale`; static and alone agents never see it, and scaling never changes the rendered config.

## Steps

- Red: add the two tests to `tests/test_render.py`; run `uv run --frozen pytest -q tests/test_render.py -k scale`: the scalable case fails (no scale tool).
- Green: add the condition where F3 builds `allow`; run the verify command.

## Notes

- Use the derived `spec.scalable` property from F3; do not read the live replica count anywhere in render.
- If F3 already renders `scale` under the same condition, this task only adds the two pinning tests and says so in the result.
