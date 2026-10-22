---
title: secrets skip gitlinks
status: todo
repo: workbench
value: "lint:secrets stops scanning component checkouts that scan themselves"
files: [mise-tasks/lint/secrets, scripts/tests/test_secret_scanning.py]
verify: "pytest scripts/tests/test_secret_scanning.py -q && mise run lint:secrets"
depends_on: []
owns: []
uses: []
model: ""
estimate: 5
estimate_by: formula
actual: ""
actual_roles: ""
review: ""
worktree: ""
branch: ""
verified_head: ""
run: ""
provides: []
---

# secrets skip gitlinks

## Requirement

mise-tasks/lint/secrets builds the set of gitlink paths (git ls-files -s entries of mode 160000) and skips them in its copy loop, so no submodule checkout is staged for gitleaks. It keeps the literal `git ls-files -coz --exclude-standard` listing, --redact and --config, stays bash 3.2 compatible (no associative arrays), copies and scans every other tracked and untracked file (including code/.gitkeep and files inside code/ that are not gitlinks), and .gitleaks.toml gains no allowlist.

## Acceptance conditions

- AC1: a secret-shaped fixture inside a gitlink checkout is not reported and the task exits 0 [evidence: test:scripts/tests/test_secret_scanning.py::test_lint_task_skips_gitlink_checkouts]
- AC2: a leak in a non-gitlink file under code/ is still detected [evidence: test:scripts/tests/test_secret_scanning.py::test_lint_task_scans_non_gitlink_files_under_code]
- AC3: the existing pins (literal listing, no allowlist) still pass [evidence: test:scripts/tests/test_secret_scanning.py::test_pinned_and_no_allowlist]
- AC4: the secrets lint family passes [evidence: command:mise run lint:secrets]

## Files

- `mise-tasks/lint/secrets`
- `scripts/tests/test_secret_scanning.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
