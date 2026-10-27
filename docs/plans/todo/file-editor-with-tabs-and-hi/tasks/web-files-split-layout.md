---
title: web files split layout
status: todo
repo: agents-web
value: "the Files panel shows the tree on the left and the open files on the right, refreshed without losing edits"
files: [src/files/FilesPanel.tsx, src/files/FilesPanel.test.tsx, src/layout/Workspace.tsx, MEMORY.md]
verify: "mise exec -- npx vitest run src/files/FilesPanel.test.tsx src/files/FileTabs.test.tsx src/files/useFileTabs.test.ts src/layout/Workspace.test.tsx src/layout/designRules.test.ts src/nomenclature.test.ts && mise exec -- npx tsc -b && mise run lint"
depends_on: [web-file-tabs-view, web-file-tabs-state, web-sync-write-api]
model: sonnet
review: ""
verified_head: ""
points: 5
expected_minutes: 11
expected_tokens: 1858483
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# web files split layout

## Requirement

User request (2026-10-27), verbatim: "* inside "Files" in RW editor mode- support python/yaml/json/terraform/toml syntax highlighting and syntax- no hints for now
* file tree always visible on the left
* multiple files can be opened- similar design to tabs in terminal"

Epic README goal, verbatim: "Files panel: file tree always visible on the left, editor area on the right."

User decision U5 (layout part), verbatim: "(my call) Layout: tree always visible on the left, editor area on the right inside the Files panel (a resizable split), the phone layout stacks or keeps the tree reachable"

User decision U6, verbatim: "(my call) Live refresh: an open RO tab refetches when the tree reports a changed mtime|size (existing behaviour); a dirty RW tab never auto-reloads, it shows a 'changed on disk' notice instead."

Design D13, verbatim: "`FilesPanel` renders a `react-resizable-panels` `Group` inside its slot: on tablet and desktop (`useLayout` not `phone`) horizontal, tree panel first (left, default 30 percent), editor area right (70 percent); on a phone vertical, tree above (40 percent) and editor below (60 percent), both always rendered so the tree stays reachable (my call). The separator reuses the Workspace divider style with its inline `flexBasis` (MEMORY 2026-10-24); sizes are not persisted (my call). The tree keeps its header, errors, polling, events and the download icon of the download epic; its selection follows the active tab. The single `Preview` state, `PreviewBody` and the `<pre>` preview are removed; the header comment stops saying read-only preview."

Design D14 (panel part), verbatim: "for each open tab the panel feeds the hook the `mtime|size` stamp of its entry in the loaded tree listings. [...] An agent write event for the path (`fileEvents` `written`) applies the same rule."

Scope (agents-web):
- `src/files/FilesPanel.tsx`: the split (`data-testid="files-split"` with `data-orientation` `horizontal` or `vertical`), the tree in the first panel, `FileTabs` (web-file-tabs-view) over `useFileTabs(sessionId)` (web-file-tabs-state) in the second, an empty-state note `Open a file from the tree` when no tab is open; tree clicks on `file` and `symlink` open a tab, on `other` an `other` tab; `selectedItems` follows the active tab; the stamp lookup of D14 fed to `observe` on every tree change; `written` routed to the hook; `Preview`, `PreviewBody`, `openFile` and the preview refetch effect removed; header comment updated.
- `src/layout/Workspace.tsx`: export the existing `Divider` and `DIVIDER_WIDTH` for reuse (no behaviour change).
- `src/files/FilesPanel.test.tsx`: the new tests below; `../editor/CodeEditor` replaced by the same stand-in as in `FileTabs.test.tsx` (real `CodeEditorProps`, renders `doc` in `data-testid="file-editor"`); the hoisted `api` mock of `../api/files` gains `writeFile` (the panel now imports it through the hook; no existing assertion changes for it); `../layout/useLayout` mocked to choose the layout class. Three existing tests are no longer accurate and are rewritten, each for the reason given: `preview_kinds` asserts the text preview is a `<pre data-testid="file-preview-text">` and that opening another file removes it (one preview at a time), while text now opens in the editor and earlier tabs stay mounted: it becomes `tab_kinds` (text in `file-editor`, binary and too_large notes, all three tabs open); `symlink_previews_and_escape_error` reads `file-preview-text` and asserts it is gone after opening `escape`, while the link's tab now stays open beside the error tab: it asserts the link tab's `file-editor` text and the `escape` tab's `file-preview-error`; `preview_dropped_on_session_change` reads `file-preview-text`, while tabs now live per session: it asserts session c2 shows no tab of c1 and that returning to c1 shows its tab again. Every other existing test, including `preview refetch when the entry mtime or size changes`, `other_entries_type_only` and the download-icon tests of the download epic, passes unchanged.
- `MEMORY.md`: a dated entry (2026-10-27, file-editor-with-tabs-and-hi D13, D14): the split inside the Files panel, the phone stacking, why clean RW tabs refetch and dirty ones show a notice.

## Acceptance conditions

- ac1: on desktop and tablet the Files panel is a horizontal split with the tree in the first (left) panel and the tab area in the second; the tree stays rendered while tabs are open; the separator has an inline `flex-basis` (new) [evidence: command:mise exec -- npx vitest run src/files/FilesPanel.test.tsx -t 'tree left editor right']
- ac2: on a phone the split is vertical with the tree above the tab area, both rendered (new) [evidence: command:mise exec -- npx vitest run src/files/FilesPanel.test.tsx -t 'phone stacks']
- ac3: clicking two files opens two tabs and the tree selection follows the active tab; clicking an open file focuses its tab without another `readFile`; with no tab open the area shows `Open a file from the tree` (new) [evidence: command:mise exec -- npx vitest run src/files/FilesPanel.test.tsx -t 'tree opens tabs']
- ac4: a changed `mtime|size` in the polled listing refetches an RO tab, while a dirty RW tab is not refetched and shows the "changed on disk" notice (new) [evidence: command:mise exec -- npx vitest run src/files/FilesPanel.test.tsx -t 'live refresh keeps edits']
- ac5: a finished Write tool event on an open file refetches its clean tab and marks a dirty one changed on disk (new) [evidence: command:mise exec -- npx vitest run src/files/FilesPanel.test.tsx -t 'written event refresh']
- ac6: text, binary and too_large files each open their own tab with the editor or today's note (rewritten from `preview_kinds`, which assumed one `<pre>` preview at a time) [evidence: command:mise exec -- npx vitest run src/files/FilesPanel.test.tsx -t 'tab_kinds']
- ac7: a symlink to a file opens in the editor and an escaping link shows its error in its own tab (rewritten, it assumed one preview) [evidence: command:mise exec -- npx vitest run src/files/FilesPanel.test.tsx -t 'symlink_previews_and_escape_error']
- ac8: a session change shows none of the old session's tabs and returning restores them (rewritten, it read the removed `<pre>` preview) [evidence: command:mise exec -- npx vitest run src/files/FilesPanel.test.tsx -t 'preview_dropped_on_session_change']
- ac9: the whole Files panel suite passes, every other existing test unchanged [evidence: command:mise exec -- npx vitest run src/files/FilesPanel.test.tsx]
- ac10: the panel no longer carries the single preview and its header no longer says read-only [evidence: command:! grep -qE 'PreviewBody|read-only file preview|file-preview-text' src/files/FilesPanel.tsx]
- ac11: MEMORY.md records the layout and refresh rulings [evidence: command:grep -q 'file-editor-with-tabs-and-hi D13' MEMORY.md && grep -qi 'changed on disk' MEMORY.md]
- ac12: the targeted suites, the guards, the type check and lint pass [evidence: command:mise exec -- npx vitest run src/files/FilesPanel.test.tsx src/files/FileTabs.test.tsx src/files/useFileTabs.test.ts src/layout/Workspace.test.tsx src/layout/designRules.test.ts src/nomenclature.test.ts && mise exec -- npx tsc -b && mise run lint]

## Files

- `src/files/FilesPanel.tsx`
- `src/files/FilesPanel.test.tsx`
- `src/layout/Workspace.tsx`
- `MEMORY.md`

## Interfaces

- `src/files/FilesPanel.tsx:FilesPanel({ sessionId })` unchanged signature; renders `data-testid="files-split"` (`data-orientation` `horizontal` or `vertical`) with the tree panel first and `FileTabs` second.
- `src/layout/Workspace.tsx`: `export { Divider, DIVIDER_WIDTH }` (no behaviour change).
- Uses `useFileTabs` (web-file-tabs-state), `FileTabs` (web-file-tabs-view), `useLayout` (src/layout/useLayout.ts), `useFileTree`, `createFileEvents`, and the download epic's `Row` trailing action.

## Expected outcome

The Files panel shows the tree on the left (above on a phone) and the open files on the right as tabs; a file click opens or focuses its tab; live refresh updates clean tabs and never overwrites unsaved edits; the single preview is gone.

## Steps

- Red: add the five new tests and rewrite the three named tests in `src/files/FilesPanel.test.tsx` (CodeEditor stand-in, `writeFile` in the hoisted mock, `useLayout` mocked); run `mise exec -- npx vitest run src/files/FilesPanel.test.tsx`: the new and rewritten tests fail.
- Green: the split, the hook and `FileTabs` wiring, the stamp lookup and `written` routing, the preview removal, the `Divider` export; rerun: passes.
- MEMORY.md entry; run the task's verify: passes, quote the vitest summary line.

## Notes

- Tests no longer accurate, and why (the requirement's list): `preview_kinds` (one `<pre>` preview at a time), `symlink_previews_and_escape_error` (one preview), `preview_dropped_on_session_change` (reads the removed `<pre>`, and tabs now live per session). Every other test passes unchanged; if another one fails, report it rather than editing it.
- The stand-in renders `doc` as text inside `data-testid="file-editor"`, so `screen.findByText('v1')` in `preview refetch when the entry mtime or size changes` and `event_driven_refresh a written file open in the preview is refetched on the result` keeps working unchanged.
- The stamp lookup returns `<mtime>|<size>` of the entry in `state.dirs[<parent>]`, or null when the entry is not listed: the same expression the removed preview effect used (FilesPanel.tsx:153-167).
- react-resizable-panels: a `Separator` needs an inline `style={{ flexBasis }}` (MEMORY 2026-10-24); nested `Group`s inside a Workspace `Panel` are supported.
- jsdom has no media queries: mock `../layout/useLayout` per test (`'desktop'`, `'phone'`).
- Workspace sizes (25/45/30) stay as they are (design Non-goals).
