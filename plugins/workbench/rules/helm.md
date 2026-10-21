---
paths:
  - "**/Chart.yaml"
  - "**/helmfile.yaml"
  - "**/helmfile.d/**"
  - "**/values*.yaml"
---

# Helm / Helmfile

Verify before claiming done:
`helm lint <chart> && helm template <chart> | kubeconform -strict`

- `helm lint` alone is not enough. A wrong `nindent` produces well-formed YAML
  with the wrong structure - a key silently promoted to a sibling of
  `containers` renders happily and passes lint. Only schema validation against
  the rendered output catches it, so always render and validate.
- `helmfile diff` before any apply. Never run `helmfile apply`/`sync` or
  `helm upgrade`/`install`/`uninstall` from a session; produce the diff.
- `values.schema.json` and chart READMEs are generated. Edit the generator
  inputs, never the outputs.
- Secrets live in sops-encrypted values files, never plaintext.
- Bump `Chart.yaml` version per semver on every chart change.
