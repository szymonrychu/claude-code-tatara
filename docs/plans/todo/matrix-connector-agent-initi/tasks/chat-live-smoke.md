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

Design D18, verbatim: "(3) Apply the connector first (migration 0002 runs in its init container; the agent listener comes up), then the orchestrator with its chat secret and the v0.3.0 plugins ref (until then the routes answer 503 `chat_unconfigured`; the ref rolls agent pods), then agents-web. (4) The orchestrator session runs every apply with `--selector` in that order; no AC runs an apply."

Open question Q1 (pending gate), verbatim: "Only the owner DM gets agents_may_initiate on, set once after deploy (my call, pending gate)?" recommended "yes".

Open question Q7 (pending gate), verbatim: "You confirm in Messenger what S1-S4 look like (one line each: shown, quoted reply shown, thumbs-up shown, second reaction replaced or rejected), while the orchestrator records the connector-side ids, statuses and reasons?" recommended "yes".

Assumption (design), verbatim: "if S2 or S3 fails, the orchestrator stops and asks (architecture "changes my mind": drop reply/react, keep send)."

Scope (agents-helmfile, orchestrator session; no subagent applies): check the new connector, orchestrator and agents-web image tags exist in Harbor; `mise run diff -- --selector name=<release>` reviewed, then `mise run apply -- --selector name=agents-matrix-connector`, then `name=agents-orchestrator`, then `name=agents-web` (workbench MEMORY 2026-10-25 standing approval for apply-smoke tasks); `mise run smoke` (the regular smoke, posts nothing); set `agents_may_initiate` on the owner DM through a port-forward to the connector api container (PUT `/matrix/api/v1/rooms/!iLWrAwaTMYnINJsyNv:szymonrichert.pl/settings`); `mise run chat-smoke`; ask the user for the Messenger confirmation (Q7); record the results in agents-helmfile `MEMORY.md` (dated: pins, S1-S4 ids, statuses, reasons, hours since the last inbound, the user's confirmation, what S4 did).

## Acceptance conditions

- ac1: (orchestrator session) the three new image tags exist in Harbor before any apply [evidence: judgement:orchestrator records the registry check of each tag in the task Notes]
- ac2: after the three applies helmfile reports no pending change [evidence: command:mise run diff]
- ac3: (orchestrator session) the regular smoke passes on the new deployment [evidence: judgement:orchestrator quotes the final line of mise run smoke with exit 0 in the task Notes]
- ac4: (orchestrator session) the owner DM reads agents_may_initiate true and no other room has it [evidence: judgement:orchestrator quotes GET /matrix/api/v1/rooms filtered to agents_may_initiate true]
- ac5: (orchestrator session) mise run chat-smoke exits 0 with S1, S2 and S3 sent and S4's status and reason printed [evidence: judgement:orchestrator quotes the S1-S4 lines in the task Notes]
- ac6: (user) Messenger shows S1, S2 as a quoted reply, S3 as a thumbs-up, and S4 replacing the first reaction or not shown [evidence: judgement:the user's one-line confirmation per step, quoted in the task Notes]
- ac7: agents-helmfile MEMORY.md records the live results, dated [evidence: command:grep -q "chat-smoke" MEMORY.md]

## Files

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
