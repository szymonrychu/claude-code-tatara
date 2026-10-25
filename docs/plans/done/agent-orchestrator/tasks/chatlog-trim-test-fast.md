---
title: chatlog trim test fast
status: done
repo: agent-orchestrator
value: frontend CI is green on slow runners
files: [frontend/src/chat/ChatLog.tsx, frontend/src/chat/useClusterChat.ts, frontend/src/chat/ChatLog.test.tsx]
verify: "cd frontend && npx vitest run src/chat && npm run lint"
depends_on: [fe-chat-log-paging]
model: ""
review: ""
verified_head: 5c862fc2504154c0de11a0d808f64d0e3338352e
points: 1
expected_minutes: 5
expected_tokens: 750000
points_actual: ""
actual_minutes: 2
actual_tokens: 289690
actual_roles: "impl 1, review 1"
actual_role_tokens: "impl 202045, review 87645"
---

# chatlog trim test fast

## Requirement

CI (GitHub runner) fails frontend/src/chat/ChatLog.test.tsx > 'trims the live window and pages from the new oldest id': Test timed out in 5000ms (5.7 s on the runner, passes locally). The test renders the full MAX_ITEMS window. Make the trim window injectable (a prop or hook option with the production default unchanged) and have the test use a small window so it completes well under the default timeout on slow runners; do not raise the timeout. Behaviour in production unchanged.

## Acceptance conditions

- AC1: the trim test uses a small injected window and passes in under 1 s locally [evidence: command:cd frontend && npx vitest run src/chat/ChatLog.test.tsx]
- AC2: the production default window is unchanged [evidence: command:cd frontend && npx vitest run src/chat]

## Files

- `frontend/src/chat/ChatLog.tsx`
- `frontend/src/chat/useClusterChat.ts`
- `frontend/src/chat/ChatLog.test.tsx`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

The frontend suite passes on slow CI runners.

What is true and observable when the task is done.

## Steps

- Red: CI timeout at 5000 ms on the trim test.
- Inject the window size; shrink it in the test; run green.

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
