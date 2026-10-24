---
title: fe agents strip
status: done
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
actual: 9
actual_roles: "impl 2, verify 4, review 1, fix 1, land 1"
review: ""
worktree: /home/user/claude-code-tatara/.claude/worktrees/web-ui-cluster-tabs-with-fil-fe-agents-strip/agent-orchestrator
branch: web-ui-cluster-tabs-with-fil-fe-agents-strip
verified_head: d5bce5e9fcc11eab8332bb1a546b54d578315aac
run: web-ui-cluster-tabs-with-fil
provides: []
acs_for_audit: []
process_gaps: []
---

# fe agents strip

## Requirement

Move the per-agent rows into the chat panel header as an agents strip merged with the agent filter (user Q2), test-first.

- New `frontend/src/chat/AgentsStrip.tsx`: `AgentsStrip({agents, selected, onToggle, autoCompactPct})`, one compact chip-like item per agent in `sortedAgents` order showing ordinal or pod name, `StateMark` for the agent state, "free since" age (`formatAge`, refreshed every second as `AgentRow` does today) and the agent's own `ContextGauge`; clicking an item toggles it in the chat filter exactly as `AgentFilter` chips do today (same selection semantics, same ChatLog filtering). The strip wraps or scrolls horizontally on narrow panels.
- `frontend/src/chat/ChatView.tsx` renders `AgentsStrip` where `AgentFilter` was; nothing else in ChatView changes (log, queue strip, composer, paging).
- Retired: `frontend/src/chat/AgentFilter.tsx` and `frontend/src/ribbon/AgentRow.tsx` (its `formatAge` and the 1 s clock move into `AgentsStrip.tsx` or a small `chat/agentAge.ts`).

## Acceptance conditions

- AC1: the strip shows each agent's name, state mark, free-since age and own gauge in ordinal order [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/chat/AgentsStrip.test.tsx -t shows_agent_rows]
- AC2: clicking an agent toggles the chat filter as the old chips did [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/chat/AgentsStrip.test.tsx -t click_toggles_filter]
- AC3: formatAge keeps its outputs [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/chat/AgentsStrip.test.tsx -t format_age_unchanged]
- AC4: AgentFilter.tsx and AgentRow.tsx are gone from git ls-files [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/chat/AgentsStrip.test.tsx -t agent_filter_and_row_retired]
- AC5: chat tests, design rules, lint and build pass [evidence: command:mise x node@24.20.0 -- npm --prefix frontend ci && mise x node@24.20.0 -- npm --prefix frontend test -- src/chat src/layout/designRules.test.ts && mise x node@24.20.0 -- npm --prefix frontend run lint && mise x node@24.20.0 -- npm --prefix frontend run build]

## Files

- `frontend/src/chat/AgentsStrip.tsx`
- `frontend/src/chat/AgentsStrip.test.tsx`
- `frontend/src/chat/ChatView.tsx`
- `frontend/src/chat/AgentFilter.tsx`
- `frontend/src/ribbon/AgentRow.tsx`

## Interfaces

- `frontend/src/chat/AgentsStrip.tsx`: `AgentsStrip` props as above; `formatAge(ms: number): string` keeps its signature wherever it lands.

## Expected outcome

The agent detail the ribbon used to show sits in the chat header, and filtering by agent works from the same items.

## Steps

- Write `frontend/src/chat/AgentsStrip.test.tsx` (jsdom; titles as in the AC refs; retirement via `git ls-files src/chat/AgentFilter.tsx src/ribbon/AgentRow.tsx`); run `mise x node@24.20.0 -- npm --prefix frontend test -- src/chat/AgentsStrip.test.tsx`: fails.
- Implement the strip, swap it into ChatView, `git rm` the two files; run the verify command: passes.

## Notes

- `ChatLog.test.tsx`, `Composer.test.tsx` and `chatModel.test.ts` must stay green unchanged: they pin "chat stays as is".
- Retirement tests assert on `git ls-files`, never on the filesystem.
