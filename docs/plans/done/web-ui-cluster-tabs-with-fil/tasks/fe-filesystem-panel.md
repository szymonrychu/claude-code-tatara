---
title: fe filesystem panel
status: done
repo: agent-orchestrator
value: the user sees what agents changed on disk as a live tree with file previews
files: [frontend/src/api/files.ts, frontend/src/files/useFileTree.ts, frontend/src/files/fileEvents.ts, frontend/src/files/FilesPanel.tsx, frontend/src/files/FilesPanel.test.tsx, frontend/src/App.tsx]
verify: "mise x node@24.20.0 -- npm --prefix frontend ci && mise x node@24.20.0 -- npm --prefix frontend test -- src/files src/App.test.tsx src/layout/designRules.test.ts && mise x node@24.20.0 -- npm --prefix frontend run lint && mise x node@24.20.0 -- npm --prefix frontend run build"
depends_on: [fe-panel-workspace, file-proxy-routes]
model: ""
review: ""
verified_head: 4ce96dff654c4486a84d50f0b9f344500cf53aac
points: 1
expected_minutes: 6
expected_tokens: 750000
points_actual: ""
actual_minutes: 10
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
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

- AC1: the root loads on mount and a folder's children load only on first expand [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/files/FilesPanel.test.tsx -t lazy_load_on_expand]
- AC2: a truncated directory shows a more row that loads the next page [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/files/FilesPanel.test.tsx -t more_row_pages]
- AC3: clicking a file previews text, binary and too-large files as specified [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/files/FilesPanel.test.tsx -t preview_kinds]
- AC4: a Write or Edit tool_call refreshes the loaded parent directory and a Bash tool_result refreshes expanded directories, debounced [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/files/FilesPanel.test.tsx -t event_driven_refresh]
- AC5: the refresh button re-fetches the tree and errors render inline [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/files/FilesPanel.test.tsx -t manual_refresh_and_errors]
- AC6: tests, design rules, lint and build pass [evidence: command:mise x node@24.20.0 -- npm --prefix frontend ci && mise x node@24.20.0 -- npm --prefix frontend test -- src/files src/App.test.tsx src/layout/designRules.test.ts && mise x node@24.20.0 -- npm --prefix frontend run lint && mise x node@24.20.0 -- npm --prefix frontend run build]
- AC7: a symlink entry is a leaf that previews through the content route and an escape error shows inline [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/files/FilesPanel.test.tsx -t symlink_previews_and_escape_error]
- AC8: other entry types are leaves showing the type only with no preview [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/files/FilesPanel.test.tsx -t other_entries_type_only]
- AC9: a missing workdir root renders an empty tree with the line workdir not created yet and no error [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/files/FilesPanel.test.tsx -t missing_root_empty_tree]
- AC10: the event stream stays open while the panel is mounted and closes on unmount [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/files/FilesPanel.test.tsx -t event_stream_closes_on_unmount]

## Files

- `frontend/src/api/files.ts`
- `frontend/src/files/useFileTree.ts`
- `frontend/src/files/fileEvents.ts`
- `frontend/src/files/FilesPanel.tsx`
- `frontend/src/files/FilesPanel.test.tsx`
- `frontend/src/App.tsx`

## Interfaces

- Uses `GET /api/v1/clusters/{cluster_id}/files` and `/files/content` (part `orch-files-api`, types from `schema.d.ts`), `openStream` and `eventStreamUrl`, the `files` slot (part `fe-workspace-slots`), `@mui/x-tree-view` and icons (part `fe-deps`).

## Expected outcome

The left panel shows the cluster workdir like the VS Code explorer, stays current as agents write, and previews files read-only.

## Steps

- Write `frontend/src/files/FilesPanel.test.tsx` (jsdom; `vi.mock('../api/files')` and `vi.mock('../api/stream')`, fake timers for the debounce; titles as in the AC refs); run `mise x node@24.20.0 -- npm --prefix frontend test -- src/files/FilesPanel.test.tsx`: fails.
- Implement `api/files.ts`, `useFileTree.ts`, `fileEvents.ts`, `FilesPanel.tsx`, wire the slot; run the verify command: passes.

## Notes

- MUI X tree lazy loading and virtualization are Pro features; load children by hand on expand (`onExpandedItemsChange`) and render a placeholder child so collapsed folders show an expand icon.
- Event data shape: `chatModel.ts` reads tool input as `data.tool_input ?? data.input` and name as `data.name ?? data.tool_name`; reuse the same accessors.
- `file_path` is absolute; map it to the tree with the listing `root` (paths outside `root` are ignored).
- Do not lift or change the private stream in `useClusterChat.ts`; ChatView stays untouched.
- Builder check ruling 8: Symlink entries are leaves that preview through the content route (an escape outside the workdir shows the wrapper error inline); other entries are leaves showing type only, no preview.
- Builder check ruling 9: Only the active cluster tab's Workspace is mounted; switching away unmounts it and terminals reattach with scrollback replay on return. A minimized panel stays mounted, so its event subscription stays live.
- Builder check ruling 11: A missing workdir root (not_found for path "") renders as an empty tree with the line "workdir not created yet", not as an error.

- 2026-10-23 amended: builder check rulings 8,9,11 add acceptance conditions AC7-AC10
