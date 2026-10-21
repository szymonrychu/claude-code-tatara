---
paths:
  - "**/*.enc.*"
  - "**/*.secret.*"
  - "**/secrets.*.y?ml"
  - "**/.sops.yaml"
---

# Sops
- Use the `sops-secret-helper` skill of the `workbench-secrets` pack, when the pack is enabled, to add/update/remove keys. Never directly decrypt/edit/re-encrypt.
- Encrypt before committing: `sops -e -i <file>`
- Key source: `.sops.yaml` in repo root
- Never commit plaintext secrets
