---
title: Triage one call
status: done
repo: workbench
value: One haiku round trip per verify instead of three
files: [plugins/workbench/scripts/verify-task.py, plugins/workbench/scripts/triage.py, plugins/workbench/scripts/tests/test_triage.py, plugins/workbench/scripts/tests/test_verify_triage_one_call.py]
verify: "cd plugins/workbench && pytest scripts/tests/test_verify_triage_one_call.py scripts/tests/test_triage.py scripts/tests/test_triage_false_finding.py scripts/tests/test_verify_task.py -q && ruff check scripts"
depends_on: [gate-provenance]
model: sonnet
review: ""
verified_head: 4e33d73c22ccb4c07e6b9d9c1c74edeb770ed6bc
points: 1
expected_minutes: 6
expected_tokens: 750000
points_actual: ""
actual_minutes: 11
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# Triage one call

## Requirement

Fold verify-task's three haiku calls into one (design D12).

- `plugins/workbench/scripts/triage.py` gains a mode `verify` that takes `{parking: [candidates], acs: [ac plausibility items], tier: {requirement, files, diffstat}}`, every part optional, and returns `{parking: [...], acs: [...], classifierTier}` from ONE `claude -p` haiku call whose schema covers the parts present. The existing modes stay for their other callers.
- `verify-task.py` makes at most one triage call per run: `verify` mode with the parts it needs, and no call at all when no part is needed. Its results fill the same result fields as today (`parking`, `acs[].plausible` and the per-AC notes, `tierHint`). `--no-triage` and `--no-tier` keep their meaning. A failed call falls back as today: a note naming the failure, empty parking, `plausible: null`, `tierHint: null`.
- `triageUsage` counts the one call.

## Acceptance conditions

- AC1: one verify-task run makes at most one triage call carrying parking, AC plausibility and tier together [evidence: test:plugins/workbench/scripts/tests/test_verify_triage_one_call.py::test_one_triage_call_per_verify]
- AC2: no triage call is made when there is nothing to triage [evidence: test:plugins/workbench/scripts/tests/test_verify_triage_one_call.py::test_no_call_when_nothing_to_triage]
- AC3: a failed verify-mode call falls back with a note and empty results [evidence: test:plugins/workbench/scripts/tests/test_verify_triage_one_call.py::test_verify_mode_failure_falls_back_with_note]
- AC4: triage verify mode answers all three parts from one call [evidence: test:plugins/workbench/scripts/tests/test_triage.py::test_verify_mode_answers_all_three_parts]
- AC5: the existing triage and verify-task tests still pass [evidence: command:cd plugins/workbench && pytest scripts/tests/test_triage.py scripts/tests/test_triage_false_finding.py scripts/tests/test_verify_task.py -q]

## Files

- `plugins/workbench/scripts/verify-task.py`
- `plugins/workbench/scripts/triage.py`
- `plugins/workbench/scripts/tests/test_triage.py`
- `plugins/workbench/scripts/tests/test_verify_triage_one_call.py`

## Interfaces

- `triage.run("verify", data, ...)` in `plugins/workbench/scripts/triage.py`; verify-task's `triage_run` injection point (`build(argv, triage_run=...)`) stays the test seam.

## Expected outcome

Each verify spends one haiku round trip instead of up to three, about a minute less per verify, with the same result fields.

## Steps

- Red: write `scripts/tests/test_verify_triage_one_call.py` with a counting fake `triage_run` (AC1-AC3) and add AC4 to `test_triage.py` with a fake runner; run `cd plugins/workbench && pytest scripts/tests/test_verify_triage_one_call.py scripts/tests/test_triage.py -q`; expect failures.
- Green: the `verify` mode and the single call site in `build`.
- Run the task verify; expect all passed.

## Notes

- Today `build` calls `triage_run` for `parking`, `ac-plausible` (through `add_plausibility`) and `tier`, each with a 120 s timeout (`lib/claude_json.py`).
- `add_plausibility` keeps its shortcut that answers obvious matches without a call; only the remaining items go into the combined call.
