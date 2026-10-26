---
title: helmfile matrix secrets
status: done
repo: agents-helmfile
value: "the connector's Matrix token and orchestrator service token are stored encrypted without rotating anything"
files: [scripts/bootstrap-secrets.sh, tests/test_secrets.py, values/agents-matrix-connector/default.secrets.yaml, values/agents-orchestrator/service-token-agents-matrix-connector.secrets.yaml, .sops.yaml]
verify: "uv run --frozen pytest -q -p no:cacheprovider tests/test_secrets.py && shellcheck --severity=error scripts/bootstrap-secrets.sh && uv run ruff check ."
depends_on: []
model: sonnet
review: ""
verified_head: f09b2a46b8f0b8bc0d6b7f49075e20391d6db70a
points: 2
expected_minutes: 7
expected_tokens: 538938
points_actual: 2
actual_minutes: 8
actual_tokens: 569216
actual_roles: "impl 5, review 3"
actual_role_tokens: "impl 475908, review 93308"
---

# helmfile matrix secrets

## Requirement

Secrets for the connector (design D2, D13, revision R1). Paths are in code/agents-helmfile.

Precondition, checked first: Secret `hermes-agent-matrix` in namespace `ai` has a non-empty key `MATRIX_ACCESS_TOKEN` (read-only kubectl, never printed) and `GET /_matrix/client/v3/account/whoami` with it answers `@hermes:szymonrichert.pl` (the token only through a file or a pipe; only the returned user id is shown). Otherwise end `blocked`, whoCanClear "user: Secret ai/hermes-agent-matrix has no working MATRIX_ACCESS_TOKEN".

- `scripts/bootstrap-secrets.sh` gains `bootstrap_matrix_connector`: when neither `values/agents-matrix-connector/default.secrets.yaml` nor `values/agents-orchestrator/service-token-agents-matrix-connector.secrets.yaml` exists, it requires `MATRIX_CONNECTOR_TOKEN_FILE` (path to a file holding the Matrix access token; missing or empty exits 1 naming the variable), generates one service token (`openssl rand -hex 32`) and writes, SOPS-encrypted through the existing `encrypt_to`:
  - `values/agents-matrix-connector/default.secrets.yaml`: `orchestrator.token` and `matrix.accessToken` (chart values of task mxc-chart-workloads).
  - `values/agents-orchestrator/service-token-agents-matrix-connector.secrets.yaml`: `serviceApi.tokenHashes.agents-matrix-connector: <sha256 hex of the service token>` (contract `orch-service-tokens`).
  When both exist it does nothing; when exactly one exists it exits 1 naming both (never rotates, never half-writes). Values only travel through pipes and files, as the script's header requires; nothing is printed.
- Pipe Secret `ai/hermes-agent-matrix` key `MATRIX_ACCESS_TOKEN` into a mode-600 file under `/Users/szymonri/Documents/claude-code-tatara/.scratchpad/agents-matrix-connector/` (never printed), run the script with `MATRIX_CONNECTOR_TOKEN_FILE` set to it, delete the file afterwards, writing the two files; `.sops.yaml` covers the new paths if its rules do not already.
- `tests/test_secrets.py`: the new files are SOPS-encrypted with the expected keys; the orchestrator hash is the sha256 of the connector's service token (checked in-process as the existing tests read encrypted files, never printed); re-running never rotates; one-of-two exits 1; a missing token file exits 1; no value is printed.

User request 2026-10-25, verbatim: 'agents-matrix-connector New microservice- is meant to connect with existing matrix deployment and allow for talking to agents through facebook. Must support user/chat/room auto discovery and white/blacklosting. Hermes already uses working bridge.'

## Acceptance conditions

- AC1: the two secret files exist, are SOPS-encrypted and hold the expected keys [evidence: test:tests/test_secrets.py::test_matrix_connector_secrets_encrypted_with_expected_keys]
- AC2: the orchestrator hash matches the connector's service token [evidence: test:tests/test_secrets.py::test_matrix_connector_token_hash_matches]
- AC3: re-running never rotates, a half-present pair exits 1 and a missing token file exits 1 [evidence: test:tests/test_secrets.py::test_matrix_connector_secrets_never_rotate]
- AC4: the script never prints a value, and shellcheck and lint pass [evidence: command:uv run --frozen pytest -q -p no:cacheprovider tests/test_secrets.py -k never_prints && shellcheck --severity=error scripts/bootstrap-secrets.sh && uv run ruff check .]

## Files

- `scripts/bootstrap-secrets.sh`
- `tests/test_secrets.py`
- `values/agents-matrix-connector/default.secrets.yaml`
- `values/agents-orchestrator/service-token-agents-matrix-connector.secrets.yaml`
- `.sops.yaml`

## Interfaces

- `values/agents-matrix-connector/default.secrets.yaml` (`orchestrator.token`, `matrix.accessToken`), read by the release of helmfile-matrix-releases through the `values/{{ .Release.Name }}/default.secrets.yaml` convention.
- `values/agents-orchestrator/service-token-agents-matrix-connector.secrets.yaml`, wired into the agents-orchestrator release by helmfile-matrix-releases.

## Expected outcome

Both files are committed encrypted; the orchestrator will accept the connector's bearer token on port 8002 after the apply.

## Steps

- Red: extend `tests/test_secrets.py` with the four tests (a temp token file for the script tests). Fails: no bootstrap function, no files.
- Green: write `bootstrap_matrix_connector`, run it with the real U2 file, commit the encrypted files. Run the verify.

## Notes

- Same shape as agents-webhook-microservice task helmfile-service-token (`bootstrap_webhook`).
- After this task is done the orchestrator deletes the U2 token file (design U2).
- The values dir is `values/agents-orchestrator/` after orchestrator-rename-sessions (design D15).

- 2026-10-25 amended: revision R1 (user 2026-10-25): the connector takes over Hermes' Matrix user and Facebook account, Hermes scaled to 0; only the Hermes home-channel owner DM is allowed

- 2026-10-26 done
