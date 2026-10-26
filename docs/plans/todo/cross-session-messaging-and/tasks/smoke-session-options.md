---
title: smoke session options
status: todo
repo: agents-helmfile
value: the live smoke proves Kubernetes access and cross-session messaging after the deploy
files: [scripts/smoke.sh, tests/test_smoke_script.py, README.md]
verify: "uv run --frozen pytest -q tests/test_smoke_script.py && mise run lint"
depends_on: [orch-render-session-tools, chart-kube-access-rbac]
model: sonnet
review: ""
verified_head: ""
points: 5
expected_minutes: 12
expected_tokens: 1686779
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# smoke session options

## Requirement

Goal G2 (epic README), verbatim: "agent pods of a session with it on run as a ServiceAccount bound to cluster-admin with its token mounted, and kubectl in-cluster access works from the agent's shell." Goal G3, verbatim: "Every other agent pod and every Job runs with an explicit ServiceAccount and no mounted token." Goal G1, verbatim: "a session with it on can list messaging-enabled sessions and send a message to another one's leader, and receives messages sent to it as turns on its leader that name the sender session." Design D15; retro (matrix-read-receipts, agents-matrix-connector-depl): live proof is an orchestrator-run step, so this task writes and offline-tests the steps; the orchestrator runs `mise run smoke` after the apply (design Rollout R5).

Scope (agents-helmfile `scripts/smoke.sh`, the style of its existing steps, same parameters):
- Kubernetes access step: `GET /api/v1/meta` reports `kube_access.available` true; a session `smoke-kube-<ts>` created with a raw spec (`replicas: 1`, `kube_access: true`) gets a Ready pod whose `spec.serviceAccountName` ends with `-kube-access` and whose `automountServiceAccountToken` is true; `kubectl exec <pod> -c ccw -- kubectl auth can-i '*' '*' --all-namespaces` prints `yes` (kubectl installed by the onStart, token at the default path); the existing smoke hive session's pod has `automountServiceAccountToken` false and `kubectl exec ... -- test ! -e /var/run/secrets/kubernetes.io/serviceaccount/token` succeeds.
- Messaging step: two sessions `smoke-msg-a-<ts>` and `smoke-msg-b-<ts>` created with raw specs (`replicas: 1`, `session_messaging: true`) get Ready pods; inside A's pod (`kubectl exec`, using the pod's own `ORCH_AGENT_URL`, `ORCH_AGENT_TOKEN`, `ORCH_SESSION_ID` env, never echoed) `GET /agent/v1/sessions` lists B, and `POST /agent/v1/sessions/<B slug>/messages` with text `smoke ping <ts>` answers 202 with a `message_id`; `GET /api/v1/messages/<id>` reaches `sent` within `SMOKE_TIMEOUT_S`; B's events (the orchestrator events API) contain a `user_message` whose text starts with `<session-message from="<A slug>"`.
- The cleanup trap deletes `smoke-kube-<ts>`, `smoke-msg-a-<ts>` and `smoke-msg-b-<ts>` on every exit.
- The header comment and `README.md` (`mise run smoke` paragraph) describe both steps. Words: "full Kubernetes access", never the word "cluster" outside the allowed phrases of `tests/test_nomenclature.py` (`in-cluster` is allowed; `cluster-admin` is not).
- `tests/test_smoke_script.py`: tests for both steps with the existing fake kubectl and curl harness.

## Acceptance conditions

- ac1: the Kubernetes access step passes when meta reports kube_access.available, the session pod runs as the -kube-access ServiceAccount with the token mounted, kubectl auth can-i inside it prints yes and the hive pod has no token, and fails smoke naming the check when any of these does not hold [evidence: test:tests/test_smoke_script.py::test_kube_access_step]
- ac2: the messaging step passes when A's pod lists B, the send answers 202 with a message_id, the message reaches sent and B's events carry a user_message starting with the session frame from A, and fails smoke naming the check otherwise [evidence: test:tests/test_smoke_script.py::test_session_messaging_step]
- ac3: the trap deletes the kube and both messaging sessions on success and on a failure [evidence: test:tests/test_smoke_script.py::test_session_option_sessions_cleaned_up]
- ac4: the new steps never print the agent token or any other secret [evidence: test:tests/test_smoke_script.py::test_session_option_steps_print_no_token]
- ac5: the smoke script tests and the nomenclature guard pass [evidence: command:uv run --frozen pytest -q tests/test_smoke_script.py tests/test_nomenclature.py tests/test_repo_hygiene.py]
- ac6: lint (ruff, shellcheck, gitleaks) passes [evidence: command:mise run lint]

## Files

- `scripts/smoke.sh`
- `tests/test_smoke_script.py`
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
