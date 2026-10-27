---
title: web command rows
status: done
repo: agents-web
value: "the chat shows each slash command once, with its live status and claude's output"
files: [src/chat/chatModel.ts, src/chat/entries.tsx, src/chat/chatModel.test.ts, src/chat/ChatLog.test.tsx]
verify: "npx vitest run src/chat/chatModel.test.ts src/chat/ChatLog.test.tsx src/layout/designRules.test.ts && npm run lint"
depends_on: []
model: sonnet
review: ""
verified_head: 24e6911363fc1ba04c254a883d21cb77bc047917
points: 3
expected_minutes: 6
expected_tokens: 963314
points_actual: 3
actual_minutes: 5
actual_tokens: 665380
actual_roles: "impl 4, review 1"
actual_role_tokens: "impl 590527, review 74853"
---

# web command rows

## Requirement

Goal G4 (README), verbatim: "The chat shows the command and its outcome." Non-goal, verbatim: "No slash-command autocomplete or picker in the composer."

Design D12, verbatim: "agents-web `chatModel.ts` adds a `command` ChatItem `{commandId, name, args, status, result?, error?, output?}` built from `command_queued`, `command_started`, `command_completed`, `command_failed` event rows (`data.record`), updated in place by `record.id` (tool-row pattern): status `queued` -> `running` -> `completed` (with result ok | dismissed | skipped_cache | turn) or `failed` (with error) or `cancelled`. `entries.tsx` renders it with the label `command`, the line `/name args`, the status and the output in a mono `<pre>`. Ruling (my call): `user_message` rows with origin `command` (the typed-line echo) are folded into the command row and not rendered on their own, so a command shows once. A promoted prompt command also shows its normal turn rows. A command the orchestrator could not deliver shows in QueueStrip as failed with the wrapper code (D10). Composer is unchanged (non-goal: no picker)."

Wrapper event shape (claude-code-wrapper `router.py:_emit_command`): `{"type": "command_queued" | "command_started" | "command_completed" | "command_failed", "data": {"record": {"id", "name", "args" (string), "origin", "turn_id", "state" (queued | running | completed | failed | cancelled), "result", "error", "output", ...}}}`; a cancelled record arrives as `command_failed` with `state: "cancelled"`.

Scope (agents-web): `src/chat/chatModel.ts`, `src/chat/entries.tsx`, `src/chat/chatModel.test.ts`, `src/chat/ChatLog.test.tsx`.

Test no longer accurate (named): `src/chat/chatModel.test.ts` "maps event types to item kinds" expects a `user_message` row with origin `command` to become a `user_message` item (row 4); under the D12 ruling that row yields no item.

## Acceptance conditions

- ac1: command_queued, command_started, command_completed rows of one record id become one command item that goes queued, running, completed with result and output, in any arrival order within a batch and across batches (new) [evidence: test:src/chat/chatModel.test.ts::command row lifecycle]
- ac2: command_failed gives status failed with the error, or cancelled when the record state is cancelled (new) [evidence: test:src/chat/chatModel.test.ts::command row failure and cancel]
- ac3: a user_message row with origin command yields no item; other origins are unchanged (updated) [evidence: test:src/chat/chatModel.test.ts::maps event types to item kinds]
- ac4: ChatLog renders the command row: label command, the line "/reload-plugins", the status and the output in a pre (new) [evidence: test:src/chat/ChatLog.test.tsx::renders command row]
- ac5: the design rules and nomenclature guards stay green [evidence: command:npx vitest run src/layout/designRules.test.ts src/nomenclature.test.ts]
- ac6: targeted tests and lint pass [evidence: command:npx vitest run src/chat/chatModel.test.ts src/chat/ChatLog.test.tsx src/layout/designRules.test.ts && npm run lint]

## Files

- `src/chat/chatModel.ts`
- `src/chat/entries.tsx`
- `src/chat/chatModel.test.ts`
- `src/chat/ChatLog.test.tsx`

## Interfaces

- `ChatItem` variant `Base & { kind: 'command'; commandId: string; name: string; args: string; status: 'queued' | 'running' | 'completed' | 'failed' | 'cancelled'; result?: string; error?: string; output?: string }`.

## Expected outcome

A slash command sent from the chat appears as one row that updates from queued to its outcome, with claude's output when there is any.

## Steps

- Red: add the chatModel and ChatLog tests (ac1, ac2, ac4), update ac3; run `npx vitest run src/chat/chatModel.test.ts src/chat/ChatLog.test.tsx`: they fail.
- Green: chatModel.ts and entries.tsx; run the task's verify: passes. Quote the vitest summary line.

## Notes

- Reuse the tool-row pairing pattern (`chatModel.ts` merge: update items already in the window, keep the earliest eventId as the row position).
- Status colours come from theme tokens (`STATUS_COLOUR` pattern in entries.tsx); no colour literals, no arrows (designRules).
- Ruling pinned by ac3: the typed-line echo folds into the command row.
- Run only the chat test files: the full suite has 10 load-dependent timeouts here (design Constraints).
- No dependency inside the epic (the event shape is the wrapper's existing one; `args` becomes a string with wrapper-command-args).

- 2026-10-27 done
