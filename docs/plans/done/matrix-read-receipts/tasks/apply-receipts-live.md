---
title: apply receipts live
status: done
repo: agents-helmfile
value: "Messenger shows the user's messages as seen once the agent has them"
files: [MEMORY.md]
verify: "mise run diff && mise run smoke"
depends_on: [connector-repin-receipts]
model: sonnet
review: ""
verified_head: 296318b4bbf54d31e3d4feb2abee24e00799b737
points: 1
expected_minutes: 4
expected_tokens: 665870
points_actual: 1
actual_minutes: 90
actual_tokens: 1044057
actual_roles: "impl 89, review 1"
actual_role_tokens: "impl 961489, review 82568"
---

# apply receipts live

## Requirement

Apply the re-pinned connector and prove receipts live (epic goal G3; live-deploy rule: only the main orchestrator session `claude-code-tatara-7b` applies, through "APPLY REQUEST <epic> <tree> <sha>"). Paths are in code/agents-helmfile.

User request 2026-10-26, verbatim: 'Add read receipts'.

- Implementer, before the apply: `mise run diff`; only the agents-matrix-connector release changes (chart version, image tag). Anything else ends `blocked` with the diff, whoCanClear "user". End the round with "ready for apply".
- After the apply, implementer: `mise run diff` (no drift) and `mise run smoke` (exit 0); `MEMORY.md`: a dated line: applied agents-matrix-connector `0.1.0-main.<sha7>` with read receipts; smoke green (quote its last log line).
- Live proof, read-only, after the user sends one new Messenger message in the owner DM `!iLWrAwaTMYnINJsyNv:szymonrichert.pl`: the bot log shows the receipt request for that room answered 200 (no token in the output), `GET /matrix/api/v1/rooms/{room_id}/messages` shows the message handed off, and the user confirms the message shows as seen in Messenger. Evidence (statuses, event ids, no bodies) goes to `/Users/szymonri/Documents/claude-code-tatara/.scratchpad/matrix-read-receipts/live-proof.md`. Never send a Matrix message, never change rules or settings.

## Acceptance conditions

- AC1: the live namespace has no drift after the apply and the smoke passes [evidence: command:mise run diff && mise run smoke]
- AC2: MEMORY.md records the applied version [evidence: command:grep -q "read receipts" MEMORY.md]
- AC3: a real handed-off message in the owner DM got a 200 receipt and shows as seen [evidence: judgement:the log excerpt, messages output and user confirmation in live-proof.md]

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

- 2026-10-26 done
