---
title: web download icon
status: done
repo: agents-web
value: "a right-aligned arrow-down icon on each file row saves the file to the user's computer"
files: [src/api/files.ts, src/api/files.test.ts, src/files/FilesPanel.tsx, src/files/FilesPanel.test.tsx, MEMORY.md]
verify: "mise exec -- npx vitest run src/files/FilesPanel.test.tsx src/api/files.test.ts src/layout/designRules.test.ts src/nomenclature.test.ts && mise exec -- npx tsc -b && mise run lint"
depends_on: [web-sync-orchestrator-api]
model: sonnet
review: ""
verified_head: e7a2499db68fcf04a25f324fed88875c3faea644
points: 3
expected_minutes: 6
expected_tokens: 963314
points_actual: 3
actual_minutes: 4
actual_tokens: 534640
actual_roles: "impl 3, review 1"
actual_role_tokens: "impl 479836, review 54804"
---

# web download icon

## Requirement

User request (2026-10-27), verbatim: "In file browser, I need to be able to download a file. I expect small "arrow down" icon aligned with right side of the file browser, that's going to download a file to my computer from agent's workspace."

Epic README goals, verbatim: "A small download (arrow down) icon on every file row of the Files tree, aligned to the right edge of the file browser." and "Clicking it downloads that file from the agent's workspace to the user's computer, byte-exact, for text and binary files of any size (no 1 MiB preview cap)."

User decision U2, verbatim: "Directories, symlinks to directories and type 'other' show no download icon; symlinks to files download the target bytes only if the existing guard allows it."

User decision U3, verbatim: "The UI triggers the download with a plain anchor to the relative basePath URL (download attribute), no blob buffering; icon FileDownloadOutlined, small IconButton with aria-label 'Download <name>', right-aligned in the tree row, click does not open the preview (stopPropagation); errors (e.g. 404, 403) cannot be read from a plain anchor, so state in design.md how errors surface (my call: plain anchor, browser shows the error page) or choose a fetch+blob path if you judge it necessary and say why."

Design D5, verbatim: "the icon is `IconButton component="a"` with `href` = the relative URL `${base()}/sessions/<id>/files/download?path=<rel>` (new `fileDownloadUrl` in `src/api/files.ts`), the `download` attribute set to the entry name, `size="small"`, `aria-label="Download <name>"`, icon `FileDownloadOutlined` (`fontSize="small"`). It is the last element of the tree row and the name grows, so the icon sits on the right edge. Its click handler calls `stopPropagation`, so the click neither opens the preview nor selects the row. Shown per D3; no icon on `dir`, `other`, or `symlink` rows whose `target_type` is not `file`. No `agent_id`: the same first usable agent the listing uses."

Design D3 (UI part): "agents-web shows the download icon for `type == "file"` and for `type == "symlink"` with `target_type == "file"`."

Scope (agents-web):
- `src/api/files.ts`: `fileDownloadUrl(sessionId: string, path: string): string` built with `base()` and `query({ path })`; the file header comment stays accurate ("read-only" still holds).
- `src/api/files.test.ts` (new): pins the URL.
- `src/files/FilesPanel.tsx`: `Row` gains an optional trailing action; file rows and symlink-to-file rows render the download anchor; the name element grows so the icon sits on the right edge.
- `src/files/FilesPanel.test.tsx`: the new tests below; the hoisted `api` mock of `../api/files` gains `fileDownloadUrl` (the panel now imports it; this extends the mock for the new export, it does not change any existing assertion).
- `MEMORY.md`: a dated entry (2026-10-27, file-download-in-file-browse D5): plain anchor, why not fetch plus blob, how errors surface.

## Acceptance conditions

- ac1: `fileDownloadUrl('c1', 'src/a b.txt')` is the relative `${base()}/sessions/c1/files/download?path=src%2Fa+b.txt` under the runtime config's basePath (new) [evidence: command:mise exec -- npx vitest run src/api/files.test.ts -t 'fileDownloadUrl']
- ac2: every `file` row and every `symlink` row with `target_type` `file` has a link named `Download <name>` whose `href` is `fileDownloadUrl(sessionId, path)` and whose `download` attribute is the name, with the FileDownloadOutlined icon; `dir`, `other` and `symlink` rows with `target_type` `dir`, `other` or null have none (new) [evidence: command:mise exec -- npx vitest run src/files/FilesPanel.test.tsx -t 'download_icon_only_on_file_rows']
- ac3: clicking the download link neither calls `readFile`, opens a preview nor selects the row (new) [evidence: command:mise exec -- npx vitest run src/files/FilesPanel.test.tsx -t 'download_click_does_not_open_preview']
- ac4: the download link is the last element of its row and the row's name element grows (`flex-grow: 1`), so the icon sits at the right edge (new) [evidence: command:mise exec -- npx vitest run src/files/FilesPanel.test.tsx -t 'download_icon_right_aligned']
- ac5: the design rules and nomenclature guards hold for the changed files [evidence: command:mise exec -- npx vitest run src/layout/designRules.test.ts src/nomenclature.test.ts]
- ac6: the Files panel and files API suites, the type check and lint pass [evidence: command:mise exec -- npx vitest run src/files/FilesPanel.test.tsx src/api/files.test.ts && mise exec -- npx tsc -b && mise run lint]

## Files

- `src/api/files.ts`
- `src/api/files.test.ts`
- `src/files/FilesPanel.tsx`
- `src/files/FilesPanel.test.tsx`
- `MEMORY.md`

## Interfaces

- `src/api/files.ts:fileDownloadUrl(sessionId: string, path: string): string`, built with `base()` and `query({ path })`.
- `src/files/FilesPanel.tsx:Row` gains an optional trailing action; the download anchor is `IconButton component="a" href download size="small" aria-label="Download <name>"` with `FileDownloadOutlined fontSize="small"`.
- Kept: `listFiles`, `readFile`, preview behaviour, polling and event refresh unchanged.

## Expected outcome

Each file row (and each symlink-to-file row) of the Files tree shows a small arrow-down icon at its right edge; clicking it saves the file through the browser's download, without opening the preview.

## Steps

- Red: write `src/api/files.test.ts` and the three FilesPanel tests (`download_icon_only_on_file_rows`, `download_click_does_not_open_preview`, `download_icon_right_aligned`), add `fileDownloadUrl` to the hoisted `api` mock; run `mise exec -- npx vitest run src/files/FilesPanel.test.tsx src/api/files.test.ts`: the new tests fail.
- Green: `fileDownloadUrl`, the `Row` action and the anchor; rerun: passes.
- MEMORY.md entry; run the task's verify: passes, quote the vitest summary line.

## Notes

- Rulings and their pin tests: icon rows (file, symlink with `target_type` file) versus no-icon rows (dir, other, symlink with `target_type` dir, other or null), pinned by `download_icon_only_on_file_rows`; click isolation, pinned by `download_click_does_not_open_preview`; right alignment, pinned by `download_icon_right_aligned`.
- Extending the hoisted `api` mock with `fileDownloadUrl` is required because the panel imports it; no existing assertion changes.
- designRules forbid `title=` on IconButton (use aria-label) and off-grid spacing; `getComputedStyle` works with emotion in jsdom (precedent `src/layout/TopBar.test.tsx:120`). The stopPropagation precedent is `src/terminal/TerminalPanel.tsx:146-149`.
- MEMORY.md entry (2026-10-27, file-download-in-file-browse D5): plain anchor, why not fetch plus blob (buffers the whole file), errors surface in the browser, not the panel.
- The full suite has 10 load-dependent timeouts in unrelated files (PresetForm, ScheduleForm, Endpoints, FiltersEditor); run only the files in `verify`.

- 2026-10-27 done
