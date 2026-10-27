---
title: helmfile relay secrets
status: todo
repo: agents-helmfile
value: "the one relay token exists, encrypted, in the shape both charts read, and never rotates"
files: [scripts/bootstrap-secrets.sh, helmfile.yaml.gotmpl, values/agents-orchestrator/schedule-token.secrets.yaml, values/agents-schedule/relay-token.secrets.yaml, tests/test_secrets.py, README.md]
verify: "uv run pytest tests/test_secrets.py && mise run lint"
depends_on: [orch-chart-schedule-relay, sched-chart-relay-port]
model: opus
review: ""
verified_head: ""
points: 3
expected_minutes: 6
expected_tokens: 936557
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# helmfile relay secrets

## Requirement

README Goal G5, verbatim: "Schedule calls go through the orchestrator, which relays them to a token-protected listener on agents-schedule that records each schedule's owner; the agent token never leaves the orchestrator."

Design D16, verbatim: "`scripts/bootstrap-secrets.sh` generates one relay token: the orchestrator file `values/agents-orchestrator/schedule-token.secrets.yaml` (`schedule.token`) and the schedule file `values/agents-schedule/relay-token.secrets.yaml` (`relay.tokenSha256`, its sha256), both SOPS-encrypted, both or neither, never rotated."

Scope (agents-helmfile): `scripts/bootstrap-secrets.sh` (a `bootstrap_schedule_relay` step), `helmfile.yaml.gotmpl` (the two files listed on their releases), the two committed SOPS files (written by the orchestrator session, which holds the SOPS key), `tests/test_secrets.py`, README (the new secret). Mirrors Matrix helmfile-chat-secrets.

## Acceptance conditions

- ac1: the script writes both files, and the hash file's relay.tokenSha256 is the sha256 of the token file's schedule.token (fake sops) [evidence: test:tests/test_secrets.py::test_schedule_relay_token_bootstrapped]
- ac2: with both files present nothing is rewritten, and with exactly one present the script exits 1 naming both and writes nothing [evidence: test:tests/test_secrets.py::test_schedule_relay_token_never_rotates]
- ac3: the token and its hash never reach stdout, stderr or a trace [evidence: test:tests/test_secrets.py::test_schedule_relay_token_not_printed]
- ac4: the two committed files are SOPS-encrypted with exactly the expected keys [evidence: test:tests/test_secrets.py::test_secrets_files_encrypted_with_expected_keys]
- ac5: helmfile.yaml.gotmpl lists schedule-token.secrets.yaml on agents-orchestrator and relay-token.secrets.yaml with default.secrets.yaml on agents-schedule [evidence: test:tests/test_secrets.py::test_schedule_relay_files_listed_on_releases]
- ac6: (orchestrator session, needs the SOPS key) the decrypted hash matches the decrypted token [evidence: test:tests/test_secrets.py::test_schedule_relay_token_hash_matches]
- ac7: the targeted tests and lint (ruff, shellcheck, gitleaks) pass [evidence: command:uv run pytest tests/test_secrets.py && mise run lint]

## Files

- `scripts/bootstrap-secrets.sh`
- `helmfile.yaml.gotmpl`
- `values/agents-orchestrator/schedule-token.secrets.yaml`
- `values/agents-schedule/relay-token.secrets.yaml`
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
