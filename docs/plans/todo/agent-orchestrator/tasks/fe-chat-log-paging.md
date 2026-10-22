---
title: fe chat log paging
status: todo
repo: agent-orchestrator
value: "The main chat view with smart loading: newest messages instantly, older ones on scroll-up, live updates, and per-agent filters."
files: [frontend/src/chat/ChatLog.tsx, frontend/src/chat/entries.tsx, frontend/src/chat/useClusterChat.ts, frontend/src/chat/AgentFilter.tsx, frontend/src/chat/ChatView.tsx, frontend/src/App.tsx, frontend/src/chat/ChatLog.test.tsx]
verify: "cd frontend && npm ci --no-audit --no-fund && npx vitest run src/chat/ChatLog.test.tsx src/layout/designRules.test.ts && npm run lint"
depends_on: [fe-chat-model, fe-shell-and-ribbon]
owns: []
uses: [chat-model, fe-api, fe-theme]
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

# fe chat log paging

## Requirement

The chat view (D14).

`useClusterChat(clusterId)`:
- On open, it loads the newest 200 events with `pageEvents`.
- `loadOlder()` pages by `before_id` of the oldest loaded event until `has_more_before` is false.
- It follows `/clusters/{id}/events/stream` after the newest id through openStream.
- An epoch guard drops responses of a previous cluster after a switch.
- It trims the window.

`ChatLog.tsx` uses react-virtuoso:
- `firstItemIndex` prepend, so scroll position holds while older items load.
- `followOutput` sticks to the bottom within 48 px.
- `startReached` calls loadOlder.
- The header reads `Loading older messages` or `Start of history`.

`entries.tsx` renders one row per item kind:
- user input, assistant markdown-free text, a collapsed thinking block
- a collapsible tool entry (name, status, input JSON, output pre)
- denied, turn end with tokens, error, a peer message with sender, and a gap notice
- Every row carries the agent ordinal tag.

`AgentFilter.tsx` shows one chip per agent.

`ChatView.tsx` shows a header (slug, state), the filter and the log. `App.tsx` renders ChatView for the selected cluster.

## Acceptance conditions

- AC1: opening a cluster loads the newest page and renders it [evidence: test:frontend/src/chat/ChatLog.test.tsx::loads newest page on open]
- AC2: reaching the top loads the older page before the oldest id [evidence: test:frontend/src/chat/ChatLog.test.tsx::loads older page on start reached]
- AC3: live stream events append to the log [evidence: test:frontend/src/chat/ChatLog.test.tsx::appends live events]
- AC4: switching clusters drops stale responses [evidence: test:frontend/src/chat/ChatLog.test.tsx::drops stale responses after switch]
- AC5: tool and thinking entries expand on click [evidence: test:frontend/src/chat/ChatLog.test.tsx::expands tool and thinking entries]
- AC6: agent filter chips hide other agents' rows [evidence: test:frontend/src/chat/ChatLog.test.tsx::filters by agent]
- AC7: design rules still hold [evidence: test:frontend/src/layout/designRules.test.ts::source files follow the design rules]

## Files

- `frontend/src/chat/ChatLog.tsx`
- `frontend/src/chat/entries.tsx`
- `frontend/src/chat/useClusterChat.ts`
- `frontend/src/chat/AgentFilter.tsx`
- `frontend/src/chat/ChatView.tsx`
- `frontend/src/App.tsx`
- `frontend/src/chat/ChatLog.test.tsx`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
