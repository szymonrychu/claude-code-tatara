---
title: fe composer and queue strip
status: todo
repo: agent-orchestrator
value: "Lets the user message a cluster (any free agent or a chosen one) and see, cancel or retry what is still queued or failed."
files: [frontend/src/chat/Composer.tsx, frontend/src/chat/QueueStrip.tsx, frontend/src/chat/ChatView.tsx, frontend/src/chat/Composer.test.tsx]
verify: "cd frontend && npm ci --no-audit --no-fund && npx vitest run src/chat/Composer.test.tsx src/layout/designRules.test.ts && npm run lint"
depends_on: [fe-chat-log-paging]
owns: []
uses: [fe-api]
model: ""
estimate: 6
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
- Lists the cluster's queued and failed messages from `listMessages(status=queued,failed)`, refreshed on `message_status` stream deltas.
- Each queued message has Cancel; each failed one has Retry and shows its error.
- It is hidden when empty.

`ChatView.tsx` mounts the strip above the composer, below the log.

## Acceptance conditions

- AC1: Enter sends to any agent and clears the input [evidence: test:frontend/src/chat/Composer.test.tsx::enter sends to any agent]
- AC2: choosing an agent sends target_agent_id [evidence: test:frontend/src/chat/Composer.test.tsx::sends to chosen agent]
- AC3: send is disabled for empty text and deleting clusters [evidence: test:frontend/src/chat/Composer.test.tsx::disables send when empty or deleting]
- AC4: an API error is shown [evidence: test:frontend/src/chat/Composer.test.tsx::shows api error]
- AC5: the queue strip cancels queued and retries failed messages [evidence: test:frontend/src/chat/Composer.test.tsx::queue strip cancels and retries]
- AC6: design rules still hold [evidence: test:frontend/src/layout/designRules.test.ts::source files follow the design rules]

## Files

- `frontend/src/chat/Composer.tsx`
- `frontend/src/chat/QueueStrip.tsx`
- `frontend/src/chat/ChatView.tsx`
- `frontend/src/chat/Composer.test.tsx`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
