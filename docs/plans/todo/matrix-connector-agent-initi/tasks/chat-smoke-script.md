---
title: chat smoke script
status: todo
repo: agents-helmfile
value: "one command proves send without inbound, quoted reply and reactions live, leaving nothing behind"
files: [scripts/chat-smoke.sh, mise.toml, tests/test_chat_smoke_script.py, README.md, tests/test_mise_tasks.py]
verify: "uv run pytest tests/test_chat_smoke_script.py tests/test_mise_tasks.py && mise run lint"
depends_on: [mxc-agent-routes, orch-chat-relay]
model: opus
review: ""
verified_head: ""
points: 5
expected_minutes: 8
expected_tokens: 1727786
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# chat smoke script

## Requirement

README Goal, verbatim: "Docs, tests (unit, contract, e2e) and a live smoke in the owner DM covering send without inbound, quoted reply and reaction."

Design D17, verbatim: "`scripts/chat-smoke.sh` (mise task `chat-smoke`), never part of `scripts/smoke.sh`, because it posts real messages from the owner's Facebook account. It creates a throwaway alone session, and from its pod (its own `ORCH_AGENT_*` env, never printed) calls the orchestrator agent routes: lists rooms (the owner DM `!iLWrAwaTMYnINJsyNv:szymonrichert.pl` must be listed), S1 sends a message with no inbound in the run, S2 replies to S1's `s<n>`, S3 reacts with a thumbs-up to S1's `s<n>`, S4 reacts with a second, different emoji to the same target; it polls each send's status to `sent` or `failed` with its own deadline per wait, prints the ids, statuses and reasons, owns its port-forwards (trap cleanup) and deletes the session."

Architecture, verbatim: "S1 a send with no inbound message for >24h shows up in Messenger; S2 a reply shows as a quoted reply; S3 a thumbs-up reaction shows; S4 a second, different reaction replaces the first or is rejected (and how the connector sees the failure)."

Open question Q8 (pending gate), verbatim: "S1 runs at smoke time even if the owner DM had an inbound message in the last 24 h; the smoke records the hours since the last inbound, and the over-24h case is confirmed at the first natural opportunity and noted in agents-helmfile MEMORY.md without holding the epic?" recommended "yes".

Retro proposals, verbatim: "for smoke-script tasks the reviewer checks every timeout or deadline against the AC and the MEMORY claim" and "smoke script owns its port-forward (trap cleanup, kill stale on the port first) and orchestrator runs no manual port-forwards during smoke."

Scope (agents-helmfile): new `scripts/chat-smoke.sh` (env `RELEASE`, `NAMESPACE`, `CHAT_SMOKE_ROOM` default `!iLWrAwaTMYnINJsyNv:szymonrichert.pl`, `CHAT_SMOKE_PRESET` or the default preset, `CHAT_SMOKE_TIMEOUT_S` per wait, `MATRIX_RELEASE`, `SMOKE_LOCAL_PORT`, `SMOKE_MATRIX_API_LOCAL_PORT`); it also reads, through a port-forward to the connector api container, the room's newest inbound message time and prints the hours since it (S1 precondition, Q8). New mise task `chat-smoke`; README names the task and says it posts to the owner DM; `tests/test_chat_smoke_script.py` with kubectl and curl fakes.

## Acceptance conditions

- ac1: against fakes the script lists the rooms, runs S1, S2 (reply_to S1's id), S3 (thumbs-up to S1's id) and S4 (a different emoji to S1's id) in that order, prints each id, status and reason, and exits 0 when S1-S3 end sent [evidence: test:tests/test_chat_smoke_script.py::test_s1_to_s4_happy_path]
- ac2: when the owner DM is not listed the script exits 1 naming the room and sends nothing [evidence: test:tests/test_chat_smoke_script.py::test_room_not_listed_stops_before_sending]
- ac3: every status wait has its own CHAT_SMOKE_TIMEOUT_S deadline, so a slow S1 does not shorten S3's wait, and a timeout exits 1 naming the step [evidence: test:tests/test_chat_smoke_script.py::test_each_wait_has_its_own_deadline]
- ac4: an S4 that ends failed or is refused is printed with its status and reason and does not fail the script, while a failed S1, S2 or S3 exits 1 [evidence: test:tests/test_chat_smoke_script.py::test_s4_failure_is_reported_not_fatal]
- ac5: the script prints the hours since the room's newest inbound message before S1 [evidence: test:tests/test_chat_smoke_script.py::test_prints_hours_since_last_inbound]
- ac6: no token or ORCH_AGENT_* value is printed, a stale port-forward on its port is killed first, and the trap deletes the session and kills its port-forwards on success, failure and interrupt [evidence: test:tests/test_chat_smoke_script.py::test_cleanup_and_no_secrets]
- ac7: the fakes replay response bodies with the shapes of the connector's committed openapi-agent.json and the orchestrator README chat section [evidence: judgement:reviewer compares the fake bodies with openapi-agent.json on agents-matrix-connector main]
- ac8: the mise task chat-smoke runs the script and README names it [evidence: test:tests/test_mise_tasks.py::test_readme_names_every_task]
- ac9: the targeted tests and lint (ruff, shellcheck, gitleaks) pass [evidence: command:uv run pytest tests/test_chat_smoke_script.py tests/test_mise_tasks.py && mise run lint]

## Files

- `scripts/chat-smoke.sh`
- `mise.toml`
- `tests/test_chat_smoke_script.py`
- `README.md`
- `tests/test_mise_tasks.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
