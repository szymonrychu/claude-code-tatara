---
title: helmfile smoke continuity
status: todo
repo: agents-helmfile
value: every deploy proves an agent keeps its conversation across a pod restart
files: [scripts/smoke.sh, tests/test_smoke_script.py, mise.toml, README.md, MEMORY.md]
verify: "uv run pytest -q tests/test_smoke_script.py && mise run lint"
depends_on: []
model: sonnet
review: ""
verified_head: ""
points: 5
expected_minutes: 8
expected_tokens: 1828146
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# helmfile smoke continuity

## Requirement

Design D12, user decision verbatim: "smoke.sh in agents-helmfile gets a session-continuity check if a safe trigger exists without rolling real agents; otherwise record why not (my call)."

Design D12 (my call), verbatim: "A safe trigger exists: deleting the pod of a session the smoke itself created (smoke already scales its own session's pods). After one real turn, the pod is deleted; the smoke asserts the pod returns Ready, the agent's wrapper session id is unchanged, the agent is not `dead`, and a message sent after the restart reaches `sent`. No user session and no template change is involved."

Goal G1, verbatim: "After an agent pod restart and a successful wrapper resume, the ingester re-attaches from the last stored event, the agent leaves `dead`, and queued messages are delivered (the 20:07-20:29 hang cannot recur)."

Scope (agents-helmfile):
- `scripts/smoke.sh`: a session-continuity step on a session the smoke created (reuse one it already makes or create `smoke-cont-<ts>`, deleted by the trap): post a message and wait for `sent` (so a transcript exists); read the agent's `wrapper_session_id` from the events API (`GET /api/v1/sessions/{id}/events?agent_id=...`); record the pod uid; `kubectl delete pod` that pod only; wait for a new uid and Ready; wait until the agent view's state is not `dead`; post a second message and wait for `sent`; assert the events after the restart carry the same `wrapper_session_id`. Each wait has its own deadline (leader-auto-handover retro). Outputs are matched, never printed.
- `tests/test_smoke_script.py`: the fake API and fake kubectl model the restart (new uid, resumed agent) and the failure cases.
- `mise.toml` smoke description, README `Operating` smoke paragraph and the header comment of `smoke.sh` mention the step; MEMORY.md dated entry with why this trigger is safe.

Steps: tests first, seen failing; then the step; run the verify. The live run is task helmfile-apply-live-check.

Notes: subagent `kubectl exec` is denied by the classifier; this step needs no exec. Never touch a session the smoke did not create. The deployed orchestrator must carry the re-attach fix (task orch-ingester-reattach) for the live run to pass; the unit tests use fakes only.

## Acceptance conditions

- AC1: after one turn the smoke deletes its own session's pod, sees a new Ready pod, the same wrapper session id, an agent that is not dead and a second message reaching sent [evidence: test:tests/test_smoke_script.py::test_session_continuity_after_pod_restart]
- AC2: a changed wrapper session id after the restart fails the smoke naming the step [evidence: test:tests/test_smoke_script.py::test_continuity_new_wrapper_session_fails]
- AC3: an agent that stays dead fails the smoke within its own deadline [evidence: test:tests/test_smoke_script.py::test_continuity_dead_agent_fails]
- AC4: a message after the restart that never reaches sent fails within its own deadline [evidence: test:tests/test_smoke_script.py::test_continuity_message_not_delivered_fails]
- AC5: the step deletes only the pod of a smoke-created session [evidence: test:tests/test_smoke_script.py::test_continuity_deletes_only_smoke_pod]
- AC6: the whole smoke test file passes [evidence: command:uv run pytest -q tests/test_smoke_script.py]
- AC7: README and MEMORY.md describe the step and why the trigger is safe [evidence: command:grep -q "continuity" README.md && grep -q "continuity" MEMORY.md]
- AC8: lint passes [evidence: command:mise run lint]

## Files

- `scripts/smoke.sh`
- `tests/test_smoke_script.py`
- `mise.toml`
- `README.md`
- `MEMORY.md`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
