---
title: chat smoke script
status: done
repo: agents-helmfile
value: "one command proves send without inbound, quoted reply and reactions live, leaving nothing behind"
files: [scripts/chat-smoke.sh, mise.toml, tests/test_chat_smoke_script.py, README.md, tests/test_mise_tasks.py]
verify: "uv run pytest tests/test_chat_smoke_script.py tests/test_mise_tasks.py && mise run lint"
depends_on: [mxc-agent-routes, orch-chat-relay, mxc-room-initiate-flag]
model: opus
review: ""
verified_head: 0804582c1488b5b936ee1969aa62bfd61ac923e9
points: 5
expected_minutes: 8
expected_tokens: 1727786
points_actual: 5
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# chat smoke script

## Requirement

README Goal, verbatim: "Docs, tests (unit, contract, e2e) and a live smoke in the owner DM covering send without inbound, quoted reply and reaction."

Design D17, verbatim: "`scripts/chat-smoke.sh` (mise task `chat-smoke`), never part of `scripts/smoke.sh`, because it posts real messages from the owner's Facebook account. Under the 1:1 binding (D9) only the owner DM's bound session may post there, so the script first reads the owner DM's `binding` through the connector UI API (port-forward to the api container) and picks its caller (gate question Q11, recommended; my call pending the answer): when the DM is bound, the leader pod of the bound session (that pod's own `ORCH_AGENT_*` env, never printed; no message to or change of that session, nothing created or deleted); when it is unbound, a throwaway alone session whose S1 initiates and binds the DM, deleted at the end, after which the script waits for the binding's release (its own deadline). From the chosen pod it calls the orchestrator agent routes: lists rooms (the owner DM `!iLWrAwaTMYnINJsyNv:szymonrichert.pl` must be listed), S1 sends a message with no inbound in the run, S2 replies to S1's `s<n>`, S3 reacts with a thumbs-up to S1's `s<n>`, S4 reacts with a second, different emoji to the same target; it polls each send's status to `sent` or `failed` with its own deadline per wait, prints the caller (bound session or throwaway), the binding before and after, the ids, statuses and reasons, owns its port-forwards (trap cleanup) and deletes the throwaway session when it made one."

User decision (final gate, 2026-10-27), verbatim: "1. hard 1:1 relationship between chat and session / Wrap other code changes around it, besides that: Go".

Open question Q11 (pending; the plan follows the recommended answer), verbatim: "Under the 1:1 rule a throwaway smoke session is refused room_bound in the owner DM whenever the DM is already bound to its chat session (for example the mx-5 hive leader). Should chat-smoke run S1-S4 from the leader pod of the session the owner DM is bound to (only that pod's own agent credentials; no message to or change of that session, nothing created or deleted), and create a throwaway session that initiates there and is deleted afterwards (releasing the binding) only when the owner DM is unbound?" recommended "yes".

Architecture, verbatim: "S1 a send with no inbound message for >24h shows up in Messenger; S2 a reply shows as a quoted reply; S3 a thumbs-up reaction shows; S4 a second, different reaction replaces the first or is rejected (and how the connector sees the failure)."

Open question Q8 (approved by the user 2026-10-27), verbatim: "S1 runs at smoke time even if the owner DM had an inbound message in the last 24 h; the smoke records the hours since the last inbound, and the over-24h case is confirmed at the first natural opportunity and noted in agents-helmfile MEMORY.md without holding the epic?" answer "yes".

Retro proposals, verbatim: "for smoke-script tasks the reviewer checks every timeout or deadline against the AC and the MEMORY claim" and "smoke script owns its port-forward (trap cleanup, kill stale on the port first) and orchestrator runs no manual port-forwards during smoke."

Scope (agents-helmfile): new `scripts/chat-smoke.sh` (env `RELEASE`, `NAMESPACE`, `CHAT_SMOKE_ROOM` default `!iLWrAwaTMYnINJsyNv:szymonrichert.pl`, `CHAT_SMOKE_PRESET` or the default preset, `CHAT_SMOKE_TIMEOUT_S` per wait, `MATRIX_RELEASE`, `SMOKE_LOCAL_PORT`, `SMOKE_MATRIX_API_LOCAL_PORT`); it also reads, through a port-forward to the connector api container, the room's `binding` (to pick its caller, D17) and newest inbound message time, and prints the hours since it (S1 precondition, Q8). New mise task `chat-smoke`; README names the task and says it posts to the owner DM; `tests/test_chat_smoke_script.py` with kubectl and curl fakes.

## Acceptance conditions

- ac1: against fakes the script lists the rooms, runs S1, S2 (reply_to S1's id), S3 (thumbs-up to S1's id) and S4 (a different emoji to S1's id) in that order, prints each id, status and reason, and exits 0 when S1-S3 end sent [evidence: test:tests/test_chat_smoke_script.py::test_s1_to_s4_happy_path]
- ac2: when the owner DM's binding names a session, the script runs S1-S4 from that session's leader pod with that pod's own agent env, creates and deletes no session, sends no message to that session, and prints the caller and the binding before and after [evidence: test:tests/test_chat_smoke_script.py::test_bound_dm_uses_bound_session]
- ac3: when the owner DM is unbound, the script creates a throwaway session whose S1 initiates there, deletes it at the end and waits, with its own deadline, until the DM's binding is released, printing the binding before, during and after; a binding still held at that deadline exits 1 naming the step [evidence: test:tests/test_chat_smoke_script.py::test_unbound_dm_uses_throwaway_and_waits_release]
- ac4: when the owner DM is not listed for the chosen caller the script exits 1 naming the room and sends nothing [evidence: test:tests/test_chat_smoke_script.py::test_room_not_listed_stops_before_sending]
- ac5: every status wait has its own CHAT_SMOKE_TIMEOUT_S deadline, so a slow S1 does not shorten S3's wait, and a timeout exits 1 naming the step [evidence: test:tests/test_chat_smoke_script.py::test_each_wait_has_its_own_deadline]
- ac6: an S4 that ends failed or is refused is printed with its status and reason and does not fail the script, while a failed S1, S2 or S3 exits 1 [evidence: test:tests/test_chat_smoke_script.py::test_s4_failure_is_reported_not_fatal]
- ac7: the script prints the hours since the room's newest inbound message before S1 [evidence: test:tests/test_chat_smoke_script.py::test_prints_hours_since_last_inbound]
- ac8: no token or ORCH_AGENT_* value is printed, a stale port-forward on its port is killed first, and the trap deletes the throwaway session (only one the script created) and kills its port-forwards on success, failure and interrupt [evidence: test:tests/test_chat_smoke_script.py::test_cleanup_and_no_secrets]
- ac9: the fakes replay response bodies with the shapes of the connector's committed openapi-agent.json and openapi.json (the room binding) and the orchestrator README chat section [evidence: judgement:reviewer compares the fake bodies with openapi-agent.json and openapi.json on agents-matrix-connector main]
- ac10: the mise task chat-smoke runs the script and README names it [evidence: test:tests/test_mise_tasks.py::test_readme_names_every_task]
- ac11: the targeted tests and lint (ruff, shellcheck, gitleaks) pass [evidence: command:uv run pytest tests/test_chat_smoke_script.py tests/test_mise_tasks.py && mise run lint]

## Files

- `scripts/chat-smoke.sh`
- `mise.toml`
- `tests/test_chat_smoke_script.py`
- `README.md`
- `tests/test_mise_tasks.py`

## Interfaces

- `mise run chat-smoke` = `bash scripts/chat-smoke.sh`.
- Output lines: `caller: bound <slug>` or `caller: throwaway <slug>`, `binding before: <slug or none>`, `hours since last inbound: <n>`, `S1 s<n> sent`, `S2 s<n> sent`, `S3 s<n> sent`, `S4 s<n> <status> <reason>`, `binding after: <slug or none>`.
- Reads `binding` from `GET /matrix/api/v1/rooms/{room_id}` of the connector UI API (mxc-room-initiate-flag) through the api container port-forward.

## Expected outcome

One command proves send without inbound, quoted reply and reactions against the live deployment, leaving no session or port-forward behind.

## Steps

- Red: write `tests/test_chat_smoke_script.py` following `tests/test_smoke_script.py` (PATH-injected kubectl and curl fakes); run `uv run pytest tests/test_chat_smoke_script.py`: fails (no script).
- Green: write the script and the mise task, README; run the task's verify: passes. Quote the summary line with counts.

## Notes

- Reuse `scripts/smoke.sh`'s patterns: session creation through the orchestrator API port-forward, waiting for a Ready pod, running curl inside the pod with its own `ORCH_AGENT_*` env (never printed), trap cleanup.
- Bound case (Q11, recommended answer; the plan follows it until Q11 is answered): the caller is the bound session's leader pod. How to find that pod for a hive session is a fact to probe at build time (the orchestrator API's session view and the pod labels `agents.szymonrichert.pl/session=<slug>` used by `scripts/smoke.sh`); if neither names the leader pod, return it as a question, never guess. The script only runs curl in that pod; it never posts a session message, never scales, restarts or deletes that session.
- The calls go through the orchestrator agent routes from inside the session pod (agent identity is the pod IP), never directly to the connector agent port, so the smoke proves the whole path including the relay.
- Each wait gets its own deadline variable computed when that wait starts (retro: a shared deadline failed a smoke spuriously).
- Never add these steps to `scripts/smoke.sh`: that smoke must never send a Matrix message.

- 2026-10-27 amended: final gate 2026-10-27: hard 1:1 room-session binding replaces last-speaker routing (D9): caller picked from the owner DM binding (Q11)

- 2026-10-28 done

- 2026-10-28 actuals: no agent records
