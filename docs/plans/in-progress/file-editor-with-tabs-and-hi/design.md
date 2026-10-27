# File editor with tabs and highlighting design

## Summary

The Files panel becomes a split: the file tree always visible on the left, a tabbed editor area on the right (stacked
on a phone). Each open file is one tab, styled like the terminal tabs; text files open in a CodeMirror 6 editor (thin
own React component, no wrapper library) with highlighting for python, yaml, json, terraform and toml and syntax errors
marked, and no hints. Tabs are read-only by default; an RO/RW toggle per tab allows editing and saving (Save button and
Ctrl/Cmd+S) through a new `PUT .../files/content` route in claude-code-wrapper, forwarded by agents-orchestrator, with
optimistic concurrency on the mtime and size the editor loaded (409 `file_changed`, the UI offers reload or overwrite).

## Intent and why

User request (2026-10-27), verbatim:

"## file open

* inside "Files" in RW editor mode- support python/yaml/json/terraform/toml syntax highlighting and syntax- no hints for now
* file tree always visible on the left
* multiple files can be opened- similar design to tabs in terminal"

Implementation order given by the user: 1. download, 2. markdown, 3. editor. Today the Files panel shows one read-only
`<pre>` preview below the tree; no editor library, RO/RW mode or file-write API exists in the UI, the orchestrator or the
wrapper (discovery, `.scratchpad/discovery/agents-web.md` "Files view").

User decisions (binding, numbered here U1 to U7), verbatim:

- U1: "Ordering: this epic runs after file-download-in-file-browse (docs/plans/todo/file-download-in-file-browse, being planned now; read its design.md and tasks if present) and after markdown-rendering-in-chat; it builds on the download epic's wrapper/orchestrator file route patterns and the FilesPanel row changes, so state the dependency and avoid redoing that work."
- U2: "(my call, pending user approval at the gate) CodeMirror 6 with a thin own hook, packages and versions from web-libs-docs.md (state 6.7.6, view 6.43.15, language, commands, lint, lang-python, lang-yaml, lang-json, legacy-modes toml, codemirror-lang-hcl for terraform, @lezer/highlight, smol-toml, yaml). The nomenclature guard (src/nomenclature.test.ts) is tripped by the transitive dep @marijn/find-cluster-break; the planned fix is adding exactly that package name to the guard's ALLOWED list in its own task with a test proving any other match still fails; this is a gate question for the user, keep the task in the plan."
- U3: "(my call) 'RW editor mode': read-only by default with an RO/RW toggle per tab; RW enables editing and Save (button and Ctrl/Cmd+S); new write route in the wrapper (PUT file content, UTF-8 text only, size cap = the existing file_preview_max_bytes, existing workspace path guards, optimistic concurrency via the mtime/size the editor loaded: a changed file answers 409 and the UI offers reload or overwrite) and an orchestrator forwarding route, then `npm run sync:api -- orchestrator`. Binary and too_large files open read-only with the current note, no editor."
- U4: "(my call) 'syntax highlighting and syntax - no hints': highlighting for python, yaml, json, terraform (.tf, .tfvars, .hcl) and toml, plus syntax error marking via @codemirror/lint (json parse linter, yaml and smol-toml parser errors, lezer parse-tree error nodes for python and hcl); no autocomplete, hover or hints (minimal setup, no autocompletion extension). Other extensions open as plain text."
- U5: "(my call) Layout: tree always visible on the left, editor area on the right inside the Files panel (a resizable split), the phone layout stacks or keeps the tree reachable; tabs mirror TerminalPanel (MUI Tabs scrollable, closable tab with IconButton aria-label 'Close <name>', closing picks the neighbour, all tabs stay mounted), one tab per path (re-opening focuses it), unsaved changes mark the tab and closing a dirty tab asks to confirm. Tabs are per session, not persisted across reloads. Highlight palette lives in src/theme.ts."
- U6: "(my call) Live refresh: an open RO tab refetches when the tree reports a changed mtime|size (existing behaviour); a dirty RW tab never auto-reloads, it shows a 'changed on disk' notice instead."
- U7: "Environment: orchestrator Postgres tests need Docker (absent here), wrapper has 3 PID-1 process-group failures here, agents-web full suite has 10 load-dependent timeouts; keep task verifies targeted and Docker-free, and name in design.md the checks only CI can run."

## Goals

- G1: Files panel: file tree always visible on the left, editor area on the right.
- G2: Multiple files open at once as tabs, styled like the terminal tabs (closable, scrollable).
- G3: RO/RW editor mode: read-only by default, RW lets the user edit and save the file back to the agent's workspace
  (new write route in claude-code-wrapper and orchestrator).
- G4: Syntax highlighting for python, yaml, json, terraform and toml, plus syntax checking (errors marked) where the
  language allows.

## Non-goals

- No hints: no autocomplete, hover info or language-server features.
- No file create, rename or delete (a write to a missing path is 404, never a create).
- Open tabs are not persisted across page reloads.
- No re-implementation of the download epic's work (download route, `target_type`, the download icon in `Row`); this
  epic builds on it (U1).
- No deploy: no agents-helmfile task (open question Q2).
- No search, find/replace, folding, minimap, formatting or multi-cursor beyond what the chosen minimal extensions bring.
- No change to the Workspace's three-panel default sizes (25/45/30); the user can maximise the Files panel (my call).
- No fix of the 10 load-dependent agents-web timeouts; noted, not doing now (U7).

## Anti-goals

- An autocomplete popup, hover tooltip or any hint appears in the editor.
- An RO tab can be edited, or a save silently overwrites a file the agent changed after it was loaded.
- Any new way to write outside the workdir, or to create a file, through the write route.
- Unsaved edits lost without a prompt (closing a dirty tab, a live refresh, a session switch and back).
- Colour literals outside `src/theme.ts`, a second copy of `@codemirror/state`, or the editor bundled into the main
  chunk (it loads lazily).
- File content or the derived wrapper bearer in a log line, URL or error message.

## Constraints

- Python only for services; TypeScript for agents-web. No backward-compatibility shims.
- Dependency on other epics (U1): file-download-in-file-browse and markdown-rendering-in-chat land first. This epic's
  tasks assume their commits on each repo's default branch: the wrapper and orchestrator download routes and
  `target_type`, `WrapperClient.open_download`, the Docker-free `tests/test_api_file_download.py` rig, the orchestrator
  wrapper pin of the download merge, `fileDownloadUrl` and the `Row` trailing action in agents-web, and the markdown
  epic's `package.json` and `theme.ts` changes. Task `depends_on` names only tasks of this epic; the cross-epic order is
  the README `blockers` (to be set by the orchestrator, no ticket.py subcommand writes it).
- Orchestrator layering pin: only `api/workspace.py` may import `agents_orchestrator.wrapper`
  (`tests/test_api_sessions.py::test_api_never_imports_k8s_or_wrapper`). `openapi.json` is generated
  (`uv run python -m agents_orchestrator.api.openapi > openapi.json`) and every route is documented in README `## API`
  (`tests/test_readme_api.py`); the wrapper README documents every route and error code (`tests/test_readme_api.py`).
- agents-web: backends only through the relative `basePath` (`src/api/client.ts:base`); `src/api/schema.d.ts` is
  generated, never hand-edited; designRules (`src/layout/designRules.ts`): no colour literal outside `theme.ts`, no
  decorative Unicode, no `title=` on Button/IconButton, spacing on the 0.5 grid, weights 400/500 only; the nomenclature
  guard scans every tracked file including `package-lock.json`.
- CodeMirror under jsdom is unsupported upstream (web-libs-docs B23, B24): editor tests stub `Range.getClientRects` and
  `getBoundingClientRect`, assert through `view.state`, never simulate typing into contenteditable, and call lint
  sources or `forceLinting` instead of waiting the 750 ms delay. Tab and panel tests replace `CodeEditor` with a
  stand-in, as `ChatLog.test.tsx` replaces react-virtuoso.
- Environment (U7): every task `verify` runs without Docker. pytest verifies never add `-q` (both Python repos set it
  in `addopts`). Checks only CI can run:
  - agents-orchestrator DB-backed tests (testcontainers Postgres), including `tests/test_api_files.py` and
    `tests/test_workspace_proxy.py` (525 errors locally in the full run);
  - the contract suite's real-wrapper leg (`pytest -m integration tests/test_fake_wrapper_contract.py`, real wrapper
    image) and the kind e2e (`mise run test:e2e`, `tests/e2e/test_e2e_kind.py`);
  - claude-code-wrapper `tests/test_container.py` (docker) and the 3 process-group tests
    (`tests/test_manager.py::test_shutdown_stops_all`, `tests/test_pty_proc.py::test_exit_without_eof_still_fires`,
    `tests/test_pty_proc.py::test_close_terminates_group_then_kill`), which fail here because PID 1 is not an init
    reaper;
  - the agents-web full suite (`mise run test`), whose 10 load-dependent 5000 ms timeouts (PresetForm, ScheduleForm,
    Endpoints, FiltersEditor) pass alone; CI runs it with `npm run build` and `npm run check:api`.

## Decisions

### D1: CodeMirror 6 with a thin own component

Decision (U2): CodeMirror 6 composed from its packages, mounted by an own React component (no React wrapper library):
`@codemirror/state` 6.7.6, `@codemirror/view` 6.43.15, `@codemirror/language` 6.13.1, `@codemirror/commands` 6.11.1,
`@codemirror/lint` 6.9.7, `@codemirror/lang-python` 6.2.1, `@codemirror/lang-yaml` 6.1.3, `@codemirror/lang-json`
6.0.2, `@codemirror/legacy-modes` 6.5.5 (toml), `codemirror-lang-hcl` 0.2.0 (terraform), `@lezer/highlight` 1.2.5,
`smol-toml` 1.9.1 and `yaml` 2.9.1 (moved from devDependencies to dependencies). Caret ranges at those versions, except
`codemirror-lang-hcl` pinned exactly (`0.2.0`, a 0.x single-maintainer package) (my call). Exactly one
`@codemirror/state` in the lockfile (web-libs-docs B19). No `codemirror` meta package, no `basicSetup`, no
`@uiw/react-codemirror`, no `@codemirror/autocomplete` as a direct dependency.

Alternatives: Monaco (rejected: no toml, about 100 MB, CDN loader by default against the offline/CSP rule in
`theme.ts:4`, per-language web workers under Vite; web-libs-docs B26-B28); `@uiw/react-codemirror` (rejected: defaults
to `basicSetup` with autocompletion and a light theme, pulls `@babel/runtime` and theme-one-dark; B21).
Why: covers all five languages with parser-backed checking, local and small, themable from JS objects in `theme.ts`, and
the minimal composition gives "no hints" by omission (B17, B18).

### D2: Nomenclature guard allows the npm name `find-cluster-break`

Decision (U2, gate question Q1): `src/nomenclature.test.ts` `ALLOWED` gains exactly the entry `'find-cluster-break'`
(the npm package `@marijn/find-cluster-break`, a runtime dependency of `@codemirror/state` since 6.5.0, written into
`package-lock.json` as the `node_modules/@marijn/find-cluster-break` key, its tarball URL and the dependency line; F0.1
to F0.4). A new test pins that the phrase is allowed in those lockfile shapes and that every other spelling of the
retired unit still fails. The guard stays accurate for project nomenclature; a third-party npm name is the same class
as the Kubernetes phrases already allowed. This is the only test edit of the epic that is not an accuracy fix, and it
lands in its own task before any dependency is added.

Alternatives: pin `@codemirror/state` below 6.5.0 (impossible: view 6.43.15 and commands 6.11.1 need ^6.7.0, F0.3);
Monaco (rejected in D1); exclude `package-lock.json` from the guard (rejected: widens the hole to every future dep).

### D3: Wrapper write route `PUT /v1/sessions/{id}/files/content`

Decision (U3): a new route in claude-code-wrapper `api/files.py`, query `path` (relative to the workdir), bearer auth
like every `/v1` route, JSON body `{"content": <string>, "expected": {"mtime": <string>, "size": <int >= 0>} | null}`
(both keys required, no other key: `extra="forbid"`, else 422 `invalid_request`). A blocking helper in `files.py`,
run in a worker thread:

1. resolves with the existing `_resolve` (`resolve_in_workdir`): absolute, NUL, `..` or symlink escape is 400
   `invalid_path`; a vanished workdir or unknown session 404 `not_found`;
2. encodes `content` as UTF-8; more bytes than `limits.file_preview_max_bytes` is 413 `too_large` (existing code), the
   file untouched;
3. opens the resolved parent directory with `O_RDONLY | O_DIRECTORY | O_NOFOLLOW` and the target inside it with
   `O_RDONLY | O_NOFOLLOW | O_NONBLOCK` (`dir_fd`), and checks `S_ISREG` on `fstat` of that descriptor: a missing path is
   404 `not_found` and nothing is created (no file create, README non-goal); a directory, the workdir itself, a FIFO,
   socket or device is 400 `not_a_file`; an unfollowable final symlink 400 `invalid_path`;
4. with `expected` not null, compares `_iso(st.st_mtime)` and `st.st_size` of that descriptor with it; any difference
   is 409 `file_changed` (new code), the file untouched;
5. writes atomically: a temporary file `.<name>.<random>.tmp` created in the same directory through the directory
   descriptor (`O_WRONLY | O_CREAT | O_EXCL | O_NOFOLLOW`), the original's permission bits applied with `fchmod`, all
   bytes written and `fsync`ed, then `os.replace` onto the name with `src_dir_fd`/`dst_dir_fd`; on any failure the
   temporary file is removed and the original stays as it was; every descriptor is closed on every exit;
6. answers 200 `{"session_id", "path", "size", "mtime"}` from `fstat` of the replaced file, `path` normalised as the
   content route does (relative real path).

A path that is a symlink inside the workdir to a regular file writes the target and keeps the link (my call: the path
resolves to the target, as the content route reads it). The content is not passed through the redactor (as for
`files/content`); it is never logged. `_raise` maps codes to statuses (`not_found` 404, `file_changed` 409, `too_large`
413, else 400). README: the route section, `file_changed` in the Errors table, `too_large` row widened, and the Trust
model sentence that calls the file API read-only rewritten to name the write route and its guards; the `files.py` and
`api/files.py` header docstrings stop saying read-only.

Alternatives: write in place through the opened descriptor (rejected (my call): a reader such as the agent's own tools
could see a half-written file and a failed write would truncate the original; the atomic replace changes the inode,
so hard links to the file are not updated, open question Q3); reuse the turn `files` field (`safe_write_files`,
rejected: needs a turn, creates files, 256 KiB cap); POST or PATCH (rejected: PUT is the full-replacement verb on the
same resource the GET reads).

### D4: Optimistic concurrency on mtime and size

Decision (U3): the editor sends back the `mtime` and `size` of the `files/content` answer it loaded (or of its last
save answer); the wrapper refuses with 409 `file_changed` when the file on disk differs. `expected: null` is an
explicit unconditional overwrite, sent only after the user chose Overwrite on a conflict. The check and the replace
are not one atomic step (a write in the small window between them is not detected), and `mtime` has millisecond
precision (the listing's `_iso`), so two writes of the same size within one millisecond are not told apart; both are
documented in the wrapper README route section (my call: acceptable for a human editor; a content hash would need a
new field in the content route).

Alternatives: a content hash or ETag (rejected: U3 names mtime/size, and the content route has no hash field);
last-write-wins (rejected: silently loses agent edits).

### D5: Orchestrator forwarding route `PUT /api/v1/sessions/{session_id}/files/content`

Decision (U3): in `api/workspace.py` (the layering pin), query `path` and optional `agent_id`, agent choice by the
existing `resolve_agent` (404 `not_found`, 409 `agent_not_ready`, 503 `unavailable`), the existing `forward` error map
(wrapper 4xx passed through with status and code, token scrubbed: 400 `invalid_path`, 400 `not_a_file`, 404
`not_found`, 409 `file_changed`, 413 `too_large`; 5xx 502 `wrapper_error`; transport 502 `wrapper_unreachable`). The
route carries the existing Origin guard (`dependencies=guarded`, 403 `forbidden_origin`) because it mutates, like the
terminal POST and DELETE. Request model `schemas.WriteFile {content: str, expected: FileStamp | None}` and
`schemas.FileStamp {mtime: str, size: int >= 0}`, both `extra="forbid"` (422 `invalid_request` before any wrapper
call); response `schemas.FileWritten {session_id, agent_id, path, size, mtime}`. `_file_call` takes the method and an
optional JSON body instead of a hard-coded GET, so the three file routes share it. Content is never logged (the
`forward` debug lines carry method and path only). Not on the service-port allowlist (no service needs it) and not on
the agent port. README `## API` gets the route section; `openapi.json` regenerated; MEMORY.md records the write route
and the Origin guard choice. Behaviour tests run without a database (as the download epic's D7): a new
`tests/test_api_file_write.py` with a real `FakeWrapper`, `workspace.resolve_agent` monkeypatched and a stub pool; the
DB-backed `tests/test_api_files.py` is extended for agent choice on PUT and runs in CI only.

Alternatives: a new api module for writes (rejected: layering pin); no Origin guard (rejected: a mutating route reached
with the SSO cookie must refuse foreign origins).

### D6: Fake wrapper parity, one contract suite

Decision: `tests/fakes/fake_wrapper.py` gets the PUT route with the wrapper's contract (body validation, cap from its
`file_preview_max_bytes` control, existing regular files only, `file_changed`, response keys), and
`tests/test_fake_wrapper_contract.py` gets cases on both legs (fake locally, real image in CI) plus fake-only cases for
what the real image cannot set up (a lowered cap, symlinks). Why: the orchestrator route tests run against the fake
(recurring retro finding: fakes encoded a wrong assumption).

### D7: Orchestrator pins the wrapper commit carrying the write route

Decision: once the wrapper change is merged on claude-code-wrapper `main`, the orchestrator pins that merge commit in
the dev dependency (`pyproject.toml`, `uv.lock`), README `## Images` and `e2e/agent-test.Dockerfile` (`BASE_IMAGE`,
`WRAPPER_SHA`), and the kind e2e gets a write case, so CI's integration leg and e2e run the real route. Precedent: the
download epic's `orch-wrapper-pin-download` and done epic web-ui-cluster-tabs-with-fil task `wrapper-sha-pin`.

### D8: Web client schema regenerated and `writeFile`

Decision (U3): after the orchestrator route lands, `npm run sync:api -- orchestrator` (vendors
`openapi/orchestrator.json`, `openapi/orchestrator.source`, regenerates `src/api/schema.d.ts`), `npm run check:api`
stays green, and `src/api/files.ts` gains `writeFile(sessionId, path, content, expected)` sending
`PUT {base}/sessions/{id}/files/content?path=` with `{content, expected}` and answering `FileWritten`; its header
comment stops saying read-only.

### D9: Languages and highlighting

Decision (U4, U5): `src/editor/languages.ts` maps a path to a language by its lower-cased file name: `.py`, `.pyi`
python (`python()`); `.yaml`, `.yml` yaml (`yaml()`); `.json` (so also `.tf.json`, web-libs-docs B5) json (`json()`);
`.tf`, `.tfvars`, `.hcl` terraform (`hcl()` from `codemirror-lang-hcl`); `.toml` toml (`StreamLanguage.define(toml)`);
anything else plain text (no language). The colours live in `src/theme.ts` as a `syntaxPalette` (keyword, string,
number, comment, property, type, function, operator, punctuation, atom, invalid) next to `terminalTheme`, reusing its
hues; `src/editor/highlight.ts` builds the `HighlightStyle` (`syntaxHighlighting`) and the dark `EditorView.theme`
(background, gutters, cursor, selection, active line, lint markers) from `TOKENS`, `MONO_FONT` and `syntaxPalette`
only. `defaultHighlightStyle` is not used (it is for light themes, B15).

### D10: Syntax checking without hints

Decision (U4): `src/editor/syntaxCheck.ts` exports `syntaxDiagnostics(language, state)`, a pure function of the
`EditorState`, and `syntaxChecker(language)`, the extension `[linter(view => syntaxDiagnostics(language, view.state)),
lintGutter()]` (default 750 ms delay). Per language: json, the `jsonParseLinter` of `@codemirror/lang-json` (B7); yaml,
`parseAllDocuments` of `yaml`, one diagnostic per document error at its `pos` range, so `---` streams are not errors
(B8); toml, `smol-toml` `parse`, one diagnostic at the `TomlError` line and column (B9); python and terraform, one
diagnostic per Lezer error node of the full tree (`ensureSyntaxTree`; a parse that does not finish within its timeout
gives no diagnostics rather than false ones) (B10); plain text none. Marks show in RO and RW tabs. No
`autocompletion()`, no hover tooltips, no `basicSetup`; `python()`'s completion sources stay inert without the
autocompletion extension (B18).

### D11: `CodeEditor` component

Decision (U2, U3): `src/editor/CodeEditor.tsx` (default export, so it can be lazy-loaded) creates one `EditorView` in an
effect and destroys it on unmount. Props: `path` (language, D9), `doc` and `docVersion` (the editor resets to `doc`,
history cleared, whenever `docVersion` changes), `readOnly`, `onChange(text)` (every doc change, full text) and
`onSave()` (Mod-s while focused, always `preventDefault`, so the browser's save dialog never opens). Extensions:
`lineNumbers`, `highlightSpecialChars`, `history`, `drawSelection`, `keymap` (`defaultKeymap`, `historyKeymap`, Mod-s),
the language, `syntaxChecker`, the D9 theme and highlight style; `readOnly` drives one `Compartment` holding
`EditorState.readOnly` and `EditorView.editable`, reconfigured in place so doc, selection and undo history survive a
toggle (B12-B14). Line endings round-trip byte-exact (my call): `EditorState.lineSeparator` is `"\r\n"` when the loaded
text contains `"\r\n"`, else `"\n"`, so an unedited document's `doc.toString()` equals the loaded text for LF, CRLF and
mixed files. No line wrapping (code scrolls horizontally) (my call). The panel loads the component with `React.lazy`,
so CodeMirror is its own build chunk and the main bundle does not grow (my call).

### D12: Tabs and their state

Decision (U3, U5, U6): `src/files/useFileTabs.ts` holds the tabs of one session: path, name, kind (`loading`, `text`,
`binary`, `too_large`, `other`, `error`), mode (`ro` default, `rw`), the loaded or saved text and its stamp (the
baseline `{mtime, size}`), dirty (current text differs from the baseline text), saving, save error, `conflict` (a save
answered 409 `file_changed`), `changedOnDisk` (the file changed while dirty), `doc`/`docVersion` for the editor. One
tab per path: opening an open path focuses it without a refetch. Closing picks the neighbour
(`rest[min(index, len - 1)]`, as `TerminalPanel`). RO is refused while the tab is dirty (save, reload or close first)
(my call). Save sends `writeFile(..., baseline)`; success makes the answer the new baseline; 409 `file_changed` sets
`conflict`, offering Reload (refetch, edits discarded) or Overwrite (`expected: null`); any other error shows inline as
`<code>: <message>`. Stale answers (a tab closed or reloaded again meanwhile) are dropped. Tabs are per session and in
memory only: a module-level store keyed by session id keeps each session's tabs (text, mode, dirty state, baseline)
for the page's lifetime, so switching to another session and back restores them (the Workspace remounts the panel per
session); a reload starts empty (my call, so a session switch never loses edits silently).

`src/files/FileTabs.tsx` renders them like `TerminalPanel`: MUI `Tabs` `variant="scrollable" scrollButtons="auto"`, a
`Tab component="div"` per file whose label is the name plus a small `IconButton component="span"` with
`aria-label="Close <name>"` (`stopPropagation`), every panel mounted (`position: absolute; inset: 0`, inactive
`display: none` and `hidden`). A dirty tab's label ends with ` *` and carries `data-dirty="true"` (my call: plain ASCII,
designRules). Closing a dirty tab opens the existing `ConfirmDialog` ("Discard unsaved changes to <name>?", confirm
"Discard"). Each text panel has a toolbar: the full relative path, an RO/RW `ToggleButtonGroup` (aria-label
"Editor mode"), and a Save button enabled only in RW with unsaved changes and no save running; Ctrl/Cmd+S in the
editor saves under the same condition. Binary, too_large and other tabs show today's notes (`file-preview-note`),
errors `file-preview-error`; they have no editor, toggle or Save.

### D13: Split layout inside the Files panel

Decision (U5): `FilesPanel` renders a `react-resizable-panels` `Group` inside its slot: on tablet and desktop
(`useLayout` not `phone`) horizontal, tree panel first (left, default 30 percent), editor area right (70 percent); on a
phone vertical, tree above (40 percent) and editor below (60 percent), both always rendered so the tree stays reachable
(my call). The separator reuses the Workspace divider style with its inline `flexBasis` (MEMORY 2026-10-24); sizes are
not persisted (my call). The tree keeps its header, errors, polling, events and the download icon of the download epic;
its selection follows the active tab. The single `Preview` state, `PreviewBody` and the `<pre>` preview are removed;
the header comment stops saying read-only preview.

### D14: Live refresh rules

Decision (U6): for each open tab the panel feeds the hook the `mtime|size` stamp of its entry in the loaded tree
listings. The hook acts when that stamp differs from the last stamp it saw for the path (initialised to the baseline
when the tab opens) and from the tab's baseline: an RO tab or a clean RW tab refetches (mode kept); a dirty RW tab
never auto-reloads, it sets `changedOnDisk`, shown as a notice with Reload and Keep editing (my call: clean RW tabs
refetch too, no edit can be lost). A save's own new stamp equals the baseline, so it triggers nothing. An agent write
event for the path (`fileEvents` `written`) applies the same rule. A refetch that answers another kind (binary,
too_large, error) turns the tab into that note.

## Research

| Lens | Ran / skipped | Adopted ideas | Rejected ideas |
|---|---|---|---|
| discovery (cartographer per repo) | ran: `.scratchpad/discovery/agents-web.md`, `.scratchpad/discovery/agents-orchestrator.md`; the claude-code-wrapper brief covers slash commands, so wrapper facts come from direct reads of `src/claude_code_wrapper/files.py`, `api/files.py`, `workdir.py` | reuse `_resolve`/`_open_nofollow`/`_iso` (ccw files.py:57,68,44); `resolve_agent`, `forward`, `_file_call`, `guarded` (orchestrator api/workspace.py:88,206,252,324); TerminalPanel tabs, neighbour close, mounted panels (agents-web TerminalPanel.tsx:112-203); stale-file refetch (FilesPanel.tsx:153-167); `ConfirmDialog`; Divider flexBasis (Workspace.tsx:34-41) | `safe_write_files` for saves (needs a turn, creates files); a custom tab component |
| research-docs | ran: `.scratchpad/discovery/web-libs-docs.md` (registry metadata, CodeMirror and Lezer reference manuals) | package set and versions (B1-B4); `jsonParseLinter`, `parseAllDocuments`, `smol-toml` errors, Lezer error nodes (B7-B10); `Compartment` for readOnly (B14); `EditorView.theme` + `HighlightStyle.define` from theme tokens (B15); minimal composition without autocompletion (B17, B18); jsdom stubs (B23, B24) | Monaco (B26-B28); `@uiw/react-codemirror` (B21); `basicSetup`; `defaultHighlightStyle` |
| research-code-internal | skipped: no parser or subsystem of our own; every helper reused is cited above | - | - |
| research-code-external | skipped: atomic replace (temp file, `fsync`, `os.replace` with dir fds) is standard POSIX practice | - | - |
| research-papers | skipped: no algorithmic core | - | - |

## Research inputs

Workflow proposals from the retros of recently done epics (`ticket.py retro --history`), recurring first:

- Recurring (generic-any-mcp-with-git-and, cross-session-messaging-and, paste-env-contents-into-the): late defects
  because test fakes encoded the same wrong assumption; ACs must tie fakes to the real output. Acted on by
  fake-wrapper-file-write (one contract suite over the fake and the real image) and web-file-tabs-view /
  web-files-split-layout (the `CodeEditor` stand-in's props are the real component's `CodeEditorProps`).
- Recurring (cross-session-messaging-and, paste-env-contents-into-the): hand-backs quote the verify summary line with
  counts; pytest verifies add no `-q` on top of `addopts`. Acted on by wrapper-file-write-route,
  fake-wrapper-file-write, orch-file-write-route, orch-wrapper-pin-write.
- Recurring (paste-env-contents-into-the, matrix-read-receipts): a ruling not pinned by a test was found only in review;
  each ruling in Notes names its pin test. Acted on by wrapper-file-write-route (symlink target, atomic replace,
  millisecond stamp), web-code-editor (line separator, Mod-s), web-file-tabs-state (refresh rules, RO while dirty,
  session store).
- Recurring (agents-matrix-connector-depl and later): live apply and smoke tasks run far over the seed. Not applicable:
  no live task in this epic (Q2).
- One-off (cross-session-messaging-and): task ACs must name existing files; new tests are marked "(new)" in every AC.
- One-off (generic-any-mcp-with-git-and): GitGuardian flagged a fake credential literal in an orchestrator test; acted
  on by orch-file-write-route (tokens derived at runtime with `derive_tokens`, as `tests/test_api_files.py` does).

Brief plan inputs:

- reuse `_resolve`, `_open_nofollow`, `_iso`, `FileError`, `_raise` - ccw files.py, api/files.py - wrapper-file-write-route.
- reuse `resolve_agent`, `forward`, `_file_call`, `guarded` - orchestrator api/workspace.py - orch-file-write-route.
- reuse FakeWrapper `_auth`/`_get`/`_locate`, `_tree`, `fake_leg` - orchestrator tests - fake-wrapper-file-write.
- reuse TerminalPanel tab pattern, `ConfirmDialog`, `errorText`, `useLayout`, Workspace `Divider` - agents-web - web-file-tabs-view, web-files-split-layout.
- reuse stale-file refetch and `written` events - agents-web FilesPanel.tsx, fileEvents.ts - web-file-tabs-state, web-files-split-layout.
- fix-as-ac (web-libs-docs): nomenclature allow for `find-cluster-break` - web-nomenclature-allowlist; one `@codemirror/state` - web-editor-languages; no autocomplete DOM - web-code-editor; RO toggle keeps doc and history - web-code-editor; `parseAllDocuments` - web-editor-syntax-check; a syntax error test per language - web-editor-syntax-check; colours only from theme.ts - web-editor-languages; jsdom stubs, assert via `view.state` - web-code-editor; bundle-size delta in MEMORY.md - web-editor-languages, web-file-tabs-view.
- fix-as-ac (agents-web brief): stale "read-only" headers in `src/files/FilesPanel.tsx:1` and `src/api/files.ts:1` - web-files-split-layout, web-sync-write-api.
- do-not-build: a React wrapper for CodeMirror, a TOML/HCL grammar, a JSON/YAML/TOML validator, a lint gutter, undo
  history or keymaps, autocompletion off-switches, a custom tab component, a second listing poll, hand edits to
  `schema.d.ts`, absolute backend URLs, Kubernetes `pods/exec` file access, a second wrapper-calling api module -
  honoured by D1, D5, D8, D10, D11, D12, D13.
- fix-as-ac (agents-web): 10 load-dependent timeouts in the full run - not fixed here (U7); noted, not doing now.
- not acted on: hive advisory file locks (orchestrator api/agent.py:291-336) are not consulted by a user save; noted, not
  doing now.

## Decision coverage

| Decision | Tasks |
|---|---|
| D1 CodeMirror 6 with a thin own component | web-editor-languages, web-code-editor |
| D2 Nomenclature guard allows find-cluster-break | web-nomenclature-allowlist |
| D3 Wrapper write route | wrapper-file-write-route |
| D4 Optimistic concurrency | wrapper-file-write-route, fake-wrapper-file-write, web-file-tabs-state |
| D5 Orchestrator forwarding route | orch-file-write-route |
| D6 Fake wrapper parity | fake-wrapper-file-write |
| D7 Orchestrator pins the wrapper commit | orch-wrapper-pin-write |
| D8 Web client schema and writeFile | web-sync-write-api |
| D9 Languages and highlighting | web-editor-languages |
| D10 Syntax checking without hints | web-editor-syntax-check, web-code-editor |
| D11 CodeEditor component | web-code-editor, web-file-tabs-view |
| D12 Tabs and their state | web-file-tabs-state, web-file-tabs-view |
| D13 Split layout | web-files-split-layout |
| D14 Live refresh rules | web-file-tabs-state, web-files-split-layout |

## Review focus

- Wrapper write: no byte written outside the workdir or to a non-regular file; no file created for a missing path;
  the precondition read from the same descriptor that was checked; the temporary file removed and every descriptor
  closed on every exit; the original intact after a failed write; permission bits kept.
- Orchestrator: the Origin guard runs before the body is forwarded; the body is validated before any wrapper call;
  content and token never in a log line or error message.
- Editor: RO is really read-only (`readOnly` and `editable` both); no autocomplete or tooltip extension anywhere;
  line endings round-trip byte-exact; the toggle reconfigures, never recreates, the view.
- Tabs: no path to losing unsaved text without a confirm (close, refresh, session switch); a 409 never overwrites
  without the user choosing Overwrite; stale fetch answers dropped.
- Colours only from `theme.ts`; one `@codemirror/state`; the editor in its own chunk.

## Left to the builder

- The temporary file name's random part and whether the write helper is one function or a few, as long as D3's order
  of checks holds and every exit closes its descriptors.
- Diagnostic messages and how adjacent Lezer error nodes merge, as long as each broken sample gets at least one mark on
  the expected line and each valid sample none.
- The exact `syntaxPalette` hues (from `terminalTheme`'s family) and the editor chrome styles, within `theme.ts`.
- How `useFileTabs` stores the per-tab text (a ref map rather than state is fine), as long as typing does not re-render
  the panel beyond the dirty flag flipping.
- The minimum sizes of the split panels.

## Assumptions and unknown facts

- Assumed: CodeMirror's view mounts in jsdom with `Range.getClientRects`/`getBoundingClientRect` stubs (upstream gives no
  guarantee, B23). web-code-editor confirms it first; if it cannot, the task returns that as a question, it never skips
  or weakens a test.
- Assumed: `codemirror-lang-hcl` 0.2.0 parses Terraform files well enough for highlighting and error nodes (B4: ported
  from tree-sitter-hcl, 2 stars). web-editor-syntax-check pins a valid Terraform sample with no diagnostics; a false
  error on valid Terraform is reported, not hidden.
- Assumed: the markdown epic adds no CodeMirror package (its plan uses react-markdown and checks the lockfile against
  the guard, docs/plans/todo/markdown-rendering-in-chat/tasks/chat-markdown-renderer.md), so this epic's guard change is
  the first.
- Assumed: the Harbor image `claude-code-wrapper:<sha7>` exists for the wrapper merge commit; orch-wrapper-pin-write
  checks it or builds from source with `scripts/e2e.sh`, as in the precedent.
- Assumed: oauth2-proxy passes PUT requests with a JSON body and the SSO cookie to the orchestrator; confirmed only by a
  live save after deploy.

## Open questions

Product questions that need the user, collected across epics by `ticket.py questions`.
- Q1: CodeMirror 6 pulls the npm package @marijn/find-cluster-break into package-lock.json, which trips src/nomenclature.test.ts; may task web-nomenclature-allowlist add exactly the phrase 'find-cluster-break' to the guard's ALLOWED list, with a new test proving every other spelling of the retired unit still fails? [recommended: yes; the guard keeps its purpose and a third-party npm name is the same class as the Kubernetes phrases already allowed (the only alternative, Monaco, has no toml and loads from a CDN)]
- Q2: Deploy is not part of this epic (no agents-helmfile task), so the editor's save works live only after a later deploy pins the new wrapper, orchestrator and web images; is that right? [recommended: yes, deploy the queued epics (download, markdown, editor, slash commands) together in one agents-helmfile deploy epic afterwards]
- Q3: A save replaces the file atomically (temporary file in the same directory, then rename), so a reader never sees a half-written file and a failed save leaves the original intact, but the file gets a new inode: hard links to it are not updated (permission bits are kept); acceptable? [recommended: yes]

## Irreversible operations in scope

none (no tag, release, migration or deploy; PRs merge through the normal flow; user saves overwrite workspace files by
design, guarded by D4).
