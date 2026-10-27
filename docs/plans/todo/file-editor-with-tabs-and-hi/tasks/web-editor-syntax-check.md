---
title: web editor syntax check
status: todo
repo: agents-web
value: "syntax errors in the five languages are marked in the editor, with no hints"
files: [src/editor/syntaxCheck.ts, src/editor/syntaxCheck.test.ts]
verify: "mise exec -- npx vitest run src/editor/syntaxCheck.test.ts src/layout/designRules.test.ts && mise exec -- npx tsc -b && mise run lint"
depends_on: [web-editor-languages]
model: opus
review: ""
verified_head: ""
points: 3
expected_minutes: 6
expected_tokens: 963314
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# web editor syntax check

## Requirement

Epic README goal, verbatim: "Syntax highlighting for python, yaml, json, terraform and toml, plus syntax checking (errors marked) where the language allows."

Epic README non-goal, verbatim: "No hints: no autocomplete, hover info or language-server features."

User decision U4, verbatim: "(my call) 'syntax highlighting and syntax - no hints': highlighting for python, yaml, json, terraform (.tf, .tfvars, .hcl) and toml, plus syntax error marking via @codemirror/lint (json parse linter, yaml and smol-toml parser errors, lezer parse-tree error nodes for python and hcl); no autocomplete, hover or hints (minimal setup, no autocompletion extension). Other extensions open as plain text."

Design D10, verbatim: "`src/editor/syntaxCheck.ts` exports `syntaxDiagnostics(language, state)`, a pure function of the `EditorState`, and `syntaxChecker(language)`, the extension `[linter(view => syntaxDiagnostics(language, view.state)), lintGutter()]` (default 750 ms delay). Per language: json, the `jsonParseLinter` of `@codemirror/lang-json` (B7); yaml, `parseAllDocuments` of `yaml`, one diagnostic per document error at its `pos` range, so `---` streams are not errors (B8); toml, `smol-toml` `parse`, one diagnostic at the `TomlError` line and column (B9); python and terraform, one diagnostic per Lezer error node of the full tree (`ensureSyntaxTree`; a parse that does not finish within its timeout gives no diagnostics rather than false ones) (B10); plain text none. Marks show in RO and RW tabs. No `autocompletion()`, no hover tooltips, no `basicSetup`; `python()`'s completion sources stay inert without the autocompletion extension (B18)."

Scope (agents-web):
- `src/editor/syntaxCheck.ts` (new): `syntaxDiagnostics(language: LanguageId, state: EditorState): Diagnostic[]` and `syntaxChecker(language: LanguageId): Extension`, using `LanguageId` and the language support of `src/editor/languages.ts` (web-editor-languages).
- `src/editor/syntaxCheck.test.ts` (new): the tests below, run in the node environment on `EditorState.create({doc, extensions: [languageFor(path).support]})`, with no view.

## Acceptance conditions

- ac1: JSON: `{"a": 1}` has no diagnostic; `{"a": 1,}` has one error diagnostic inside the document (new) [evidence: command:mise exec -- npx vitest run src/editor/syntaxCheck.test.ts -t 'json']
- ac2: YAML: a two-document stream separated by `---` has no diagnostic; a mapping with a bad indentation or an unclosed flow sequence has at least one error diagnostic on the offending line (new) [evidence: command:mise exec -- npx vitest run src/editor/syntaxCheck.test.ts -t 'yaml']
- ac3: TOML: a valid table with keys has no diagnostic; a duplicate key or a missing value has one error diagnostic on the line smol-toml reports (new) [evidence: command:mise exec -- npx vitest run src/editor/syntaxCheck.test.ts -t 'toml']
- ac4: Python: a valid function with a class and a comprehension has no diagnostic; `def f(:` has at least one error diagnostic on line 1 (new) [evidence: command:mise exec -- npx vitest run src/editor/syntaxCheck.test.ts -t 'python']
- ac5: Terraform: a valid file with `terraform`, `variable`, `resource` and `locals` blocks, interpolations, a heredoc and a `for` expression has no diagnostic; a block missing its closing brace has at least one error diagnostic (new) [evidence: command:mise exec -- npx vitest run src/editor/syntaxCheck.test.ts -t 'terraform']
- ac6: plain text never has a diagnostic, whatever its content (new) [evidence: command:mise exec -- npx vitest run src/editor/syntaxCheck.test.ts -t 'plain']
- ac7: every diagnostic has severity `error`, `from` < `to` and both inside the document, so a mark is visible even at the end of the file (new) [evidence: command:mise exec -- npx vitest run src/editor/syntaxCheck.test.ts -t 'diagnostic ranges']
- ac8: `syntaxChecker(language)` is the linter plus the lint gutter: a view-less `EditorState` built with it and given diagnostics through `setDiagnostics` reports them through `diagnosticCount`; no file under `src` imports `@codemirror/autocomplete` (new) [evidence: command:mise exec -- npx vitest run src/editor/syntaxCheck.test.ts -t 'checker extension' && ! grep -rn '@codemirror/autocomplete' src]
- ac9: the targeted suites, the type check and lint pass [evidence: command:mise exec -- npx vitest run src/editor/syntaxCheck.test.ts src/layout/designRules.test.ts && mise exec -- npx tsc -b && mise run lint]

## Files

- `src/editor/syntaxCheck.ts`
- `src/editor/syntaxCheck.test.ts`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
