---
title: web editor languages
status: done
repo: agents-web
value: "python, yaml, json, terraform and toml files get their language and theme-coloured highlighting"
files: [package.json, package-lock.json, src/theme.ts, src/editor/languages.ts, src/editor/highlight.ts, src/editor/languages.test.ts, MEMORY.md]
verify: "mise exec -- npx vitest run src/editor/languages.test.ts src/layout/designRules.test.ts src/nomenclature.test.ts && mise exec -- npx tsc -b && mise run lint"
depends_on: [web-nomenclature-allowlist]
model: opus
review: ""
verified_head: 0ed55f27897b16d29830ba6aebc2a0dbc338b9b0
points: 5
expected_minutes: 11
expected_tokens: 1858483
points_actual: 3
actual_minutes: 7
actual_tokens: 1919629
actual_roles: "impl 6, review 1"
actual_role_tokens: "impl 1827299, review 92330"
---

# web editor languages

## Requirement

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

## Acceptance conditions

- ac1: `package.json` `dependencies` hold the D1 packages at `^` ranges of the listed versions and `codemirror-lang-hcl` at exactly `0.2.0`, `yaml` moved from `devDependencies` to `dependencies`, and no `codemirror`, `@uiw/react-codemirror`, `@codemirror/autocomplete` or `monaco-editor` entry [evidence: command:node -e "const p=require('./package.json');const d=p.dependencies,dv=p.devDependencies||{};const want={'@codemirror/state':'^6.7.6','@codemirror/view':'^6.43.15','@codemirror/language':'^6.13.1','@codemirror/commands':'^6.11.1','@codemirror/lint':'^6.9.7','@codemirror/lang-python':'^6.2.1','@codemirror/lang-yaml':'^6.1.3','@codemirror/lang-json':'^6.0.2','@codemirror/legacy-modes':'^6.5.5','codemirror-lang-hcl':'0.2.0','@lezer/highlight':'^1.2.5','smol-toml':'^1.9.1','yaml':'^2.9.1'};const bad=Object.entries(want).filter(([k,v])=>d[k]!==v).concat(['codemirror','@uiw/react-codemirror','@codemirror/autocomplete','monaco-editor'].filter(k=>d[k]||dv[k]).map(k=>[k,'present'])).concat(dv.yaml?[['yaml','still a devDependency']]:[]);if(bad.length){console.error(bad);process.exit(1)}"]
- ac2: the lockfile holds exactly one `@codemirror/state` [evidence: command:node -e "const l=require('./package-lock.json');const n=Object.keys(l.packages).filter(k=>k.endsWith('node_modules/@codemirror/state')).length;process.exit(n===1?0:1)"]
- ac3: the nomenclature guard passes with the new lockfile [evidence: command:mise exec -- npx vitest run src/nomenclature.test.ts]
- ac4: `languageFor` maps `.py` and `.pyi` to python, `.yaml` and `.yml` to yaml, `.json` and `main.tf.json` to json, `.tf`, `.tfvars` and `.hcl` to terraform, `.toml` to toml, case-insensitively (`SETUP.PY`), and `README.md`, `Makefile`, `notes.txt` and `.env` to plain with no language extension (new) [evidence: command:mise exec -- npx vitest run src/editor/languages.test.ts -t 'languageFor']
- ac5: for each of the five languages a sample document parsed with its language yields at least one token styled by `editorHighlight` (python `def`, yaml key, json string, terraform block keyword, toml key) (new) [evidence: command:mise exec -- npx vitest run src/editor/languages.test.ts -t 'highlights every language']
- ac6: every colour in `editorHighlight` and `editorChrome` is a value of `syntaxPalette` or `TOKENS` from `src/theme.ts` (new) [evidence: command:mise exec -- npx vitest run src/editor/languages.test.ts -t 'colours from the theme']
- ac7: the design rules hold for the new and changed files (no colour literal outside `theme.ts`) [evidence: command:mise exec -- npx vitest run src/layout/designRules.test.ts]
- ac8: MEMORY.md records the decision [evidence: command:grep -q 'file-editor-with-tabs-and-hi' MEMORY.md && grep -q 'find-cluster-break' MEMORY.md && grep -q 'codemirror-lang-hcl' MEMORY.md]
- ac9: the targeted suites, the type check and lint pass [evidence: command:mise exec -- npx vitest run src/editor/languages.test.ts src/layout/designRules.test.ts src/nomenclature.test.ts && mise exec -- npx tsc -b && mise run lint]

## Files

- `package.json`
- `package-lock.json`
- `src/theme.ts`
- `src/editor/languages.ts`
- `src/editor/highlight.ts`
- `src/editor/languages.test.ts`
- `MEMORY.md`

## Interfaces

- `src/theme.ts:syntaxPalette` (keys `keyword`, `string`, `number`, `comment`, `property`, `type`, `function`, `operator`, `punctuation`, `atom`, `invalid`), `as const`, colour literals allowed here only.
- `src/editor/languages.ts`: `export type LanguageId = 'python' | 'yaml' | 'json' | 'terraform' | 'toml' | 'plain'`; `export function languageFor(path: string): { id: LanguageId; support: Extension }` (`support` is `[]` for plain).
- `src/editor/highlight.ts`: `export const editorHighlight: HighlightStyle`, `export const editorChrome: Extension` (`EditorView.theme(..., { dark: true })`), `export const editorAppearance: Extension`.
- Consumed by web-editor-syntax-check and web-code-editor.

## Expected outcome

The CodeMirror packages are installed with one `@codemirror/state`, the nomenclature guard stays green, every one of the five languages is recognised from the file name and highlighted in theme colours, and other files are plain text.

## Steps

- Install: `mise exec -- npm install @codemirror/state@^6.7.6 @codemirror/view@^6.43.15 @codemirror/language@^6.13.1 @codemirror/commands@^6.11.1 @codemirror/lint@^6.9.7 @codemirror/lang-python@^6.2.1 @codemirror/lang-yaml@^6.1.3 @codemirror/lang-json@^6.0.2 @codemirror/legacy-modes@^6.5.5 @lezer/highlight@^1.2.5 smol-toml@^1.9.1 yaml@^2.9.1` and `mise exec -- npm install --save-exact codemirror-lang-hcl@0.2.0`; remove `yaml` from `devDependencies`; check ac1 and ac2; run `mise exec -- npx vitest run src/nomenclature.test.ts`: passes (needs web-nomenclature-allowlist).
- Red: write `src/editor/languages.test.ts` (node environment); run `mise exec -- npx vitest run src/editor/languages.test.ts`: fails (no module).
- Green: `syntaxPalette`, `languages.ts`, `highlight.ts`; rerun: passes.
- MEMORY.md entry; run the task's verify: passes, quote the vitest summary line.

## Notes

- Highlight test: parse with the language's parser (`pythonLanguage.parser.parse`, `jsonLanguage.parser`, `yamlLanguage.parser`, `hclLanguage.parser`) or, for the toml stream language, `ensureSyntaxTree(EditorState.create({doc, extensions: [support]}), len, 1000)`, then `highlightTree(tree, editorHighlight, cb)` from `@lezer/highlight`.
- The colour test reads the colours out of `editorHighlight.specs` and the chrome spec; keep the chrome spec an exported object so it can be inspected.
- `@codemirror/legacy-modes/mode/toml` exports `toml`; `codemirror-lang-hcl` exports `hcl()` and `hclLanguage`.
- No `basicSetup`, no `defaultHighlightStyle` (light theme), no `@codemirror/autocomplete` import.
- If the markdown epic already added a code palette to `theme.ts`, reuse its hues rather than adding a near-duplicate set.
- `package-lock.json` is guarded by the nomenclature test; after install, `grep -inE 'c[l]uster|agent[-_]orchestrator' package-lock.json` must show only `find-cluster-break` lines.

- 2026-10-27 done
