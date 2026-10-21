---
title: AC evidence map
status: todo
repo: workbench
value: "A renamed test no longer costs a fix round; loose matches are shown to the auditor"
files: [plugins/workbench/workflows/plan-execute.js, plugins/workbench/scripts/verify-task.py, plugins/workbench/agents/implementer.md, plugins/workbench/agents/scope-auditor.md, plugins/workbench/scripts/tests/test_verify_ac_evidence.py, plugins/workbench/workflows/tests/plan-execute-ac-evidence.test.mjs]
verify: "cd plugins/workbench && pytest scripts/tests/test_verify_ac_evidence.py scripts/tests/test_verify_task.py scripts/tests/test_verify_ref_runner.py -q && ruff check scripts && bash scripts/run-tests.sh --only workflows"
depends_on: [verify-scope-wiring]
owns: [ac-evidence]
uses: []
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

# AC evidence map

## Requirement

Carry acceptance conditions to the implementer and resolve renamed test refs by evidence (design D2). The harness-config-migrate#1 case (AC3-AC5 ref-missing although the tests existed under other names) must not recur.

- `implPrompt` and `fixPrompt` include, when `t.ac` exists, a block `Acceptance conditions (prove each; return acEvidence):` with one line per AC: `<id>: <text> [<kind>: <ref>]`.
- The implementer and fixer result schema gains optional `acEvidence`: an object mapping AC id to the final `file::name` of the test that proves it.
- `verifyPrompt`: when the latest implementer or fixer result has `acEvidence`, the agent writes it as JSON to a second temp file and passes `--ac-evidence "$ACE"`.
- `verify-task.py --ac-evidence <file>`: a `test:` AC resolves in this order: (1) the acEvidence entry for its id, when that file exists and defines that name; (2) the exact ref (today's lookup); (3) the single test in the ref's file (after the existing basename lookup) whose name contains the ref's name or is contained in it. Each AC result carries `matchedBy: acEvidence|exact|substring` and `resolvedRef`. Zero or several substring candidates keep today's ref-missing result.
- An AC resolved by `substring` is listed in the task's `acsForAudit`, so the audit shows it `open: judge it`.
- `plugins/workbench/agents/implementer.md`: return `acEvidence` naming the final test of every `test:` AC. `plugins/workbench/agents/scope-auditor.md`: an AC row with `matchedBy: substring` is judged by reading the test.

## Acceptance conditions

- AC1: impl and fix prompts carry the AC list [evidence: test:plugins/workbench/workflows/tests/plan-execute-ac-evidence.test.mjs::impl-and-fix-prompts-carry-the-ac-list]
- AC2: the verifier passes the implementer's acEvidence as --ac-evidence [evidence: test:plugins/workbench/workflows/tests/plan-execute-ac-evidence.test.mjs::verify-passes-ac-evidence-file]
- AC3: an AC matched by substring is open for the audit [evidence: test:plugins/workbench/workflows/tests/plan-execute-ac-evidence.test.mjs::substring-match-is-open-for-audit]
- AC4: verify-task resolves acEvidence, then exact, then substring, and records matchedBy [evidence: test:plugins/workbench/scripts/tests/test_verify_ac_evidence.py::test_resolution_order_and_matched_by]
- AC5: a fixture modelled on harness-config-migrate#1 (refs naming tests later renamed) yields no ref-missing [evidence: test:plugins/workbench/scripts/tests/test_verify_ac_evidence.py::test_renamed_tests_fixture_has_no_ref_missing]
- AC6: an ambiguous substring match stays ref-missing [evidence: test:plugins/workbench/scripts/tests/test_verify_ac_evidence.py::test_ambiguous_substring_stays_ref_missing]
- AC7: the implementer and scope-auditor agents name acEvidence and matchedBy [evidence: command:grep -q acEvidence plugins/workbench/agents/implementer.md && grep -q matchedBy plugins/workbench/agents/scope-auditor.md]

## Files

- `plugins/workbench/workflows/plan-execute.js`
- `plugins/workbench/scripts/verify-task.py`
- `plugins/workbench/agents/implementer.md`
- `plugins/workbench/agents/scope-auditor.md`
- `plugins/workbench/scripts/tests/test_verify_ac_evidence.py`
- `plugins/workbench/workflows/tests/plan-execute-ac-evidence.test.mjs`

## Interfaces

- Owns `ac-evidence`: the `acEvidence` result field (AC id to `file::name`) in plan-execute.js's implementer schema, and verify-task's `matchedBy` and `resolvedRef` per AC. audit-context-and-models reads `matchedBy` to decide which rows the verifier settled.
- verify-task flag `--ac-evidence <json file>`.

## Expected outcome

An AC whose test was renamed resolves on the first verify instead of costing a fix round; a loose match is visible to the auditor.

## Steps

- Red: write `scripts/tests/test_verify_ac_evidence.py` (AC4-AC6, throwaway git repos with pytest files) and `workflows/tests/plan-execute-ac-evidence.test.mjs` (AC1-AC3); run `cd plugins/workbench && pytest scripts/tests/test_verify_ac_evidence.py -q && node --test workflows/tests/plan-execute-ac-evidence.test.mjs`; expect failures.
- Green: prompts and schema, verifyPrompt, `_test_name_missing` and `check_ac` in verify-task.py, the two agent docs.
- Run the task verify; expect all green.

## Notes

- Measured: 58 of 104 fix rounds carried a ref-missing finding; implPrompt and fixPrompt never received `t.ac` although implementer.md asks for exact refs (brief item 2).
- Keep exact before substring; the substring step looks only inside the ref's file.
- Node test titles are single kebab tokens (refRunners `--test-name-pattern {name}`).
