---
title: orch kube access render
status: in-progress
repo: agents-orchestrator
value: agents of a kube_access session have in-cluster API access to every namespace from their shell
files: [src/agents_orchestrator/k8s/render.py, tests/test_render_kube_access.py, README.md, MEMORY.md]
verify: "unset VIRTUAL_ENV && uv run --frozen pytest -q tests/test_render_kube_access.py tests/test_render.py && mise run lint"
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

User decision 2026-10-26, verbatim: "Kubernetes access means: all namespaces, all resources, full read-write." Goal G2 (epic README), verbatim: "A sparse create-time spec option for Kubernetes access; agent pods of a session with it on run as a ServiceAccount bound to cluster-admin with its token mounted and the in-cluster API address passed to the agent's shell, so in-cluster access works from it (kubectl comes from a user hook or the agent, not the orchestrator)." User gate answers 2026-10-26, verbatim: "Q1. No- it will be something either hook will do, or agent will handle if needed, Q2: yes". Q1 no: the orchestrator does not install kubectl; Q2 yes: trigger-started sessions from a kube_access preset get the same access. Design D3 (fail closed), D5, D16.

Scope (agents-orchestrator):
- `src/agents_orchestrator/k8s/render.py`, for a session with `spec.kube_access` true and `settings.kube_access_service_account` set:
  - the StatefulSet pod spec sets `serviceAccountName: settings.kube_access_service_account` and `automountServiceAccountToken: True`; no volume, mount or env overrides the default token path `/var/run/secrets/kubernetes.io/serviceaccount` and no `KUBECONFIG` is rendered;
  - `claude.passthrough_env` adds `KUBERNETES_SERVICE_HOST` and `KUBERNETES_SERVICE_PORT` (sorted list as today).
  - When `spec.kube_access` is true but the setting is empty (removed after the session was created), render fails closed: the agent ServiceAccount, no token, no KUBERNETES_* passthrough.
  - Sessions without `kube_access` render exactly as after task orch-agent-service-accounts. Jobs of a `kube_access` session stay on the agent ServiceAccount with no token.
- No kubectl install and no onStart change (user decision Q1): kubectl comes from a user hook or the agent; the rendered onStart is identical for every spec.
- `README.md`: `## Security` states that a `kube_access` agent can read every Secret in every namespace (including the orchestrator master key, the Claude token and the database credentials) and can mint tokens, certificates and bindings that outlive its session, so discarding the session is not a full revocation; and that sessions started by trigger services from a preset with `kube_access` get the same access, so untrusted webhook content reaching such a session is a cluster-admin prompt-injection path (user decision Q2). and that any superleader session can feed text to the leader of any `kube_access` session, and any session's leader can feed text to a superleader session that has `kube_access`, the frame trailer being the only defence. `### Session configuration` describes what `kube_access` renders and that kubectl is the user's hook's or the agent's to provide.
- `MEMORY.md`: dated entry for D2, D3, D4, D5 (why one helm-owned SA, why the setting gate, why fail closed, why the orchestrator does not install kubectl: user decision Q1).

## Acceptance conditions

- ac1: a kube_access session's agent pod spec sets serviceAccountName to ORCH_KUBE_ACCESS_SERVICE_ACCOUNT and automountServiceAccountToken true, with no volume or mount at the token path and no KUBECONFIG env [evidence: test:tests/test_render_kube_access.py::test_kube_access_pod_identity]
- ac1b: no spec without kube_access true ever renders serviceAccountName ORCH_KUBE_ACCESS_SERVICE_ACCOUNT, for agent pods and every Job, with the setting present (parametrized over alone, hive, static, messaging-only and cache specs) [evidence: test:tests/test_render_kube_access.py::test_only_kube_access_yields_privileged_account]
- ac2: claude.passthrough_env contains KUBERNETES_SERVICE_HOST and KUBERNETES_SERVICE_PORT for a kube_access session and neither for a session without it [evidence: test:tests/test_render_kube_access.py::test_kube_access_passthrough_env]
- ac3: the rendered onStart script of a kube_access session is identical to that of the same spec without kube_access (no kubectl install) [evidence: test:tests/test_render_kube_access.py::test_kube_access_leaves_on_start_unchanged]
- ac4: a kube_access session rendered while ORCH_KUBE_ACCESS_SERVICE_ACCOUNT is empty gets the agent ServiceAccount, automountServiceAccountToken false and no KUBERNETES_* passthrough [evidence: test:tests/test_render_kube_access.py::test_kube_access_fails_closed_without_setting]
- ac5: the init, check and cache Jobs of a kube_access session use the agent ServiceAccount with automountServiceAccountToken false [evidence: test:tests/test_render_kube_access.py::test_kube_access_jobs_stay_unprivileged]
- ac6: render, onStart, ServiceAccount, settings and nomenclature tests still pass [evidence: command:unset VIRTUAL_ENV && uv run --frozen pytest -q tests/test_render.py tests/test_on_start.py tests/test_service_accounts.py tests/test_settings.py tests/test_nomenclature.py]
- ac7: README Security names the Secret exposure, the non-revocation, the trigger-service path, and that any superleader session can feed text to a kube_access leader (the frame trailer is the only defence) [evidence: command:grep -q 'kube_access' README.md && grep -qi 'revocation' README.md && grep -qi 'superleader' README.md]
- ac8: lint passes [evidence: command:mise run lint]

## Files

- `src/agents_orchestrator/k8s/render.py`
- `tests/test_render_kube_access.py`
- `README.md`
- `MEMORY.md`

## Interfaces

- Reads `SessionSpec.kube_access`, `Settings.kube_access_service_account`, `Settings.agent_service_account` (task orch-session-options-spec).
- Pod spec of an opted-in agent pod: `serviceAccountName: <ORCH_KUBE_ACCESS_SERVICE_ACCOUNT>`, `automountServiceAccountToken: true`.
- The chart (task chart-kube-access-rbac) creates that ServiceAccount and binds it to cluster-admin; the reconciler only references it.

## Expected outcome

A `kube_access` session's agents run as the privileged ServiceAccount with its token at the default path, see `KUBERNETES_SERVICE_HOST/PORT` in their Bash, so any client the agent or a user hook brings (kubectl included) uses the in-cluster config; every other pod and Job is unchanged.

## Steps

- Red: write `tests/test_render_kube_access.py` with the six tests named in the acceptance conditions; run `unset VIRTUAL_ENV && uv run --frozen pytest -q tests/test_render_kube_access.py`: fails.
- Green: change `render.py`; run the task's verify: passes.
- README and MEMORY; run ac6, ac7 and ac8 commands: pass.

## Notes

- Rulings and their pin tests: fail closed when the setting is gone (ac4); Jobs never privileged (ac5); onStart identical with and without the option (ac3), so goldens do not move (ac6).
- Research: pod-level `automountServiceAccountToken` overrides the SA (rbac B1); kubectl uses in-cluster config only when no kubeconfig is found and `KUBERNETES_SERVICE_HOST/PORT` and the token file exist (B8, B9); no subPath for the token (B4).
- kubectl is not in the wrapper image and the orchestrator does not install it (user decision Q1); a user onStart hook or the agent installs it when needed.
- `cluster-admin` is on the nomenclature allowlist after task orch-session-options-spec; any other "cluster" word is not.
- Orchestrator tests need Docker; run with `VIRTUAL_ENV` unset; `uv sync` if the `.venv` shebang is stale.

- 2026-10-26 amended: gate 2026-10-26: one-sided superleader messaging (tools for every session, target_not_superleader), Q1 no orchestrator kubectl install, Q2 yes
