---
title: secrets skip gitlinks
status: in-progress
repo: workbench
value: "lint:secrets stops scanning component checkouts that scan themselves"
files: [mise-tasks/lint/secrets, scripts/tests/test_secret_scanning.py]
verify: "mise exec -- pytest scripts/tests/test_secret_scanning.py -q && mise run lint:secrets"
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

mise-tasks/lint/secrets: bash 3.2, no associative arrays; keep literal `git ls-files -coz --exclude-standard`.

## Expected outcome

A gitlink checkout holding a secret-shaped fixture does not fail the task; a leak in any non-gitlink file still does.

## Steps

- Add the two failing tests to test_secret_scanning.py (fixture secret built at run time); run red.
- Build the gitlink path set from `git ls-files -s` (mode 160000) and skip those in the copy loop; run green, then `mise run lint:secrets`.

## Notes

Design D3. test_secret_scanning.py:19/:26 pin the no-allowlist policy; do not touch .gitleaks.toml. Precedent for 160000 detection: test_adopt.py:99.
