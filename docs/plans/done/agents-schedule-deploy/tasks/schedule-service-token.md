---
title: schedule service token
status: done
repo: agents-helmfile
value: "the schedule service authenticates to the orchestrator with its own token, bootstrapped like the other secrets"
files: [scripts/bootstrap-secrets.sh, tests/test_secrets.py, values/agents-schedule/default.secrets.yaml, values/agents-orchestrator/service-token-agents-schedule.secrets.yaml, .sops.yaml]
verify: "uv run --frozen pytest -q -p no:cacheprovider tests/test_secrets.py && shellcheck --severity=error scripts/bootstrap-secrets.sh && uv run ruff check ."
depends_on: []
model: ""
review: full
verified_head: fd8696fbcee140c7bf2338ba83ca06101cfb442c
points: 1
expected_minutes: 5
expected_tokens: 678580
points_actual: 1
actual_minutes: 4
actual_tokens: 265212
actual_roles: "impl 1, review 3"
actual_role_tokens: "impl 174527, review 90685"
---

# schedule service token

## Requirement

Secrets for agents-schedule (design D14; approval A6), the same shape as agents-webhook task helmfile-service-token (contracts `orch-service-tokens`, `orch-services-service`). Paths are in code/agents-helmfile.

- `scripts/bootstrap-secrets.sh` gains `bootstrap_schedule`: when neither `values/agents-schedule/default.secrets.yaml` nor `values/agents-orchestrator/service-token-agents-schedule.secrets.yaml` exists, generate one service token (`openssl rand -hex 32`) and write, SOPS-encrypted through the existing `encrypt_to`:
  - `values/agents-schedule/default.secrets.yaml`: `orchestrator.token` (chart values shape of task helm-chart).
  - `values/agents-orchestrator/service-token-agents-schedule.secrets.yaml`: `serviceApi.tokenHashes.agents-schedule: <sha256 hex of the token>` (orchestrator chart values of `orch-services-service`).
  When both exist it does nothing; when exactly one exists it exits 1 naming both (never rotates, never half-writes). Values only travel through pipes, as the script's header requires.
- `.sops.yaml` covers the new paths if its rules do not already.
- `tests/test_secrets.py`: the new files are encrypted with the expected keys; the script is idempotent; one-of-two existing exits 1; the hash in the orchestrator file is the sha256 of the token in the schedule file (checked in-process the way the existing tests read encrypted files, never printed); no value printed.

## Acceptance conditions

- AC1: the script writes both encrypted files with the token and its hash [evidence: test:tests/test_secrets.py::test_schedule_service_token_bootstrapped]
- AC2: a second run changes nothing and one-of-two existing exits 1 [evidence: test:tests/test_secrets.py::test_schedule_service_token_idempotent]
- AC3: no token value is printed [evidence: test:tests/test_secrets.py::test_schedule_service_token_not_printed]
- AC4: shellcheck passes [evidence: command:shellcheck --severity=error scripts/bootstrap-secrets.sh]

## Files

- `scripts/bootstrap-secrets.sh`
- `tests/test_secrets.py`
- `values/agents-schedule/default.secrets.yaml`
- `values/agents-orchestrator/service-token-agents-schedule.secrets.yaml`
- `.sops.yaml`

## Interfaces

- `values/agents-schedule/default.secrets.yaml` `orchestrator.token` and `values/agents-orchestrator/service-token-agents-schedule.secrets.yaml` `serviceApi.tokenHashes.agents-schedule` (part `agents-schedule-token-bootstrap`).

## Expected outcome

One bootstrap run gives the schedule service a working orchestrator credential.

## Steps

- Add the three tests to tests/test_secrets.py the way the existing secret tests run the script; they fail.
- Extend the script; they pass.
- shellcheck clean.

## Notes

- The webhook epic adds its own pair of files the same way; the two stay independent. The orchestrator release picks up `service-token-*.secrets.yaml` per `orch-services-service`.

- 2026-10-25 amended: align to released agents-common v0.3.0 session names and the reuse rule

- 2026-10-25 done
