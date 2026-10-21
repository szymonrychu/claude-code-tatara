---
paths:
  - "**/playbooks/**/*.yml"
  - "**/playbooks/**/*.yaml"
  - "**/roles/**/*.yml"
  - "**/roles/**/*.yaml"
  - "**/ansible.cfg"
  - "**/inventory/**"
---

# Ansible

Verify before claiming done:
`ansible-lint && ansible-playbook --check --diff <playbook>` then `molecule test`
where the role has a scenario.

- Idempotency is the property that matters. A task reporting `changed` on every
  run is a bug, and it is what generated code produces by default.
- No bare `shell`/`command` without `changed_when`, `creates`, or `removes`.
  Prefer a real module over shelling out.
- Never run a playbook for real from a session. `--check --diff` only; the
  unchecked form is a live change.
- Name every task. Unnamed tasks make `--check` output unreadable.
- Secrets via sops or vault, never inline.
