---
paths:
  - "**/*.tf"
  - "**/*.tfvars"
---

# Terraform

Verify before claiming done:
`terraform fmt -check && terraform validate && terraform plan -out=tfplan`

- Never run `apply`, `destroy`, or `state rm`. Produce a plan and hand it over.
  `apply` only ever consumes an existing plan file, never a bare invocation.
- Do not invent resource arguments. If unsure an argument exists in the pinned
  provider version, read the provider docs first (context7 or the registry).
  Hallucinated arguments are this stack's most common failure.
- `count`/`for_each` changes rename resource addresses: emit a `moved` block
  rather than letting Terraform destroy and recreate.
- `plan` still takes the state lock, so it is safe but not side-effect free.
  Expect contention if CI is planning at the same time.
- Variables in `variables.tf`, outputs in `outputs.tf`, repeated expressions in
  `locals {}`.
