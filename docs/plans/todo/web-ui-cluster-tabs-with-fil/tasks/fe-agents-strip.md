---
title: fe agents strip
status: todo
repo: agent-orchestrator
value: per-agent state and context stay visible in the chat header and double as the agent filter
files: [frontend/src/chat/AgentsStrip.tsx, frontend/src/chat/AgentsStrip.test.tsx, frontend/src/chat/ChatView.tsx, frontend/src/chat/AgentFilter.tsx, frontend/src/ribbon/AgentRow.tsx]
verify: "mise x node@24.20.0 -- npm --prefix frontend ci && mise x node@24.20.0 -- npm --prefix frontend test -- src/chat src/layout/designRules.test.ts && mise x node@24.20.0 -- npm --prefix frontend run lint && mise x node@24.20.0 -- npm --prefix frontend run build"
depends_on: [fe-retire-ribbon]
owns: []
uses: []
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

# fe agents strip

## Requirement

Move the per-agent rows into the chat panel header as an agents strip merged with the agent filter (user Q2), test-first.

- New `frontend/src/chat/AgentsStrip.tsx`: `AgentsStrip({agents, selected, onToggle, autoCompactPct})`, one compact chip-like item per agent in `sortedAgents` order showing ordinal or pod name, `StateMark` for the agent state, "free since" age (`formatAge`, refreshed every second as `AgentRow` does today) and the agent's own `ContextGauge`; clicking an item toggles it in the chat filter exactly as `AgentFilter` chips do today (same selection semantics, same ChatLog filtering). The strip wraps or scrolls horizontally on narrow panels.
- `frontend/src/chat/ChatView.tsx` renders `AgentsStrip` where `AgentFilter` was; nothing else in ChatView changes (log, queue strip, composer, paging).
- Retired: `frontend/src/chat/AgentFilter.tsx` and `frontend/src/ribbon/AgentRow.tsx` (its `formatAge` and the 1 s clock move into `AgentsStrip.tsx` or a small `chat/agentAge.ts`).

## Acceptance conditions

- AC1: the strip shows each agent's name, state mark, free-since age and own gauge in ordinal order [evidence: test:frontend/src/chat/AgentsStrip.test.tsx::shows_agent_rows]
- AC2: clicking an agent toggles the chat filter as the old chips did [evidence: test:frontend/src/chat/AgentsStrip.test.tsx::click_toggles_filter]
- AC3: formatAge keeps its outputs [evidence: test:frontend/src/chat/AgentsStrip.test.tsx::format_age_unchanged]
- AC4: AgentFilter.tsx and AgentRow.tsx are gone from git ls-files [evidence: test:frontend/src/chat/AgentsStrip.test.tsx::agent_filter_and_row_retired]
- AC5: chat tests, design rules, lint and build pass [evidence: command:mise x node@24.20.0 -- npm --prefix frontend ci && mise x node@24.20.0 -- npm --prefix frontend test -- src/chat src/layout/designRules.test.ts && mise x node@24.20.0 -- npm --prefix frontend run lint && mise x node@24.20.0 -- npm --prefix frontend run build]

## Files

- `frontend/src/chat/AgentsStrip.tsx`
- `frontend/src/chat/AgentsStrip.test.tsx`
- `frontend/src/chat/ChatView.tsx`
- `frontend/src/chat/AgentFilter.tsx`
- `frontend/src/ribbon/AgentRow.tsx`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
