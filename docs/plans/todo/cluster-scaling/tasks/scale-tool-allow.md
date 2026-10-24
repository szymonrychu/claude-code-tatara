---
title: scale tool allow
status: todo
repo: agent-orchestrator
value: "only scalable clusters offer the scale tool, so static and alone agents never see it"
files: [src/agent_orchestrator/k8s/on_start.py, tests/test_render.py]
verify: "uv run --frozen pytest -q tests/test_render.py && uv run ruff check . && uv run ruff format --check ."
depends_on: []
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

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
