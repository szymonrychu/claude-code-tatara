---
name: secrets-env
description: "Load secrets into a gitignored local .env from a committed .env.op reference file, using 1Password (op inject) or a loader command. Use when a task needs credentials in the environment and no .env exists."
---

# secrets-env

Writes a gitignored `.env` from a committed `.env.op` file of references
(for example `TOKEN=op://vault/item/token`). Tools such as `mise` load `.env`
automatically afterwards.

## Check first

If `.env` already exists, do not regenerate it: a fresh `op` call can prompt the
user for biometrics. Regenerate only when secrets were rotated or the file is missing.

## Run

```bash
python3 plugins/workbench-secrets/skills/secrets-env/scripts/secrets_env.py
python3 .../secrets_env.py --out path/to/local.env --ref path/to/.env.op
```

Loader choice:

- default: `op inject -i .env.op -o <tmp>` (needs the 1Password CLI `op`)
- `WORKBENCH_SECRETS_CMD=<command>`: run with the reference file path as its only
  argument; its stdout becomes the dotenv content. Use this for any other secret store.

## Guarantees

- Refuses when the output path is tracked by git or not ignored by git.
- Refuses when neither `op` nor `WORKBENCH_SECRETS_CMD` is available.
- Output file mode is 0600.
- Prints only key names and a count, never values. Do not `cat` the resulting file.
