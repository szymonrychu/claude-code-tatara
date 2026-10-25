---
title: helmfile drop source secrets
status: in-progress
repo: agents-helmfile
value: no unused per-source webhook secrets are bootstrapped or kept
files: [scripts/bootstrap-secrets.sh, values/agents-webhook/default.secrets.yaml, tests/test_secrets.py]
verify: "uv run pytest -q -p no:cacheprovider tests/test_secrets.py && mise run lint"
depends_on: [helmfile-service-token]
model: sonnet
review: ""
verified_head: ""
points: 2
expected_minutes: 13
expected_tokens: 542616
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# helmfile drop source secrets

## Requirement

Drop the per-source webhook secrets (design D3, D13; re-plan 2026-10-25: per-webhook endpoints with basic auth replace the GitHub HMAC, GitLab token and Grafana bearer secrets that task helmfile-service-token bootstrapped). Paths are in code/agents-helmfile.

- `scripts/bootstrap-secrets.sh`: `bootstrap_webhook` generates only the orchestrator service token and its hash; no `sources` key; it still never rotates an existing value and never half-writes.
- `values/agents-webhook/default.secrets.yaml`: the `sources` key removed with the project's secret helper and the repo's SOPS config, `orchestrator.token` kept unchanged in value; the file stays encrypted. No secret value is printed to the terminal or the task notes.
- `tests/test_secrets.py`: the bootstrap writes no `sources` key; the decrypted file (through the test's existing `_decrypt` helper, in-process) has `orchestrator.token` and no `sources`; the token hash file still matches the token.

## Acceptance conditions

- AC1: the bootstrap generates only the service token for agents-webhook [evidence: test:tests/test_secrets.py::test_webhook_bootstrap_writes_no_sources]
- AC2: the encrypted values file has no sources key and keeps the token, and the hash still matches [evidence: test:tests/test_secrets.py::test_webhook_secrets_have_no_sources]
- AC3: the secrets tests and lint pass [evidence: command:uv run pytest -q -p no:cacheprovider tests/test_secrets.py && mise run lint]

## Files

- `scripts/bootstrap-secrets.sh`
- `values/agents-webhook/default.secrets.yaml`
- `tests/test_secrets.py`

## Interfaces

- Changes the output of done task helmfile-service-token: `values/agents-webhook/default.secrets.yaml` keeps only `orchestrator.token`.

## Expected outcome

No GitHub, GitLab or Grafana source secret is generated or stored for agents-webhook.

## Steps

- Red: the two tests; run `uv run pytest -q -p no:cacheprovider tests/test_secrets.py -k webhook`: fail.
- Green: the script, then the encrypted file through the secret helper; run the verify command.

## Notes

- Never print a decrypted value; decrypt only in-process in the tests.
- The values were never applied live (apply-smoke-webhook has not run), so nothing live changes.

- 2026-10-25 in-progress: re-plan 2026-10-25: added; not started
