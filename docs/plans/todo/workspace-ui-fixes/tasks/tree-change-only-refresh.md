---
title: tree change only refresh
status: todo
repo: agent-orchestrator
value: tree state can refresh safely and catches new directories and notebooks
files: [frontend/src/files/useFileTree.ts, frontend/src/files/fileEvents.ts, frontend/src/files/FilesPanel.test.tsx]
verify: "cd frontend && npx vitest run src/files/FilesPanel.test.tsx && npm run lint"
depends_on: []
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

# tree change only refresh

## Requirement

Make the tree state layer ready for automatic refresh, in frontend/src/files/useFileTree.ts and frontend/src/files/fileEvents.ts.
1. useFileTree: a refresh of a path commits the new listing only when it differs from the cached one (compare name, type, size, mtime per entry, plus total/next offset), so an idle refresh causes no state change and no re-render. Expose a `pollExpanded()` (root plus every expanded directory) that skips any directory whose load is in flight (a refresh bumps the per-path seq and would swallow a pending "Load more") and that also retries the root when it is in an error or missing state (409 agent_not_ready, 404 missing workdir).
2. fileEvents: a Write/Edit/NotebookEdit result refreshes the nearest loaded ancestor of the written path (a write into a new directory makes the new directory appear), and the path is read from `tool_input.file_path` or `tool_input.notebook_path`.
Keep the Bash-result throttled refresh as is.

## Acceptance conditions

- AC1: a refresh that returns an identical listing does not change tree state or re-render [evidence: command:cd frontend && npx vitest run src/files/FilesPanel.test.tsx -t "unchanged listing"]
- AC2: pollExpanded skips a directory whose load is in flight and retries a root that is in error or missing state [evidence: command:cd frontend && npx vitest run src/files/FilesPanel.test.tsx -t "pollExpanded"]
- AC3: a Write into a new directory refreshes the nearest loaded ancestor so the directory appears [evidence: command:cd frontend && npx vitest run src/files/FilesPanel.test.tsx -t "new directory"]
- AC4: a NotebookEdit with tool_input.notebook_path refreshes its parent directory [evidence: command:cd frontend && npx vitest run src/files/FilesPanel.test.tsx -t "notebook_path"]

## Files

- `frontend/src/files/useFileTree.ts`
- `frontend/src/files/fileEvents.ts`
- `frontend/src/files/FilesPanel.test.tsx`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

Identical listings cause no render; new-dir and notebook writes refresh the right directory.

## Steps

- Red: add tests named in the ACs to FilesPanel.test.tsx and see them fail.
- Green: change-only commit and pollExpanded in useFileTree, ancestor and notebook_path in fileEvents; run the verify command.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.

- Entries carry name, type, size, mtime (api/schema.d.ts). `load(path, 'refresh')` in useFileTree.ts is where to compare before `patchDir`. In-flight = `dirs[path].loading`. Root retry condition: `dirs[''].error` set or `missing` true. In fileEvents.ts the write path comes from the tool_call input (`tool_input` or `input`); extend to `notebook_path`. Nearest loaded ancestor: walk up from the parent via `isLoaded` until one is loaded (my call: stop at root '').
