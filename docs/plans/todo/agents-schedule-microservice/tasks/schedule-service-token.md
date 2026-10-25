---
title: schedule service token
status: todo
repo: agents-helmfile
value: "the schedule service authenticates to the orchestrator with its own token, bootstrapped like the other secrets"
files: [scripts/bootstrap-secrets.sh, tests/test_secrets.py]
verify: "uv run --frozen pytest -q -p no:cacheprovider tests/test_secrets.py && shellcheck --severity=error scripts/bootstrap-secrets.sh && uv run ruff check ."
depends_on: []
owns: [agents-schedule-token-bootstrap]
uses: [orch-service-tokens]
model: ""
estimate: 5
estimate_by: formula
actual: ""
actual_roles: ""
review: full
worktree: ""
branch: ""
verified_head: ""
run: ""
provides: []
---

# schedule service token

## Requirement

Extend `scripts/bootstrap-secrets.sh` (design D14; approval A6): generate a random service token for agents-schedule once (kept when it exists), store it in Secret `agents-schedule-orchestrator-token` key `token` in namespace `agents`, and add the same token to the orchestrator's service-token list in the form and Secret the contract `orch-service-tokens` defines (name `agents-schedule`). Idempotent: a second run changes nothing; prints no secret value.

## Acceptance conditions

- AC1: the script creates the schedule token Secret and the orchestrator entry [evidence: test:tests/test_secrets.py::test_schedule_service_token_bootstrapped]
- AC2: a second run keeps the existing token [evidence: test:tests/test_secrets.py::test_schedule_service_token_idempotent]
- AC3: no token value is printed [evidence: test:tests/test_secrets.py::test_schedule_service_token_not_printed]
- AC4: shellcheck passes [evidence: command:shellcheck --severity=error scripts/bootstrap-secrets.sh]

## Files

- `scripts/bootstrap-secrets.sh`
- `tests/test_secrets.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
