---
title: secrets bootstrap
status: todo
repo: agents-helmfile
value: "The Claude token, master key and backup credentials exist encrypted in git without ever being shown, so the orchestrator can authenticate agents."
files: [scripts/bootstrap-secrets.sh, values/agent-orchestrator/default.secrets.yaml, values/agent-orchestrator-db/default.secrets.yaml, tests/test_secrets.py]
verify: "uv run pytest tests/test_secrets.py tests/test_repo_hygiene.py -q && mise run lint"
depends_on: [helmfile-base]
owns: []
uses: []
model: ""
estimate: 6
estimate_by: formula
actual: ""
actual_roles: ""
review: ""
worktree: ""
branch: ""
verified_head: ""
run: ""
provides: []
---

# secrets bootstrap

## Requirement

Create the encrypted secrets the two releases need, with a repeatable script, without any secret value ever being printed, logged or committed unencrypted. Use the project's secret helper conventions: the infrastructure helmfile's `scripts/sops-secret-helper.sh` shows the safe way to encrypt and decrypt; raw sops decrypt to stdout is blocked by the guard hook, so the script must only pipe values between processes.

- `scripts/bootstrap-secrets.sh` (bash, `set -euo pipefail`, shellcheck clean, no `set -x`, no echo or printf of any value). It writes each target only when the target file does not exist yet (re-running never rotates a secret):
  1. `values/agent-orchestrator/default.secrets.yaml`, encrypted in place (path matches the `.sops.yaml` rule), holding `claudeOauthToken` (the value of key `CLAUDE_CODE_OAUTH_TOKEN`) and `masterKey` (`openssl rand -hex 32`, 64 hex chars, generated once). The OAuth token is read from the existing Kubernetes secret: the script finds the secret holding key `CLAUDE_CODE_OAUTH_TOKEN` by listing secret names and key NAMES only (`kubectl -n tatara get secrets -o json | jq -r '.items[] | select(.data | has("CLAUDE_CODE_OAUTH_TOKEN")) | .metadata.name'`), then falls back to namespace `magic-trainer`; the value is read with `kubectl get secret <name> -o jsonpath='{.data.CLAUDE_CODE_OAUTH_TOKEN}' | base64 -d` straight into a variable or pipe to the encryptor, never to the terminal. When neither namespace has the key the script exits 1 naming the namespaces and no value.
  2. `values/agent-orchestrator-db/default.secrets.yaml`, holding the S3 backup credentials `backups.s3.accessKey` and `backups.s3.secretKey` copied from the infrastructure helmfile's `helmfiles/media/values/jellystat-database/default.secrets.yaml` (decrypted in memory, filtered with jq/yq to exactly those two keys, re-encrypted with this repo's `.sops.yaml`).
- The script is run once by the implementer; the two encrypted files are committed. The plaintext of neither file ever touches disk or output.
- `tests/test_secrets.py`: both files exist, are encrypted (top-level `sops.pgp`, all scalar leaves `ENC[`), contain the expected key names, and the script source has no `set -x`, no echo/printf of the variables holding secret values, and passes shellcheck `--severity=error`.

## Acceptance conditions

- AC1: both secrets files exist, are encrypted and carry the expected key names [evidence: command:uv run pytest tests/test_secrets.py -q -k secrets_files_encrypted_with_expected_keys]
- AC2: the script never prints or traces a secret value [evidence: command:uv run pytest tests/test_secrets.py -q -k script_never_prints_values]
- AC3: the script never overwrites an existing secrets file [evidence: command:uv run pytest tests/test_secrets.py -q -k script_does_not_overwrite_existing]
- AC4: the script is shellcheck clean [evidence: command:shellcheck --severity=error scripts/bootstrap-secrets.sh]
- AC5: no plaintext secret is tracked [evidence: command:uv run pytest tests/test_repo_hygiene.py -q]

## Files

- `scripts/bootstrap-secrets.sh`
- `values/agent-orchestrator/default.secrets.yaml`
- `values/agent-orchestrator-db/default.secrets.yaml`
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
