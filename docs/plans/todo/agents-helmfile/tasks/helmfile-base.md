---
title: helmfile base
status: todo
repo: agents-helmfile
value: "The namespace-agents helmfile skeleton with the regcred hook, so releases render and apply the way the rest of the homelab does."
files: [helmfile.yaml.gotmpl, .hook.sh, values/common.yaml, raw/regcred.pre.secrets.yaml, tests/conftest.py, tests/test_helmfile_base.py]
verify: "uv run pytest tests/test_helmfile_base.py -q && mise run lint"
depends_on: [scaffold-repo]
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

# helmfile base

## Requirement

Add the helmfile skeleton for namespace `agents` that the release tasks fill. Copy the shape of the infrastructure helmfile (`helmfiles/ai/helmfile.yaml.gotmpl` header and `templates.default`, `.hook.sh`) but flatten it to one helmfile.

- `helmfile.yaml.gotmpl`: `repositories` (cnpg https://cloudnative-pg.github.io/charts), `helmDefaults` (`wait: true`, `syncArgs: [--rollback-on-failure]`), `templates.default` anchor with `missingFileHandler: Warn`, the prepare/presync/postsync hook running `./.hook.sh` with the same six args, the `values:` layering `values/common.yaml` -> `values/<release>/common.yaml` -> `values/<release>/default.yaml` and `secrets: values/<release>/default.secrets.yaml`; `releases: []` (the release tasks append to it). A comment states that releases live in namespace `agents`, which helm creates on first install.
- `.hook.sh`: copied from the infrastructure helmfile and trimmed: keep fail(), apply_dir, run_kubectl and its secrets variant with the prepare drift banding, the unreachable-cluster guard, the failed-release cleanup, per-release `values/<release>/raw/*.common.{pre,post}.yaml` and `*.secrets.yaml` handling and the global `raw/` apply. Before the first `raw/` apply of a presync it ensures the release namespace exists (`kubectl create namespace "$RELEASE_NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -`), because the regcred Secret is applied before helm creates the namespace. Drop the GitLab-pipeline-specific drift handling (no CI here); drift during `prepare` only prints.
- `values/common.yaml`: `global.imagePullSecrets` and `imagePullSecrets` = `[{name: regcred}]`.
- `raw/regcred.pre.secrets.yaml`: copy the encrypted file from ~/Documents/infrastructure/code/helmfile/raw/ byte for byte (same PGP key); never decrypt it to disk.
- `tests/conftest.py`: fixtures `repo_root`, `helmfile_build()` (runs `helmfile -f helmfile.yaml.gotmpl build` and returns the parsed release documents; fails when helmfile is missing rather than skipping) and `layered_values(release)` (deep-merges the plain values files in helmfile order, no decryption) so release tasks assert on real rendered state.
- `tests/test_helmfile_base.py` asserts the structure above, that `.hook.sh` is executable and passes shellcheck `--severity=error`, that the hook source creates the namespace before applying `raw/`, and that `raw/regcred.pre.secrets.yaml` is encrypted.

## Acceptance conditions

- AC1: helmfile build succeeds and the default template layers values and secrets as specified [evidence: command:uv run pytest tests/test_helmfile_base.py -q -k default_template_layers_values]
- AC2: the hook ensures the namespace exists before applying raw manifests [evidence: command:uv run pytest tests/test_helmfile_base.py -q -k hook_creates_namespace_first]
- AC3: .hook.sh is executable and shellcheck clean [evidence: command:uv run pytest tests/test_helmfile_base.py -q -k hook_is_executable_and_shellcheck_clean]
- AC4: values/common.yaml sets regcred as the image pull secret [evidence: command:uv run pytest tests/test_helmfile_base.py -q -k common_values_use_regcred]
- AC5: raw/regcred.pre.secrets.yaml is present and encrypted [evidence: command:uv run pytest tests/test_helmfile_base.py -q -k regcred_is_encrypted]
- AC6: the shared render fixture exists [evidence: symbol:tests/conftest.py::helmfile_build]
- AC7: layered_values merges plain values in helmfile order [evidence: symbol:tests/conftest.py::layered_values]

## Files

- `helmfile.yaml.gotmpl`
- `.hook.sh`
- `values/common.yaml`
- `raw/regcred.pre.secrets.yaml`
- `tests/conftest.py`
- `tests/test_helmfile_base.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
