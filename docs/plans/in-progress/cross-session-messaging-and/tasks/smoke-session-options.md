---
title: smoke session options
status: in-progress
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

Goal G2 (epic README), verbatim: "agent pods of a session with it on run as a ServiceAccount bound to cluster-admin with its token mounted and the in-cluster API address passed to the agent's shell, so in-cluster access works from it (kubectl comes from a user hook or the agent, not the orchestrator)." User gate answers 2026-10-26, verbatim: "Q1. No- it will be something either hook will do, or agent will handle if needed, Q2: yes". (Q1 no: the orchestrator installs no kubectl, so the probe uses curl.) Goal G3, verbatim: "Every other agent pod and every Job runs with an explicit ServiceAccount and no mounted token." Goal G1, verbatim: "A sparse create-time spec option for cross-session messaging that makes a session a superleader: its leader lists the leaders of all open sessions and can send a message to any of them; the leader of every other session, alone sessions included, lists only the superleader sessions and can send only to them; every session receives messages sent to it as turns on its leader that name the sender session." Design D15; retro (matrix-read-receipts, agents-matrix-connector-depl): live proof is an orchestrator-run step, so this task writes and offline-tests the steps; the orchestrator runs `mise run smoke` after the apply (design Rollout R5).

Scope (agents-helmfile `scripts/smoke.sh`, the style of its existing steps, same parameters):
- Kubernetes access step: `GET /api/v1/meta` reports `kube_access.available` true; a session `smoke-kube-<ts>` created with a raw spec (`replicas: 1`, `kube_access: true`) gets a Ready pod whose `spec.serviceAccountName` ends with `-kube-access` and whose `automountServiceAccountToken` is true; inside it (`kubectl exec <pod> -c ccw -- sh -c ...`, the token read from `/var/run/secrets/kubernetes.io/serviceaccount/token` inside the pod and never printed) `curl --cacert /var/run/secrets/kubernetes.io/serviceaccount/ca.crt` to `https://$KUBERNETES_SERVICE_HOST:$KUBERNETES_SERVICE_PORT` posts a SelfSubjectAccessReview for verb `*`, group `*`, resource `*` with no namespace and gets `status.allowed` true, and `GET /api/v1/namespaces` answers 200 (no kubectl in the pod: user decision Q1); the existing smoke hive session's pod has `automountServiceAccountToken` false and `kubectl exec ... -- test ! -e /var/run/secrets/kubernetes.io/serviceaccount/token` succeeds.
- Messaging step (superleader model, design D7): a superleader session `smoke-msg-a-<ts>` (raw spec `replicas: 1`, `session_messaging: true`) and a plain session `smoke-msg-b-<ts>` (`replicas: 1`, no option) get Ready pods; inside A's pod (`kubectl exec`, using the pod's own `ORCH_AGENT_URL`, `ORCH_AGENT_TOKEN`, `ORCH_SESSION_ID` env, never echoed) `GET /agent/v1/sessions` lists B and the smoke hive session; `POST /agent/v1/sessions/<B slug>/messages` with text `smoke ping <ts>` answers 202 with a `message_id`; `GET /api/v1/messages/<id>` reaches `sent` within `SMOKE_TIMEOUT_S`; B's events (the orchestrator events API) contain a `user_message` whose text starts with `<session-message from="<A slug>"`. Inside B's pod `GET /agent/v1/sessions` lists A and not the smoke hive session, and `POST /agent/v1/sessions/<smoke hive slug>/messages` answers 403 `target_not_superleader`.
- The cleanup trap deletes `smoke-kube-<ts>`, `smoke-msg-a-<ts>` and `smoke-msg-b-<ts>` on every exit.
- The header comment and `README.md` (`mise run smoke` paragraph) describe both steps. Words: "full Kubernetes access", never the word "cluster" outside the allowed phrases of `tests/test_nomenclature.py` (`in-cluster` is allowed; `cluster-admin` is not).
- `tests/test_smoke_script.py`: tests for both steps with the existing fake kubectl and curl harness.

## Acceptance conditions

- ac1: the Kubernetes access step passes when meta reports kube_access.available, the session pod runs as the -kube-access ServiceAccount with the token mounted, the in-pod curl SelfSubjectAccessReview for * on * answers allowed true and GET /api/v1/namespaces answers 200, and the hive pod has no token, and fails smoke naming the check when any of these does not hold [evidence: test:tests/test_smoke_script.py::test_kube_access_step]
- ac2: the messaging step passes when superleader A's pod lists B, the send answers 202 with a message_id, the message reaches sent, B's events carry a user_message starting with the session frame from A, and plain B lists A but not the hive session and its send to the hive session gets 403 target_not_superleader, and fails smoke naming the check otherwise [evidence: test:tests/test_smoke_script.py::test_session_messaging_step]
- ac3: the trap deletes the kube and both messaging sessions on success and on a failure [evidence: test:tests/test_smoke_script.py::test_session_option_sessions_cleaned_up]
- ac4: the new steps never print the agent token or any other secret [evidence: test:tests/test_smoke_script.py::test_session_option_steps_print_no_token]
- ac5: the smoke script tests and the nomenclature guard pass [evidence: command:uv run --frozen pytest -q tests/test_smoke_script.py tests/test_nomenclature.py tests/test_repo_hygiene.py]
- ac6: lint (ruff, shellcheck, gitleaks) passes [evidence: command:mise run lint]

## Files

- `scripts/smoke.sh`
- `tests/test_smoke_script.py`
- `README.md`

## Interfaces

- Orchestrator API used: `GET /api/v1/meta` (`kube_access.available`), `POST /api/v1/sessions` (raw spec with `kube_access` / `session_messaging`), `GET /api/v1/messages/{id}`, the session events API, `DELETE /api/v1/sessions/{id}`.
- Agent API used from inside a pod: `GET /agent/v1/sessions`, `POST /agent/v1/sessions/{slug}/messages` (task orch-agent-session-messaging).
- Frame prefix checked: `<session-message from="<slug>"` (task orch-session-message-sender).

## Expected outcome

`mise run smoke` after the apply proves in the live namespace that a `kube_access` pod has working in-cluster API access with full rights, an ordinary pod has no token, a superleader's leader can message a plain session's leader, and a plain session can reach only superleaders.

## Steps

- Red: add the four tests named in the acceptance conditions to `tests/test_smoke_script.py`; run `uv run --frozen pytest -q tests/test_smoke_script.py`: fails.
- Green: add the steps and trap entries to `scripts/smoke.sh`, update its header and README; run the task's verify: passes.
- Run ac5 and ac6 commands: pass.

## Notes

- Rulings and their pin tests: each failing check fails smoke with a named message (ac1, ac2); cleanup on every exit (ac3); no secret on stdout or stderr (ac4).
- Never run `mise run smoke` or `mise run apply` in this task: the live run is the orchestrator's (design Rollout R5); the AC evidence is offline.
- The messaging step makes session B run one real turn on "smoke ping"; keep the text short.
- Existing patterns: session create and delete (smoke.sh:91, 201), `kubectl exec` into the smoke pod, the workspace cache step (two sessions, trap cleanup).
- Smoke tasks ran 3-5x their minute seeds before (retro agents-schedule-deploy); the fake harness in `tests/test_smoke_script.py` is large, read its fixtures first.

- 2026-10-26 amended: gate 2026-10-26: one-sided superleader messaging (tools for every session, target_not_superleader), Q1 no orchestrator kubectl install, Q2 yes
