# workbench-secrets

Optional pack for the workbench template: load secrets into a local, gitignored
`.env` without personal shell functions.

Requires the workbench core plugin.

## Contents

- `secrets-env` skill: `scripts/secrets_env.py` writes `.env` from a committed
  `.env.op` reference file via `op inject` (1Password CLI) or the loader command in
  `WORKBENCH_SECRETS_CMD`. Refuses tracked or non-ignored output paths, writes mode
  0600, never prints values.
- `sops-secret-helper` skill: `scripts/sops_helper.py` with `keys`, `set` and `remove`
  for SOPS-encrypted YAML. Refuses files matching no `path_regex` in `.sops.yaml`,
  reads values from stdin or `--from-env`, never decrypts or prints values.

## Enable

Add the pack to the project's `.claude/settings.json`:

```json
{
  "enabledPlugins": {
    "workbench@workbench": true,
    "workbench-secrets@workbench": true
  }
}
```

## Test

`mise run test:pack-secrets`
