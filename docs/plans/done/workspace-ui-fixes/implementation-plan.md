# workspace ui fixes implementation plan

## Agreed rung

Rung 1 of plan.md, migrated from the epic format: the steps are the epic's tasks.

## Approach

Migrated from the epic format: one step per task file, in dependency order, each with its status, files, verify, verified head and every body section.

## Chunk 1: migrated tasks (model: sonnet)

### S1: pane divider lines

- Status: done
- Files: `frontend/src/layout/Workspace.tsx`, `frontend/src/layout/Workspace.test.tsx`
- Verify: `cd frontend && npx vitest run src/layout/Workspace.test.tsx src/layout/designRules.test.ts && npm run lint`
- Verified head: f2b25e81b32c67ea6c32d03ca5b322d5c6f7fe98

#### Requirement

The separators between the files, chat and terminal panes in frontend/src/layout/Workspace.tsx render as visible vertical lines. Root cause: react-resizable-panels 4.14.8 Separator writes an inline style `flex-basis: auto` (styleDefaults) that beats the emotion `flex: 0 0 4px` shorthand, so the div is 0px wide. Fix by giving the Divider an explicit size the inline style cannot override (pass `style={{ flexBasis: ... }}` on the Separator, since props.style is spread after styleDefaults, and/or width in the styled rule), coloured from theme tokens only (TOKENS.borderStrong, not a colour literal), keeping hover/active/focus primary colour, drag, double-click reset and keyboard resize working. Applies to both separators, including next to the minimized strip. Phone layout is unchanged.

#### Acceptance conditions

- AC1: each of the two separators has an inline flex-basis that is a pixel size, not auto [evidence: command:cd frontend && npx vitest run src/layout/Workspace.test.tsx -t "divider"]
- AC2: existing Workspace layout, double-click reset and keyboard resize tests still pass, and the design rules test passes [evidence: command:cd frontend && npx vitest run src/layout/Workspace.test.tsx src/layout/designRules.test.ts]
- AC3: the dividers are visibly drawn in the real browser (user smoke after deploy) [evidence: judgement:]

#### Files

- `frontend/src/layout/Workspace.tsx`
- `frontend/src/layout/Workspace.test.tsx`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

Both separators render as visible lines of the intended pixel width.

#### Steps

- Red: add a divider test asserting each separator inline flex-basis is a px size; run it and see it fail on 'auto'.
- Green: size the Divider, colour from TOKENS.borderStrong; run the verify command.

#### Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.

- Divider is `styled(Separator)` in Workspace.tsx (flex `0 0 spacing(0.5)`, background `palette.divider`); TOKENS from '../theme' is already imported. Size: 2px line (my call), pass `style={{ flexBasis: 2 }}` (px) on both `<Divider>` uses, background `TOKENS.borderStrong`, hover/active/focus keep primary.

### S2: tree change only refresh

- Status: done
- Files: `frontend/src/files/useFileTree.ts`, `frontend/src/files/fileEvents.ts`, `frontend/src/files/FilesPanel.test.tsx`
- Verify: `cd frontend && npx vitest run src/files/FilesPanel.test.tsx && npm run lint`
- Verified head: e4a80eb32b3ee13487ab41bec896ec97412cbfa5

#### Requirement

Make the tree state layer ready for automatic refresh, in frontend/src/files/useFileTree.ts and frontend/src/files/fileEvents.ts.
1. useFileTree: a refresh of a path commits the new listing only when it differs from the cached one (compare name, type, size, mtime per entry, plus total/next offset), so an idle refresh causes no state change and no re-render. Expose a `pollExpanded()` (root plus every expanded directory) that skips any directory whose load is in flight (a refresh bumps the per-path seq and would swallow a pending "Load more") and that also retries the root when it is in an error or missing state (409 agent_not_ready, 404 missing workdir).
2. fileEvents: a Write/Edit/NotebookEdit result refreshes the nearest loaded ancestor of the written path (a write into a new directory makes the new directory appear), and the path is read from `tool_input.file_path` or `tool_input.notebook_path`.
Keep the Bash-result throttled refresh as is.

#### Acceptance conditions

- AC1: a refresh that returns an identical listing does not change tree state or re-render [evidence: command:cd frontend && npx vitest run src/files/FilesPanel.test.tsx -t "unchanged listing"]
- AC2: pollExpanded skips a directory whose load is in flight and retries a root that is in error or missing state [evidence: command:cd frontend && npx vitest run src/files/FilesPanel.test.tsx -t "pollExpanded"]
- AC3: a Write into a new directory refreshes the nearest loaded ancestor so the directory appears [evidence: command:cd frontend && npx vitest run src/files/FilesPanel.test.tsx -t "new directory"]
- AC4: a NotebookEdit with tool_input.notebook_path refreshes its parent directory [evidence: command:cd frontend && npx vitest run src/files/FilesPanel.test.tsx -t "notebook_path"]

#### Files

- `frontend/src/files/useFileTree.ts`
- `frontend/src/files/fileEvents.ts`
- `frontend/src/files/FilesPanel.test.tsx`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

Identical listings cause no render; new-dir and notebook writes refresh the right directory.

#### Steps

- Red: add tests named in the ACs to FilesPanel.test.tsx and see them fail.
- Green: change-only commit and pollExpanded in useFileTree, ancestor and notebook_path in fileEvents; run the verify command.

#### Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.

- Entries carry name, type, size, mtime (api/schema.d.ts). `load(path, 'refresh')` in useFileTree.ts is where to compare before `patchDir`. In-flight = `dirs[path].loading`. Root retry condition: `dirs[''].error` set or `missing` true. In fileEvents.ts the write path comes from the tool_call input (`tool_input` or `input`); extend to `notebook_path`. Nearest loaded ancestor: walk up from the parent via `isLoaded` until one is loaded (my call: stop at root '').

### S3: files auto poll no button

- Status: done
- Files: `frontend/src/files/FilesPanel.tsx`, `frontend/src/files/FilesPanel.test.tsx`, `MEMORY.md`
- Verify: `cd frontend && npx vitest run src/files/FilesPanel.test.tsx && npm run lint`
- Verified head: 0f99a786e0045e77d491887dac203a2ca6c1a98e

#### Requirement

The file tree updates by itself and the refresh button is gone (user decisions U2, X2; amends prior design D25). In frontend/src/files/FilesPanel.tsx: remove the "Refresh files" IconButton, the Refresh icon import and `onRefresh`. Add a poll that calls the tree's pollExpanded() every 3 seconds while document.visibilityState is 'visible', plus one pass on visibilitychange to visible and on every event stream open (onOpen), so terminal shells, check jobs and any writer outside the agent hooks show up, and an initial 409/missing tree recovers with no button. No timer runs while the tab is hidden or the panel is unmounted. When the open preview's entry mtime or size changes in its parent listing, refetch the preview (replaces the button's preview refetch). Keep the instant stream path. No backend or API change: the tree reads the existing files API (headless parity already holds). Rewrite the FilesPanel tests: retire manual_refresh_and_errors and the no-more-listing-calls-over-5s test, pin the button's absence, and cover poll, hidden tab, visibility return, change-only render, preview refetch and recovery from 409 and missing. Record in code/agent-orchestrator/MEMORY.md (dated 2026-10-24, with why): the react-resizable-panels Separator inline `flex-basis: auto` pitfall, and D25 amended (refresh button removed, visible-tab poll added; no inotify).

#### Acceptance conditions

- AC1: no element labelled "Refresh files" renders, and no Refresh icon import remains [evidence: command:cd frontend && npx vitest run src/files/FilesPanel.test.tsx -t "no refresh button"]
- AC2: a file added on disk with no stream event appears within one poll interval [evidence: command:cd frontend && npx vitest run src/files/FilesPanel.test.tsx -t "polls while visible"]
- AC3: no listing calls are made while the tab is hidden, and one pass runs when it becomes visible [evidence: command:cd frontend && npx vitest run src/files/FilesPanel.test.tsx -t "hidden tab"]
- AC4: a tree that loaded with a 409 or missing root recovers on a later poll without a click [evidence: command:cd frontend && npx vitest run src/files/FilesPanel.test.tsx -t "recovers"]
- AC5: the open preview refetches when its entry mtime or size changes [evidence: command:cd frontend && npx vitest run src/files/FilesPanel.test.tsx -t "preview refetch"]
- AC6: MEMORY.md has the separator pitfall and the amended D25 entry [evidence: command:grep -q "flex-basis" MEMORY.md && grep -q "D25" MEMORY.md]
- AC7: lint, typecheck build and API drift check pass [evidence: command:cd frontend && npm run lint && npm run build && npm run check:api]
- AC8: live tree updates in a real browser, including terminal writes (user smoke after deploy) [evidence: judgement:]

#### Files

- `frontend/src/files/FilesPanel.tsx`
- `frontend/src/files/FilesPanel.test.tsx`
- `MEMORY.md`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

The tree updates by itself with no button; MEMORY.md records the decisions.

#### Steps

- Red: rewrite the FilesPanel tests per the requirement (fake timers, visibility stubs) and see them fail.
- Green: remove the button, add the visible-tab poll and preview mtime refetch, write MEMORY.md; run the verify command, then npm run build and npm run check:api.

#### Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.

- Wire the poll in a FilesPanel effect with setInterval 3000 ms (my call), cleared on unmount and when hidden; `openStream` in src/api/stream.ts already takes `onOpen`. Preview refetch: compare the open file's entry mtime and size in `state.dirs[parent]` against the last seen, then call `openFile`. MEMORY.md is code/agent-orchestrator/MEMORY.md (no D25 entry exists there yet; write it fresh). Retired tests: manual_refresh_and_errors and the 5000 ms advance test in the event_driven_refresh Bash case.

## Files to delete

none recorded in the epic format

## Final verify

none recorded in the epic format

## After merge

none
