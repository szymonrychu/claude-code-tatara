---
title: helmfile chat secrets
status: todo
repo: agents-helmfile
value: "the one chat token exists, encrypted, in the shape both charts read, and never rotates"
files: [scripts/bootstrap-secrets.sh, helmfile.yaml.gotmpl, values/agents-orchestrator/chat-token.secrets.yaml, values/agents-matrix-connector/agent-token.secrets.yaml, tests/test_secrets.py, README.md]
verify: "uv run pytest tests/test_secrets.py && mise run lint"
depends_on: [mxc-chart-agent-port, orch-chart-chat]
model: opus
review: ""
verified_head: ""
points: 3
expected_minutes: 6
expected_tokens: 941421
points_actual: ""
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

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
