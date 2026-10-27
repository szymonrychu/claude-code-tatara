---
title: web file tabs view
status: done
repo: agents-web
value: "open files show as terminal-style tabs with an RO/RW toggle, Save and conflict notices"
files: [src/files/FileTabs.tsx, src/files/FileTabs.test.tsx, MEMORY.md]
verify: "mise exec -- npx vitest run src/files/FileTabs.test.tsx src/layout/designRules.test.ts && mise exec -- npx tsc -b && mise run lint"
depends_on: [web-file-tabs-state, web-code-editor]
model: opus
review: ""
verified_head: 618d5dae343d4deb88a08351f660e49d38ba62ab
points: 5
expected_minutes: 11
expected_tokens: 1858483
points_actual: 5
actual_minutes: 7
actual_tokens: 1828146
actual_roles: "impl 6, review 1"
actual_role_tokens: "impl 1726090, review 102056"
---

# web file tabs view

## Requirement

User request (2026-10-27), verbatim: "multiple files can be opened- similar design to tabs in terminal"

Epic README goals, verbatim: "Multiple files open at once as tabs, styled like the terminal tabs (closable, scrollable)." and "RO/RW editor mode: read-only by default, RW lets the user edit and save the file back to the agent's workspace (new write route in claude-code-wrapper and orchestrator)."

User decision U3, verbatim: "(my call) 'RW editor mode': read-only by default with an RO/RW toggle per tab; RW enables editing and Save (button and Ctrl/Cmd+S); new write route in the wrapper (PUT file content, UTF-8 text only, size cap = the existing file_preview_max_bytes, existing workspace path guards, optimistic concurrency via the mtime/size the editor loaded: a changed file answers 409 and the UI offers reload or overwrite) and an orchestrator forwarding route, then `npm run sync:api -- orchestrator`. Binary and too_large files open read-only with the current note, no editor."

User decision U5 (tabs part), verbatim: "tabs mirror TerminalPanel (MUI Tabs scrollable, closable tab with IconButton aria-label 'Close <name>', closing picks the neighbour, all tabs stay mounted), one tab per path (re-opening focuses it), unsaved changes mark the tab and closing a dirty tab asks to confirm."

User decision U6, verbatim: "(my call) Live refresh: an open RO tab refetches when the tree reports a changed mtime|size (existing behaviour); a dirty RW tab never auto-reloads, it shows a 'changed on disk' notice instead."

Design D12 (view part), verbatim: "`src/files/FileTabs.tsx` renders them like `TerminalPanel`: MUI `Tabs` `variant="scrollable" scrollButtons="auto"`, a `Tab component="div"` per file whose label is the name plus a small `IconButton component="span"` with `aria-label="Close <name>"` (`stopPropagation`), every panel mounted (`position: absolute; inset: 0`, inactive `display: none` and `hidden`). A dirty tab's label ends with ` *` and carries `data-dirty="true"` (my call: plain ASCII, designRules). Closing a dirty tab opens the existing `ConfirmDialog` ("Discard unsaved changes to <name>?", confirm "Discard"). Each text panel has a toolbar: the full relative path, an RO/RW `ToggleButtonGroup` (aria-label "Editor mode"), and a Save button enabled only in RW with unsaved changes and no save running; Ctrl/Cmd+S in the editor saves under the same condition. Binary, too_large and other tabs show today's notes (`file-preview-note`), errors `file-preview-error`; they have no editor, toggle or Save."

Design D11 (lazy part), verbatim: "The panel loads the component with `React.lazy`, so CodeMirror is its own build chunk and the main bundle does not grow (my call)."

Scope (agents-web):
- `src/files/FileTabs.tsx` (new): `FileTabs({ tabs })` taking the `useFileTabs` result (web-file-tabs-state); `CodeEditor` (web-code-editor) through `React.lazy(() => import('../editor/CodeEditor'))` inside a `Suspense` with a `loading` note; the conflict notice (role `alert`, "changed on disk", Reload and Overwrite) and the changed-on-disk notice of a dirty tab (role `alert`, "changed on disk", Reload and Keep editing); the save error inline (role `alert`); the notes and error texts of today's `PreviewBody` (`Binary file, <size> bytes, <mime>`, `<size> bytes, too large to preview`, `Type: other. No preview.`).
- `src/files/FileTabs.test.tsx` (new, jsdom): the tests below, with `../editor/CodeEditor` replaced by a stand-in default export that takes the real `CodeEditorProps`, renders `doc` in a `data-testid="file-editor"` element with `data-readonly`, and exposes buttons that call `onChange` and `onSave`.
- `MEMORY.md`: a dated entry (2026-10-27, file-editor-with-tabs-and-hi D11, D12): the lazy editor chunk with the `npm run build` sizes of the main and editor chunks, RO refused while dirty, the per-session in-memory tab store.

## Acceptance conditions

- ac1: the tab strip is an MUI `Tabs` with scroll buttons; each tab shows the file name and a `Close <name>` button; clicking a tab activates it; every tab panel stays mounted and only the active one is visible (others `hidden`) (new) [evidence: command:mise exec -- npx vitest run src/files/FileTabs.test.tsx -t 'terminal style tabs']
- ac2: closing a clean tab calls `close` at once; closing a dirty tab opens the dialog "Discard unsaved changes to <name>?", Cancel keeps the tab and Discard closes it; the close click does not activate the tab (new) [evidence: command:mise exec -- npx vitest run src/files/FileTabs.test.tsx -t 'dirty close confirms']
- ac3: a dirty tab's label ends with ` *` and has `data-dirty="true"`; a clean one has neither (new) [evidence: command:mise exec -- npx vitest run src/files/FileTabs.test.tsx -t 'dirty mark']
- ac4: a text tab shows its full relative path, the "Editor mode" toggle with RO selected and the editor read-only; choosing RW calls `setMode(path, 'rw')`; RO is disabled while the tab is dirty; Save is disabled in RO, in RW without changes and while saving, and calls `save` in RW with changes (new) [evidence: command:mise exec -- npx vitest run src/files/FileTabs.test.tsx -t 'mode toggle and save button']
- ac5: the editor's `onSave` (Ctrl/Cmd+S) calls `save` only in RW with unsaved changes and not while saving (new) [evidence: command:mise exec -- npx vitest run src/files/FileTabs.test.tsx -t 'keyboard save']
- ac6: a tab in `conflict` shows an alert containing "changed on disk" with Reload and Overwrite calling `reload` and `overwrite`; a dirty tab with `changedOnDisk` shows an alert containing "changed on disk" with Reload and Keep editing; a save error shows as an alert with its text (new) [evidence: command:mise exec -- npx vitest run src/files/FileTabs.test.tsx -t 'notices']
- ac7: binary, too_large and other tabs show today's notes in `file-preview-note` and an error tab its text in `file-preview-error`, with no editor, no mode toggle and no Save (new) [evidence: command:mise exec -- npx vitest run src/files/FileTabs.test.tsx -t 'non-text tabs']
- ac8: the production build emits the editor as its own chunk [evidence: command:mise exec -- npm run build 2>&1 | grep -qE 'assets/CodeEditor-[^ ]+\.js']
- ac9: MEMORY.md records the lazy chunk sizes and the tab rulings [evidence: command:grep -q 'CodeEditor' MEMORY.md && grep -qi 'chunk' MEMORY.md]
- ac10: the design rules hold for the new file [evidence: command:mise exec -- npx vitest run src/layout/designRules.test.ts]
- ac11: the targeted suites, the type check and lint pass [evidence: command:mise exec -- npx vitest run src/files/FileTabs.test.tsx src/layout/designRules.test.ts && mise exec -- npx tsc -b && mise run lint]

## Files

- `src/files/FileTabs.tsx`
- `src/files/FileTabs.test.tsx`
- `MEMORY.md`

## Interfaces

- `src/files/FileTabs.tsx`: `export function FileTabs({ tabs }: { tabs: FileTabs }): JSX.Element` (the `useFileTabs` result type); `const CodeEditor = lazy(() => import('../editor/CodeEditor'))`.
- Test ids kept from today's preview: `file-preview-note`, `file-preview-error`; new: `file-editor` (inside `CodeEditor`), `file-tab-path` (the toolbar path).
- Uses `ConfirmDialog` (src/layout/ConfirmDialog.tsx), `TOKENS`, `MONO_FONT` (src/theme.ts).
- Consumed by web-files-split-layout.

## Expected outcome

Open files show as terminal-style tabs: closable, scrollable, all mounted, dirty ones marked and confirmed on close; text tabs have the path, the RO/RW toggle, Save and the editor; conflicts and changes on disk show as notices with their actions; the editor loads as its own chunk.

## Steps

- Red: write `src/files/FileTabs.test.tsx` (seven behaviour tests, `CodeEditor` stand-in via `vi.mock('../editor/CodeEditor', ...)`, the `FileTabs` api as `vi.fn()`s over fixture tabs); run `mise exec -- npx vitest run src/files/FileTabs.test.tsx`: fails (no module).
- Green: `FileTabs.tsx`; rerun: passes.
- Run `mise exec -- npm run build` and read the chunk sizes; MEMORY.md entry; run the task's verify: passes, quote the vitest summary line.

## Notes

- Mirror `src/terminal/TerminalPanel.tsx:132-203` for the strip and the mounted panels; the close button's `stopPropagation` precedent is `TerminalPanel.tsx:146-149`.
- The stand-in in the test must take the real `CodeEditorProps` (import the type) so it cannot drift from the component (retro: fakes encoding a wrong assumption).
- Rulings and their pin tests: ` *` and `data-dirty` mark, pinned by `dirty mark`; Save and Ctrl/Cmd+S only in RW with changes and not while saving, pinned by `mode toggle and save button` and `keyboard save`; Reload and Overwrite on a conflict, Reload and Keep editing on a change on disk, pinned by `notices`.
- designRules: `aria-label` on IconButtons (never `title=`), no decorative Unicode (the dirty mark is an ASCII `*`), spacing on the 0.5 grid, colours from theme palette paths.
- The ToggleButtonGroup's RO button is disabled while dirty (the hook refuses it too).

- 2026-10-27 done: ac8 (editor chunk) moved to web-files-split-layout ac13 by orchestrator ruling
