---
title: workflow hardening
status: todo
repo: any-mcp
value: CI and release tokens get least privilege and the release cannot be shell-injected
files: [.github/workflows/ci.yml, .github/workflows/release.yml, tests/test_release.py]
verify: "uv run --frozen pytest tests/test_release.py -q && mise run lint"
depends_on: [release, scaffold]
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

# workflow hardening

## Requirement

Security findings (low): .github/workflows/ci.yml has no permissions block: add `permissions: contents: read`. release.yml grants contents: write at workflow level and interpolates ${{ github.ref_name }} into run: (line 38): set workflow-level contents: read and contents: write only on the job that creates the release; pass the tag through env: and quote it; the job fails unless the tag matches ^v[0-9]+\.[0-9]+\.[0-9]+$ and the tagged commit is an ancestor of origin/main.

## Acceptance conditions

- AC1: ci.yml declares contents: read [evidence: test:tests/test_release.py::test_ci_permissions_read_only]
- AC2: release.yml scopes write to the job, passes the tag via env and validates it [evidence: test:tests/test_release.py::test_release_workflow_hardened]

## Files

- `.github/workflows/ci.yml`
- `.github/workflows/release.yml`
- `tests/test_release.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

The requirement holds, pinned by the acceptance tests.

What is true and observable when the task is done.

## Steps

- Write the failing acceptance tests; run red.
- Implement; run green with the verify command.

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
