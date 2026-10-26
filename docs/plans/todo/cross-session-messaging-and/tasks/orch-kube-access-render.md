---
title: orch kube access render
status: todo
repo: agents-orchestrator
value: agents of a kube_access session can run kubectl against every namespace from their shell
files: [src/agents_orchestrator/k8s/render.py, src/agents_orchestrator/k8s/on_start.py, tests/test_render_kube_access.py, README.md, MEMORY.md]
verify: "unset VIRTUAL_ENV && uv run --frozen pytest -q tests/test_render_kube_access.py tests/test_render.py tests/test_on_start.py && mise run lint"
depends_on: [orch-session-options-spec, orch-agent-service-accounts]
model: sonnet
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

# orch kube access render

## Requirement

User decision 2026-10-26, verbatim: "Kubernetes access means: all namespaces, all resources, full read-write." Goal G2 (epic README), verbatim: "A sparse create-time spec option for Kubernetes access; agent pods of a session with it on run as a ServiceAccount bound to cluster-admin with its token mounted, and kubectl in-cluster access works from the agent's shell." Design D3 (fail closed), D5, D16; open question Q1 (recommended path planned).

Scope (agents-orchestrator):
- `src/agents_orchestrator/k8s/render.py`, for a session with `spec.kube_access` true and `settings.kube_access_service_account` set:
  - the StatefulSet pod spec sets `serviceAccountName: settings.kube_access_service_account` and `automountServiceAccountToken: True`; no volume, mount or env overrides the default token path `/var/run/secrets/kubernetes.io/serviceaccount` and no `KUBECONFIG` is rendered;
  - `claude.passthrough_env` adds `KUBERNETES_SERVICE_HOST` and `KUBERNETES_SERVICE_PORT` (sorted list as today).
  - When `spec.kube_access` is true but the setting is empty (removed after the session was created), render fails closed: the agent ServiceAccount, no token, no KUBERNETES_* passthrough.
  - Sessions without `kube_access` render exactly as after task orch-agent-service-accounts. Jobs of a `kube_access` session stay on the agent ServiceAccount with no token.
- `src/agents_orchestrator/k8s/on_start.py` `render_on_start`: when `spec.kube_access` is true, the script installs kubectl `settings.kubectl_version` through mise so it is on PATH through `/opt/mise/shims`, and checks it with `kubectl version --client`; the script runs under `set -eu`, so a failed install fails the onStart hook. Without the option the script is byte-identical to today.
- `README.md`: `## Security` states that a `kube_access` agent can read every Secret in every namespace (including the orchestrator master key, the Claude token and the database credentials) and can mint tokens, certificates and bindings that outlive its session, so discarding the session is not a full revocation; and that sessions started by trigger services from a preset with `kube_access` get the same access, so untrusted webhook content reaching such a session is a cluster-admin prompt-injection path (open question Q2, recommended answer). `### Session configuration` describes what `kube_access` renders.
- `MEMORY.md`: dated entry for D2, D3, D4, D5 (why one helm-owned SA, why the setting gate, why fail closed, why kubectl via mise).

## Acceptance conditions

- ac1: a kube_access session's agent pod spec sets serviceAccountName to ORCH_KUBE_ACCESS_SERVICE_ACCOUNT and automountServiceAccountToken true, with no volume or mount at the token path and no KUBECONFIG env [evidence: test:tests/test_render_kube_access.py::test_kube_access_pod_identity]
- ac1b: no spec without kube_access true ever renders serviceAccountName ORCH_KUBE_ACCESS_SERVICE_ACCOUNT, for agent pods and every Job, with the setting present (parametrized over alone, hive, static, messaging-only and cache specs) [evidence: test:tests/test_render_kube_access.py::test_only_kube_access_yields_privileged_account]
- ac2: claude.passthrough_env contains KUBERNETES_SERVICE_HOST and KUBERNETES_SERVICE_PORT for a kube_access session and neither for a session without it [evidence: test:tests/test_render_kube_access.py::test_kube_access_passthrough_env]
- ac3: the onStart script of a kube_access session installs kubectl at ORCH_KUBECTL_VERSION through mise and checks kubectl version --client under set -eu, and the script of a session without kube_access is unchanged [evidence: test:tests/test_render_kube_access.py::test_kube_access_on_start_installs_kubectl]
- ac4: a kube_access session rendered while ORCH_KUBE_ACCESS_SERVICE_ACCOUNT is empty gets the agent ServiceAccount, automountServiceAccountToken false and no KUBERNETES_* passthrough [evidence: test:tests/test_render_kube_access.py::test_kube_access_fails_closed_without_setting]
- ac5: the init, check and cache Jobs of a kube_access session use the agent ServiceAccount with automountServiceAccountToken false [evidence: test:tests/test_render_kube_access.py::test_kube_access_jobs_stay_unprivileged]
- ac6: render, onStart, ServiceAccount, settings and nomenclature tests still pass [evidence: command:unset VIRTUAL_ENV && uv run --frozen pytest -q tests/test_render.py tests/test_on_start.py tests/test_service_accounts.py tests/test_settings.py tests/test_nomenclature.py]
- ac7: README Security names the Secret exposure, the non-revocation, the trigger-service path, and that a session with both session_messaging and kube_access lets any other messaging session feed text to a cluster-admin leader (the frame trailer is the only defence) [evidence: command:grep -q 'kube_access' README.md && grep -qi 'revocation' README.md && grep -q 'session_messaging' README.md]
- ac8: lint passes [evidence: command:mise run lint]

## Files

- `src/agents_orchestrator/k8s/render.py`
- `src/agents_orchestrator/k8s/on_start.py`
- `tests/test_render_kube_access.py`
- `README.md`
- `MEMORY.md`

## Interfaces

- Reads `SessionSpec.kube_access`, `Settings.kube_access_service_account`, `Settings.agent_service_account`, `Settings.kubectl_version` (task orch-session-options-spec).
- Pod spec of an opted-in agent pod: `serviceAccountName: <ORCH_KUBE_ACCESS_SERVICE_ACCOUNT>`, `automountServiceAccountToken: true`.
- The chart (task chart-kube-access-rbac) creates that ServiceAccount and binds it to cluster-admin; the reconciler only references it.

## Expected outcome

A `kube_access` session's agents run as the privileged ServiceAccount with its token at the default path, see `KUBERNETES_SERVICE_HOST/PORT` in their Bash and have kubectl on PATH, so `kubectl get namespaces` uses the in-cluster config; every other pod and Job is unchanged.

## Steps

- Red: write `tests/test_render_kube_access.py` with the five tests named in the acceptance conditions; run `unset VIRTUAL_ENV && uv run --frozen pytest -q tests/test_render_kube_access.py`: fails.
- Green: change `render.py` and `on_start.py`; run the task's verify: passes.
- README and MEMORY; run ac6, ac7 and ac8 commands: pass.

## Notes

- Rulings and their pin tests: fail closed when the setting is gone (ac4); Jobs never privileged (ac5); onStart unchanged without the option, so goldens do not move (ac3, ac6).
- Research: pod-level `automountServiceAccountToken` overrides the SA (rbac B1); kubectl uses in-cluster config only when no kubeconfig is found and `KUBERNETES_SERVICE_HOST/PORT` and the token file exist (B8, B9); no subPath for the token (B4).
- The wrapper image has mise with `MISE_DATA_DIR=/opt/mise` and `/opt/mise/shims` on PATH (claude-code-wrapper Dockerfile:70-81); `/opt/mise` is an emptyDir, so the install runs on every pod start like the any-mcp install.
- `cluster-admin` is on the nomenclature allowlist after task orch-session-options-spec; any other "cluster" word is not.
- Orchestrator tests need Docker; run with `VIRTUAL_ENV` unset; `uv sync` if the `.venv` shebang is stale.
