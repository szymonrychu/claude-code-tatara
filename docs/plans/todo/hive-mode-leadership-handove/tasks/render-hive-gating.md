---
title: render hive gating
status: todo
repo: agent-orchestrator
value: "hive clusters get peers, notes and lock warnings, alone clusters get none, and scaling never rolls pods"
files: [src/agent_orchestrator/k8s/render.py, tests/test_render.py]
verify: "uv run pytest tests/test_render.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [agent-token-env-render, orch-pin-bumps]
owns: [orch-render-hash-invariant, orch-peer-seeds-cap]
uses: [orch-agent-env, orch-hive-pins, orch-spec-cap-static, wrapper-main-agent-only-tools, wrapper-notes-inbox]
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

# render hive gating

## Requirement

Foundation part F3, render (D2, D3, Q7, Q11, S3). In `k8s/render.py` `_ccw_config`:

- `peers.static` = the pod URLs for ordinals `range(spec.max_replicas)` (seeds from the immutable cap) instead of `range(spec.replicas)`; `name: ${POD_NAME}` and `advertise_url` unchanged.
- `peers.enabled = spec.peers and spec.hive`: an alone cluster (static single pod) gets no peers, `peers` or `send_message` tools.
- `notes.enabled = spec.hive` (wrapper defaults for caps and throttle).
- `claude.main_agent_only_tools = ["mcp__any-mcp__orchestrator_*"]` for every cluster.
- When `spec.hive` and `settings.agent_api_url` is set: one `hooks.onAgentToolCall` webhook action appended after any existing ones: `{type: webhook, url: "${ORCH_AGENT_URL}/agent/v1/locks/check", headers: {Authorization: "Bearer ${ORCH_AGENT_TOKEN}", X-Orch-Cluster: "${ORCH_CLUSTER_ID}"}, matcher: "^(Write|Edit|MultiEdit|NotebookEdit)$", blocking: true, on_error: allow, timeout_seconds: 2, retries: 0}` (advisory lock warning, Q11; the wrapper interpolates `${VAR}` from the pod env).
- No ConfigMap byte, Secret, Service or pod template field may depend on the live replica count. New test `tests/test_render.py::test_runtime_fields_change_only_statefulset_replicas`: rendering one cluster at two replica counts within `max_replicas` differs only in `StatefulSet.spec.replicas` (ConfigMap data, Secret, Service, PVC and pod template, hash annotation included, byte-identical). It is parametrised over runtime fields so agent-init-scripts adds `init_scripts` to it.
- The rendered config validates against the pinned wrapper Config (existing test).

## Acceptance conditions

- AC1: peers.static lists ordinals 0..max_replicas-1 [evidence: test:tests/test_render.py::test_peer_seeds_from_cap]
- AC2: an alone cluster renders peers and notes disabled and no lock webhook [evidence: test:tests/test_render.py::test_alone_cluster_no_hive_config]
- AC3: a hive cluster renders notes enabled, peers per spec.peers and the lock-check webhook with token and cluster headers [evidence: test:tests/test_render.py::test_hive_cluster_config]
- AC4: main_agent_only_tools is rendered for every cluster [evidence: test:tests/test_render.py::test_main_agent_only_tools_rendered]
- AC5: changing replicas changes only StatefulSet.spec.replicas [evidence: test:tests/test_render.py::test_runtime_fields_change_only_statefulset_replicas]
- AC6: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

## Files

- `src/agent_orchestrator/k8s/render.py`
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
