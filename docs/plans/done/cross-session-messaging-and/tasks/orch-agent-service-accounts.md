---
title: orch agent service accounts
status: done
repo: agents-orchestrator
value: no ordinary agent pod or Job carries a Kubernetes token any more
files: [src/agents_orchestrator/k8s/render.py, src/agents_orchestrator/reconciler/init.py, src/agents_orchestrator/reconciler/checks.py, src/agents_orchestrator/reconciler/cache.py, tests/test_service_accounts.py, tests/golden/session_single.yaml, tests/golden/session_two_peers.yaml, README.md]
verify: "unset VIRTUAL_ENV && uv run --frozen pytest -q tests/test_service_accounts.py tests/test_render.py tests/test_cache_jobs_render.py && mise run lint"
depends_on: [orch-session-options-spec]
model: opus
review: ""
verified_head: bbb9c1cc2d8fa45ed2a5ab52c59f4d1aeba750fc
points: 3
expected_minutes: 7
expected_tokens: 977684
points_actual: 3
actual_minutes: 14
actual_tokens: 1056760
actual_roles: "impl 13, review 2"
actual_role_tokens: "impl 932278, review 124482"
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

- Pod spec keys on every agent StatefulSet and every Job: `serviceAccountName: <settings.agent_service_account>`, `automountServiceAccountToken: false`.
- Reads `settings.py:Settings.agent_service_account` (task orch-session-options-spec).

## Expected outcome

No agent pod or Job rendered by the orchestrator mounts a Kubernetes token, and each names its ServiceAccount explicitly.

## Steps

- Red: write `tests/test_service_accounts.py` with the two tests named in the acceptance conditions; run `unset VIRTUAL_ENV && uv run --frozen pytest -q tests/test_service_accounts.py`: fails (keys absent).
- Green: set the keys in `render.py`, `init.py`, `checks.py`, `cache.py`; regenerate the goldens; run the task's verify: passes.
- README; run ac3 and ac4 commands: pass.

## Notes

- Rulings and their pin tests: one setting for pods and Jobs (ac1, ac2); Jobs stay unprivileged for every session (ac2, and task orch-kube-access-render pins it for kube_access sessions).
- A pod-template change rolls running StatefulSets once on upgrade (render.py comment on the config hash); that is expected (design Rollout R3).
- `tests/fakes/fake_kube.py` models the reconciler Role; it does not need ServiceAccount support because the reconciler only references an existing SA.
- The reuse brief notes imagePullSecrets and the workspace volume are duplicated across render.py, checks.py, init.py, cache.py; a shared pod-spec helper is allowed only if it stays within these files.
- Do not write the word "cluster" in new lines (nomenclature guard).
- Orchestrator tests need Docker; run with `VIRTUAL_ENV` unset; `uv sync` if the `.venv` shebang is stale.

- 2026-10-26 done
