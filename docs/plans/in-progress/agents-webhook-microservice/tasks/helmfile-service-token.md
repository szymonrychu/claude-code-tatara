---
title: helmfile service token
status: in-progress
repo: agents-helmfile
value: "the webhook service and the orchestrator share a service token and the three source secrets exist, without rotating any existing secret"
files: [scripts/bootstrap-secrets.sh, tests/test_secrets.py, values/agents-webhook/default.secrets.yaml, values/agent-orchestrator/service-token-agents-webhook.secrets.yaml, .sops.yaml]
verify: "uv run pytest -q -p no:cacheprovider tests/test_secrets.py && mise run lint"
depends_on: [orch-service-port-auth]
model: ""
review: full
verified_head: ""
points: 1
expected_minutes: 6
expected_tokens: 750000
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# helmfile service token

## Requirement

Secrets for agents-webhook (design D3, D10, D13). Paths are in code/agents-helmfile.

- `scripts/bootstrap-secrets.sh` gains `bootstrap_webhook`: when neither `values/agents-webhook/default.secrets.yaml` nor `values/agent-orchestrator/service-token-agents-webhook.secrets.yaml` exists, generate one service token (`openssl rand -hex 32`) and three source secrets (GitHub HMAC secret, GitLab token, Grafana token, each `openssl rand -hex 32`), and write, SOPS-encrypted through the existing `encrypt_to`:
  - `values/agents-webhook/default.secrets.yaml`: `orchestrator.token`, `sources.github`, `sources.gitlab`, `sources.grafana` (chart values shape of task webhook-chart-workloads).
  - `values/agent-orchestrator/service-token-agents-webhook.secrets.yaml`: `serviceApi.tokenHashes.agents-webhook: <sha256 hex of the token>` (chart values of task orch-chart-services-port).
  When both exist it does nothing; when exactly one exists it exits 1 naming both (never rotates, never half-writes). Values only travel through pipes, as the script's header requires.
- Running the script writes the two files (no kube context needed for this step); `.sops.yaml` covers the new paths if its rules do not already.
- `tests/test_secrets.py`: the new files are encrypted with the expected keys; the script is idempotent; one-of-two existing exits 1; the hash in the orchestrator file is the sha256 of the token in the webhook file (checked in-process the way the existing tests read encrypted files, never printed); no value printed.
- The source secrets are what the user pastes into GitHub, GitLab and Grafana; README (task smoke-webhook-check) says to read them with the project's secret helper.

## Acceptance conditions

- AC1: the two new secret files exist, are SOPS-encrypted and hold the expected keys [evidence: test:tests/test_secrets.py::test_secrets_files_encrypted_with_expected_keys]
- AC2: the orchestrator hash matches the webhook token [evidence: test:tests/test_secrets.py::test_webhook_token_hash_matches]
- AC3: re-running never rotates and a half-present pair exits 1 [evidence: test:tests/test_secrets.py::test_webhook_secrets_never_rotate]
- AC4: the script never prints a value and lint passes [evidence: command:uv run pytest -q -p no:cacheprovider tests/test_secrets.py -k never_prints && mise run lint]

## Files

- `scripts/bootstrap-secrets.sh`
- `tests/test_secrets.py`
- `values/agents-webhook/default.secrets.yaml`
- `values/agent-orchestrator/service-token-agents-webhook.secrets.yaml`
- `.sops.yaml`

## Interfaces

- Uses `orch-service-tokens` (`<name>:<sha256 hex>`); writes `serviceApi.tokenHashes.agents-webhook` for the orchestrator release and `orchestrator.token`, `sources.*` for the agents-webhook release.

## Expected outcome

Both releases have their secrets; nothing existing changed.

## Steps

- Red: tests; run: fail. Green: script; run it; run the verify command.

## Notes

- The SOPS key setup is the repo's existing one (`.sops.yaml`); never commit plaintext; never decrypt to stdout in a transcript.
