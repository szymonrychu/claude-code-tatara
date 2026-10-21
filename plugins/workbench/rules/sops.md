---
paths:
  - "**/*.secret.*.yaml"
  - "**/*.secret.*.yml"
  - "**/default.secrets.yaml"
  - "**/.sops.yaml"
---

# Sops
- Use the `sops-secret-helper` skill to add/update/remove keys. Never directly decrypt/edit/re-encrypt.
- Encrypt before committing: `sops -e -i <file>`
- Key source: `.sops.yaml` in repo root
- Never commit plaintext secrets
