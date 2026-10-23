---
title: fast full-spec form test
status: todo
repo: agent-orchestrator
value: "PR #3 frontend CI goes green, so the form fix can ship"
files: [frontend/src/clusters/ClusterForm.test.tsx]
verify: "cd frontend && npx vitest run src/clusters && npm run lint"
depends_on: []
owns: []
uses: []
model: sonnet
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

# fast full-spec form test

## Requirement

PR #3 frontend CI fails: frontend/src/clusters/ClusterForm.test.tsx "creates cluster with full spec" hits the 5000 ms vitest default timeout on the GitHub runner (5046 ms; job 120353282871). Make it fast without weakening its assertions: replace character-by-character userEvent.type calls for long values (slug, env key/value, webhook URL, every prefilled field it rewrites) with the file's existing paste helper or a userEvent.setup({ delay: null }) instance, so the test runs well under 2 s locally. Also give that one test an explicit 15000 ms timeout as CI headroom. Do not change ClusterForm.tsx behaviour.

## Acceptance conditions

- AC1: ClusterForm tests pass and "creates cluster with full spec" runs under 2000 ms locally [evidence: command:cd frontend && npx vitest run src/clusters/ClusterForm.test.tsx --reporter=verbose]

## Files

- `frontend/src/clusters/ClusterForm.test.tsx`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
