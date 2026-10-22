---
title: Existing remote kept
status: todo
repo: workbench
value: "An update never rewrites the user's template remote"
files: [scripts/tests/init_engine/test_update.py]
verify: "pytest scripts/tests/init_engine/test_update.py -q && ruff check scripts"
depends_on: []
owns: []
uses: []
model: sonnet
estimate: ""
actual: ""
review: ""
worktree: ""
branch: ""
verified_head: ""
run: ""
provides: []
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

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
