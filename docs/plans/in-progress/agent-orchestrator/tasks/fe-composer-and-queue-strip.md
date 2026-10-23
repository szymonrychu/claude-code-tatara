---
title: fe composer and queue strip
status: done
repo: agent-orchestrator
value: "Lets the user message a cluster (any free agent or a chosen one) and see, cancel or retry what is still queued or failed."
files: [frontend/src/chat/Composer.tsx, frontend/src/chat/QueueStrip.tsx, frontend/src/chat/ChatView.tsx, frontend/src/chat/Composer.test.tsx]
verify: "cd frontend && npm ci --no-audit --no-fund && npx vitest run src/chat/Composer.test.tsx src/layout/designRules.test.ts && npm run lint"
depends_on: [fe-api-client-and-stream, fe-chat-log-paging]
owns: []
uses: [fe-api]
model: ""
estimate: 6
estimate_by: formula
actual: ""
actual_roles: ""
review: ""
worktree: /Users/szymonri/Documents/claude-code-tatara/.claude/worktrees/agent-orchestrator-fe-composer-and-queue-strip/agent-orchestrator
branch: agent-orchestrator-fe-composer-and-queue-strip
verified_head: bf7f8d67207f4a79cb0366298e64357e9717a1a6
run: agent-orchestrator
provides: []
acs_for_audit: []
process_gaps: []
---

# fe composer and queue strip

## Requirement

Composer and queue strip (D4, D14).

`Composer.tsx`:
- A multiline input: Enter sends, Shift+Enter inserts a newline.
- A target select: `Any free agent` (the default, round-robin) or a specific agent ordinal.
- A send button that is disabled for empty text or a deleting cluster.
- `postMessage` with `target_agent_id` when one is chosen.
- It clears on 202 and shows the ApiError message in an outlined Alert on failure.

`QueueStrip.tsx`:
- Lists the cluster's queued, verifying and failed messages from `listMessages(status=queued,verifying,failed)`, refreshed on `message_status` stream deltas.
- A queued message waiting out a retry shows `attempt n of max` and its `next_attempt_at`; a verifying one shows `checking delivery`.
- Each queued message has Cancel; each failed one has Retry and shows its error. Retry on a message failed as `ambiguous` first warns that the turn may already have run.
- It is hidden when empty.

`ChatView.tsx` mounts the strip above the composer, below the log.

## Acceptance conditions

- AC1: Enter sends to any agent and clears the input [evidence: command:cd frontend && (test -d node_modules || npm ci --no-audit --no-fund) && npx vitest run src/chat/Composer.test.tsx -t 'enter sends to any agent']
- AC2: choosing an agent sends target_agent_id [evidence: command:cd frontend && (test -d node_modules || npm ci --no-audit --no-fund) && npx vitest run src/chat/Composer.test.tsx -t 'sends to chosen agent']
- AC3: send is disabled for empty text and deleting clusters [evidence: command:cd frontend && (test -d node_modules || npm ci --no-audit --no-fund) && npx vitest run src/chat/Composer.test.tsx -t 'disables send when empty or deleting']
- AC4: an API error is shown [evidence: command:cd frontend && (test -d node_modules || npm ci --no-audit --no-fund) && npx vitest run src/chat/Composer.test.tsx -t 'shows api error']
- AC5: the queue strip cancels queued and retries failed messages [evidence: command:cd frontend && (test -d node_modules || npm ci --no-audit --no-fund) && npx vitest run src/chat/Composer.test.tsx -t 'queue strip cancels and retries']
- AC7: the queue strip shows the attempt count, next attempt time and verifying state, and warns before retrying an ambiguous failure [evidence: command:cd frontend && (test -d node_modules || npm ci --no-audit --no-fund) && npx vitest run src/chat/Composer.test.tsx -t 'queue strip shows retry state']
- AC6: design rules still hold [evidence: command:cd frontend && (test -d node_modules || npm ci --no-audit --no-fund) && npx vitest run src/layout/designRules.test.ts -t 'source files follow the design rules']

## Files

- `frontend/src/chat/Composer.tsx`
- `frontend/src/chat/QueueStrip.tsx`
- `frontend/src/chat/ChatView.tsx`
- `frontend/src/chat/Composer.test.tsx`

## Interfaces

- `frontend/src/chat/Composer.tsx:Composer({cluster, agents})`; `frontend/src/chat/QueueStrip.tsx:QueueStrip({clusterId})`

## Expected outcome

Messages can be sent round-robin or targeted, and the queue is visible and actionable.

## Steps

- Write Composer.test.tsx with the five named tests (jsdom, user-event, mocked client). Run it; expect failures.
- Implement Composer, QueueStrip and the ChatView wiring.
- Rerun; expect `5 passed`.
- Run the designRules test and `npm run lint`.

## Notes

The ros2 composer is tabs/AgentChatTab.tsx:110-126. The dispatcher retries definite non-accepts automatically with backoff and verifies ambiguous sends (D24). The Retry button is the user's explicit re-send of a failed message.

- 2026-10-23 run agent-orchestrator: dependency-failed on fe-chat-log-paging
