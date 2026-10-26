---
title: orch agent service accounts
status: todo
repo: agents-orchestrator
value: no ordinary agent pod or Job carries a Kubernetes token any more
files: [src/agents_orchestrator/k8s/render.py, src/agents_orchestrator/reconciler/init.py, src/agents_orchestrator/reconciler/checks.py, src/agents_orchestrator/reconciler/cache.py, tests/test_service_accounts.py, tests/golden/session_single.yaml, tests/golden/session_two_peers.yaml, README.md]
verify: "unset VIRTUAL_ENV && uv run --frozen pytest -q tests/test_service_accounts.py tests/test_render.py tests/test_cache_jobs_render.py && mise run lint"
depends_on: [orch-session-options-spec]
model: opus
review: ""
verified_head: ""
points: 3
expected_minutes: 7
expected_tokens: 977684
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# orch agent service accounts

## Requirement

Goal G3 (epic README), verbatim: "Every other agent pod and every Job runs with an explicit ServiceAccount and no mounted token." Design D4.

Scope (agents-orchestrator):
- `src/agents_orchestrator/k8s/render.py` `render_session`: the StatefulSet pod spec sets `serviceAccountName: settings.agent_service_account` and `automountServiceAccountToken: False` for every session (task orch-kube-access-render later overrides both for `kube_access` sessions only).
- `src/agents_orchestrator/reconciler/init.py` (init Job), `src/agents_orchestrator/reconciler/checks.py` (check Job), `src/agents_orchestrator/reconciler/cache.py` (cache Jobs): each pod spec sets `serviceAccountName: settings.agent_service_account` and `automountServiceAccountToken: False` (cache Jobs already set the automount, cache.py:121).
- Jobs never get the privileged identity, whatever the session's spec.
- `tests/golden/session_single.yaml` and `tests/golden/session_two_peers.yaml` regenerated with the golden helper of `tests/test_render.py` (they are expected render output, regenerated, not hand-edited).
- `README.md` `## Kubernetes permissions`: agent pods and Jobs run as `ORCH_AGENT_SERVICE_ACCOUNT` with no token.

The setting `agent_service_account` (default `default`) exists from task orch-session-options-spec; the chart SA `<fullname>-agent` comes from task chart-kube-access-rbac.

## Acceptance conditions

- ac1: the agent StatefulSet pod spec sets serviceAccountName to ORCH_AGENT_SERVICE_ACCOUNT (default and a custom value) and automountServiceAccountToken false [evidence: test:tests/test_service_accounts.py::test_agent_pod_explicit_sa_no_token]
- ac2: the init Job, a check Job and both cache Jobs set serviceAccountName to ORCH_AGENT_SERVICE_ACCOUNT and automountServiceAccountToken false [evidence: test:tests/test_service_accounts.py::test_jobs_explicit_sa_no_token]
- ac3: the regenerated goldens and the existing render and Job tests pass [evidence: command:unset VIRTUAL_ENV && uv run --frozen pytest -q tests/test_render.py tests/test_cache_jobs_render.py tests/test_checks.py tests/test_init_runner.py tests/test_reconciler.py]
- ac4: lint passes [evidence: command:mise run lint]

## Files

- `src/agents_orchestrator/k8s/render.py`
- `src/agents_orchestrator/reconciler/init.py`
- `src/agents_orchestrator/reconciler/checks.py`
- `src/agents_orchestrator/reconciler/cache.py`
- `tests/test_service_accounts.py`
- `tests/golden/session_single.yaml`
- `tests/golden/session_two_peers.yaml`
- `README.md`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
