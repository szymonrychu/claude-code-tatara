# file editor with tabs and highlighting implementation plan

## Agreed rung

Rung 1 of plan.md, migrated from the epic format: the steps are the epic's tasks.

## Approach

Migrated from the epic format: one step per task file, in dependency order, each with its status, files, verify, verified head and every body section.

## Chunk 1: migrated tasks (model: opus)

### S1: web nomenclature allowlist

- Status: done
- Files: `src/nomenclature.test.ts`
- Verify: `mise exec -- npx vitest run src/nomenclature.test.ts && mise run lint`
- Verified head: 8a6d7fef456956261bd627e1587ed35c02397ee5

#### Requirement

User decision U2, verbatim: "(my call, pending user approval at the gate) CodeMirror 6 with a thin own hook, packages and versions from web-libs-docs.md (state 6.7.6, view 6.43.15, language, commands, lint, lang-python, lang-yaml, lang-json, legacy-modes toml, codemirror-lang-hcl for terraform, @lezer/highlight, smol-toml, yaml). The nomenclature guard (src/nomenclature.test.ts) is tripped by the transitive dep @marijn/find-cluster-break; the planned fix is adding exactly that package name to the guard's ALLOWED list in its own task with a test proving any other match still fails; this is a gate question for the user, keep the task in the plan."

Design D2, verbatim: "`src/nomenclature.test.ts` `ALLOWED` gains exactly the entry `'find-cluster-break'` (the npm package `@marijn/find-cluster-break`, a runtime dependency of `@codemirror/state` since 6.5.0, written into `package-lock.json` as the `node_modules/@marijn/find-cluster-break` key, its tarball URL and the dependency line; F0.1 to F0.4). A new test pins that the phrase is allowed in those lockfile shapes and that every other spelling of the retired unit still fails. The guard stays accurate for project nomenclature; a third-party npm name is the same class as the Kubernetes phrases already allowed. This is the only test edit of the epic that is not an accuracy fix, and it lands in its own task before any dependency is added."

Precondition: the user approved this guard change at the gate (design.md open question Q1). Without that answer recorded, do not start; return it as a blocker.

Scope (agents-web): `src/nomenclature.test.ts` only: the `ALLOWED` entry, the doc comment of `ALLOWED` naming npm package names as a second allowed class, and the new test below. No other list (`HISTORY`, `GUARDED`, `RETIRED`, `FORBIDDEN`) and no existing test changes.

#### Acceptance conditions

- ac1: the three lockfile shapes of the package (the `"node_modules/@marijn/find-<unit>-break": {` key, a tarball URL of the shape `https://registry.npmjs.org/@marijn/find-<unit>-break/-/find-<unit>-break-<version>.tgz` and the `"@marijn/find-<unit>-break": "^1.0.0"` dependency line) do not offend, while `find-<unit>`, `<unit>-break`, `my-<unit>-break` and `find-<unit>-break and a <unit>` still offend (the unit spelled through the file's `unit` constant) (new) [evidence: command:mise exec -- npx vitest run src/nomenclature.test.ts -t 'npm package name']
- ac2: `ALLOWED` is the previous list plus exactly `'find-cluster-break'` at its end [evidence: command:grep -qF "const ALLOWED = ['cluster.local', 'ClusterIP', 'clusterIP', 'ClusterIssuer', 'cluster-issuer', 'ClusterRole', 'in-cluster', 'cluster-internal', 'cluster node', 'cluster-info', 'find-cluster-break']" src/nomenclature.test.ts]
- ac3: every existing nomenclature test passes unchanged against the current tree [evidence: command:mise exec -- npx vitest run src/nomenclature.test.ts]
- ac4: lint passes [evidence: command:mise run lint]

#### Files

- `src/nomenclature.test.ts`

#### Interfaces

- `src/nomenclature.test.ts:ALLOWED` gains `'find-cluster-break'`; `offends`, `FORBIDDEN`, `HISTORY`, `GUARDED`, `RETIRED` unchanged.
- New test in the `nomenclature` describe block, named so `-t 'npm package name'` selects it.

#### Expected outcome

Installing CodeMirror (task web-editor-languages) keeps `src/nomenclature.test.ts` green, and every spelling of the retired unit other than the npm package name still fails the guard.

#### Steps

- Red: add the new test asserting the three lockfile shapes do not offend and the four other spellings do; run `mise exec -- npx vitest run src/nomenclature.test.ts -t 'npm package name'`: the lockfile shapes offend, the test fails.
- Green: add the `ALLOWED` entry and widen its doc comment; run the task's verify: passes, quote the vitest summary line.

#### Notes

- Gate: this is the guard edit the user approves at the gate (design Q1). It is the deliberate exception to "never edit a test to make it pass": the guard's purpose (project nomenclature) is unchanged and a third-party npm name is the same class as the Kubernetes phrases already allowed.
- Spell the unit through the file's `unit` constant in the new test, as the existing tests do; the literal `'find-cluster-break'` in `ALLOWED` is itself stripped by the guard.
- Ruling and its pin test: only the exact phrase `find-cluster-break` is allowed, pinned by the new test (`find-<unit>`, `<unit>-break`, `my-<unit>-break` still offend).

- 2026-10-27 done

### S2: wrapper file write route

- Status: done
- Files: `src/claude_code_wrapper/files.py`, `src/claude_code_wrapper/api/files.py`, `README.md`, `tests/test_api_files.py`
- Verify: `unset VIRTUAL_ENV && uv run --frozen pytest tests/test_api_files.py tests/test_readme_api.py && mise run lint`
- Verified head: d13b2a327d86f4e3ea6fd324ed087a1d27dadfb2

#### Requirement

Epic README goal, verbatim: "RO/RW editor mode: read-only by default, RW lets the user edit and save the file back to the agent's workspace (new write route in claude-code-wrapper and orchestrator)."

User decision U3, verbatim: "(my call) 'RW editor mode': read-only by default with an RO/RW toggle per tab; RW enables editing and Save (button and Ctrl/Cmd+S); new write route in the wrapper (PUT file content, UTF-8 text only, size cap = the existing file_preview_max_bytes, existing workspace path guards, optimistic concurrency via the mtime/size the editor loaded: a changed file answers 409 and the UI offers reload or overwrite) and an orchestrator forwarding route, then `npm run sync:api -- orchestrator`. Binary and too_large files open read-only with the current note, no editor."

Epic README non-goal, verbatim: "No file create, rename or delete."

This task is the claude-code-wrapper part: design D3 (write route `PUT /v1/sessions/{id}/files/content`) and D4 (optimistic concurrency on mtime and size), as written in design.md.

Scope (claude-code-wrapper):
- `src/claude_code_wrapper/files.py`: a blocking write helper following D3 steps 1 to 6 (resolve with `_resolve`; UTF-8 encode and cap at `limits.file_preview_max_bytes` as `too_large`; parent opened `O_RDONLY | O_DIRECTORY | O_NOFOLLOW`, target opened `O_RDONLY | O_NOFOLLOW | O_NONBLOCK` with `dir_fd` and `S_ISREG` checked on its `fstat`; `expected` compared with `_iso(st_mtime)` and `st_size` of that descriptor as `file_changed`; atomic replace through a temporary file in the same directory with the original permission bits, `fsync`, `os.replace` with dir fds; temp removed and every descriptor closed on every exit); the module docstring stops saying read-only.
- `src/claude_code_wrapper/api/files.py`: `PUT /sessions/{session_id}/files/content` with a pydantic body `{content: str, expected: {mtime: str, size: int >= 0} | null}` (both required, `extra="forbid"`), run in a worker thread, answering `{session_id, path, size, mtime}`; `_raise` maps `not_found` 404, `file_changed` 409, `too_large` 413, else 400; the module docstring names the write route.
- `README.md`: a `### \`PUT /v1/sessions/{id}/files/content\`` section in the API reference (body, response, the D4 limits: check and replace are not one atomic step, millisecond mtime; no create; symlink writes its target; content not redacted; errors 400 invalid_path, 400 not_a_file, 401 unauthorized, 404 not_found, 409 file_changed, 413 too_large, 422 invalid_request); the Errors table gains `file_changed` and the `too_large` and `not_a_file` rows name the write route; the Trust model sentence that says the file API is read-only is rewritten to name the write route and its guards.
- `tests/test_api_files.py`: the new tests below.

#### Acceptance conditions

- ac1: a PUT replaces the file content byte-exact for UTF-8 text with non-ASCII letters, CRLF line endings, no trailing newline and the empty string, and the answer `{session_id, path, size, mtime}` equals the `size` and `mtime` a following `GET .../files/content` reports (new) [evidence: test:tests/test_api_files.py::test_write_replaces_content]
- ac2: with `expected` equal to the loaded `mtime` and `size` the write succeeds; with a different `mtime` or a different `size` it answers 409 `file_changed` and the file is unchanged; with `expected: null` it overwrites unconditionally (new) [evidence: test:tests/test_api_files.py::test_write_optimistic_concurrency]
- ac3: content whose UTF-8 encoding is longer than `limits.file_preview_max_bytes` answers 413 `too_large` and leaves the file unchanged; content exactly at the cap is written (with `make_client(..., file_preview_max_bytes=8)`) (new) [evidence: test:tests/test_api_files.py::test_write_size_cap]
- ac4: `..`, an absolute path, a NUL byte and a symlink escaping the workdir answer 400 `invalid_path` and leave the outside file unchanged; a directory, the workdir itself (empty path) and a FIFO answer 400 `not_a_file`; a missing path answers 404 `not_found` and creates nothing; an unknown session and a vanished workdir answer 404 `not_found`; no bearer answers 401; a body without `content`, without `expected`, with an extra key or with a non-string `content` answers 422 `invalid_request` (new) [evidence: test:tests/test_api_files.py::test_write_guards]
- ac5: a path swapped after the confinement check (to a FIFO, a symlink to an outside file, a symlink to a device) is refused with 400 and the outside file is unchanged; every open of the target uses `O_NOFOLLOW`; a symlink inside the workdir to a regular file writes the target and the link stays a symlink (new) [evidence: test:tests/test_api_files.py::test_write_open_nofollow_and_fstat]
- ac6: the write keeps the file's permission bits, leaves no temporary file in the directory after a success and after a write failure (an `os.write` monkeypatched to raise `OSError`), and after the failure the original content is intact (new) [evidence: test:tests/test_api_files.py::test_write_atomic_replace]
- ac7: the process holds no more open descriptors after a successful write and after each refused one than before (new) [evidence: test:tests/test_api_files.py::test_write_closes_descriptors]
- ac8: the new route is documented in the README API reference [evidence: test:tests/test_readme_api.py::test_every_public_route_documented]
- ac9: `file_changed` and every other code the API answers are in the README Errors table [evidence: test:tests/test_readme_api.py::test_error_codes_documented]
- ac10: README carries the route heading, the `file_changed` code and no longer calls the file API read-only [evidence: command:grep -qF '### `PUT /v1/sessions/{id}/files/content`' README.md && grep -q 'file_changed' README.md && ! grep -q 'is read-only and reads only' README.md]
- ac11: the file and README suites and lint pass [evidence: command:unset VIRTUAL_ENV && uv run --frozen pytest tests/test_api_files.py tests/test_readme_api.py && mise run lint]

#### Files

- `src/claude_code_wrapper/files.py`
- `src/claude_code_wrapper/api/files.py`
- `README.md`
- `tests/test_api_files.py`

#### Interfaces

- New wrapper route `PUT /v1/sessions/{id}/files/content?path=<rel>` (`api/files.py`): body `{"content": str, "expected": {"mtime": str, "size": int >= 0} | null}` (both keys required, `extra="forbid"`); 200 `{"session_id", "path", "size", "mtime"}`; errors 400 `invalid_path`, 400 `not_a_file`, 401 `unauthorized`, 404 `not_found`, 409 `file_changed` (new code), 413 `too_large`, 422 `invalid_request`, as JSON envelopes.
- New helper in `files.py` (name the builder's, for example `write_file(workdir, rel, content, expected, max_bytes) -> dict`), blocking, raising `FileError` with the codes above.
- `api/files.py:_raise`: status by code (`not_found` 404, `file_changed` 409, `too_large` 413, else 400).
- Kept unchanged: `resolve_in_workdir`, `_resolve`, `_open_nofollow`, `list_directory`, `read_preview`, the `GET` listing, content and download contracts.
- Consumed by fake-wrapper-file-write (the fake mirrors it) and orch-file-write-route.

#### Expected outcome

`curl -X PUT -H "$H" -H 'Content-Type: application/json' -d '{"content":"x\n","expected":null}' "localhost:8080/v1/sessions/$SID/files/content?path=<rel>"` replaces an existing workspace file atomically and answers its new size and mtime; a stale `expected` answers 409 `file_changed`; nothing outside the workdir, no non-regular file and no missing path can be written.

#### Steps

- Red: add the seven write tests of the acceptance conditions to `tests/test_api_files.py`; run `unset VIRTUAL_ENV && uv run --frozen pytest tests/test_api_files.py`: the write tests fail with 405 `method_not_allowed` (no PUT route).
- Green: the `files.py` helper, the route and `_raise` in `api/files.py`; rerun: the file tests pass.
- Docs: README route section, Errors table, Trust model sentence, module docstrings; run the task's verify: passes, quote the pytest summary line.

#### Notes

- Rulings and their pin tests: a symlink inside the workdir writes its target and stays a link, pinned by `test_write_open_nofollow_and_fstat`; atomic replace keeps permission bits and leaves no temp file, pinned by `test_write_atomic_replace`; a missing path is 404 and never created, pinned by `test_write_guards`; the stamp compare uses `_iso(st_mtime)` (milliseconds) and `st_size` of the opened descriptor, pinned by `test_write_optimistic_concurrency`; the cap counts UTF-8 bytes, not characters, pinned by `test_write_size_cap`.
- Order of checks (design D3): resolve, encode and cap, open parent and target and `fstat`, compare `expected`, replace. The cap is checked before the file is opened, so an over-cap body never touches the disk.
- Mimic `test_content_open_nofollow_and_fstat` (swap the path after `resolve_in_workdir`) and `test_escapes_refused`; `make_client(work, tmp_path, file_preview_max_bytes=8)` sets the cap; count descriptors with `os.listdir("/proc/self/fd")`.
- The download epic changed this file and `tests/test_api_files.py`; build on its state, do not undo its download route or `target_type`.
- Never log the content. Never block the event loop (`asyncio.to_thread`, like the other file routes).
- The component has no MEMORY.md; record the non-obvious calls (atomic replace, D4 limits) in the README section.
- Known environment failures outside this task's verify: `tests/test_container.py` (no docker) and the 3 process-group tests (container PID 1).

- 2026-10-27 done

### S3: fake wrapper file write

- Status: done
- Files: `tests/fakes/fake_wrapper.py`, `tests/test_fake_wrapper_contract.py`
- Verify: `unset VIRTUAL_ENV && uv run --frozen pytest tests/test_fake_wrapper_contract.py && mise run lint`
- Verified head: cf729243c3abf7cd49d04a9f518377eca81d94b2

#### Requirement

Design D6, verbatim: "`tests/fakes/fake_wrapper.py` gets the PUT route with the wrapper's contract (body validation, cap from its `file_preview_max_bytes` control, existing regular files only, `file_changed`, response keys), and `tests/test_fake_wrapper_contract.py` gets cases on both legs (fake locally, real image in CI) plus fake-only cases for what the real image cannot set up (a lowered cap, symlinks). Why: the orchestrator route tests run against the fake (recurring retro finding: fakes encoded a wrong assumption)."

Design D4, verbatim (the contract part): "the editor sends back the `mtime` and `size` of the `files/content` answer it loaded (or of its last save answer); the wrapper refuses with 409 `file_changed` when the file on disk differs. `expected: null` is an explicit unconditional overwrite, sent only after the user chose Overwrite on a conflict."

The contract the fake mirrors is the claude-code-wrapper one built by task wrapper-file-write-route (design D3): `PUT /v1/sessions/{id}/files/content?path=` with body `{"content": str, "expected": {"mtime": str, "size": int >= 0} | null}` (both keys required, no other key, else 422 `invalid_request`); 413 `too_large` over `file_preview_max_bytes` (UTF-8 bytes); only an existing regular file inside the workdir (missing 404 `not_found`, nothing created; directory or workdir root 400 `not_a_file`; escapes 400 `invalid_path`); 409 `file_changed` when `expected` differs from the file's `mtime` (the listing's ISO milliseconds) or `size`; 200 `{session_id, path, size, mtime}`. Read the wrapper's README section and `src/claude_code_wrapper/api/files.py` on its epic branch before writing the fake.

Scope (agents-orchestrator):
- `tests/fakes/fake_wrapper.py`: the PUT route (honours `_auth`, `_get`, `_locate`, the `file_preview_max_bytes` control), writing through a temporary file and `os.replace` as the wrapper does, and keeping the permission bits.
- `tests/test_fake_wrapper_contract.py`: new both-leg cases `test_files_write`, `test_files_write_conflict`, `test_files_write_errors`; new fake-only cases `test_fake_files_write_cap` and `test_fake_files_write_through_symlink`.

#### Acceptance conditions

- ac1: on both legs, a PUT of new UTF-8 text (non-ASCII letters, CRLF) to `src/main.py` of `_tree` answers 200 with exactly the keys `session_id`, `path`, `size`, `mtime`, and a following `files/content` returns the new content with that `size` and `mtime` (new) [evidence: test:tests/test_fake_wrapper_contract.py::test_files_write]
- ac2: on both legs, `expected` equal to the loaded `mtime` and `size` writes; a stale `mtime` or `size` answers 409 `file_changed` and the content is unchanged; `expected: null` overwrites (new) [evidence: test:tests/test_fake_wrapper_contract.py::test_files_write_conflict]
- ac3: on both legs, `../outside`, `/etc/passwd`, a NUL path and `src/../../x` answer 400 `invalid_path`; `src` and the empty path 400 `not_a_file`; `missing` 404 `not_found` and a following listing does not show it; an unknown session 404 `not_found`; no bearer 401; a body without `expected`, with an extra key or with a non-string `content` 422 `invalid_request` (new) [evidence: test:tests/test_fake_wrapper_contract.py::test_files_write_errors]
- ac4: on the fake, with `file_preview_max_bytes` lowered, content over the cap answers 413 `too_large` and the file is unchanged, content at the cap is written (new) [evidence: test:tests/test_fake_wrapper_contract.py::test_fake_files_write_cap]
- ac5: on the fake, a symlink inside the workdir to a file writes the target and stays a link; a symlink escaping the workdir answers 400 `invalid_path` and the outside file is unchanged (new) [evidence: test:tests/test_fake_wrapper_contract.py::test_fake_files_write_through_symlink]
- ac6: the contract suite (fake leg) and lint pass [evidence: command:unset VIRTUAL_ENV && uv run --frozen pytest tests/test_fake_wrapper_contract.py && mise run lint]

#### Files

- `tests/fakes/fake_wrapper.py`
- `tests/test_fake_wrapper_contract.py`

#### Interfaces

- Fake route `PUT /v1/sessions/{session_id}/files/content` in `tests/fakes/fake_wrapper.py:FakeWrapper` with the contract of wrapper-file-write-route (body, response keys, error codes, `file_preview_max_bytes` cap).
- Kept: every existing fake control (`files_max_entries`, `file_preview_max_bytes`, `set_unreachable`, `workdir(sid)`, `token`) and the download route of the download epic.
- Consumed by orch-file-write-route (`tests/test_api_file_write.py`, `tests/test_api_files.py`).

#### Expected outcome

The fake answers a save exactly as the real wrapper does, and one contract suite proves it on both legs (fake here, real image in CI after orch-wrapper-pin-write).

#### Steps

- Red: add `test_files_write`, `test_files_write_conflict`, `test_files_write_errors`, `test_fake_files_write_cap`, `test_fake_files_write_through_symlink`; run `unset VIRTUAL_ENV && uv run --frozen pytest tests/test_fake_wrapper_contract.py`: the new cases fail (405, no route).
- Green: the fake route; run the task's verify: passes, quote the pytest summary line.

#### Notes

- The real leg (`-m integration`, real wrapper image) runs only in CI and passes only once orch-wrapper-pin-write pins the wrapper commit carrying the route; locally the verify runs the fake leg.
- `_tree` writes files through the turn `files` field on both legs; the stamp for `expected` comes from a `files/content` GET on the same leg, never computed by the test.
- Symlinks and the outside file of the fake-only cases are written straight into `fake.workdir(sid)` and a `tmp_path` sibling.
- Copy the wrapper's semantics from its `api/files.py` and README section on its epic branch; do not import the wrapper package.

- 2026-10-27 done

### S4: web editor languages

- Status: done
- Files: `package.json`, `package-lock.json`, `src/theme.ts`, `src/editor/languages.ts`, `src/editor/highlight.ts`, `src/editor/languages.test.ts`, `MEMORY.md`
- Verify: `mise exec -- npx vitest run src/editor/languages.test.ts src/layout/designRules.test.ts src/nomenclature.test.ts && mise exec -- npx tsc -b && mise run lint`
- Verified head: 0ed55f27897b16d29830ba6aebc2a0dbc338b9b0

#### Requirement

User request (2026-10-27), verbatim: "inside "Files" in RW editor mode- support python/yaml/json/terraform/toml syntax highlighting and syntax- no hints for now"

Epic README goal, verbatim: "Syntax highlighting for python, yaml, json, terraform and toml, plus syntax checking (errors marked) where the language allows."

User decision U2, verbatim: "(my call, pending user approval at the gate) CodeMirror 6 with a thin own hook, packages and versions from web-libs-docs.md (state 6.7.6, view 6.43.15, language, commands, lint, lang-python, lang-yaml, lang-json, legacy-modes toml, codemirror-lang-hcl for terraform, @lezer/highlight, smol-toml, yaml). The nomenclature guard (src/nomenclature.test.ts) is tripped by the transitive dep @marijn/find-cluster-break; the planned fix is adding exactly that package name to the guard's ALLOWED list in its own task with a test proving any other match still fails; this is a gate question for the user, keep the task in the plan."

User decision U4, verbatim: "(my call) 'syntax highlighting and syntax - no hints': highlighting for python, yaml, json, terraform (.tf, .tfvars, .hcl) and toml, plus syntax error marking via @codemirror/lint (json parse linter, yaml and smol-toml parser errors, lezer parse-tree error nodes for python and hcl); no autocomplete, hover or hints (minimal setup, no autocompletion extension). Other extensions open as plain text."

User decision U5 (palette part), verbatim: "Highlight palette lives in src/theme.ts."

Design D1, verbatim (packages): "`@codemirror/state` 6.7.6, `@codemirror/view` 6.43.15, `@codemirror/language` 6.13.1, `@codemirror/commands` 6.11.1, `@codemirror/lint` 6.9.7, `@codemirror/lang-python` 6.2.1, `@codemirror/lang-yaml` 6.1.3, `@codemirror/lang-json` 6.0.2, `@codemirror/legacy-modes` 6.5.5 (toml), `codemirror-lang-hcl` 0.2.0 (terraform), `@lezer/highlight` 1.2.5, `smol-toml` 1.9.1 and `yaml` 2.9.1 (moved from devDependencies to dependencies). Caret ranges at those versions, except `codemirror-lang-hcl` pinned exactly (`0.2.0`, a 0.x single-maintainer package) (my call). Exactly one `@codemirror/state` in the lockfile (web-libs-docs B19). No `codemirror` meta package, no `basicSetup`, no `@uiw/react-codemirror`, no `@codemirror/autocomplete` as a direct dependency."

Design D9, verbatim: "`src/editor/languages.ts` maps a path to a language by its lower-cased file name: `.py`, `.pyi` python (`python()`); `.yaml`, `.yml` yaml (`yaml()`); `.json` (so also `.tf.json`, web-libs-docs B5) json (`json()`); `.tf`, `.tfvars`, `.hcl` terraform (`hcl()` from `codemirror-lang-hcl`); `.toml` toml (`StreamLanguage.define(toml)`); anything else plain text (no language). The colours live in `src/theme.ts` as a `syntaxPalette` (keyword, string, number, comment, property, type, function, operator, punctuation, atom, invalid) next to `terminalTheme`, reusing its hues; `src/editor/highlight.ts` builds the `HighlightStyle` (`syntaxHighlighting`) and the dark `EditorView.theme` (background, gutters, cursor, selection, active line, lint markers) from `TOKENS`, `MONO_FONT` and `syntaxPalette` only. `defaultHighlightStyle` is not used (it is for light themes, B15)."

Precondition: task web-nomenclature-allowlist is on the branch (the lockfile entries of `@marijn/find-cluster-break` would otherwise turn the guard red).

Scope (agents-web):
- `package.json`, `package-lock.json`: the D1 dependencies (installed with `mise exec -- npm install`), `yaml` moved to `dependencies`.
- `src/theme.ts`: `syntaxPalette`.
- `src/editor/languages.ts` (new): `LanguageId`, `languageFor(path)`.
- `src/editor/highlight.ts` (new): `editorHighlight` (the `HighlightStyle`) and `editorChrome` (the `EditorView.theme`), plus `editorAppearance` = `[editorChrome, syntaxHighlighting(editorHighlight)]`.
- `src/editor/languages.test.ts` (new): the tests below.
- `MEMORY.md`: a dated entry (2026-10-27, file-editor-with-tabs-and-hi D1, D2, D9): CodeMirror 6 composed from packages and why not Monaco or a wrapper library, the `find-cluster-break` guard entry and why, `codemirror-lang-hcl` pinned exactly and its maintenance risk, `yaml` now a runtime dependency.

#### Acceptance conditions

- ac1: `package.json` `dependencies` hold the D1 packages at `^` ranges of the listed versions and `codemirror-lang-hcl` at exactly `0.2.0`, `yaml` moved from `devDependencies` to `dependencies`, and no `codemirror`, `@uiw/react-codemirror`, `@codemirror/autocomplete` or `monaco-editor` entry [evidence: command:node -e "const p=require('./package.json');const d=p.dependencies,dv=p.devDependencies||{};const want={'@codemirror/state':'^6.7.6','@codemirror/view':'^6.43.15','@codemirror/language':'^6.13.1','@codemirror/commands':'^6.11.1','@codemirror/lint':'^6.9.7','@codemirror/lang-python':'^6.2.1','@codemirror/lang-yaml':'^6.1.3','@codemirror/lang-json':'^6.0.2','@codemirror/legacy-modes':'^6.5.5','codemirror-lang-hcl':'0.2.0','@lezer/highlight':'^1.2.5','smol-toml':'^1.9.1','yaml':'^2.9.1'};const bad=Object.entries(want).filter(([k,v])=>d[k]!==v).concat(['codemirror','@uiw/react-codemirror','@codemirror/autocomplete','monaco-editor'].filter(k=>d[k]||dv[k]).map(k=>[k,'present'])).concat(dv.yaml?[['yaml','still a devDependency']]:[]);if(bad.length){console.error(bad);process.exit(1)}"]
- ac2: the lockfile holds exactly one `@codemirror/state` [evidence: command:node -e "const l=require('./package-lock.json');const n=Object.keys(l.packages).filter(k=>k.endsWith('node_modules/@codemirror/state')).length;process.exit(n===1?0:1)"]
- ac3: the nomenclature guard passes with the new lockfile [evidence: command:mise exec -- npx vitest run src/nomenclature.test.ts]
- ac4: `languageFor` maps `.py` and `.pyi` to python, `.yaml` and `.yml` to yaml, `.json` and `main.tf.json` to json, `.tf`, `.tfvars` and `.hcl` to terraform, `.toml` to toml, case-insensitively (`SETUP.PY`), and `README.md`, `Makefile`, `notes.txt` and `.env` to plain with no language extension (new) [evidence: command:mise exec -- npx vitest run src/editor/languages.test.ts -t 'languageFor']
- ac5: for each of the five languages a sample document parsed with its language yields at least one token styled by `editorHighlight` (python `def`, yaml key, json string, terraform block keyword, toml key) (new) [evidence: command:mise exec -- npx vitest run src/editor/languages.test.ts -t 'highlights every language']
- ac6: every colour in `editorHighlight` and `editorChrome` is a value of `syntaxPalette` or `TOKENS` from `src/theme.ts` (new) [evidence: command:mise exec -- npx vitest run src/editor/languages.test.ts -t 'colours from the theme']
- ac7: the design rules hold for the new and changed files (no colour literal outside `theme.ts`) [evidence: command:mise exec -- npx vitest run src/layout/designRules.test.ts]
- ac8: MEMORY.md records the decision [evidence: command:grep -q 'file-editor-with-tabs-and-hi' MEMORY.md && grep -q 'find-cluster-break' MEMORY.md && grep -q 'codemirror-lang-hcl' MEMORY.md]
- ac9: the targeted suites, the type check and lint pass [evidence: command:mise exec -- npx vitest run src/editor/languages.test.ts src/layout/designRules.test.ts src/nomenclature.test.ts && mise exec -- npx tsc -b && mise run lint]

#### Files

- `package.json`
- `package-lock.json`
- `src/theme.ts`
- `src/editor/languages.ts`
- `src/editor/highlight.ts`
- `src/editor/languages.test.ts`
- `MEMORY.md`

#### Interfaces

- `src/theme.ts:syntaxPalette` (keys `keyword`, `string`, `number`, `comment`, `property`, `type`, `function`, `operator`, `punctuation`, `atom`, `invalid`), `as const`, colour literals allowed here only.
- `src/editor/languages.ts`: `export type LanguageId = 'python' | 'yaml' | 'json' | 'terraform' | 'toml' | 'plain'`; `export function languageFor(path: string): { id: LanguageId; support: Extension }` (`support` is `[]` for plain).
- `src/editor/highlight.ts`: `export const editorHighlight: HighlightStyle`, `export const editorChrome: Extension` (`EditorView.theme(..., { dark: true })`), `export const editorAppearance: Extension`.
- Consumed by web-editor-syntax-check and web-code-editor.

#### Expected outcome

The CodeMirror packages are installed with one `@codemirror/state`, the nomenclature guard stays green, every one of the five languages is recognised from the file name and highlighted in theme colours, and other files are plain text.

#### Steps

- Install: `mise exec -- npm install @codemirror/state@^6.7.6 @codemirror/view@^6.43.15 @codemirror/language@^6.13.1 @codemirror/commands@^6.11.1 @codemirror/lint@^6.9.7 @codemirror/lang-python@^6.2.1 @codemirror/lang-yaml@^6.1.3 @codemirror/lang-json@^6.0.2 @codemirror/legacy-modes@^6.5.5 @lezer/highlight@^1.2.5 smol-toml@^1.9.1 yaml@^2.9.1` and `mise exec -- npm install --save-exact codemirror-lang-hcl@0.2.0`; remove `yaml` from `devDependencies`; check ac1 and ac2; run `mise exec -- npx vitest run src/nomenclature.test.ts`: passes (needs web-nomenclature-allowlist).
- Red: write `src/editor/languages.test.ts` (node environment); run `mise exec -- npx vitest run src/editor/languages.test.ts`: fails (no module).
- Green: `syntaxPalette`, `languages.ts`, `highlight.ts`; rerun: passes.
- MEMORY.md entry; run the task's verify: passes, quote the vitest summary line.

#### Notes

- Highlight test: parse with the language's parser (`pythonLanguage.parser.parse`, `jsonLanguage.parser`, `yamlLanguage.parser`, `hclLanguage.parser`) or, for the toml stream language, `ensureSyntaxTree(EditorState.create({doc, extensions: [support]}), len, 1000)`, then `highlightTree(tree, editorHighlight, cb)` from `@lezer/highlight`.
- The colour test reads the colours out of `editorHighlight.specs` and the chrome spec; keep the chrome spec an exported object so it can be inspected.
- `@codemirror/legacy-modes/mode/toml` exports `toml`; `codemirror-lang-hcl` exports `hcl()` and `hclLanguage`.
- No `basicSetup`, no `defaultHighlightStyle` (light theme), no `@codemirror/autocomplete` import.
- If the markdown epic already added a code palette to `theme.ts`, reuse its hues rather than adding a near-duplicate set.
- `package-lock.json` is guarded by the nomenclature test; after install, `grep -inE 'c[l]uster|agent[-_]orchestrator' package-lock.json` must show only `find-cluster-break` lines.

- 2026-10-27 done

### S5: orch file write route

- Status: done
- Files: `src/agents_orchestrator/api/workspace.py`, `src/agents_orchestrator/api/schemas.py`, `README.md`, `openapi.json`, `MEMORY.md`, `tests/test_api_file_write.py`, `tests/test_api_files.py`
- Verify: `unset VIRTUAL_ENV && uv run --frozen pytest tests/test_api_file_write.py tests/test_readme_api.py tests/test_fake_wrapper_contract.py tests/test_origin.py tests/test_api_sessions.py::test_api_never_imports_k8s_or_wrapper && mise run lint`
- Verified head: 0c99a1a0d1060fa0426bb95e334425630f6fa019

#### Requirement

Epic README goal, verbatim: "RO/RW editor mode: read-only by default, RW lets the user edit and save the file back to the agent's workspace (new write route in claude-code-wrapper and orchestrator)."

User decision U3, verbatim: "(my call) 'RW editor mode': read-only by default with an RO/RW toggle per tab; RW enables editing and Save (button and Ctrl/Cmd+S); new write route in the wrapper (PUT file content, UTF-8 text only, size cap = the existing file_preview_max_bytes, existing workspace path guards, optimistic concurrency via the mtime/size the editor loaded: a changed file answers 409 and the UI offers reload or overwrite) and an orchestrator forwarding route, then `npm run sync:api -- orchestrator`. Binary and too_large files open read-only with the current note, no editor."

Design D5, verbatim: "in `api/workspace.py` (the layering pin), query `path` and optional `agent_id`, agent choice by the existing `resolve_agent` (404 `not_found`, 409 `agent_not_ready`, 503 `unavailable`), the existing `forward` error map (wrapper 4xx passed through with status and code, token scrubbed: 400 `invalid_path`, 400 `not_a_file`, 404 `not_found`, 409 `file_changed`, 413 `too_large`; 5xx 502 `wrapper_error`; transport 502 `wrapper_unreachable`). The route carries the existing Origin guard (`dependencies=guarded`, 403 `forbidden_origin`) because it mutates, like the terminal POST and DELETE. Request model `schemas.WriteFile {content: str, expected: FileStamp | None}` and `schemas.FileStamp {mtime: str, size: int >= 0}`, both `extra="forbid"` (422 `invalid_request` before any wrapper call); response `schemas.FileWritten {session_id, agent_id, path, size, mtime}`. `_file_call` takes the method and an optional JSON body instead of a hard-coded GET, so the three file routes share it. Content is never logged (the `forward` debug lines carry method and path only). Not on the service-port allowlist (no service needs it) and not on the agent port. README `## API` gets the route section; `openapi.json` regenerated; MEMORY.md records the write route and the Origin guard choice. Behaviour tests run without a database (as the download epic's D7): a new `tests/test_api_file_write.py` with a real `FakeWrapper`, `workspace.resolve_agent` monkeypatched and a stub pool; the DB-backed `tests/test_api_files.py` is extended for agent choice on PUT and runs in CI only."

Scope (agents-orchestrator):
- `src/agents_orchestrator/api/workspace.py`: route `PUT /api/v1/sessions/{session_id}/files/content` with `dependencies=guarded`; `_file_call` generalised to a method and an optional JSON body.
- `src/agents_orchestrator/api/schemas.py`: `FileStamp`, `WriteFile`, `FileWritten`.
- `README.md`: `### \`PUT /api/v1/sessions/{session_id}/files/content\`` in `## API` (body, response, the 409 `file_changed` semantics and `expected: null`, the Origin guard, errors 400 invalid_path, 400 not_a_file, 403 forbidden_origin, 404 not_found, 409 agent_not_ready, 409 file_changed, 413 too_large, 422 invalid_request, 502 wrapper_unreachable, 502 wrapper_error, 503 unavailable); the listing and content sections stop calling the workdir read-only where they describe the API as a whole.
- `openapi.json`: regenerated with `uv run python -m agents_orchestrator.api.openapi > openapi.json`.
- `MEMORY.md`: a dated entry (2026-10-27, file-editor-with-tabs-and-hi D5): the write route, why the Origin guard, why not on the service port, content never logged.
- `tests/test_api_file_write.py` (new, Docker-free): the tests below.
- `tests/test_api_files.py` (CI only): `test_no_ready_agent` and the agent choice cases loop over the PUT route too (new route, same agent rules).

#### Acceptance conditions

- ac1: a PUT through the route with the loaded stamp writes the file in the fake wrapper's workdir byte-exact and answers `{session_id, agent_id, path, size, mtime}` with the orchestrator session and agent ids (new) [evidence: test:tests/test_api_file_write.py::test_write_proxied]
- ac2: wrapper refusals pass through with their status and code in the error envelope (409 `file_changed` for a stale stamp, 413 `too_large`, 400 `invalid_path`, 400 `not_a_file`, 404 `not_found`); `expected: null` overwrites; a wrapper 401 is relayed without the derived token in the body; an unreachable wrapper is 502 `wrapper_unreachable` and a wrapper 5xx is 502 `wrapper_error` (new) [evidence: test:tests/test_api_file_write.py::test_write_errors_pass_through]
- ac3: a body with an unknown key, without `content`, without `expected` or with a negative `size` answers 422 `invalid_request` and the wrapper receives no request (new) [evidence: test:tests/test_api_file_write.py::test_write_body_validated]
- ac4: a request with an Origin outside `allowed_origins` answers 403 `forbidden_origin` and the wrapper receives no request; an allowed Origin and no Origin pass (new) [evidence: test:tests/test_api_file_write.py::test_write_origin_guarded]
- ac5: `resolve_agent` refusals (404 `not_found`, 409 `agent_not_ready`, 503 `unavailable`) answer as JSON error envelopes before any wrapper call (new) [evidence: test:tests/test_api_file_write.py::test_write_resolve_errors]
- ac6: with logging at DEBUG, no log record of a write carries the file content or the derived token (new) [evidence: test:tests/test_api_file_write.py::test_write_never_logs_content_or_token]
- ac7: the existing GET listing and content routes still answer through the generalised `_file_call` (new) [evidence: test:tests/test_api_file_write.py::test_reads_still_proxied]
- ac8: README documents the route and openapi.json matches the app (the PUT has a `WriteFile` request body and a `FileWritten` 200) [evidence: command:unset VIRTUAL_ENV && uv run --frozen pytest tests/test_readme_api.py && python3 -c "import json,sys; d=json.load(open('openapi.json')); op=d['paths']['/api/v1/sessions/{session_id}/files/content']['put']; ok='WriteFile' in json.dumps(op['requestBody']) and 'FileWritten' in json.dumps(op['responses']['200']); sys.exit(0 if ok else 1)"]
- ac9: only `api/workspace.py` imports the wrapper package (layering pin unchanged) [evidence: test:tests/test_api_sessions.py::test_api_never_imports_k8s_or_wrapper]
- ac10: (CI only, needs Docker) the DB-backed file route tests cover agent choice and no ready agent on the PUT route [evidence: command:unset VIRTUAL_ENV && uv run --frozen pytest tests/test_api_files.py]
- ac11: targeted Docker-free suites and lint pass [evidence: command:unset VIRTUAL_ENV && uv run --frozen pytest tests/test_api_file_write.py tests/test_readme_api.py tests/test_fake_wrapper_contract.py tests/test_origin.py tests/test_api_sessions.py::test_api_never_imports_k8s_or_wrapper && mise run lint]

#### Files

- `src/agents_orchestrator/api/workspace.py`
- `src/agents_orchestrator/api/schemas.py`
- `README.md`
- `openapi.json`
- `MEMORY.md`
- `tests/test_api_file_write.py`
- `tests/test_api_files.py`

#### Interfaces

- New route `PUT /api/v1/sessions/{session_id}/files/content?path=<rel>&agent_id=<uuid?>` in `api/workspace.py`, `dependencies=guarded`: request `schemas.WriteFile`, 200 `schemas.FileWritten`; errors as JSON envelopes: wrapper 4xx passed through (400 `invalid_path`, 400 `not_a_file`, 404 `not_found`, 409 `file_changed`, 413 `too_large`), 403 `forbidden_origin`, 404 `not_found`, 409 `agent_not_ready`, 422 `invalid_request`, 502 `wrapper_unreachable`, 502 `wrapper_error`, 503 `unavailable`.
- `api/schemas.py`: `FileStamp {mtime: str, size: int (ge=0)}` and `WriteFile {content: str, expected: FileStamp | None}` (both `extra="forbid"`, `expected` required), `FileWritten {session_id: UUID, agent_id: UUID, path: str, size: int, mtime: str}`.
- `api/workspace.py:_file_call` gains the HTTP method and an optional JSON body; the GET listing and content routes call it with `GET`.
- Kept: `resolve_agent`, `forward`, the download route of the download epic, the layering pin.
- Consumed by web-sync-write-api (openapi.json) and the web save path.

#### Expected outcome

`PUT /api/v1/sessions/<id>/files/content?path=<rel>` with `{"content", "expected"}` saves the file through the first usable agent's wrapper and answers its new stamp; a stale stamp answers 409 `file_changed`; a foreign Origin is refused before anything is forwarded; README and openapi.json document it.

#### Steps

- Red: write `tests/test_api_file_write.py` (the seven tests of the acceptance conditions) and the CI-only extensions in `tests/test_api_files.py`; run `unset VIRTUAL_ENV && uv run --frozen pytest tests/test_api_file_write.py`: fails (405, no route).
- Green: schemas, `_file_call` generalised, the route; rerun: passes.
- Docs: README `## API` section; `uv run python -m agents_orchestrator.api.openapi > openapi.json`; MEMORY.md entry; run the task's verify: passes, quote the pytest summary line. `tests/test_api_files.py` needs Docker and is left to CI.

#### Notes

- Docker-free rig: reuse the one the download epic built in `tests/test_api_file_download.py` (`create_app(make_settings(master_key=KEY), pool=<stub>)` with a stub whose `connection()` is an async context manager, `workspace.resolve_agent` monkeypatched to return a `WrapperTarget` for a real `FakeWrapper` or raise `ApiError`, `client_for(app)`); import its helpers or mirror them, do not copy them into a third place if a shared helper fits.
- The Origin test sets `allowed_origins` in `make_settings` and sends `Origin` headers; `require_allowed_origin` passes a request without Origin (`api/origin.py`).
- Assert "the wrapper receives no request" by counting requests on the fake (or an `httpx.MockTransport` preset on `app.state.wrapper_http`).
- Derive tokens at runtime (`derive_tokens(KEY.encode(), session_id).auth`), never a literal credential string (a GitGuardian false positive cost a PR in generic-any-mcp-with-git-and).
- The 409 of `file_changed` and of `agent_not_ready` share a status; clients tell them apart by code, say so in README.
- `tests/test_api_files.py`, `tests/test_workspace_proxy.py` and the contract real leg run only in CI (Docker); say so in the hand-back rather than claiming them.

- 2026-10-27 done

### S6: web editor syntax check

- Status: done
- Files: `src/editor/syntaxCheck.ts`, `src/editor/syntaxCheck.test.ts`
- Verify: `mise exec -- npx vitest run src/editor/syntaxCheck.test.ts src/layout/designRules.test.ts && mise exec -- npx tsc -b && mise run lint`
- Verified head: 1c3c4da0d5eb1d851d10b9288e7aae9e53e9ab49

#### Requirement

Epic README goal, verbatim: "Syntax highlighting for python, yaml, json, terraform and toml, plus syntax checking (errors marked) where the language allows."

Epic README non-goal, verbatim: "No hints: no autocomplete, hover info or language-server features."

User decision U4, verbatim: "(my call) 'syntax highlighting and syntax - no hints': highlighting for python, yaml, json, terraform (.tf, .tfvars, .hcl) and toml, plus syntax error marking via @codemirror/lint (json parse linter, yaml and smol-toml parser errors, lezer parse-tree error nodes for python and hcl); no autocomplete, hover or hints (minimal setup, no autocompletion extension). Other extensions open as plain text."

Design D10, verbatim: "`src/editor/syntaxCheck.ts` exports `syntaxDiagnostics(language, state)`, a pure function of the `EditorState`, and `syntaxChecker(language)`, the extension `[linter(view => syntaxDiagnostics(language, view.state)), lintGutter()]` (default 750 ms delay). Per language: json, the `jsonParseLinter` of `@codemirror/lang-json` (B7); yaml, `parseAllDocuments` of `yaml`, one diagnostic per document error at its `pos` range, so `---` streams are not errors (B8); toml, `smol-toml` `parse`, one diagnostic at the `TomlError` line and column (B9); python and terraform, one diagnostic per Lezer error node of the full tree (`ensureSyntaxTree`; a parse that does not finish within its timeout gives no diagnostics rather than false ones) (B10); plain text none. Marks show in RO and RW tabs. No `autocompletion()`, no hover tooltips, no `basicSetup`; `python()`'s completion sources stay inert without the autocompletion extension (B18)."

Scope (agents-web):
- `src/editor/syntaxCheck.ts` (new): `syntaxDiagnostics(language: LanguageId, state: EditorState): Diagnostic[]` and `syntaxChecker(language: LanguageId): Extension`, using `LanguageId` and the language support of `src/editor/languages.ts` (web-editor-languages).
- `src/editor/syntaxCheck.test.ts` (new): the tests below, run in the node environment on `EditorState.create({doc, extensions: [languageFor(path).support]})`, with no view.

#### Acceptance conditions

- ac1: JSON: `{"a": 1}` has no diagnostic; `{"a": 1,}` has one error diagnostic inside the document (new) [evidence: command:mise exec -- npx vitest run src/editor/syntaxCheck.test.ts -t 'json']
- ac2: YAML: a two-document stream separated by `---` has no diagnostic; a mapping with a bad indentation or an unclosed flow sequence has at least one error diagnostic on the offending line (new) [evidence: command:mise exec -- npx vitest run src/editor/syntaxCheck.test.ts -t 'yaml']
- ac3: TOML: a valid table with keys has no diagnostic; a duplicate key or a missing value has one error diagnostic on the line smol-toml reports (new) [evidence: command:mise exec -- npx vitest run src/editor/syntaxCheck.test.ts -t 'toml']
- ac4: Python: a valid function with a class and a comprehension has no diagnostic; `def f(:` has at least one error diagnostic on line 1 (new) [evidence: command:mise exec -- npx vitest run src/editor/syntaxCheck.test.ts -t 'python']
- ac5: Terraform: a valid file with `terraform`, `variable`, `resource` and `locals` blocks, interpolations, a heredoc and a `for` expression has no diagnostic; a block missing its closing brace has at least one error diagnostic (new) [evidence: command:mise exec -- npx vitest run src/editor/syntaxCheck.test.ts -t 'terraform']
- ac6: plain text never has a diagnostic, whatever its content (new) [evidence: command:mise exec -- npx vitest run src/editor/syntaxCheck.test.ts -t 'plain']
- ac7: every diagnostic has severity `error`, `from` < `to` and both inside the document, so a mark is visible even at the end of the file (new) [evidence: command:mise exec -- npx vitest run src/editor/syntaxCheck.test.ts -t 'diagnostic ranges']
- ac8: `syntaxChecker(language)` is the linter plus the lint gutter: a view-less `EditorState` built with it and given diagnostics through `setDiagnostics` reports them through `diagnosticCount`; no file under `src` imports `@codemirror/autocomplete` (new) [evidence: command:mise exec -- npx vitest run src/editor/syntaxCheck.test.ts -t 'checker extension' && ! grep -rn '@codemirror/autocomplete' src]
- ac9: the targeted suites, the type check and lint pass [evidence: command:mise exec -- npx vitest run src/editor/syntaxCheck.test.ts src/layout/designRules.test.ts && mise exec -- npx tsc -b && mise run lint]

#### Files

- `src/editor/syntaxCheck.ts`
- `src/editor/syntaxCheck.test.ts`

#### Interfaces

- `src/editor/syntaxCheck.ts`: `export function syntaxDiagnostics(language: LanguageId, state: EditorState): Diagnostic[]`; `export function syntaxChecker(language: LanguageId): Extension` (`[linter(view => syntaxDiagnostics(language, view.state)), lintGutter()]`).
- Uses `LanguageId` and `languageFor` from `src/editor/languages.ts` (web-editor-languages).
- Consumed by web-code-editor.

#### Expected outcome

For every language the user named, a broken file gets an error diagnostic on the offending line and a valid file none; plain text is never marked; nothing offers completions or hints.

#### Steps

- Red: write `src/editor/syntaxCheck.test.ts` (node environment) with one valid and one broken sample per language plus the range and checker tests; run `mise exec -- npx vitest run src/editor/syntaxCheck.test.ts`: fails (no module).
- Green: `syntaxCheck.ts`; run the task's verify: passes, quote the vitest summary line.

#### Notes

- Rulings and their pin tests: multi-document YAML is valid (`parseAllDocuments`), pinned by the `yaml` test; an unfinished Lezer parse yields no diagnostics, not false ones (pass a timeout to `ensureSyntaxTree` and treat `null` as none), pinned by the `python` test with a valid long file; a zero-width error node at the end gets `to = from + 1` clamped inside the document, pinned by `diagnostic ranges`.
- `jsonParseLinter()` returns `(view) => Diagnostic[]` and only reads `view.state`; call it with `{ state }` cast to `EditorView`.
- smol-toml `TomlError` has 1-based `line` and `column`; map with `state.doc.line(line).from + column - 1`.
- Report, never hide, a false error on the valid Terraform sample (design: `codemirror-lang-hcl` is a 0.x community grammar); a grammar gap is a question back, not a weakened sample.

- 2026-10-27 done

### S7: orch wrapper pin write

- Status: done
- Files: `pyproject.toml`, `uv.lock`, `e2e/agent-test.Dockerfile`, `README.md`, `tests/e2e/test_e2e_kind.py`
- Verify: `unset VIRTUAL_ENV && uv run --frozen pytest tests/test_images.py tests/test_render.py && mise run lint`
- Verified head: c6860bb2419af9a90931c50e968bc6d2a3d6a8f5

#### Requirement

Design D7, verbatim: "once the wrapper change is merged on claude-code-wrapper `main`, the orchestrator pins that merge commit in the dev dependency (`pyproject.toml`, `uv.lock`), README `## Images` and `e2e/agent-test.Dockerfile` (`BASE_IMAGE`, `WRAPPER_SHA`), and the kind e2e gets a write case, so CI's integration leg and e2e run the real route. Precedent: the download epic's `orch-wrapper-pin-download` and done epic web-ui-cluster-tabs-with-fil task `wrapper-sha-pin`."

Needs a merged upstream: the claude-code-wrapper PR carrying task wrapper-file-write-route merged on `main`. Do not start before `git -C <wrapper checkout> fetch origin main` shows a `main` commit whose `src/claude_code_wrapper/api/files.py` has the `PUT` `files/content` route; the pin is that merge commit (40-character sha, image tag its first 7 characters). The orchestrator amends this task with the sha when the PR merges. The current pin (after the download epic) is replaced, not kept beside it.

Scope (agents-orchestrator):
- `pyproject.toml`: dev dependency `claude-code-wrapper @ git+https://github.com/szymonrychu/claude-code-wrapper@<sha>`; `uv.lock` refreshed with `uv lock`.
- `e2e/agent-test.Dockerfile`: `ARG BASE_IMAGE=harbor.szymonrichert.pl/containers/claude-code-wrapper:<sha7>`, `ARG WRAPPER_SHA=<sha>`.
- `README.md` `## Images`: the recommended agent image `harbor.szymonrichert.pl/containers/claude-code-wrapper:<sha7>`.
- `tests/e2e/test_e2e_kind.py`: new `test_files_write_through_api`, modelled on `test_files_list_and_read_through_api`: the agent writes a text file through its shell; the API reads it, writes new content with the loaded `mtime` and `size` (200, content read back equal), a second write with the old stamp answers 409 `file_changed`, `expected: null` overwrites, `../etc/passwd` answers 400 `invalid_path` and a missing path 404 `not_found`.


Merged (2026-10-27): claude-code-wrapper PR #6, merge commit `fb005fdd397183c42bb7f73b6cb67e17edc7a0b3`; `<sha>` is that value and `<sha7>` is `fb005fd`.

#### Acceptance conditions

- ac1: pyproject, uv.lock, README Images and the agent-test Dockerfile name the same wrapper commit, the merge commit carrying the write route [evidence: test:tests/test_images.py::test_agent_test_dockerfile_matches_dev_dependency]
- ac2: the dev dependency and README image pin agree [evidence: test:tests/test_images.py::test_ccw_dev_dependency_matches_agent_image_sha]
- ac3: the pinned wrapper package has the PUT content route [evidence: command:unset VIRTUAL_ENV && uv run --frozen python -c "import claude_code_wrapper.api.files as f, sys; sys.exit(0 if any(getattr(r, 'path', '').endswith('/files/content') and 'PUT' in getattr(r, 'methods', set()) for r in f.router.routes) else 1)"]
- ac4: (CI only, kind) the e2e write case passes against the real agent image (new) [evidence: command:mise run test:e2e]
- ac5: images and render suites and lint pass [evidence: command:unset VIRTUAL_ENV && uv run --frozen pytest tests/test_images.py tests/test_render.py && mise run lint]

#### Files

- `pyproject.toml`
- `uv.lock`
- `e2e/agent-test.Dockerfile`
- `README.md`
- `tests/e2e/test_e2e_kind.py`

#### Interfaces

- The wrapper pin (pyproject dev dependency, `uv.lock`, `e2e/agent-test.Dockerfile` `BASE_IMAGE` and `WRAPPER_SHA`, README `## Images`), all one sha: the claude-code-wrapper `main` merge commit carrying wrapper-file-write-route.
- New kind e2e case `tests/e2e/test_e2e_kind.py::test_files_write_through_api`.

#### Expected outcome

CI's integration contract leg and kind e2e build the agent image from the wrapper commit that has the write route, and the e2e proves a save, a conflict and the guards through the API.

#### Steps

- Confirm the merged upstream (the requirement's precondition) and read the merge sha.
- Change the pyproject pin, run `uv lock`; run `unset VIRTUAL_ENV && uv run --frozen pytest tests/test_images.py`: the Dockerfile and README checks fail on the old sha.
- Update the Dockerfile args and README `## Images`, add the e2e case; run the task's verify: passes, quote the pytest summary line. The e2e runs in CI only.

#### Notes

- `tests/test_images.py` ties pyproject, uv.lock, README Images and the Dockerfile to one sha (`test_ccw_dev_dependency_matches_agent_image_sha`, `test_agent_test_dockerfile_matches_dev_dependency`); `tests/test_render.py` validates rendered configs against the pinned wrapper's config schema.
- Another epic (leader-auto-handover, in progress) also moves the wrapper pin; take the newest `main` merge that carries this route, which includes the earlier changes.
- The Harbor image exists only for wrapper `main` builds; check with `regctl image digest` when credentials allow, else `scripts/e2e.sh` builds from source.
- The e2e reads the stamp from `files/content` before writing; never compute it in the test.

- 2026-10-27 amended: wrapper PR #6 merged at fb005fd

- 2026-10-27 done

### S8: web code editor

- Status: done
- Files: `src/editor/CodeEditor.tsx`, `src/editor/CodeEditor.test.tsx`
- Verify: `mise exec -- npx vitest run src/editor/CodeEditor.test.tsx src/layout/designRules.test.ts && mise exec -- npx tsc -b && mise run lint`
- Verified head: dd388de129dde2e6057a4337d850c965fd3c7b32

#### Requirement

User request (2026-10-27), verbatim: "inside "Files" in RW editor mode- support python/yaml/json/terraform/toml syntax highlighting and syntax- no hints for now"

User decision U2, verbatim: "(my call, pending user approval at the gate) CodeMirror 6 with a thin own hook, packages and versions from web-libs-docs.md (state 6.7.6, view 6.43.15, language, commands, lint, lang-python, lang-yaml, lang-json, legacy-modes toml, codemirror-lang-hcl for terraform, @lezer/highlight, smol-toml, yaml). The nomenclature guard (src/nomenclature.test.ts) is tripped by the transitive dep @marijn/find-cluster-break; the planned fix is adding exactly that package name to the guard's ALLOWED list in its own task with a test proving any other match still fails; this is a gate question for the user, keep the task in the plan."

User decision U3 (editor part), verbatim: "read-only by default with an RO/RW toggle per tab; RW enables editing and Save (button and Ctrl/Cmd+S)"

User decision U4 (hints part), verbatim: "no autocomplete, hover or hints (minimal setup, no autocompletion extension)."

Design D11, verbatim: "`src/editor/CodeEditor.tsx` (default export, so it can be lazy-loaded) creates one `EditorView` in an effect and destroys it on unmount. Props: `path` (language, D9), `doc` and `docVersion` (the editor resets to `doc`, history cleared, whenever `docVersion` changes), `readOnly`, `onChange(text)` (every doc change, full text) and `onSave()` (Mod-s while focused, always `preventDefault`, so the browser's save dialog never opens). Extensions: `lineNumbers`, `highlightSpecialChars`, `history`, `drawSelection`, `keymap` (`defaultKeymap`, `historyKeymap`, Mod-s), the language, `syntaxChecker`, the D9 theme and highlight style; `readOnly` drives one `Compartment` holding `EditorState.readOnly` and `EditorView.editable`, reconfigured in place so doc, selection and undo history survive a toggle (B12-B14). Line endings round-trip byte-exact (my call): `EditorState.lineSeparator` is `"\r\n"` when the loaded text contains `"\r\n"`, else `"\n"`, so an unedited document's `doc.toString()` equals the loaded text for LF, CRLF and mixed files. No line wrapping (code scrolls horizontally) (my call). The panel loads the component with `React.lazy`, so CodeMirror is its own build chunk and the main bundle does not grow (my call)."

Scope (agents-web):
- `src/editor/CodeEditor.tsx` (new): `export interface CodeEditorProps` and `export default function CodeEditor(props)`, built on `languageFor` (src/editor/languages.ts), `editorAppearance` (src/editor/highlight.ts) and `syntaxChecker` (src/editor/syntaxCheck.ts); the root element carries `data-testid="file-editor"`. The lazy import site is task web-file-tabs-view.
- `src/editor/CodeEditor.test.tsx` (new, `// @vitest-environment jsdom`): the tests below, with `Range.prototype.getClientRects` and `getBoundingClientRect` stubbed in the test file, the view reached with `EditorView.findFromDOM`, assertions on `view.state`, never typing into contenteditable.

#### Acceptance conditions

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

#### Files

- `src/editor/CodeEditor.tsx`
- `src/editor/CodeEditor.test.tsx`

#### Interfaces

- `src/editor/CodeEditor.tsx`:
  `export interface CodeEditorProps { path: string; doc: string; docVersion: number; readOnly: boolean; onChange: (text: string) => void; onSave: () => void }` and `export default function CodeEditor(props: CodeEditorProps): JSX.Element`; root element `data-testid="file-editor"`.
- Uses `languageFor` (src/editor/languages.ts), `editorAppearance` (src/editor/highlight.ts), `syntaxChecker` (src/editor/syntaxCheck.ts).
- Consumed by web-file-tabs-view (through `React.lazy`) and, as the stand-in's prop type, by the `FileTabs` and `FilesPanel` tests.

#### Expected outcome

A mounted `CodeEditor` shows the file with highlighting and syntax marks, is read-only until `readOnly` turns false, toggles without losing the doc or undo history, reports every change, saves on Ctrl/Cmd+S without the browser dialog, keeps line endings byte-exact and shows no hints.

#### Steps

- Probe first: mount a bare `EditorView` in a jsdom test with the `Range` stubs; if it cannot mount, stop and return that as a question (design: Assumptions), never skip or weaken a test.
- Red: write `src/editor/CodeEditor.test.tsx` (the nine behaviour tests); run `mise exec -- npx vitest run src/editor/CodeEditor.test.tsx`: fails (no module).
- Green: `CodeEditor.tsx`; run the task's verify: passes, quote the vitest summary line.

#### Notes

- Rulings and their pin tests: `lineSeparator` `"\r\n"` when the loaded text holds `"\r\n"`, else `"\n"`, pinned by `line endings round-trip`; Mod-s always `preventDefault` and calls `onSave` in both modes (the caller decides whether to save), pinned by `mod-s saves`; one `Compartment` for `EditorState.readOnly` plus `EditorView.editable`, reconfigured not recreated, pinned by `read-only toggle keeps the view`; a `docVersion` change resets the state (history cleared), pinned by `docVersion resets`.
- Keep `onChange` and `onSave` in refs so a new callback identity never recreates the view.
- jsdom: stub `Range.prototype.getClientRects` (returning an empty list) and `getBoundingClientRect` in the test file; assert through `view.state`; dispatch transactions instead of typing; `forceLinting(view)` instead of waiting the lint delay; fake timers for the "no hints" wait (web-libs-docs B23, B24).
- Extensions per design D11 only; no `basicSetup`, no `autocompletion`, no `closeBrackets`, no `EditorView.lineWrapping`, no tooltips extension.
- Keyboard test: dispatch `keydown` with `key: 's'` and `ctrlKey` or `metaKey` on `view.contentDOM`; CodeMirror's keymap maps `Mod` to Ctrl or Cmd by platform, so register both `Ctrl-s` and `Mod-s` if needed for the jsdom platform.

- 2026-10-27 done

### S9: web sync write api

- Status: done
- Files: `openapi/orchestrator.json`, `openapi/orchestrator.source`, `src/api/schema.d.ts`, `src/api/files.ts`, `src/api/files.test.ts`
- Verify: `mise exec -- npm run check:api && mise exec -- npx vitest run src/api/files.test.ts && mise exec -- npx tsc -b && mise run lint`
- Verified head: 45a1e37ccf5c6c7080e17352c433929af76b21da

#### Requirement

User decision U3, verbatim (the web client part): "new write route in the wrapper (PUT file content, UTF-8 text only, size cap = the existing file_preview_max_bytes, existing workspace path guards, optimistic concurrency via the mtime/size the editor loaded: a changed file answers 409 and the UI offers reload or overwrite) and an orchestrator forwarding route, then `npm run sync:api -- orchestrator`."

Design D8, verbatim: "after the orchestrator route lands, `npm run sync:api -- orchestrator` (vendors `openapi/orchestrator.json`, `openapi/orchestrator.source`, regenerates `src/api/schema.d.ts`), `npm run check:api` stays green, and `src/api/files.ts` gains `writeFile(sessionId, path, content, expected)` sending `PUT {base}/sessions/{id}/files/content?path=` with `{content, expected}` and answering `FileWritten`; its header comment stops saying read-only."

Scope (agents-web):
- Run `mise exec -- npm run sync:api -- orchestrator --from <agents-orchestrator tree at the commit of orch-file-write-route>` (the default `../agents-orchestrator` is the sibling integration tree; the script refuses an uncommitted `openapi.json`). Commit the three generated files as they come out; no hand edits.
- `src/api/files.ts`: `export type FileWritten`, `export type FileStamp` from the generated schema, and `writeFile(sessionId: string, path: string, content: string, expected: FileStamp | null): Promise<FileWritten>` through `request('PUT', ...)`; the header comment describes listing, reading, downloading and writing.
- `src/api/files.test.ts` (created by the download epic's web-download-icon): the new tests below.

#### Acceptance conditions

- ac1: `openapi/orchestrator.source` names the agents-orchestrator commit that carries the write route, and the vendored document has the PUT operation and its schemas [evidence: command:grep -q '"put"' openapi/orchestrator.json && grep -q 'FileWritten' openapi/orchestrator.json && grep -q 'WriteFile' openapi/orchestrator.json && grep -q 'FileStamp' openapi/orchestrator.json]
- ac2: the generated types carry the PUT operation and the three schemas [evidence: command:grep -q 'FileWritten' src/api/schema.d.ts && grep -q 'WriteFile' src/api/schema.d.ts && grep -q 'FileStamp' src/api/schema.d.ts]
- ac3: the generated schemas match the vendored documents [evidence: command:mise exec -- npm run check:api]
- ac4: `writeFile('c1', 'src/a b.txt', 'x\n', {mtime, size})` sends `PUT` to the relative `${base()}/sessions/c1/files/content?path=src%2Fa+b.txt` with header `Content-Type: application/json` and body `{"content":"x\n","expected":{"mtime":...,"size":...}}`, and resolves to the parsed `FileWritten`; `expected: null` is sent as `null` (new) [evidence: command:mise exec -- npx vitest run src/api/files.test.ts -t 'writeFile sends']
- ac5: a 409 answer with code `file_changed` rejects with an `ApiError` whose `status` is 409 and `code` is `file_changed` (new) [evidence: command:mise exec -- npx vitest run src/api/files.test.ts -t 'writeFile conflict']
- ac6: the header comment of `src/api/files.ts` no longer says read-only [evidence: command:! grep -qi 'read-only' src/api/files.ts]
- ac7: the files API suite, the type check and lint pass [evidence: command:mise exec -- npx vitest run src/api/files.test.ts && mise exec -- npx tsc -b && mise run lint]

#### Files

- `openapi/orchestrator.json`
- `openapi/orchestrator.source`
- `src/api/schema.d.ts`
- `src/api/files.ts`
- `src/api/files.test.ts`

#### Interfaces

- Generated: `openapi/orchestrator.json`, `openapi/orchestrator.source` (`agents-orchestrator <sha>`), `src/api/schema.d.ts` (`paths['/api/v1/sessions/{session_id}/files/content']['put']`, `components['schemas']['WriteFile' | 'FileStamp' | 'FileWritten']`).
- `src/api/files.ts`: `export type FileStamp = components['schemas']['FileStamp']`, `export type FileWritten = components['schemas']['FileWritten']`, `writeFile(sessionId: string, path: string, content: string, expected: FileStamp | null): Promise<FileWritten>`, sent with `request('PUT', ...)` to `/sessions/<id>/files/content?path=<rel>` with the body `{ content, expected }`.
- Kept: `listFiles`, `readFile`, `fileDownloadUrl` (download epic) unchanged.
- Consumed by web-file-tabs-state.

#### Expected outcome

The web client's generated types match the orchestrator commit carrying the write route, `npm run check:api` is green, and `writeFile` saves through the relative base path.

#### Steps

- Run `mise exec -- npm run sync:api -- orchestrator --from <agents-orchestrator tree at orch-file-write-route's commit>`: it prints the gen:api output and exits 0.
- Red: add the two `writeFile` tests to `src/api/files.test.ts` (fetch stubbed as the file already does for `fileDownloadUrl`, or `vi.stubGlobal('fetch', ...)` as `src/api/client.test.ts` does); run `mise exec -- npx vitest run src/api/files.test.ts`: fails (no export).
- Green: `writeFile` and the types; run the task's verify: passes, quote the vitest summary line.

#### Notes

- The default `../agents-orchestrator` is the sibling integration tree; the script refuses an `openapi.json` with uncommitted changes.
- If the regenerated types break compilation elsewhere (drift since the download epic's sync), report it as a `discovered` entry; do not patch it here.
- No hand edits to generated files. `request` already sets `Content-Type: application/json` when a body is given (`src/api/client.ts:requestAt`).

- 2026-10-27 done

### S10: orch write body cap

- Status: done
- Files: `src/agents_orchestrator/api/schemas.py`, `src/agents_orchestrator/api/workspace.py`, `tests/test_api_file_write.py`, `openapi.json`, `README.md`
- Verify: `unset VIRTUAL_ENV && uv run --frozen pytest tests/test_api_file_write.py tests/test_readme_api.py && mise run lint`
- Verified head: 1cd6f3b877c50d6fa3901e8566d1fe31323b5156

#### Requirement

Epic security review finding (2026-10-27), verbatim: "agents-orchestrator/src/agents_orchestrator/api/schemas.py:289-296 (WriteFile); api/workspace.py:349-374. evidence: `content: str` has no max_length; the route is `body: schemas.WriteFile`, and the 1 MiB cap is enforced only by the wrapper (files.py write_file: `if len(data) > max_bytes`). impact: the orchestrator and the wrapper each buffer and parse the whole body before the cap check. A client that reaches the route can force large allocations on both. fix: add max_length or a Content-Length guard on the orchestrator."

Scope (agents-orchestrator): the file-write route refuses a request whose body is larger than the wrapper's write cap can ever accept (1 MiB of UTF-8 content plus JSON overhead, worst-case escaping included) before parsing it fully and before forwarding anything to the wrapper, with 413 and the same error envelope the API uses elsewhere; a content at exactly the wrapper's cap is still forwarded; openapi.json and README stay in sync if the schema changes. The wrapper side is unchanged (noted, not doing now).

#### Acceptance conditions

- ac1: an oversized write body is refused with 413 before any wrapper request is made [evidence: test:tests/test_api_file_write.py::test_write_body_too_large]
- ac2: content at the wrapper's cap (1 MiB of UTF-8) is still forwarded [evidence: test:tests/test_api_file_write.py::test_write_at_cap_forwarded]
- ac3: openapi.json matches the generated document and the README API check passes [evidence: test:tests/test_readme_api.py]
- ac4: the targeted suites and lint pass [evidence: command:unset VIRTUAL_ENV && uv run --frozen pytest tests/test_api_file_write.py tests/test_readme_api.py && mise run lint]

#### Files

- `src/agents_orchestrator/api/schemas.py`
- `src/agents_orchestrator/api/workspace.py`
- `tests/test_api_file_write.py`
- `openapi.json`
- `README.md`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

What is true and observable when the task is done.

#### Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

#### Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.

- 2026-10-27 done

### S11: web file tabs state

- Status: done
- Files: `src/files/useFileTabs.ts`, `src/files/useFileTabs.test.ts`
- Verify: `mise exec -- npx vitest run src/files/useFileTabs.test.ts && mise exec -- npx tsc -b && mise run lint`
- Verified head: 92529d1fdc3e4256246a68db975bc3dedfe26b8c

#### Requirement

Epic README goals, verbatim: "Multiple files open at once as tabs, styled like the terminal tabs (closable, scrollable)." and "RO/RW editor mode: read-only by default, RW lets the user edit and save the file back to the agent's workspace (new write route in claude-code-wrapper and orchestrator)."

Epic README non-goal, verbatim: "Open tabs are not persisted across page reloads."

User decision U3, verbatim: "(my call) 'RW editor mode': read-only by default with an RO/RW toggle per tab; RW enables editing and Save (button and Ctrl/Cmd+S); new write route in the wrapper (PUT file content, UTF-8 text only, size cap = the existing file_preview_max_bytes, existing workspace path guards, optimistic concurrency via the mtime/size the editor loaded: a changed file answers 409 and the UI offers reload or overwrite) and an orchestrator forwarding route, then `npm run sync:api -- orchestrator`. Binary and too_large files open read-only with the current note, no editor."

User decision U5 (tabs part), verbatim: "tabs mirror TerminalPanel (MUI Tabs scrollable, closable tab with IconButton aria-label 'Close <name>', closing picks the neighbour, all tabs stay mounted), one tab per path (re-opening focuses it), unsaved changes mark the tab and closing a dirty tab asks to confirm. Tabs are per session, not persisted across reloads."

User decision U6, verbatim: "(my call) Live refresh: an open RO tab refetches when the tree reports a changed mtime|size (existing behaviour); a dirty RW tab never auto-reloads, it shows a 'changed on disk' notice instead."

Design D12 (state part), verbatim: "`src/files/useFileTabs.ts` holds the tabs of one session: path, name, kind (`loading`, `text`, `binary`, `too_large`, `other`, `error`), mode (`ro` default, `rw`), the loaded or saved text and its stamp (the baseline `{mtime, size}`), dirty (current text differs from the baseline text), saving, save error, `conflict` (a save answered 409 `file_changed`), `changedOnDisk` (the file changed while dirty), `doc`/`docVersion` for the editor. One tab per path: opening an open path focuses it without a refetch. Closing picks the neighbour (`rest[min(index, len - 1)]`, as `TerminalPanel`). RO is refused while the tab is dirty (save, reload or close first) (my call). Save sends `writeFile(..., baseline)`; success makes the answer the new baseline; 409 `file_changed` sets `conflict`, offering Reload (refetch, edits discarded) or Overwrite (`expected: null`); any other error shows inline as `<code>: <message>`. Stale answers (a tab closed or reloaded again meanwhile) are dropped. Tabs are per session and in memory only: a module-level store keyed by session id keeps each session's tabs (text, mode, dirty state, baseline) for the page's lifetime, so switching to another session and back restores them (the Workspace remounts the panel per session); a reload starts empty (my call, so a session switch never loses edits silently)."

Design D14, verbatim: "for each open tab the panel feeds the hook the `mtime|size` stamp of its entry in the loaded tree listings. The hook acts when that stamp differs from the last stamp it saw for the path (initialised to the baseline when the tab opens) and from the tab's baseline: an RO tab or a clean RW tab refetches (mode kept); a dirty RW tab never auto-reloads, it sets `changedOnDisk`, shown as a notice with Reload and Keep editing (my call: clean RW tabs refetch too, no edit can be lost). A save's own new stamp equals the baseline, so it triggers nothing. An agent write event for the path (`fileEvents` `written`) applies the same rule. A refetch that answers another kind (binary, too_large, error) turns the tab into that note."

Scope (agents-web):
- `src/files/useFileTabs.ts` (new): `useFileTabs(sessionId)` and its types, built on `readFile` and `writeFile` (src/api/files.ts) and `errorText` (src/files/useFileTree.ts).
- `src/files/useFileTabs.test.ts` (new, `// @vitest-environment jsdom`, `renderHook`, `../api/files` mocked with `vi.hoisted`): the tests below.

#### Acceptance conditions

- ac1: `open(path, type)` adds a tab named by the last path segment, makes it active and loads it with `readFile`; a `text` answer gives kind `text` with `doc` the content, mode `ro` and the baseline `{mtime, size}`; `binary` and `too_large` answers give those kinds; type `other` gives kind `other` without a `readFile` call; a rejected read gives kind `error` with `<code>: <message>`; opening an open path focuses it and calls `readFile` no more (new) [evidence: command:mise exec -- npx vitest run src/files/useFileTabs.test.ts -t 'open and focus']
- ac2: closing the active tab activates its right neighbour, or the left one when it was last, and none when it was the only one; closing an inactive tab keeps the active one; a read answering after its tab closed changes nothing (new) [evidence: command:mise exec -- npx vitest run src/files/useFileTabs.test.ts -t 'close picks the neighbour']
- ac3: `edit(path, text)` marks the tab dirty when the text differs from the baseline text and clean again when it equals it; `setMode(path, 'ro')` is refused while dirty and the tab stays `rw`; a clean tab switches both ways (new) [evidence: command:mise exec -- npx vitest run src/files/useFileTabs.test.ts -t 'dirty and mode']
- ac4: `save(path)` calls `writeFile(sessionId, path, text, baseline)` with `saving` true until it settles; success makes the answer the baseline and the tab clean; a 409 `file_changed` sets `conflict` and keeps the text and dirty mark; another error sets the save error to `<code>: <message>`; `overwrite(path)` calls `writeFile` with `null` and clears `conflict` on success; `reload(path)` refetches, bumps `docVersion`, drops the edits and clears `conflict` and `changedOnDisk` (new) [evidence: command:mise exec -- npx vitest run src/files/useFileTabs.test.ts -t 'save conflict overwrite reload']
- ac5: `observe(stampOf)` with a changed `mtime|size` stamp refetches an RO tab and a clean RW tab (mode kept, `docVersion` bumped); for a dirty RW tab it sets `changedOnDisk` and does not call `readFile`; the stamp of the tab's own save triggers nothing; an unchanged stamp, a null stamp (entry not listed) and a symlink entry's stable stamp after the first refetch trigger nothing more; a refetch answering `binary` turns the tab into that kind (new) [evidence: command:mise exec -- npx vitest run src/files/useFileTabs.test.ts -t 'live refresh rules']
- ac6: `written(path)` applies the same rule: refetch for a clean tab, `changedOnDisk` for a dirty one, nothing for a path with no tab (new) [evidence: command:mise exec -- npx vitest run src/files/useFileTabs.test.ts -t 'written events']
- ac7: unmounting and mounting the hook again for the same session restores its tabs, the active tab, each mode, dirty text and baseline without a `readFile` call; another session starts with no tab; a `sessionId` change on a mounted hook shows the other session's tabs and back (new) [evidence: command:mise exec -- npx vitest run src/files/useFileTabs.test.ts -t 'tabs per session']
- ac8: the targeted suite, the type check and lint pass [evidence: command:mise exec -- npx vitest run src/files/useFileTabs.test.ts && mise exec -- npx tsc -b && mise run lint]

#### Files

- `src/files/useFileTabs.ts`
- `src/files/useFileTabs.test.ts`

#### Interfaces

- `src/files/useFileTabs.ts`:
  - `export type TabKind = 'loading' | 'text' | 'binary' | 'too_large' | 'other' | 'error'`, `export type TabMode = 'ro' | 'rw'`.
  - `export interface FileTab { path: string; name: string; kind: TabKind; file: FileContent | null; error: string | null; mode: TabMode; baseline: FileStamp | null; doc: string; docVersion: number; dirty: boolean; saving: boolean; saveError: string | null; conflict: boolean; changedOnDisk: boolean }`.
  - `export interface FileTabs { tabs: FileTab[]; active: string | null; open(path: string, type: FileEntry['type']): void; focus(path: string): void; close(path: string): void; setMode(path: string, mode: TabMode): void; edit(path: string, text: string): void; save(path: string): void; overwrite(path: string): void; reload(path: string): void; keepEditing(path: string): void; observe(stampOf: (path: string) => string | null): void; written(path: string): void }`.
  - `export function useFileTabs(sessionId: string): FileTabs`.
- Uses `readFile`, `writeFile`, `FileContent`, `FileStamp`, `FileEntry` (src/api/files.ts, web-sync-write-api) and `errorText` (src/files/useFileTree.ts).
- Consumed by web-file-tabs-view and web-files-split-layout.

#### Expected outcome

One hook owns every open file of a session: opening, focusing, closing with the neighbour rule, RO/RW, unsaved text, saves with the loaded stamp, conflicts with reload or overwrite, and the live refresh rules, and it gives a session's tabs back when the user returns to it.

#### Steps

- Red: write `src/files/useFileTabs.test.ts` (seven behaviour tests, `renderHook` under jsdom, `readFile` and `writeFile` mocked); run `mise exec -- npx vitest run src/files/useFileTabs.test.ts`: fails (no module).
- Green: `useFileTabs.ts`; run the task's verify: passes, quote the vitest summary line.

#### Notes

- Rulings and their pin tests: RO refused while dirty, pinned by `dirty and mode`; clean RW tabs refetch like RO ones and dirty tabs only get `changedOnDisk`, pinned by `live refresh rules`; the last seen stamp starts at the baseline when a tab opens and is never reset by a reload (so a symlink, whose listing stamp is the link's own, refetches at most once), pinned by `live refresh rules`; dirty means the text differs from the baseline text (undo back to it is clean), pinned by `dirty and mode`; the store keeps tabs per session id for the page's lifetime, pinned by `tabs per session`.
- `keepEditing(path)` clears `changedOnDisk` and keeps the edits; a later save then answers 409 and offers Overwrite.
- Keep per-tab text out of React state if it helps (a ref map), but `dirty` flips must re-render; typing must not re-render on every keystroke beyond that.
- Drop stale answers with a per-tab request token, as `FilesPanel.openFile` does today with `previewToken`.
- Export a reset of the module store for tests only if needed; tests may simply use distinct session ids.
- `observe` receives a lookup built by the panel from `state.dirs`; the hook never fetches listings itself (do-not-build: a second listing poll).

- 2026-10-27 done

### S12: web file tabs view

- Status: done
- Files: `src/files/FileTabs.tsx`, `src/files/FileTabs.test.tsx`, `MEMORY.md`
- Verify: `mise exec -- npx vitest run src/files/FileTabs.test.tsx src/layout/designRules.test.ts && mise exec -- npx tsc -b && mise run lint`
- Verified head: 618d5dae343d4deb88a08351f660e49d38ba62ab

#### Requirement

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

#### Acceptance conditions

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

#### Files

- `src/files/FileTabs.tsx`
- `src/files/FileTabs.test.tsx`
- `MEMORY.md`

#### Interfaces

- `src/files/FileTabs.tsx`: `export function FileTabs({ tabs }: { tabs: FileTabs }): JSX.Element` (the `useFileTabs` result type); `const CodeEditor = lazy(() => import('../editor/CodeEditor'))`.
- Test ids kept from today's preview: `file-preview-note`, `file-preview-error`; new: `file-editor` (inside `CodeEditor`), `file-tab-path` (the toolbar path).
- Uses `ConfirmDialog` (src/layout/ConfirmDialog.tsx), `TOKENS`, `MONO_FONT` (src/theme.ts).
- Consumed by web-files-split-layout.

#### Expected outcome

Open files show as terminal-style tabs: closable, scrollable, all mounted, dirty ones marked and confirmed on close; text tabs have the path, the RO/RW toggle, Save and the editor; conflicts and changes on disk show as notices with their actions; the editor loads as its own chunk.

#### Steps

- Red: write `src/files/FileTabs.test.tsx` (seven behaviour tests, `CodeEditor` stand-in via `vi.mock('../editor/CodeEditor', ...)`, the `FileTabs` api as `vi.fn()`s over fixture tabs); run `mise exec -- npx vitest run src/files/FileTabs.test.tsx`: fails (no module).
- Green: `FileTabs.tsx`; rerun: passes.
- Run `mise exec -- npm run build` and read the chunk sizes; MEMORY.md entry; run the task's verify: passes, quote the vitest summary line.

#### Notes

- Mirror `src/terminal/TerminalPanel.tsx:132-203` for the strip and the mounted panels; the close button's `stopPropagation` precedent is `TerminalPanel.tsx:146-149`.
- The stand-in in the test must take the real `CodeEditorProps` (import the type) so it cannot drift from the component (retro: fakes encoding a wrong assumption).
- Rulings and their pin tests: ` *` and `data-dirty` mark, pinned by `dirty mark`; Save and Ctrl/Cmd+S only in RW with changes and not while saving, pinned by `mode toggle and save button` and `keyboard save`; Reload and Overwrite on a conflict, Reload and Keep editing on a change on disk, pinned by `notices`.
- designRules: `aria-label` on IconButtons (never `title=`), no decorative Unicode (the dirty mark is an ASCII `*`), spacing on the 0.5 grid, colours from theme palette paths.
- The ToggleButtonGroup's RO button is disabled while dirty (the hook refuses it too).

- 2026-10-27 done: ac8 (editor chunk) moved to web-files-split-layout ac13 by orchestrator ruling

### S13: web files split layout

- Status: done
- Files: `src/files/FilesPanel.tsx`, `src/files/FilesPanel.test.tsx`, `src/layout/Workspace.tsx`, `MEMORY.md`
- Verify: `mise exec -- npx vitest run src/files/FilesPanel.test.tsx src/files/FileTabs.test.tsx src/files/useFileTabs.test.ts src/layout/Workspace.test.tsx src/layout/designRules.test.ts src/nomenclature.test.ts && mise exec -- npx tsc -b && mise run lint`
- Verified head: 8a20af29af3e61beee7396475d627ad485e1174d

#### Requirement

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

#### Acceptance conditions

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

- ac13: the production build emits the editor as its own chunk, now that FilesPanel mounts FileTabs (moved from web-file-tabs-view ac8, which could not pass before this task) [evidence: command:mise exec -- npm run build 2>&1 | grep -qE 'assets/CodeEditor-[^ ]+\.js']

#### Files

- `src/files/FilesPanel.tsx`
- `src/files/FilesPanel.test.tsx`
- `src/layout/Workspace.tsx`
- `MEMORY.md`

#### Interfaces

- `src/files/FilesPanel.tsx:FilesPanel({ sessionId })` unchanged signature; renders `data-testid="files-split"` (`data-orientation` `horizontal` or `vertical`) with the tree panel first and `FileTabs` second.
- `src/layout/Workspace.tsx`: `export { Divider, DIVIDER_WIDTH }` (no behaviour change).
- Uses `useFileTabs` (web-file-tabs-state), `FileTabs` (web-file-tabs-view), `useLayout` (src/layout/useLayout.ts), `useFileTree`, `createFileEvents`, and the download epic's `Row` trailing action.

#### Expected outcome

The Files panel shows the tree on the left (above on a phone) and the open files on the right as tabs; a file click opens or focuses its tab; live refresh updates clean tabs and never overwrites unsaved edits; the single preview is gone.

#### Steps

- Red: add the five new tests and rewrite the three named tests in `src/files/FilesPanel.test.tsx` (CodeEditor stand-in, `writeFile` in the hoisted mock, `useLayout` mocked); run `mise exec -- npx vitest run src/files/FilesPanel.test.tsx`: the new and rewritten tests fail.
- Green: the split, the hook and `FileTabs` wiring, the stamp lookup and `written` routing, the preview removal, the `Divider` export; rerun: passes.
- MEMORY.md entry; run the task's verify: passes, quote the vitest summary line.

#### Notes

- Tests no longer accurate, and why (the requirement's list): `preview_kinds` (one `<pre>` preview at a time), `symlink_previews_and_escape_error` (one preview), `preview_dropped_on_session_change` (reads the removed `<pre>`, and tabs now live per session). Every other test passes unchanged; if another one fails, report it rather than editing it.
- The stand-in renders `doc` as text inside `data-testid="file-editor"`, so `screen.findByText('v1')` in `preview refetch when the entry mtime or size changes` and `event_driven_refresh a written file open in the preview is refetched on the result` keeps working unchanged.
- The stamp lookup returns `<mtime>|<size>` of the entry in `state.dirs[<parent>]`, or null when the entry is not listed: the same expression the removed preview effect used (FilesPanel.tsx:153-167).
- react-resizable-panels: a `Separator` needs an inline `style={{ flexBasis }}` (MEMORY 2026-10-24); nested `Group`s inside a Workspace `Panel` are supported.
- jsdom has no media queries: mock `../layout/useLayout` per test (`'desktop'`, `'phone'`).
- Workspace sizes (25/45/30) stay as they are (design Non-goals).

- 2026-10-27 amended: carry web-file-tabs-view ac8 (editor chunk) which only passes once FilesPanel mounts FileTabs

- 2026-10-27 done

### S14: web symlink tab stamps

- Status: done
- Files: `src/files/useFileTabs.ts`, `src/files/useFileTabs.test.ts`, `src/files/FilesPanel.tsx`
- Verify: `mise exec -- npx vitest run src/files && mise exec -- npx tsc -b && mise run lint`
- Verified head: 4c2690c948c72b6690bebf8dff55375f63a9100b

#### Requirement

Epic review finding (whole-epic reviewer, 2026-10-27), verbatim: "src/files/useFileTabs.ts:123 (`answer` seeds `e.seen`; `observe` at ~l.281). The first stamp comes from the content answer, which is the target's `mtime|size`. The tree listing stamps a symlink entry by itself (wrapper `files.py` `entry.stat(follow_symlinks=False)`, size null), so the first `observe` always sees a change. A dirty RW tab on a symlink gets a false "changed on disk" notice. A clean RW tab is refetched, which resets the editor and its undo history. Later edits to the target are never detected through the listing. The save's 409 still protects the file. Fix: seed `seen` from the first listing stamp, as the old FilesPanel did, or skip `observe` for symlinks."

Scope audit duplicate (2026-10-27), verbatim: "The `mtime|size` stamp format is spelled twice: src/files/FilesPanel.tsx:113 builds it as `${e.mtime}|${e.size}`; src/files/useFileTabs.ts:97 has `stampKey`, which is not exported. Suggested task: export `stampKey` and use it in `FilesPanel`."

Scope (agents-web): a tab opened on a symlink never gets a false "changed on disk" notice or a refetch from the first listing observation; the live-refresh comparison uses the same stamp source on both sides (listing stamp vs listing stamp), so a change to the listed entry is still detected; `stampKey` is exported from useFileTabs.ts and FilesPanel.tsx uses it instead of its own template string. The existing test at useFileTabs.test.ts:332 ("refetches once") is no longer accurate for symlinks and is updated with the reason stated in the commit.

#### Acceptance conditions

- ac1: a dirty RW tab opened on a symlink gets no "changed on disk" notice from the first listing observation, and a clean one is not refetched [evidence: test:src/files/useFileTabs.test.ts::symlink tab first observation is not a change]
- ac2: after the first observation, a changed listing stamp for the same entry still triggers the live-refresh behaviour (notice when dirty, refetch when clean) [evidence: test:src/files/useFileTabs.test.ts::symlink tab later listing change is detected]
- ac3: FilesPanel builds stamps only through the exported stampKey [evidence: command:grep -q 'export function stampKey\|export const stampKey' src/files/useFileTabs.ts && ! grep -qE '\$\{[a-z]+\.mtime\}\|\$\{[a-z]+\.size\}' src/files/FilesPanel.tsx]
- ac4: the targeted suites, type check and lint pass [evidence: command:mise exec -- npx vitest run src/files && mise exec -- npx tsc -b && mise run lint]

#### Files

- `src/files/useFileTabs.ts`
- `src/files/useFileTabs.test.ts`
- `src/files/FilesPanel.tsx`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

What is true and observable when the task is done.

#### Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

#### Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.

- 2026-10-27 done

## Files to delete

none recorded in the epic format

## Final verify

none recorded in the epic format

## After merge

none
