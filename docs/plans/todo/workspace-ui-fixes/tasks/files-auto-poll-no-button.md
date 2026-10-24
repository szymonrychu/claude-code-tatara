---
title: files auto poll no button
status: todo
repo: agent-orchestrator
value: the file tree stays current by itself and the refresh button is gone
files: [frontend/src/files/FilesPanel.tsx, frontend/src/files/FilesPanel.test.tsx, MEMORY.md]
verify: "cd frontend && npx vitest run src/files/FilesPanel.test.tsx && npm run lint"
depends_on: [tree-change-only-refresh]
owns: []
uses: []
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

# files auto poll no button

## Requirement

The file tree updates by itself and the refresh button is gone (user decisions U2, X2; amends prior design D25). In frontend/src/files/FilesPanel.tsx: remove the "Refresh files" IconButton, the Refresh icon import and `onRefresh`. Add a poll that calls the tree's pollExpanded() every 3 seconds while document.visibilityState is 'visible', plus one pass on visibilitychange to visible and on every event stream open (onOpen), so terminal shells, check jobs and any writer outside the agent hooks show up, and an initial 409/missing tree recovers with no button. No timer runs while the tab is hidden or the panel is unmounted. When the open preview's entry mtime or size changes in its parent listing, refetch the preview (replaces the button's preview refetch). Keep the instant stream path. No backend or API change: the tree reads the existing files API (headless parity already holds). Rewrite the FilesPanel tests: retire manual_refresh_and_errors and the no-more-listing-calls-over-5s test, pin the button's absence, and cover poll, hidden tab, visibility return, change-only render, preview refetch and recovery from 409 and missing. Record in code/agent-orchestrator/MEMORY.md (dated 2026-10-24, with why): the react-resizable-panels Separator inline `flex-basis: auto` pitfall, and D25 amended (refresh button removed, visible-tab poll added; no inotify).

## Acceptance conditions

- AC1: no element labelled "Refresh files" renders, and no Refresh icon import remains [evidence: command:cd frontend && npx vitest run src/files/FilesPanel.test.tsx -t "no refresh button"]
- AC2: a file added on disk with no stream event appears within one poll interval [evidence: command:cd frontend && npx vitest run src/files/FilesPanel.test.tsx -t "polls while visible"]
- AC3: no listing calls are made while the tab is hidden, and one pass runs when it becomes visible [evidence: command:cd frontend && npx vitest run src/files/FilesPanel.test.tsx -t "hidden tab"]
- AC4: a tree that loaded with a 409 or missing root recovers on a later poll without a click [evidence: command:cd frontend && npx vitest run src/files/FilesPanel.test.tsx -t "recovers"]
- AC5: the open preview refetches when its entry mtime or size changes [evidence: command:cd frontend && npx vitest run src/files/FilesPanel.test.tsx -t "preview refetch"]
- AC6: MEMORY.md has the separator pitfall and the amended D25 entry [evidence: command:grep -q "flex-basis" MEMORY.md && grep -q "D25" MEMORY.md]
- AC7: lint, typecheck build and API drift check pass [evidence: command:cd frontend && npm run lint && npm run build && npm run check:api]
- AC8: live tree updates in a real browser, including terminal writes (user smoke after deploy) [evidence: judgement:]

## Files

- `frontend/src/files/FilesPanel.tsx`
- `frontend/src/files/FilesPanel.test.tsx`
- `MEMORY.md`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

The tree updates by itself with no button; MEMORY.md records the decisions.

## Steps

- Red: rewrite the FilesPanel tests per the requirement (fake timers, visibility stubs) and see them fail.
- Green: remove the button, add the visible-tab poll and preview mtime refetch, write MEMORY.md; run the verify command, then npm run build and npm run check:api.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
