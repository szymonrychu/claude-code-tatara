---
title: web nomenclature allowlist
status: todo
repo: agents-web
value: "CodeMirror can be installed without turning the nomenclature guard red, and the guard still catches the retired unit"
files: [src/nomenclature.test.ts]
verify: "mise exec -- npx vitest run src/nomenclature.test.ts && mise run lint"
depends_on: []
model: sonnet
review: ""
verified_head: ""
points: 1
expected_minutes: 4
expected_tokens: 656326
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# web nomenclature allowlist

## Requirement

User decision U2, verbatim: "(my call, pending user approval at the gate) CodeMirror 6 with a thin own hook, packages and versions from web-libs-docs.md (state 6.7.6, view 6.43.15, language, commands, lint, lang-python, lang-yaml, lang-json, legacy-modes toml, codemirror-lang-hcl for terraform, @lezer/highlight, smol-toml, yaml). The nomenclature guard (src/nomenclature.test.ts) is tripped by the transitive dep @marijn/find-cluster-break; the planned fix is adding exactly that package name to the guard's ALLOWED list in its own task with a test proving any other match still fails; this is a gate question for the user, keep the task in the plan."

Design D2, verbatim: "`src/nomenclature.test.ts` `ALLOWED` gains exactly the entry `'find-cluster-break'` (the npm package `@marijn/find-cluster-break`, a runtime dependency of `@codemirror/state` since 6.5.0, written into `package-lock.json` as the `node_modules/@marijn/find-cluster-break` key, its tarball URL and the dependency line; F0.1 to F0.4). A new test pins that the phrase is allowed in those lockfile shapes and that every other spelling of the retired unit still fails. The guard stays accurate for project nomenclature; a third-party npm name is the same class as the Kubernetes phrases already allowed. This is the only test edit of the epic that is not an accuracy fix, and it lands in its own task before any dependency is added."

Precondition: the user approved this guard change at the gate (design.md open question Q1). Without that answer recorded, do not start; return it as a blocker.

Scope (agents-web): `src/nomenclature.test.ts` only: the `ALLOWED` entry, the doc comment of `ALLOWED` naming npm package names as a second allowed class, and the new test below. No other list (`HISTORY`, `GUARDED`, `RETIRED`, `FORBIDDEN`) and no existing test changes.

## Acceptance conditions

- ac1: the three lockfile shapes of the package (the `"node_modules/@marijn/find-<unit>-break": {` key, a tarball URL of the shape `https://registry.npmjs.org/@marijn/find-<unit>-break/-/find-<unit>-break-<version>.tgz` and the `"@marijn/find-<unit>-break": "^1.0.0"` dependency line) do not offend, while `find-<unit>`, `<unit>-break`, `my-<unit>-break` and `find-<unit>-break and a <unit>` still offend (the unit spelled through the file's `unit` constant) (new) [evidence: command:mise exec -- npx vitest run src/nomenclature.test.ts -t 'npm package name']
- ac2: `ALLOWED` is the previous list plus exactly `'find-cluster-break'` at its end [evidence: command:grep -qF "const ALLOWED = ['cluster.local', 'ClusterIP', 'clusterIP', 'ClusterIssuer', 'cluster-issuer', 'ClusterRole', 'in-cluster', 'cluster-internal', 'cluster node', 'cluster-info', 'find-cluster-break']" src/nomenclature.test.ts]
- ac3: every existing nomenclature test passes unchanged against the current tree [evidence: command:mise exec -- npx vitest run src/nomenclature.test.ts]
- ac4: lint passes [evidence: command:mise run lint]

## Files

- `src/nomenclature.test.ts`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
