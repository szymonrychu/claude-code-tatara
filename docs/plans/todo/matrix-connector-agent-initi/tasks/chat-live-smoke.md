---
title: chat live smoke
status: todo
repo: agents-helmfile
value: "the chat tools are live and the user saw an agent post, reply and react in Messenger"
files: [MEMORY.md]
verify: "mise run lint && grep -q chat-smoke MEMORY.md"
depends_on: [helmfile-chat-values, helmfile-web-toggle-pin, helmfile-chat-secrets, chat-smoke-script]
model: sonnet
review: ""
verified_head: ""
points: 8
expected_minutes: 14
expected_tokens: 3155191
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# chat live smoke

## Requirement

README Goal, verbatim: "Docs, tests (unit, contract, e2e) and a live smoke in the owner DM covering send without inbound, quoted reply and reaction."

Design D17, verbatim: "The orchestrator session runs it after the applies and after setting `agents_may_initiate` on the owner DM; the user confirms in Messenger what S1-S4 look like (gate question Q7)."

User decision (final gate, 2026-10-27), verbatim: "1. hard 1:1 relationship between chat and session / Wrap other code changes around it, besides that: Go". Design D17, verbatim (the caller): "Under the 1:1 binding (D9) only the owner DM's bound session may post there, so the script first reads the owner DM's `binding` through the connector UI API (port-forward to the api container) and picks its caller (gate question Q11, recommended; my call pending the answer)". Open question Q11 is pending; the plan follows its recommended answer "yes".

Design D18, verbatim: "(3) Apply the connector first (migration 0002 runs in its init container, creating `room_bindings` with its backfill; the agent listener comes up), then the orchestrator with its chat secret and the v0.3.0 plugins ref (until then the routes answer 503 `chat_unconfigured`; the ref rolls agent pods), then agents-web. (4) The orchestrator session runs every apply with `--selector` in that order; no AC runs an apply. Standing rule (user, 2026-10-27): deploy whenever possible; live applies need no approval."

Open question Q1 (approved by the user 2026-10-27, "All yes"), verbatim: "Only the owner DM gets agents_may_initiate on, set once after deploy (my call, pending gate)?" answer "yes".

Open question Q7 (approved by the user 2026-10-27), verbatim: "You confirm in Messenger what S1-S4 look like (one line each: shown, quoted reply shown, thumbs-up shown, second reaction replaced or rejected), while the orchestrator records the connector-side ids, statuses and reasons?" answer "yes".

User decision (2026-10-27), verbatim: "if the post-deploy smoke shows mautrix-meta does not carry quoted replies/reactions to Messenger, reply/react are dropped and send stays (user-approved)".

Design D17, verbatim (the drop): "If S2 or S3 shows that the deployed mautrix-meta does not carry quoted replies or reactions to Messenger, reply and react are dropped and send stays (user decision 2026-10-27): the orchestrator records it in agents-helmfile MEMORY.md and adds the removal as tasks of this epic (`ticket.py new-task`), without asking again."

Scope (agents-helmfile, orchestrator session; no subagent applies): check the new connector, orchestrator and agents-web image tags exist in Harbor; `mise run diff -- --selector name=<release>` reviewed, then `mise run apply -- --selector name=agents-matrix-connector`, then `name=agents-orchestrator`, then `name=agents-web` (workbench MEMORY 2026-10-25 standing approval for apply-smoke tasks); `mise run smoke` (the regular smoke, posts nothing); set `agents_may_initiate` on the owner DM through a port-forward to the connector api container (PUT `/matrix/api/v1/rooms/!iLWrAwaTMYnINJsyNv:szymonrichert.pl/settings`) and read its `binding` (GET `/matrix/api/v1/rooms/!iLWrAwaTMYnINJsyNv:szymonrichert.pl`) before and after the smoke; `mise run chat-smoke`; ask the user for the Messenger confirmation (Q7); record the results in agents-helmfile `MEMORY.md` (dated: pins, S1-S4 ids, statuses, reasons, hours since the last inbound, the user's confirmation, what S4 did).

## Acceptance conditions

- ac1: (orchestrator session) the three new image tags exist in Harbor before any apply [evidence: judgement:orchestrator records the registry check of each tag in the task Notes]
- ac2: after the three applies helmfile reports no pending change [evidence: command:mise run diff]
- ac3: (orchestrator session) the regular smoke passes on the new deployment [evidence: judgement:orchestrator quotes the final line of mise run smoke with exit 0 in the task Notes]
- ac4: (orchestrator session) the owner DM reads agents_may_initiate true and no other room has it [evidence: judgement:orchestrator quotes GET /matrix/api/v1/rooms filtered to agents_may_initiate true]
- ac5: (orchestrator session) the owner DM's binding is quoted before and after mise run chat-smoke: when it was bound, it is bound to the same session afterwards; when it was unbound, it is released after the throwaway session's deletion [evidence: judgement:orchestrator quotes the binding field of GET /matrix/api/v1/rooms/{owner DM} before and after in the task Notes]
- ac6: (orchestrator session) mise run chat-smoke exits 0 with S1, S2 and S3 sent and S4's status and reason printed [evidence: judgement:orchestrator quotes the S1-S4 lines in the task Notes]
- ac7: (user) Messenger shows S1, S2 as a quoted reply, S3 as a thumbs-up, and S4 replacing the first reaction or not shown; when S2 or S3 does not show, the orchestrator records that reply/react are dropped and send stays (user decision 2026-10-27) and the removal tasks exist in this epic, with no stop to ask [evidence: judgement:the user's one-line confirmation per step, quoted in the task Notes, and for a failed S2 or S3 the drop line and the new task ids]
- ac8: agents-helmfile MEMORY.md records the live results, dated, including the caller (bound session or throwaway), the binding before and after, and whether reply/react were kept or dropped [evidence: command:grep -q "chat-smoke" MEMORY.md]

## Files

- `MEMORY.md`

## Interfaces

- None new; uses `mise run diff`, `mise run apply`, `mise run smoke`, `mise run chat-smoke`, the connector UI API through a port-forward.

## Expected outcome

The chat tools work live: an agent posted, replied and reacted in the owner DM without an inbound message, and the user saw it in Messenger.

## Steps

- Preconditions: helmfile-chat-secrets ac6 (hash matches) green; Q6 precondition holds; tags exist (ac1).
- Diff and apply per release in D18's order; after each apply wait for the rollout; then `mise run diff` (ac2).
- `mise run smoke` (ac3); set the flag (ac4); `mise run chat-smoke` (ac5); ask the user (ac6); write MEMORY.md (ac7) and commit it.

## Notes

- Live and irreversible operations listed in design.md: the applies (the plugins ref rolls every running agent pod, including the mx-5 hive), migration 0002, the flag grant, the Messenger sends.
- Never put an apply in AC evidence (workbench MEMORY 2026-10-25); `mise run diff` exits 0 only when nothing is pending.
- If S2 or S3 shows wrongly in Messenger, reply/react are dropped and send stays (user decision 2026-10-27): record it in MEMORY.md and add the removal (connector reply_to and reactions routes, orchestrator reactions route and `reply_to`, plugin chat_react and `reply_to`, docs) as new tasks of this epic with `ticket.py new-task`; do not stop to ask.
- Minutes run 3-4x over seeds for live tasks in recent epics (retro); plan for several smoke runs.

- 2026-10-27 amended: user decision 2026-10-27: reply/react dropped and send kept if S2 or S3 fails, no stop to ask; Q1 approved

- 2026-10-27 amended: final gate 2026-10-27: hard 1:1 room-session binding replaces last-speaker routing (D9): binding quoted before and after; Q7 approved
