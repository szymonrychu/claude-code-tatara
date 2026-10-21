---
title: Gate provenance
status: todo
repo: workbench
value: "Dependents are gated only on the lines they wrote, ending the gate-repeat cascades"
files: [plugins/workbench/scripts/verify-task.py, plugins/workbench/workflows/plan-execute.js, plugins/workbench/scripts/tests/test_verify_provenance.py, plugins/workbench/workflows/tests/plan-execute-provenance.test.mjs]
verify: "cd plugins/workbench && pytest scripts/tests/test_verify_provenance.py scripts/tests/test_verify_task.py -q && ruff check scripts && bash scripts/run-tests.sh --only workflows"
depends_on: [ac-evidence-map]
owns: []
uses: [fork-point]
model: sonnet
estimate: 6
actual: ""
review: ""
worktree: ""
branch: ""
verified_head: ""
run: ""
provides: []
---

# Gate provenance

## Requirement

Stop the parking and debt gates from reporting text a merged dependency added (design D7). The init-engine-new case (AGENTS.md placeholders added by its dependency agents-md, reported against the dependent) must not recur.

- `verify-task.py --exclude-ref <ref>` (repeatable): compute the lines `<ref>` adds relative to `merge-base(<ref>, <base>)`, normalised the way `added_lines` and `drop_moved` normalise, and drop every added line of HEAD whose (file, text) is in that set before `find_debt` and `parking_candidates` run. The result carries `excludedByRef` (the count of dropped lines).
- plan-execute.js: in a run without `args.epic`, verifyPrompt adds `--exclude-ref <branch>` (quoted) for every same-repo dependency branch the task merged (the branches `dependencyLines` names). An epic run adds none, because its diff base is the epic branch or the recorded fork point.
- A line the dependent itself adds is still gated.

## Acceptance conditions

- AC1: with --exclude-ref, lines added by a merged dependency branch are not gated [evidence: test:plugins/workbench/scripts/tests/test_verify_provenance.py::test_dependency_lines_are_not_gated_with_exclude_ref]
- AC2: without --exclude-ref the same lines are still reported [evidence: test:plugins/workbench/scripts/tests/test_verify_provenance.py::test_without_exclude_ref_dependency_lines_are_gated]
- AC3: a debt marker the dependent adds itself is still reported [evidence: test:plugins/workbench/scripts/tests/test_verify_provenance.py::test_own_debt_is_still_reported]
- AC4: a non-epic run passes each merged same-repo dependency branch as --exclude-ref [evidence: test:plugins/workbench/workflows/tests/plan-execute-provenance.test.mjs::non-epic-verify-excludes-dependency-branches]
- AC5: an epic run passes no --exclude-ref [evidence: test:plugins/workbench/workflows/tests/plan-execute-provenance.test.mjs::epic-verify-passes-no-exclude-ref]

## Files

- `plugins/workbench/scripts/verify-task.py`
- `plugins/workbench/workflows/plan-execute.js`
- `plugins/workbench/scripts/tests/test_verify_provenance.py`
- `plugins/workbench/workflows/tests/plan-execute-provenance.test.mjs`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
