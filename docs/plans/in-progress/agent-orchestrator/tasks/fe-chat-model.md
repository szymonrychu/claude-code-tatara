---
title: fe chat model
status: in-progress
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
worktree: /Users/szymonri/Documents/claude-code-tatara/.claude/worktrees/agent-orchestrator-fe-chat-model/agent-orchestrator
branch: agent-orchestrator-fe-chat-model
verified_head: ""
run: agent-orchestrator
provides: []
acs_for_audit: []
process_gaps: []
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

- AC1: each event type maps to its item kind [evidence: command:cd frontend && (test -d node_modules || npm ci --no-audit --no-fund) && npx vitest run src/chat/chatModel.test.ts -t 'maps event types to item kinds']
- AC2: tool calls pair with results by tool_use_id [evidence: command:cd frontend && (test -d node_modules || npm ci --no-audit --no-fund) && npx vitest run src/chat/chatModel.test.ts -t 'pairs tool calls with results']
- AC3: thinking items start collapsed [evidence: command:cd frontend && (test -d node_modules || npm ci --no-audit --no-fund) && npx vitest run src/chat/chatModel.test.ts -t 'thinking starts collapsed']
- AC4: peer-origin user messages become peer items [evidence: command:cd frontend && (test -d node_modules || npm ci --no-audit --no-fund) && npx vitest run src/chat/chatModel.test.ts -t 'peer origin becomes peer item']
- AC5: prepend and append dedupe by event id and keep order [evidence: command:cd frontend && (test -d node_modules || npm ci --no-audit --no-fund) && npx vitest run src/chat/chatModel.test.ts -t 'dedupes and orders on prepend and append']
- AC6: trimWindow keeps the newest items [evidence: command:cd frontend && (test -d node_modules || npm ci --no-audit --no-fund) && npx vitest run src/chat/chatModel.test.ts -t 'trims to newest']
- AC7: gap rows render as gap items [evidence: command:cd frontend && (test -d node_modules || npm ci --no-audit --no-fund) && npx vitest run src/chat/chatModel.test.ts -t 'gap rows become gap items']

## Files

- `frontend/src/chat/chatModel.ts`
- `frontend/src/chat/chatModel.test.ts`

## Interfaces

- `frontend/src/chat/chatModel.ts` (contract `chat-model`): `ChatItem` union, `ChatState`, `applyEvents`, `prependHistory`, `trimWindow`, `filterByAgents`

## Expected outcome

The chat log renders from one tested model.

## Steps

- Write chatModel.test.ts with the seven named tests. Run `npx vitest run src/chat/chatModel.test.ts`; expect failures.
- Implement chatModel.ts.
- Rerun; expect `7 passed`.
- Run `npm run lint`.

## Notes

Adapted from ros2 agent/agentModel.ts (reduceEvent :331, trimWindow :503, prependHistory :519). That file has no thinking kind, so add it here. Event names follow the wrapper README (brief-wrapper section 1) plus `user_message` from epic claude-code-wrapper-orchestr.

- 2026-10-23 run agent-orchestrator: dependency-failed on fe-api-client-and-stream
