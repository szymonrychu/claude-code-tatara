---
title: helmfile chat secrets
status: done
repo: agents-helmfile
value: "the one chat token exists, encrypted, in the shape both charts read, and never rotates"
files: [scripts/bootstrap-secrets.sh, helmfile.yaml.gotmpl, values/agents-orchestrator/chat-token.secrets.yaml, values/agents-matrix-connector/agent-token.secrets.yaml, tests/test_secrets.py, README.md]
verify: "uv run pytest tests/test_secrets.py && mise run lint"
depends_on: [mxc-chart-agent-port, orch-chart-chat]
model: opus
review: ""
verified_head: 4c7ef2aa9c1bebfdc96c825d9f53797b7fd2f3fb
points: 3
expected_minutes: 6
expected_tokens: 941421
points_actual: 3
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# helmfile chat secrets

## Requirement

README Goal, verbatim: "Agents may post only to policy-allowed rooms that are bound to their session or flagged agents_may_initiate (off by default, set per room by the user); the agent token never leaves the orchestrator."

Design D14, verbatim: "One new token. `scripts/bootstrap-secrets.sh` gains `bootstrap_chat_token`: both files or neither, never rotates, never prints. (probe) The architecture says the sha256 goes to `values/agents-matrix-connector/default.secrets.yaml`; that file exists and the script never touches an existing target, so the token goes to two new files instead: `values/agents-orchestrator/chat-token.secrets.yaml` (`{chat: {token}}`) and `values/agents-matrix-connector/agent-token.secrets.yaml` (`{agentApi: {tokenSha256}}`), both listed on their releases in `helmfile.yaml.gotmpl`."

Scope (agents-helmfile): `bootstrap_chat_token` in `scripts/bootstrap-secrets.sh` (mirrors `bootstrap_service_token`: `openssl rand -hex 32`, sha256 with `openssl dgst -sha256`, both files or neither, refuses a half state, never prints), called from the script's main list; run the script once to create and commit the two SOPS-encrypted files (encryption needs only the public recipients in `.sops.yaml`); list `values/agents-orchestrator/chat-token.secrets.yaml` on the agents-orchestrator release and `values/agents-matrix-connector/agent-token.secrets.yaml` (with its `default.secrets.yaml`) on the agents-matrix-connector release in `helmfile.yaml.gotmpl`; README bootstrap section names the new files.

## Acceptance conditions

- ac1: the script writes both files, and the hash file's agentApi.tokenSha256 is the sha256 of the token file's chat.token (fake sops) [evidence: test:tests/test_secrets.py::test_chat_token_bootstrapped]
- ac2: with both files present nothing is rewritten, and with exactly one present the script exits 1 naming both and writes nothing [evidence: test:tests/test_secrets.py::test_chat_token_never_rotates]
- ac3: the token and its hash never reach stdout, stderr or a trace [evidence: test:tests/test_secrets.py::test_chat_token_not_printed]
- ac4: the two committed files are SOPS-encrypted with exactly the expected keys [evidence: test:tests/test_secrets.py::test_secrets_files_encrypted_with_expected_keys]
- ac5: helmfile.yaml.gotmpl lists chat-token.secrets.yaml on agents-orchestrator and agent-token.secrets.yaml with default.secrets.yaml on agents-matrix-connector [evidence: test:tests/test_secrets.py::test_chat_token_files_listed_on_releases]
- ac6: (orchestrator session, needs the SOPS key) the decrypted hash matches the decrypted token [evidence: test:tests/test_secrets.py::test_chat_token_hash_matches]
- ac7: the targeted tests and lint (ruff, shellcheck, gitleaks) pass [evidence: command:uv run pytest tests/test_secrets.py && mise run lint]

## Files

- `scripts/bootstrap-secrets.sh`
- `helmfile.yaml.gotmpl`
- `values/agents-orchestrator/chat-token.secrets.yaml`
- `values/agents-matrix-connector/agent-token.secrets.yaml`
- `tests/test_secrets.py`
- `README.md`

## Interfaces

- `values/agents-orchestrator/chat-token.secrets.yaml`: `{chat: {token: <64 hex>}}` (SOPS).
- `values/agents-matrix-connector/agent-token.secrets.yaml`: `{agentApi: {tokenSha256: <64 hex>}}` (SOPS).
- `scripts/bootstrap-secrets.sh:bootstrap_chat_token`.

## Expected outcome

The one chat token exists, encrypted, in the shape each chart reads, and re-running the bootstrap never rotates it.

## Steps

- Red: add the five non-decrypting tests and `test_chat_token_hash_matches` (extend the parametrised `test_secrets_files_encrypted_with_expected_keys`); run `uv run pytest tests/test_secrets.py`: the new tests fail.
- Green: the function, the helmfile listing, README; run `bash scripts/bootstrap-secrets.sh` (only the new function writes; every existing file is left untouched) and commit the two encrypted files; run the task's verify: passes. Quote the summary line with counts.

## Notes

- Follow `bootstrap_service_token` and `bootstrap_matrix_connector` exactly (pipes and env of one command only; nothing echoed or traced).
- `test_chat_token_hash_matches` decrypts and needs the SOPS age key, like `test_matrix_connector_token_hash_matches`; if this pod has no key it fails "sops could not decrypt (key unavailable?)": the orchestrator session runs it (ac6) before chat-live-smoke.
- Build fake tokens at runtime in tests (retro proposal, GitGuardian); gitleaks runs in lint.
- agents-helmfile has no CI workflow (retro tech debt): the reviewer's local verify is the evidence; quote it.

- 2026-10-28 done: PR #41 held unmerged until chat-values (my call)

- 2026-10-28 actuals: no agent records
