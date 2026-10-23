---
title: fixtures not secret shaped
status: done
repo: agent-orchestrator
value: secret scanners stay quiet on fake test data
files: [e2e/values-kind.yaml, scripts/e2e.sh, tests/test_chart_config.py]
verify: "uv run pytest tests/test_chart_config.py -q -p no:cacheprovider && mise run lint"
depends_on: [helm-chart-config-postgres, kind-e2e]
owns: []
uses: []
model: ""
estimate: 5
estimate_by: formula
actual: ""
actual_roles: ""
review: ""
worktree: /Users/szymonri/Documents/claude-code-tatara/.claude/worktrees/agent-orchestrator-fixtures-not-secret-shaped/agent-orchestrator
branch: agent-orchestrator-fixtures-not-secret-shaped
verified_head: e147d5a194d0e409be6aefa3cc660cdd85f15aaa
run: agent-orchestrator
provides: []
acs_for_audit: []
process_gaps: ["TDD skipped without a listed exception; prove the tests catch the change - commit first, then for each changed non-test file: git show <merge-base>:<path> > <path>; run the test (must fail); git show HEAD:<path> > <path>; run again (must pass); paste both tails into tests.red and verification.evidence"]
---

# fixtures not secret shaped

## Requirement

GitGuardian (PR #1) flags two fake fixtures as secrets: e2e/values-kind.yaml master key 'e2e-master-key-0123...' (matches the Mailgun key-<hex> pattern) and tests/test_chart_config.py postgres password 's3cr...' (generic password). Make every secret-shaped fixture non-secret-shaped: tests build values at run time (as the workbench template does) and e2e/values-kind.yaml gets the master key and claude token from scripts/e2e.sh at install time (--set from generated values) instead of literals. No real secret exists; behaviour unchanged.

## Acceptance conditions

- AC1: no literal secret-shaped values remain in e2e/ and tests/ (gitleaks dir over them is clean and the two flagged literals are gone) [evidence: command:mise exec gitleaks -- gitleaks dir e2e tests --no-banner --redact]
- AC2: chart config tests still pass [evidence: test:tests/test_chart_config.py]
- AC3: the kind e2e still installs with generated values [evidence: command:mise run test:e2e]

## Files

- `e2e/values-kind.yaml`
- `scripts/e2e.sh`
- `tests/test_chart_config.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

No secret-shaped literals in fixtures; tests and e2e unchanged in behaviour.

What is true and observable when the task is done.

## Steps

- Red: gitleaks/GitGuardian flags the two literals today.
- Generate the values at run/install time; run the verify command and the e2e.

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
