---
title: fast full-spec form test
status: done
repo: agent-orchestrator
value: "PR #3 frontend CI goes green, so the form fix can ship"
files: [frontend/src/clusters/ClusterForm.test.tsx]
verify: "cd frontend && npx vitest run src/clusters && npm run lint"
depends_on: [model-default-option]
model: sonnet
review: ""
verified_head: 3f272a6823fb43b2d13b3de545b5d8cb23b42a83
points: 1
expected_minutes: 5
expected_tokens: 750000
points_actual: ""
actual_minutes: 3
actual_tokens: 538399
actual_roles: "impl 2, review 2"
actual_role_tokens: "impl 339534, review 198865"
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

The full-spec test runs in well under 2 s locally with a 15 s explicit timeout; assertions unchanged.

## Steps

- Test-only change (exception: no behaviour change). Record the current duration with `npx vitest run src/clusters/ClusterForm.test.tsx --reporter=verbose`.
- Switch long typing to paste or a no-delay userEvent instance, add the 15000 ms timeout, rerun: passes, duration under 2000 ms.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
