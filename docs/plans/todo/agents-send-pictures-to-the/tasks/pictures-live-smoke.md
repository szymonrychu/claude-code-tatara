---
title: pictures live smoke
status: todo
repo: agents-helmfile
value: "a real picture with a caption reaches the owner's Messenger DM from the deployed system"
files: [MEMORY.md]
verify: "mise run lint && grep -q 'pictures live smoke' MEMORY.md"
depends_on: [helmfile-pictures-pin]
model: sonnet
review: ""
verified_head: ""
points: 2
expected_minutes: 5
expected_tokens: 545296
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# pictures live smoke

## Requirement

User decision (binding), verbatim: "Live smoke posts one real picture with a caption to the owner's Messenger DM after the helmfile apply under the deploy lease (Lease agents/agents-helmfile-apply)."

README Goal G5, verbatim: "released and deployed in order (plugins, connector, orchestrator, web, helmfile) and proven by a live smoke that posts one real picture with a caption to the owner's Messenger DM."

Design D10, verbatim: "After the helmfile apply (deploy lease taken), the session posts one real picture with a caption to the owner's Messenger DM through the tool; the owner confirms in Messenger; the web chat shows the picture; orchestrator_chat_status shows the send `sent`. User Q7."

Open question Q7 (planned on its recommended answer): "The live smoke posts one real picture with a caption to your Messenger DM? [recommended: yes]"

Steps, run by the orchestrator session (never a subagent: subagent `kubectl exec` and applies are denied), in `code/agents-helmfile` on `main` after the helmfile-pictures-pin PR merged, least destructive first:
1. Claim the deploy lease, Lease `agents/agents-helmfile-apply`, before the first diff; hold it through the applies and the smoke; release it at the end. If the session does not know the claim procedure, it asks; it never applies without the lease.
2. Check each pinned image tag and chart version exists in Harbor; run the release tests that need `helmfile build` (helmfile-pictures-pin Notes).
3. Per release in the order connector, orchestrator, web (`--selector name=agents-matrix-connector`, then `name=agents-orchestrator`, then `name=agents-web`): `mise run diff -- --selector name=<release>` and read it: the change is the chart version, the image tag and, for the orchestrator, `ORCH_ANY_MCP_PLUGINS_REF`; anything else stops the task. Before the orchestrator apply (it rolls agent pods, the session running this task included) write a handoff checkpoint (`workbench:handoff`) naming the remaining steps, the pins and the Notes so far. Then `mise run apply -- --selector name=<release>`. The connector applies its send-images migration on start.
4. After the applies (by the resumed leader if the session was rolled): `mise run diff` shows no pending change; `mise run smoke` green.
5. Live picture (my call: "the session" of D10 is this orchestrator session, an agent session with the orchestrator plugin): save one small picture (a png) in its own workspace and call `orchestrator_chat_send_image` with that path, a caption naming the smoke and the date, and `room` the owner DM (`!iLWrAwaTMYnINJsyNv:szymonrichert.pl`, the chat-smoke default). The DM must be bound to this session, or unbound, flagged `agents_may_initiate` and this session bound to no room; a `room_bound` or `session_bound` refusal stops the task and asks the user, with no binding changed. Poll `orchestrator_chat_status` to `sent`. Open this session's chat in the web UI and confirm the picture shows in the tool-call box. Ask the user to confirm the picture and the caption in Messenger.
6. MEMORY.md entry containing the words `pictures live smoke`, dated, with the applied pins, the plugins ref, the send id, its status, the web check and the user's confirmation, and the Synapse `m.upload.size` the bot read (design: "Synapse `max_upload_size` is unknown ... the smoke confirms it").

Notes: never put `mise run apply` in AC evidence (agents-helmfile MEMORY 2026-10-25).

## Acceptance conditions

- ac1: (orchestrator session) the deploy lease Lease agents/agents-helmfile-apply was held from the first diff to the end of the smoke [evidence: judgement:orchestrator records the claim and release times in the task Notes]
- ac2: (orchestrator session) each pinned image tag and chart version existed in Harbor before its apply, and each release's diff showed only its pins before its apply, applied in the order connector, orchestrator, web [evidence: judgement:orchestrator records the registry checks and the three diff summaries in the task Notes]
- ac3: after the applies helmfile reports no pending change [evidence: command:mise run diff]
- ac4: the regular smoke passes against the applied releases [evidence: command:mise run smoke]
- ac5: (orchestrator session) orchestrator_chat_send_image sent one real picture with a caption to the owner DM and orchestrator_chat_status reports it sent [evidence: judgement:orchestrator quotes the tool result (s<n>, path) and the final status in the task Notes]
- ac6: (orchestrator session) the session's web chat shows the picture in the tool-call box [evidence: judgement:orchestrator records what the web chat showed, with the session id, in the task Notes]
- ac7: (user) Messenger shows the picture followed by its caption [evidence: judgement:the user's one-line confirmation, quoted in the task Notes]
- ac8: (orchestrator session) a handoff checkpoint naming the remaining steps was written before the orchestrator apply, and the steps after the roll ran from it [evidence: judgement:orchestrator quotes the checkpoint path in the task Notes]
- ac9: agents-helmfile MEMORY.md records the live picture smoke and the applied versions [evidence: command:grep -q "pictures live smoke" MEMORY.md]

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
