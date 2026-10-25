---
title: Existing remote kept
status: done
repo: workbench
value: "An update never rewrites the user's template remote"
files: [scripts/tests/init_engine/test_update.py]
verify: "pytest scripts/tests/init_engine/test_update.py -q && ruff check scripts"
depends_on: [update-safety, e2e-template-update]
model: sonnet
review: ""
verified_head: a8d952468624aa0afef9b2865629c635253cc411
points: ""
expected_minutes: ""
expected_tokens: ""
points_actual: ""
actual_minutes: 4
actual_tokens: 362093
actual_roles: "impl 2, review 2"
actual_role_tokens: "impl 202888, review 159205"
---

# Existing remote kept

## Requirement

Scope audit gap (2026-10-22): update-command AC4 says an existing template remote keeps its URL, citing scripts/tests/init_engine/test_update.py::test_update_keeps_existing_template_remote, but no such test exists on main and nothing asserts it.

Deliver: the test `test_update_keeps_existing_template_remote` in scripts/tests/init_engine/test_update.py. A workbench whose `template` remote points at a local upstream (a URL other than the default) runs `update` with no `--url`. The update succeeds from that remote, and afterwards `git remote get-url template` still prints the original URL. If the behaviour is missing, fix update.py so it holds. Reuse the init_helpers fixtures.

## Acceptance conditions

- AC1: with an existing template remote and no --url, update succeeds and the remote URL is unchanged [evidence: test:scripts/tests/init_engine/test_update.py::test_update_keeps_existing_template_remote]

## Files

- `scripts/tests/init_engine/test_update.py`

## Interfaces

- No interface change; test only unless the behaviour is missing.

## Expected outcome

update-command AC4 is pinned by a real test.

## Steps

1. Write the test and run it; if it passes at once, this is a pinning test of existing behaviour (say so in tests.note).
2. If it fails, fix update.py.
3. Run the verify command.

## Ruling

- 2026-10-22 accepted: Accepted 2026-10-22: pin test of existing behaviour, red shown by mutation; TDD-skipped exception (no non-test change). Landed on main.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
