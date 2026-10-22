---
title: fe chat model
status: todo
repo: agent-orchestrator
value: "Turns stored agent events into readable chat items: inputs, outputs, thinking, paired tool calls, peer messages and gaps."
files: [frontend/src/chat/chatModel.ts, frontend/src/chat/chatModel.test.ts]
verify: "cd frontend && npm ci --no-audit --no-fund && npx vitest run src/chat/chatModel.test.ts && npm run lint"
depends_on: [fe-api-client-and-stream]
owns: [chat-model]
uses: [fe-api]
model: ""
estimate: 5
estimate_by: formula
actual: ""
actual_roles: ""
review: ""
worktree: ""
branch: ""
verified_head: ""
run: ""
provides: []
---

# fe chat model

## Requirement

`chatModel.ts`: a pure reducer over stored event rows `{id, agent_id, type, ts, turn_id, data}` (D14).

Item kinds:
- `user_message`: from `user_message` with origin user, hook, restart or command.
- `peer`: from `user_message` with origin peer, and from `peer_message_received`.
- `assistant`: from `assistant_text`.
- `thinking`: from `thinking`, collapsed by default.
- `tool`: from `tool_call`, paired by tool_use_id with `tool_result`, which sets status ok or error and the output; unpaired means running.
- `denied`: from `tool_denied`.
- `turn_end`: from `turn_completed`, carrying usage.
- `error`: from `turn_failed` and `error`.
- `gap`: from `gap`.
- Unknown types are ignored.

Every item carries `eventId`, `agentId`, `agentOrdinal` (through a supplied map) and `ts`.

Operations:
- `applyEvents(state, rows)` appends in id order and dedupes by event id.
- `prependHistory(state, rows)` inserts older rows, dedupes, and keeps pairing across the page boundary.
- `trimWindow(state, max = 2000)` keeps the newest.
- `filterByAgents(items, ids)`.

## Acceptance conditions

- AC1: each event type maps to its item kind [evidence: test:frontend/src/chat/chatModel.test.ts::maps event types to item kinds]
- AC2: tool calls pair with results by tool_use_id [evidence: test:frontend/src/chat/chatModel.test.ts::pairs tool calls with results]
- AC3: thinking items start collapsed [evidence: test:frontend/src/chat/chatModel.test.ts::thinking starts collapsed]
- AC4: peer-origin user messages become peer items [evidence: test:frontend/src/chat/chatModel.test.ts::peer origin becomes peer item]
- AC5: prepend and append dedupe by event id and keep order [evidence: test:frontend/src/chat/chatModel.test.ts::dedupes and orders on prepend and append]
- AC6: trimWindow keeps the newest items [evidence: test:frontend/src/chat/chatModel.test.ts::trims to newest]
- AC7: gap rows render as gap items [evidence: test:frontend/src/chat/chatModel.test.ts::gap rows become gap items]

## Files

- `frontend/src/chat/chatModel.ts`
- `frontend/src/chat/chatModel.test.ts`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
