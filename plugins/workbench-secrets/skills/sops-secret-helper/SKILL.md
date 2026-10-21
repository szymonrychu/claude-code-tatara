---
name: sops-secret-helper
description: "Add, update, or remove keys in SOPS-encrypted YAML files. Never decrypt, edit, or re-encrypt directly - always use the bundled helper script."
---

# sops-secret-helper

Manages SOPS-encrypted YAML files without exposing secret values to AI agents.

**Helper:** `scripts/sops_helper.py` in this skill directory (stdlib python, no dependencies). Run it from anywhere inside the repo; it needs the `sops` binary on PATH and the credentials sops uses (age key, KMS, PGP) available to it.

It only edits files that match a `path_regex` creation rule in the repo's `.sops.yaml` (searched upward from the file) and refuses everything else. It never decrypts to stdout.

## Commands

```bash
H=<path to this skill>/scripts/sops_helper.py

# List key paths (names only, never values) - safe for an agent
python3 "$H" keys <file>

# Add or update a key - the value is read from stdin or from an environment variable
python3 "$H" set <file> <key.path> --from-env MY_VAR
python3 "$H" set <file> <key.path> < value-source

# Remove a key - safe for an agent, no value involved
python3 "$H" remove <file> <key.path>
```

Key path format: dot-separated names, for example `encryptionKey` or `database.password` (letters, digits, `_`, `-`).

## Agent rules - mandatory

| Command | Who runs it | Why |
|---------|-------------|-----|
| `keys` | agent | names only |
| `remove` | agent | no secret value involved |
| `set` | the user, or the agent only with `--from-env` on a variable the user already exported | the value must never be typed into an agent command line or chat |

When a secret value is needed, ask the user to run `set` themselves (they pipe the value on stdin or export the variable first), wait for confirmation, then verify with `keys`.

Never:
- run `sops -d`, `sops --decrypt`, or read an encrypted file's values in any way;
- pipe decrypted output through `yq`, `sed` or anything else;
- echo, cat or print secret content;
- pass a secret value as a command-line argument or in chat.

## Credentials

If sops needs credentials that are not in your shell, load them with the `secrets-env` skill from the `workbench-secrets` pack (it writes a gitignored `.env` from a reference file). Do not hardcode credential commands here.

## Workflow: moving a plaintext secret into an encrypted file

1. Note the key name and where the plaintext value lives.
2. Make sure the target file exists, is encrypted with sops, and matches a `path_regex` rule in `.sops.yaml`.
3. Ask the user to run `set <file> <key.path>` with the value.
4. Delete the plaintext entry from the old file.
5. Verify with `keys` that the key exists in the encrypted file.
6. Run the project's own render or test command to confirm values still resolve.

## Troubleshooting

- "matches no path_regex creation rule": the file path does not match any rule in `.sops.yaml`; fix the rule or the file location.
- "no .sops.yaml found": add a `.sops.yaml` with a `creation_rules` entry for the file.
- "sops failed": credentials for the file's recipients are missing; load them (see Credentials) or import the key.
- "empty value refused": the value source produced nothing; re-run with a non-empty value.
