---
title: helmfile service token
status: todo
repo: agents-helmfile
value: "the webhook service and the orchestrator share a service token and the three source secrets exist, without rotating any existing secret"
files: [scripts/bootstrap-secrets.sh, tests/test_secrets.py, values/agents-webhook/default.secrets.yaml, values/agent-orchestrator/service-token-agents-webhook.secrets.yaml, .sops.yaml]
verify: "uv run pytest -q -p no:cacheprovider tests/test_secrets.py && mise run lint"
depends_on: [orch-service-port-auth]
owns: []
uses: [orch-service-tokens]
model: ""
estimate: 6
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

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
