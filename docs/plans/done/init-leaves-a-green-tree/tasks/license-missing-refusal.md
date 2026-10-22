---
title: license missing refusal
status: done
repo: workbench
value: "init still refuses a first run with no LICENSE, as before the epic"
files: [scripts/init_engine/finalize.py, scripts/tests/init_engine/test_finalize.py]
verify: mise exec -- pytest scripts/tests/init_engine/test_finalize.py -q
depends_on: [refresh-writes-allow-entries]
owns: []
uses: []
model: ""
estimate: 5
estimate_by: formula
actual: ""
actual_roles: ""
review: ""
worktree: /Users/szymonri/Documents/workbench/.claude/worktrees/init-leaves-a-green-tree-license-missing-refusal
branch: init-leaves-a-green-tree-license-missing-refusal
verified_head: b8c4d961156e31aee4df83055a80b29e20456f66
run: init-leaves-a-green-tree
provides: []
acs_for_audit: []
process_gaps: []
fork_point: 8bfd79ad2557a25c7f3c73ca2d9e6027773a3fb7
---

# license missing refusal

## Requirement

Restore the refusal finalize.license_file raised before this epic: with license unset (None) on the first run and the root LICENSE missing, init refuses with `Refusal("LICENSE is missing...")` as it did before (review finding, finalize.py:178-183), while the epic's new behaviour (holder in every plugins/*/LICENSE, --license none removes only the root, --license-file copied everywhere) stays.

## Acceptance conditions

- AC1: first run with no --license and no root LICENSE refuses with the LICENSE-missing message [evidence: test:scripts/tests/init_engine/test_finalize.py::test_license_missing_refuses_on_first_run]
- AC2: existing license tests stay green [evidence: test:scripts/tests/init_engine/test_finalize.py::test_license_options]

## Files

- `scripts/init_engine/finalize.py`
- `scripts/tests/init_engine/test_finalize.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

The requirement above holds, pinned by the acceptance tests.

What is true and observable when the task is done.

## Steps

- Write the failing acceptance tests; run red.
- Implement; run green with the verify command.

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
