---
title: fe filesystem panel
status: todo
repo: agent-orchestrator
value: the user sees what agents changed on disk as a live tree with file previews
files: [frontend/src/api/files.ts, frontend/src/files/useFileTree.ts, frontend/src/files/fileEvents.ts, frontend/src/files/FilesPanel.tsx, frontend/src/files/FilesPanel.test.tsx, frontend/src/App.tsx]
verify: "mise x node@24.20.0 -- npm --prefix frontend ci && mise x node@24.20.0 -- npm --prefix frontend test -- src/files src/App.test.tsx src/layout/designRules.test.ts && mise x node@24.20.0 -- npm --prefix frontend run lint && mise x node@24.20.0 -- npm --prefix frontend run build"
depends_on: [fe-panel-workspace, file-proxy-routes]
owns: []
uses: [orch-files-api, fe-workspace-slots, fe-deps]
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

# fe filesystem panel

## Requirement

The filesystem panel (design D8; user Q8, Q9, Q10), test-first.

- New `frontend/src/api/files.ts`: `listFiles(clusterId, path, offset?)` and `readFile(clusterId, path)` over `request` with the generated `FileListing`/`FileContent` types.
- New `frontend/src/files/useFileTree.ts`: per-cluster cache of loaded directories keyed by relative path; `expand(path)` loads a directory lazily on first expand; a truncated directory (`next_offset` not null) shows a "more" row that loads the next page and appends; `refresh(path)` re-fetches one directory; `refreshExpanded()` re-fetches every expanded directory.
- New `frontend/src/files/fileEvents.ts`: maps cluster events to refreshes: `tool_call` with name `Write`, `Edit` or `NotebookEdit` and `tool_input.file_path` inside the listing `root` refreshes the parent directory if it is loaded; a `tool_result` of `Bash` triggers `refreshExpanded()`, debounced to at most once per second. The panel subscribes with `openStream` on the cluster event stream URL for `tool_call` and `tool_result` from the live tail (no history replay) and closes it on unmount or cluster change.
- New `frontend/src/files/FilesPanel.tsx`: MUI X `SimpleTreeView` (MIT) rendering everything the API lists (dotfiles and `.git` included), folders and files with `@mui/icons-material` icons, a refresh button for the whole tree, and a read-only preview below or beside the tree: `text` shown in a monospace block, `binary` shown as size and mime type, `too_large` shown as size and "too large to preview"; errors shown inline (for example `agent_not_ready` while the cluster starts).
- `frontend/src/App.tsx` passes `FilesPanel` into the workspace `files` slot.

## Acceptance conditions

- AC1: the root loads on mount and a folder's children load only on first expand [evidence: test:frontend/src/files/FilesPanel.test.tsx::lazy_load_on_expand]
- AC2: a truncated directory shows a more row that loads the next page [evidence: test:frontend/src/files/FilesPanel.test.tsx::more_row_pages]
- AC3: clicking a file previews text, binary and too-large files as specified [evidence: test:frontend/src/files/FilesPanel.test.tsx::preview_kinds]
- AC4: a Write or Edit tool_call refreshes the loaded parent directory and a Bash tool_result refreshes expanded directories, debounced [evidence: test:frontend/src/files/FilesPanel.test.tsx::event_driven_refresh]
- AC5: the refresh button re-fetches the tree and errors render inline [evidence: test:frontend/src/files/FilesPanel.test.tsx::manual_refresh_and_errors]
- AC6: tests, design rules, lint and build pass [evidence: command:mise x node@24.20.0 -- npm --prefix frontend ci && mise x node@24.20.0 -- npm --prefix frontend test -- src/files src/App.test.tsx src/layout/designRules.test.ts && mise x node@24.20.0 -- npm --prefix frontend run lint && mise x node@24.20.0 -- npm --prefix frontend run build]

## Files

- `frontend/src/api/files.ts`
- `frontend/src/files/useFileTree.ts`
- `frontend/src/files/fileEvents.ts`
- `frontend/src/files/FilesPanel.tsx`
- `frontend/src/files/FilesPanel.test.tsx`
- `frontend/src/App.tsx`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
