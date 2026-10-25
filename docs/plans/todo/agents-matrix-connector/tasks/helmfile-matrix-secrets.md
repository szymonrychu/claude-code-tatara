---
title: helmfile matrix secrets
status: todo
repo: agents-helmfile
value: "the connector's Matrix token and orchestrator service token are stored encrypted without rotating anything"
files: [scripts/bootstrap-secrets.sh, tests/test_secrets.py, values/agents-matrix-connector/default.secrets.yaml, values/agents-orchestrator/service-token-agents-matrix-connector.secrets.yaml, .sops.yaml]
verify: "uv run --frozen pytest -q -p no:cacheprovider tests/test_secrets.py && shellcheck --severity=error scripts/bootstrap-secrets.sh && uv run ruff check ."
depends_on: []
model: sonnet
review: full
verified_head: ""
points: 2
expected_minutes: 8
expected_tokens: 542616
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# helmfile matrix secrets

## Requirement

Secrets for the connector (design D2, D13; user-run step U2). Paths are in code/agents-helmfile.

Precondition, checked first: the U2 token file `/Users/szymonri/Documents/claude-code-tatara/.scratchpad/agents-matrix-connector/matrix-token` exists and is non-empty (never print it). Otherwise end `blocked`, whoCanClear "user: user-run steps U1 and U2 of agents-matrix-connector design.md".

- `scripts/bootstrap-secrets.sh` gains `bootstrap_matrix_connector`: when neither `values/agents-matrix-connector/default.secrets.yaml` nor `values/agents-orchestrator/service-token-agents-matrix-connector.secrets.yaml` exists, it requires `MATRIX_CONNECTOR_TOKEN_FILE` (path to the U2 token file; missing or empty exits 1 naming the variable), generates one service token (`openssl rand -hex 32`) and writes, SOPS-encrypted through the existing `encrypt_to`:
  - `values/agents-matrix-connector/default.secrets.yaml`: `orchestrator.token` and `matrix.accessToken` (chart values of task mxc-chart-workloads).
  - `values/agents-orchestrator/service-token-agents-matrix-connector.secrets.yaml`: `serviceApi.tokenHashes.agents-matrix-connector: <sha256 hex of the service token>` (contract `orch-service-tokens`).
  When both exist it does nothing; when exactly one exists it exits 1 naming both (never rotates, never half-writes). Values only travel through pipes and files, as the script's header requires; nothing is printed.
- Run the script with `MATRIX_CONNECTOR_TOKEN_FILE` set to the U2 file, writing the two files; `.sops.yaml` covers the new paths if its rules do not already.
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

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
