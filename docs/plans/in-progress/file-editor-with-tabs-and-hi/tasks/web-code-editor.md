---
title: web code editor
status: in-progress
repo: agents-web
value: "a read-only-by-default CodeMirror editor that edits, saves on Ctrl/Cmd+S and keeps line endings intact"
files: [src/editor/CodeEditor.tsx, src/editor/CodeEditor.test.tsx]
verify: "mise exec -- npx vitest run src/editor/CodeEditor.test.tsx src/layout/designRules.test.ts && mise exec -- npx tsc -b && mise run lint"
depends_on: [web-editor-languages, web-editor-syntax-check]
model: opus
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

# web code editor

## Requirement

User request (2026-10-27), verbatim: "inside "Files" in RW editor mode- support python/yaml/json/terraform/toml syntax highlighting and syntax- no hints for now"

User decision U2, verbatim: "(my call, pending user approval at the gate) CodeMirror 6 with a thin own hook, packages and versions from web-libs-docs.md (state 6.7.6, view 6.43.15, language, commands, lint, lang-python, lang-yaml, lang-json, legacy-modes toml, codemirror-lang-hcl for terraform, @lezer/highlight, smol-toml, yaml). The nomenclature guard (src/nomenclature.test.ts) is tripped by the transitive dep @marijn/find-cluster-break; the planned fix is adding exactly that package name to the guard's ALLOWED list in its own task with a test proving any other match still fails; this is a gate question for the user, keep the task in the plan."

User decision U3 (editor part), verbatim: "read-only by default with an RO/RW toggle per tab; RW enables editing and Save (button and Ctrl/Cmd+S)"

User decision U4 (hints part), verbatim: "no autocomplete, hover or hints (minimal setup, no autocompletion extension)."

Design D11, verbatim: "`src/editor/CodeEditor.tsx` (default export, so it can be lazy-loaded) creates one `EditorView` in an effect and destroys it on unmount. Props: `path` (language, D9), `doc` and `docVersion` (the editor resets to `doc`, history cleared, whenever `docVersion` changes), `readOnly`, `onChange(text)` (every doc change, full text) and `onSave()` (Mod-s while focused, always `preventDefault`, so the browser's save dialog never opens). Extensions: `lineNumbers`, `highlightSpecialChars`, `history`, `drawSelection`, `keymap` (`defaultKeymap`, `historyKeymap`, Mod-s), the language, `syntaxChecker`, the D9 theme and highlight style; `readOnly` drives one `Compartment` holding `EditorState.readOnly` and `EditorView.editable`, reconfigured in place so doc, selection and undo history survive a toggle (B12-B14). Line endings round-trip byte-exact (my call): `EditorState.lineSeparator` is `"\r\n"` when the loaded text contains `"\r\n"`, else `"\n"`, so an unedited document's `doc.toString()` equals the loaded text for LF, CRLF and mixed files. No line wrapping (code scrolls horizontally) (my call). The panel loads the component with `React.lazy`, so CodeMirror is its own build chunk and the main bundle does not grow (my call)."

Scope (agents-web):
- `src/editor/CodeEditor.tsx` (new): `export interface CodeEditorProps` and `export default function CodeEditor(props)`, built on `languageFor` (src/editor/languages.ts), `editorAppearance` (src/editor/highlight.ts) and `syntaxChecker` (src/editor/syntaxCheck.ts); the root element carries `data-testid="file-editor"`. The lazy import site is task web-file-tabs-view.
- `src/editor/CodeEditor.test.tsx` (new, `// @vitest-environment jsdom`): the tests below, with `Range.prototype.getClientRects` and `getBoundingClientRect` stubbed in the test file, the view reached with `EditorView.findFromDOM`, assertions on `view.state`, never typing into contenteditable.

## Acceptance conditions

- ac1: with `readOnly` true the view has `EditorState.readOnly` true and its `.cm-content` is not `contenteditable="true"`; rerendered with `readOnly` false, the same `EditorView` instance has `readOnly` false and an editable content element, with the same doc, the same selection and the same `undoDepth` as before (new) [evidence: command:mise exec -- npx vitest run src/editor/CodeEditor.test.tsx -t 'read-only toggle keeps the view']
- ac2: the language follows `path`: `main.py` python, `main.tf` the HCL language, `pyproject.toml` the toml stream language, `notes.txt` no language (new) [evidence: command:mise exec -- npx vitest run src/editor/CodeEditor.test.tsx -t 'language by path']
- ac3: `view.state.doc.toString()` equals the loaded text byte for byte for an LF file, a CRLF file, a mixed LF/CRLF file, a file without a trailing newline and a file starting with a byte-order mark; after one dispatched insertion in a CRLF file, the text passed to `onChange` still has CRLF on every other line (new) [evidence: command:mise exec -- npx vitest run src/editor/CodeEditor.test.tsx -t 'line endings round-trip']
- ac4: every doc change calls `onChange` with the full text; a selection-only change does not (new) [evidence: command:mise exec -- npx vitest run src/editor/CodeEditor.test.tsx -t 'onChange on doc changes']
- ac5: a Ctrl+S and a Meta+S keydown on the content element call `onSave` once each and are `defaultPrevented`, in read-only and in editable mode (new) [evidence: command:mise exec -- npx vitest run src/editor/CodeEditor.test.tsx -t 'mod-s saves']
- ac6: a new `docVersion` with a new `doc` replaces the document and clears the undo history (`undoDepth` 0); a rerender with the same `docVersion` keeps the edited document (new) [evidence: command:mise exec -- npx vitest run src/editor/CodeEditor.test.tsx -t 'docVersion resets']
- ac7: no hints: after a dispatched user insertion (`userEvent: 'input.type'`) at the end of a python document and the timers advanced past 1 s, the DOM holds no `.cm-tooltip` element of any kind (new) [evidence: command:mise exec -- npx vitest run src/editor/CodeEditor.test.tsx -t 'no hints']
- ac8: a broken JSON document gets a syntax mark: after `forceLinting(view)` `diagnosticCount(view.state)` is at least 1 and the lint gutter element is rendered (new) [evidence: command:mise exec -- npx vitest run src/editor/CodeEditor.test.tsx -t 'syntax marks']
- ac9: unmounting destroys the view: no `.cm-editor` element remains and `EditorView.findFromDOM` of the old element is null (new) [evidence: command:mise exec -- npx vitest run src/editor/CodeEditor.test.tsx -t 'destroyed on unmount']
- ac10: the design rules hold for the new file [evidence: command:mise exec -- npx vitest run src/layout/designRules.test.ts]
- ac11: the targeted suites, the type check and lint pass [evidence: command:mise exec -- npx vitest run src/editor/CodeEditor.test.tsx src/layout/designRules.test.ts && mise exec -- npx tsc -b && mise run lint]

## Files

- `src/editor/CodeEditor.tsx`
- `src/editor/CodeEditor.test.tsx`

## Interfaces

- `src/editor/CodeEditor.tsx`:
  `export interface CodeEditorProps { path: string; doc: string; docVersion: number; readOnly: boolean; onChange: (text: string) => void; onSave: () => void }` and `export default function CodeEditor(props: CodeEditorProps): JSX.Element`; root element `data-testid="file-editor"`.
- Uses `languageFor` (src/editor/languages.ts), `editorAppearance` (src/editor/highlight.ts), `syntaxChecker` (src/editor/syntaxCheck.ts).
- Consumed by web-file-tabs-view (through `React.lazy`) and, as the stand-in's prop type, by the `FileTabs` and `FilesPanel` tests.

## Expected outcome

A mounted `CodeEditor` shows the file with highlighting and syntax marks, is read-only until `readOnly` turns false, toggles without losing the doc or undo history, reports every change, saves on Ctrl/Cmd+S without the browser dialog, keeps line endings byte-exact and shows no hints.

## Steps

- Probe first: mount a bare `EditorView` in a jsdom test with the `Range` stubs; if it cannot mount, stop and return that as a question (design: Assumptions), never skip or weaken a test.
- Red: write `src/editor/CodeEditor.test.tsx` (the nine behaviour tests); run `mise exec -- npx vitest run src/editor/CodeEditor.test.tsx`: fails (no module).
- Green: `CodeEditor.tsx`; run the task's verify: passes, quote the vitest summary line.

## Notes

- Rulings and their pin tests: `lineSeparator` `"\r\n"` when the loaded text holds `"\r\n"`, else `"\n"`, pinned by `line endings round-trip`; Mod-s always `preventDefault` and calls `onSave` in both modes (the caller decides whether to save), pinned by `mod-s saves`; one `Compartment` for `EditorState.readOnly` plus `EditorView.editable`, reconfigured not recreated, pinned by `read-only toggle keeps the view`; a `docVersion` change resets the state (history cleared), pinned by `docVersion resets`.
- Keep `onChange` and `onSave` in refs so a new callback identity never recreates the view.
- jsdom: stub `Range.prototype.getClientRects` (returning an empty list) and `getBoundingClientRect` in the test file; assert through `view.state`; dispatch transactions instead of typing; `forceLinting(view)` instead of waiting the lint delay; fake timers for the "no hints" wait (web-libs-docs B23, B24).
- Extensions per design D11 only; no `basicSetup`, no `autocompletion`, no `closeBrackets`, no `EditorView.lineWrapping`, no tooltips extension.
- Keyboard test: dispatch `keydown` with `key: 's'` and `ctrlKey` or `metaKey` on `view.contentDOM`; CodeMirror's keymap maps `Mod` to Ctrl or Cmd by platform, so register both `Ctrl-s` and `Mod-s` if needed for the jsdom platform.
