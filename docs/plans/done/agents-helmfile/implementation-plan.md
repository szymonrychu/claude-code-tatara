# agents-helmfile implementation plan

## Agreed rung

Rung 1 of plan.md, migrated from the epic format: the steps are the epic's tasks.

## Approach

Migrated from the epic format: one step per task file, in dependency order, each with its status, files, verify, verified head and every body section.

## Chunk 1: migrated tasks (model: sonnet)

### S1: scaffold repo

- Status: done
- Files: `pyproject.toml`, `uv.lock`, `mise.toml`, `.gitignore`, `.sops.yaml`, `.gitleaks.toml`, `.pre-commit-config.yaml`, `tests/test_repo_hygiene.py`
- Verify: `uv run pytest tests/test_repo_hygiene.py -q && mise run lint`
- Verified head: 4f155da761f11325817e9d628bce76eb0d80a1cb

#### Requirement

Create the repo skeleton of code/agents-helmfile (public GitHub origin szymonrychu/agents-helmfile; the orchestrator creates the empty repo, its origin and the superrepo submodule pointer before the run). Mirror ~/Documents/infrastructure/code/helmfile but only what one namespace needs.

- `pyproject.toml` (uv project `agents-helmfile`, Python 3.12, no package; dev group pytest, pyyaml, ruff) and `uv.lock`; pytest config `testpaths = ["tests"]`, `addopts = "-q"`; ruff line length 100.
- `mise.toml`: tools helm 4.3.1, helmfile 1.8.2, sops 3.13.3, kubectl 1.33.13, shellcheck 0.11.0, gitleaks, pre-commit 4.7.0, python 3.12, uv, jq; `[env]` optionally loads a local `.env` if present (`_.file = { path = ".env", redact = true }` or equivalent that tolerates absence); the helm plugin postinstall hooks copied from the infrastructure helmfile `.mise.toml` (helm-secrets v4.7.4 incl. secrets-getter and post-renderer, helm-diff); tasks `lint` (`uv run ruff check . && uv run ruff format --check .`, shellcheck `--severity=error` over tracked `*.sh` and `.hook.sh`, then `gitleaks detect --no-git --source . --redact`) and `test` (`uv run pytest`).
- `.sops.yaml` copied from the infrastructure helmfile (PGP D39E46932A270AA3BA490B9DB9FE928D3E8BCED8; rules for `default.secrets.yaml`, `.*.secret.*.yaml`, plus one for `.*\.secrets\.yaml`).
- `.gitignore`: `.env`, `.venv`, `__pycache__`, `.pytest_cache`, `.ruff_cache`.
- `.gitleaks.toml` (default ruleset extended; allowlist only paths of SOPS-encrypted files) and `.pre-commit-config.yaml` (trailing-whitespace, end-of-file-fixer, check-yaml with multiple documents, gitleaks, conventional-pre-commit) copied and trimmed from the infrastructure helmfile.
- `.envrc` (`use mise`) mirrored from the infrastructure helmfile repo; no `.env` file is created. User decision (2026-10-23): ~/Documents/infrastructure/code/helmfile has no .env (its .envrc is `use mise`); do not copy any .env. Mirror that repo's `.envrc` (`use mise`) and `.mise.toml` instead: its tools (helm 4.3.1, helmfile 1.8.2, sops 3.13.3, kubectl 1.33.13, kubectx, stern, shellcheck, pre-commit) and its postinstall hooks (helm-secrets 4.7.4 plugins, helm-diff, pre-commit install), plus python/uv/gitleaks for tests. Keep `.env` in .gitignore for local overrides, but create none.
- `tests/test_repo_hygiene.py`: (1) `.env` is git-ignored (`git check-ignore .env`) and no `.env` is tracked; (2) every tracked file whose name matches `*.secrets.yaml` or `*.secret.*.yaml` has a top-level `sops` key with a `pgp` entry and its scalar leaves start with `ENC[`; (3) no tracked file contains a plaintext secret pattern (`sk-ant-`, `-----BEGIN .*PRIVATE KEY-----`, a `CLAUDE_CODE_OAUTH_TOKEN:` value that is not `ENC[`); (4) `gitleaks detect --no-git --source . --redact` exits 0.

#### Acceptance conditions

- AC1: .env is git-ignored and never tracked [evidence: command:uv run pytest tests/test_repo_hygiene.py -q -k env_ignored_and_untracked]
- AC2: every tracked secrets file is encrypted [evidence: command:uv run pytest tests/test_repo_hygiene.py -q -k secrets_files_are_encrypted]
- AC3: no tracked file holds a plaintext secret pattern [evidence: command:uv run pytest tests/test_repo_hygiene.py -q -k no_plaintext_secrets]
- AC4: gitleaks finds nothing in the tree [evidence: command:uv run pytest tests/test_repo_hygiene.py -q -k gitleaks_clean]
- AC5: mise defines the lint and test tasks and loads .env [evidence: command:mise tasks ls | grep -q '^lint' && mise tasks ls | grep -q '^test' && grep -q '\.env' mise.toml]
- AC6: no .env is created or tracked; .env stays git-ignored for local overrides (user decision 2026-10-23) [evidence: command:! git ls-files --error-unmatch .env 2>/dev/null && git check-ignore -q .env]
- AC7: lint passes [evidence: command:mise run lint]

#### Files

- `pyproject.toml`
- `uv.lock`
- `mise.toml`
- `.gitignore`
- `.sops.yaml`
- `.gitleaks.toml`
- `.pre-commit-config.yaml`
- `tests/test_repo_hygiene.py`

#### Interfaces

none (no shared parts owned).

#### Expected outcome

The repo has working lint and test tasks, a local mode-600 untracked `.env`, and hygiene tests that guard every later commit.

#### Steps

- Write tests/test_repo_hygiene.py; run `uv run pytest tests/test_repo_hygiene.py -q`; expect failures (no .gitignore yet, gitleaks missing).
- Write pyproject.toml, mise.toml, .gitignore, .sops.yaml, .gitleaks.toml, .pre-commit-config.yaml; `uv lock`; `cp` the .env and chmod 600 (never print it).
- Rerun the tests and `mise run lint`; expect `passed` and a clean lint.

#### Notes

Copy from ~/Documents/infrastructure/code/helmfile (`.mise.toml`, `.sops.yaml`, `.gitleaks.toml`, `.pre-commit-config.yaml`). Reading `.env` is forbidden: copy only. The tests assert on `git ls-files`, never the filesystem, for tracked-ness.

### S2: helmfile base

- Status: done
- Files: `helmfile.yaml.gotmpl`, `.hook.sh`, `values/common.yaml`, `raw/regcred.pre.secrets.yaml`, `tests/conftest.py`, `tests/test_helmfile_base.py`
- Verify: `uv run pytest tests/test_helmfile_base.py -q && mise run lint`
- Verified head: bccbbef451145660efb6091b91ad618385eed8d4

#### Requirement

Add the helmfile skeleton for namespace `agents` that the release tasks fill. Copy the shape of the infrastructure helmfile (`helmfiles/ai/helmfile.yaml.gotmpl` header and `templates.default`, `.hook.sh`) but flatten it to one helmfile.

- `helmfile.yaml.gotmpl`: `repositories` (cnpg https://cloudnative-pg.github.io/charts), `helmDefaults` (`wait: true`, `syncArgs: [--rollback-on-failure]`), `templates.default` anchor with `missingFileHandler: Warn`, the prepare/presync/postsync hook running `./.hook.sh` with the same six args, the `values:` layering `values/common.yaml` -> `values/<release>/common.yaml` -> `values/<release>/default.yaml` and `secrets: values/<release>/default.secrets.yaml`; `releases: []` (the release tasks append to it). A comment states that releases live in namespace `agents`, which helm creates on first install.
- `.hook.sh`: copied from the infrastructure helmfile and trimmed: keep fail(), apply_dir, run_kubectl and its secrets variant with the prepare drift banding, the unreachable-cluster guard, the failed-release cleanup, per-release `values/<release>/raw/*.common.{pre,post}.yaml` and `*.secrets.yaml` handling and the global `raw/` apply. Before the first `raw/` apply of a presync it ensures the release namespace exists (`kubectl create namespace "$RELEASE_NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -`), because the regcred Secret is applied before helm creates the namespace. Drop the GitLab-pipeline-specific drift handling (no CI here); drift during `prepare` only prints.
- `values/common.yaml`: `global.imagePullSecrets` and `imagePullSecrets` = `[{name: regcred}]`.
- `raw/regcred.pre.secrets.yaml`: copy the encrypted file from ~/Documents/infrastructure/code/helmfile/raw/ byte for byte (same PGP key); never decrypt it to disk.
- `tests/conftest.py`: fixtures `repo_root`, `helmfile_build()` (runs `helmfile -f helmfile.yaml.gotmpl build` and returns the parsed release documents; fails when helmfile is missing rather than skipping) and `layered_values(release)` (deep-merges the plain values files in helmfile order, no decryption) so release tasks assert on real rendered state.
- `tests/test_helmfile_base.py` asserts the structure above, that `.hook.sh` is executable and passes shellcheck `--severity=error`, that the hook source creates the namespace before applying `raw/`, and that `raw/regcred.pre.secrets.yaml` is encrypted.

#### Acceptance conditions

- AC1: helmfile build succeeds and the default template layers values and secrets as specified [evidence: command:uv run pytest tests/test_helmfile_base.py -q -k default_template_layers_values]
- AC2: the hook ensures the namespace exists before applying raw manifests [evidence: command:uv run pytest tests/test_helmfile_base.py -q -k hook_creates_namespace_first]
- AC3: .hook.sh is executable and shellcheck clean [evidence: command:uv run pytest tests/test_helmfile_base.py -q -k hook_is_executable_and_shellcheck_clean]
- AC4: values/common.yaml sets regcred as the image pull secret [evidence: command:uv run pytest tests/test_helmfile_base.py -q -k common_values_use_regcred]
- AC5: raw/regcred.pre.secrets.yaml is present and encrypted [evidence: command:uv run pytest tests/test_helmfile_base.py -q -k regcred_is_encrypted]
- AC6: the shared render fixture exists [evidence: symbol:tests/conftest.py::helmfile_build]
- AC7: layered_values merges plain values in helmfile order [evidence: symbol:tests/conftest.py::layered_values]

#### Files

- `helmfile.yaml.gotmpl`
- `.hook.sh`
- `values/common.yaml`
- `raw/regcred.pre.secrets.yaml`
- `tests/conftest.py`
- `tests/test_helmfile_base.py`

#### Interfaces

Fixtures `helmfile_build` and `layered_values` in tests/conftest.py, used by db-release and orchestrator-release.

#### Expected outcome

`helmfile build` renders the (still empty) helmfile, the hook is shellcheck clean and creates the namespace before applying regcred, and the render fixtures exist for the release tasks.

#### Steps

- Write tests/conftest.py and tests/test_helmfile_base.py; run `uv run pytest tests/test_helmfile_base.py -q`; expect failures (files missing).
- Create helmfile.yaml.gotmpl, .hook.sh (copy and trim), values/common.yaml; copy raw/regcred.pre.secrets.yaml with `cp`.
- Rerun the tests and `mise run lint`; expect `passed`. Probe whether `helmfile build` needs network or decryption and write the result into the conftest docstring.

#### Notes

Source: ~/Documents/infrastructure/code/helmfile/.hook.sh and helmfiles/ai/helmfile.yaml.gotmpl header. The hook runs as ./.hook.sh from the repo root, so CURRENT_PWD logic and the `helmfiles/<phase>/values` path must become `values/<release>`.

### S3: hook missing namespace

- Status: done
- Files: `.hook.sh`, `tests/test_helmfile_base.py`
- Verify: `uv run pytest tests/test_helmfile_base.py -q && mise run lint`
- Verified head: 1fcd489ba971394e2d64fdca49f904ba730a3f11

#### Requirement

Found by db-release on the live cluster: the .hook.sh prepare step runs kubectl diff on raw/regcred.pre.secrets.yaml and fails (rc=2, 'namespaces "agents" not found') before the namespace exists, so helmfile build/diff exits 1 on a fresh cluster. Make the prepare step tolerate a missing namespace: when namespace agents does not exist, skip the regcred diff (report it as to-be-created) and let presync create the namespace and apply regcred as today. Keep the rc>1 abort for every other kubectl failure. Pin it with a test that stubs kubectl to return NotFound for the namespace.

#### Acceptance conditions

- AC1: prepare on a missing namespace does not fail and reports the namespace as to-be-created [evidence: test:tests/test_helmfile_base.py::test_prepare_tolerates_missing_namespace]
- AC2: any other kubectl failure still aborts [evidence: test:tests/test_helmfile_base.py::test_prepare_aborts_on_other_kubectl_errors]

#### Files

- `.hook.sh`
- `tests/test_helmfile_base.py`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

helmfile build/diff/apply work against a cluster without namespace agents.

What is true and observable when the task is done.

#### Steps

- Red: live helmfile build exits 1 (namespaces agents not found); write the stubbed-kubectl tests, see them fail.
- Make prepare tolerate a missing namespace; run green and the live build.

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

#### Ruling

- 2026-10-23 accepted: round-cap only on AC3, which could not pass before the release tasks land (planning error by the orchestrator); AC3 moved to db-release AC5. AC1/AC2 verified on 1fcd489: tests/test_helmfile_base.py passed, lint and gitleaks clean.

- 2026-10-23 accepted: round-cap only on AC3, which could not pass before the release tasks land (orchestrator planning error); AC3 moved to db-release AC5; AC1/AC2 verified on 1fcd489.

#### Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.

#### Notes

AC3 (live helmfile build on a cluster without namespace agents) moved to db-release AC5: it cannot pass before any release exists (orchestrator ruling 2026-10-23).

### S4: mise tasks

- Status: done
- Files: `mise.toml`, `README.md`, `tests/test_mise_tasks.py`
- Verify: `uv run pytest tests/test_mise_tasks.py -q && mise run lint`
- Verified head: 05c971cbc6dfcb03a0a6f259508d894dd6f1b8db

#### Requirement

Add the operator tasks and the README.

- `mise.toml` tasks `diff`: `helmfile -f helmfile.yaml.gotmpl diff --detailed-exitcode --suppress-secrets` (exit 2 means changes; the task documents it and passes it through); `apply`: `helmfile -f helmfile.yaml.gotmpl apply --suppress-secrets` (hook-driven regcred and raw manifests, rollback on failure from helmDefaults). Both load `.env` through the mise `[env]` block, never call scripts/bootstrap-secrets.sh, and accept `--selector name=<release>` as a task argument. `apply` has `depends = ["lint", "test"]` so a broken tree cannot be applied. A `kube-context` guard task (a `depends` of diff and apply) fails unless `kubectl config current-context` is non-empty and `kubectl version` reaches the API, printing only the context name.
- `README.md`: what the repo is, the namespace, releases and host, that the ingress is LAN-only without auth, tooling (mise mirrored from the infrastructure helmfile; optional local `.env`, ignored, never printed), the secrets bootstrap, and a `## Operating` section covering `mise run lint|test|diff|apply|smoke`; applies are manual and local.
- `tests/test_mise_tasks.py` parses mise.toml (tomllib) and asserts the tasks diff, apply, lint and test exist, diff uses `--detailed-exitcode` and `--suppress-secrets`, apply depends on lint and test, no task redirects a decrypt to a file, and the README names every task.

#### Acceptance conditions

- AC1: diff and apply tasks exist with the detailed exit code and suppressed secrets [evidence: command:uv run pytest tests/test_mise_tasks.py -q -k diff_and_apply_tasks]
- AC2: apply depends on lint and test [evidence: command:uv run pytest tests/test_mise_tasks.py -q -k apply_depends_on_lint_and_test]
- AC3: no task decrypts secrets to disk [evidence: command:uv run pytest tests/test_mise_tasks.py -q -k no_task_decrypts_to_disk]
- AC4: README documents the repo and every mise task [evidence: doc-section:README.md#Operating]
- AC5: mise lists the tasks [evidence: command:mise tasks ls | grep -q '^diff' && mise tasks ls | grep -q '^apply']

#### Files

- `mise.toml`
- `README.md`
- `tests/test_mise_tasks.py`

#### Interfaces

none

#### Expected outcome

`mise run diff` and `mise run apply` exist, are guarded, and the README explains the repo.

#### Steps

- Write tests/test_mise_tasks.py; run it; expect failures.
- Add the tasks to mise.toml and write README.md.
- Rerun the test and `mise run lint`; expect `passed`.

#### Notes

Do not run apply or diff against the cluster in this task. mise.toml was created by scaffold-repo: only add tasks.

### S5: secrets bootstrap

- Status: done
- Files: `scripts/bootstrap-secrets.sh`, `values/agent-orchestrator/default.secrets.yaml`, `values/agent-orchestrator-db/default.secrets.yaml`, `tests/test_secrets.py`
- Verify: `uv run pytest tests/test_secrets.py tests/test_repo_hygiene.py -q && mise run lint`
- Verified head: bc4e0d317f1aedade99bfd0a70633790275f3d37

#### Requirement

Create the encrypted secrets the two releases need, with a repeatable script, without any secret value ever being printed, logged or committed unencrypted. Use the project's secret helper conventions: the infrastructure helmfile's `scripts/sops-secret-helper.sh` shows the safe way to encrypt and decrypt; raw sops decrypt to stdout is blocked by the guard hook, so the script must only pipe values between processes.

- `scripts/bootstrap-secrets.sh` (bash, `set -euo pipefail`, shellcheck clean, no `set -x`, no echo or printf of any value). It writes each target only when the target file does not exist yet (re-running never rotates a secret):
  1. `values/agent-orchestrator/default.secrets.yaml`, encrypted in place (path matches the `.sops.yaml` rule), holding `claudeOauthToken` (the value of key `CLAUDE_CODE_OAUTH_TOKEN`) and `masterKey` (`openssl rand -hex 32`, 64 hex chars, generated once). The OAuth token is read from the existing Kubernetes secret: the script finds the secret holding key `CLAUDE_CODE_OAUTH_TOKEN` by listing secret names and key NAMES only (`kubectl -n tatara get secrets -o json | jq -r '.items[] | select(.data | has("CLAUDE_CODE_OAUTH_TOKEN")) | .metadata.name'`), then falls back to namespace `magic-trainer`; the value is read with `kubectl get secret <name> -o jsonpath='{.data.CLAUDE_CODE_OAUTH_TOKEN}' | base64 -d` straight into a variable or pipe to the encryptor, never to the terminal. When neither namespace has the key the script exits 1 naming the namespaces and no value.
  2. `values/agent-orchestrator-db/default.secrets.yaml`, holding the S3 backup credentials `backups.s3.accessKey` and `backups.s3.secretKey` copied from the infrastructure helmfile's `helmfiles/media/values/jellystat-database/default.secrets.yaml` (decrypted in memory, filtered with jq/yq to exactly those two keys, re-encrypted with this repo's `.sops.yaml`).
- The script is run once by the implementer; the two encrypted files are committed. The plaintext of neither file ever touches disk or output.
- `tests/test_secrets.py`: both files exist, are encrypted (top-level `sops.pgp`, all scalar leaves `ENC[`), contain the expected key names, and the script source has no `set -x`, no echo/printf of the variables holding secret values, and passes shellcheck `--severity=error`.

#### Acceptance conditions

- AC1: both secrets files exist, are encrypted and carry the expected key names [evidence: command:uv run pytest tests/test_secrets.py -q -k secrets_files_encrypted_with_expected_keys]
- AC2: the script never prints or traces a secret value [evidence: command:uv run pytest tests/test_secrets.py -q -k script_never_prints_values]
- AC3: the script never overwrites an existing secrets file [evidence: command:uv run pytest tests/test_secrets.py -q -k script_does_not_overwrite_existing]
- AC4: the script is shellcheck clean [evidence: command:shellcheck --severity=error scripts/bootstrap-secrets.sh]
- AC5: no plaintext secret is tracked [evidence: command:uv run pytest tests/test_repo_hygiene.py -q]

#### Files

- `scripts/bootstrap-secrets.sh`
- `values/agent-orchestrator/default.secrets.yaml`
- `values/agent-orchestrator-db/default.secrets.yaml`
- `tests/test_secrets.py`

#### Interfaces

Encrypted keys: `claudeOauthToken`, `masterKey` (values/agent-orchestrator/default.secrets.yaml); `backups.s3.accessKey`, `backups.s3.secretKey` (values/agent-orchestrator-db/default.secrets.yaml).

#### Expected outcome

Two committed, encrypted secrets files exist; running the script again changes nothing; no value appears in any output.

#### Steps

- Write tests/test_secrets.py; run it; expect failures (files missing).
- Write scripts/bootstrap-secrets.sh and run it once with cluster access (`bash scripts/bootstrap-secrets.sh`), reading its exit status only.
- Rerun `uv run pytest tests/test_secrets.py tests/test_repo_hygiene.py -q` and `mise run lint`; expect `passed`.

#### Notes

The guard hook blocks raw sops decrypt to stdout and secrets in transcripts: read ~/Documents/infrastructure/code/helmfile/scripts/sops-secret-helper.sh for the sanctioned way, and never run a command whose output could contain a value. Secret key names the chart reads (`claudeOauthToken`, `masterKey`) may be remapped by orchestrator-release to the chart's key names; keep them stable here.

### S6: db release

- Status: done
- Files: `helmfile.yaml.gotmpl`, `values/agent-orchestrator-db/common.yaml`, `tests/test_db_release.py`
- Verify: `uv run pytest tests/test_db_release.py -q && mise run lint`
- Verified head: 1544c272131989687db0f9aa02024cd3ca7074f7

#### Requirement

Add release `agent-orchestrator-db` to `helmfile.yaml.gotmpl`: chart `cnpg/cluster` version 0.9.0, namespace `agents`, `force: false` (helm --force would delete and recreate the Cluster CR and is incompatible with Helm 4 server-side apply), timeout 600, labels `purpose: agents`, `application: agent-orchestrator`, `<<: *default`.

`values/agent-orchestrator-db/common.yaml`, sized like the infrastructure `helmfiles/ai/values/buzz-database/common.yaml`: `version.postgresql: "16"`, `cluster` with `enablePDB: false`, `instances: 1`, storage 5Gi on `rook-ceph`, walStorage enabled 2Gi on `rook-ceph`, resources (requests 100m/256Mi, limits 1000m/1Gi), `monitoring.enabled: false`, `initdb` database `agent_orchestrator` owner `agent_orchestrator` (CNPG generates the `agent-orchestrator-db-app` Secret with keys `uri`, `host`, `port`, `dbname`, `user`, `password`; the orchestrator release reads that Secret). Backups copied from the infrastructure helmfile's `helmfiles/media/values/jellystat-database/common.yaml` (the databases in the ai bucket have backups disabled; jellystat and home-assistant are the ones with `backups.enabled: true`): `backups.enabled: true`, `provider: s3`, `s3.region: eu-central-1`, `s3.bucket: database-backup-szymonrychu`, `s3.path: /agent-orchestrator-db/`, `retentionPolicy: "30d"`, `scheduledBackups` daily at `0 0 3 * * *` with `backupOwnerReference: self` and `method: barmanObjectStore`; accessKey and secretKey come from the encrypted file made by secrets-bootstrap.

`tests/test_db_release.py` asserts on `helmfile_build()` and `layered_values('agent-orchestrator-db')`: chart, version, namespace, `force: false`, the initdb names, storage classes, backups enabled with the path `/agent-orchestrator-db/` (never another application's path), and that the layered plain values contain no accessKey or secretKey.

#### Acceptance conditions

- AC1: the release uses cnpg/cluster 0.9.0 in namespace agents with force false [evidence: command:uv run pytest tests/test_db_release.py -q -k release_chart_namespace_and_force]
- AC2: initdb creates database and owner agent_orchestrator [evidence: command:uv run pytest tests/test_db_release.py -q -k initdb_names]
- AC3: backups are enabled to the agent-orchestrator-db path with a daily schedule and 30d retention [evidence: command:uv run pytest tests/test_db_release.py -q -k backups_enabled_with_own_path]
- AC4: plain values carry no S3 credentials [evidence: command:uv run pytest tests/test_db_release.py -q -k no_credentials_in_plain_values]
- AC5: helmfile build still succeeds with the release [evidence: command:mise exec -- helmfile -f helmfile.yaml.gotmpl build >/dev/null]

#### Files

- `helmfile.yaml.gotmpl`
- `values/agent-orchestrator-db/common.yaml`
- `tests/test_db_release.py`

#### Interfaces

Provides CNPG Secret `agent-orchestrator-db-app` (keys uri, host, port, dbname, user, password) to orchestrator-release.

#### Expected outcome

`helmfile build` lists release agent-orchestrator-db with the CNPG values and backups to its own S3 path.

#### Steps

- Write tests/test_db_release.py; run it; expect failures.
- Add the release to helmfile.yaml.gotmpl and write values/agent-orchestrator-db/common.yaml.
- Rerun the test, then `mise exec -- helmfile -f helmfile.yaml.gotmpl build`; expect `passed`.

#### Notes

Template: ~/Documents/infrastructure/code/helmfile helmfiles/ai/values/buzz-database/common.yaml and helmfiles/media/values/jellystat-database/common.yaml. The app Secret name is CNPG's `<release>-app`.

- 2026-10-23 run agents-helmfile: dependency-failed on hook-missing-namespace

### S7: orchestrator release

- Status: done
- Files: `helmfile.yaml.gotmpl`, `values/agent-orchestrator/common.yaml`, `tests/test_orchestrator_release.py`
- Verify: `uv run pytest tests/test_orchestrator_release.py tests/test_db_release.py -q && mise run lint`
- Verified head: fa002cae130bc3a28a8d7d713d91aceb9e12b712

#### Requirement

Add release `agent-orchestrator` to `helmfile.yaml.gotmpl`: chart `oci://harbor.szymonrichert.pl/charts/agent-orchestrator`, `version` pinned to the chart version published by the agent-orchestrator epic (read it with `helm show chart oci://harbor.szymonrichert.pl/charts/agent-orchestrator`; an unpublished chart means the blocker epic is not done), namespace `agents`, timeout 600, `needs: [agents/agent-orchestrator-db]`, labels `purpose: agents`, `application: agent-orchestrator`, `<<: *default`. Consume contracts `agent-orchestrator-chart`, `agent-orchestrator-settings-env` and `agent-orchestrator-image`: read the chart's real `values.yaml` (`helm show values`) and map onto its actual key names; where this text names a value, the chart key that carries it is the one to set.

`values/agent-orchestrator/common.yaml`:
- image: `harbor.szymonrichert.pl/containers/agent-orchestrator` at the tag CI published (`<sha7>`, or the chart default when it tracks appVersion); `imagePullSecrets` regcred comes from `values/common.yaml`.
- database: the chart's Postgres connection pointed at the CNPG app Secret `agent-orchestrator-db-app` (key `uri` for `ORCH_DATABASE_URL`, or the host/user/password keys when the chart takes parts); no password in plain values.
- master key and Claude token from the encrypted file made by secrets-bootstrap: `masterKey` into `ORCH_MASTER_KEY` and `claudeOauthToken` into Secret `agent-orchestrator-claude` key `CLAUDE_CODE_OAUTH_TOKEN` in namespace agents (the name the settings default `claude_secret_name` uses). Render them as a chart-supported secret, or when the chart cannot create them, as `values/agent-orchestrator/raw/*.common.pre.secrets.yaml` applied by the hook (encrypted, never decrypted to disk).
- ingress: enabled, `className: nginx`, host `agents.szymonrichert.pl`, annotations `cert-manager.io/cluster-issuer: letsencrypt-prod`, `kubernetes.io/tls-acme: "true"`, `nginx.ingress.kubernetes.io/whitelist-source-range: "192.168.1.0/24"`, `nginx.ingress.kubernetes.io/proxy-read-timeout: "3600"` and `proxy-send-timeout: "3600"` (SSE streams), tls secret `agent-orchestrator-tls`; no auth annotations. external-dns publishes the record by default (user decision: the public Cloudflare record is accepted; access is gated by the whitelist). The orchestrator also enforces `ORCH_ALLOWED_CIDRS` itself.
- RBAC and the service account come from the chart; the release adds none.

`tests/test_orchestrator_release.py` asserts on `helmfile_build()` and `layered_values('agent-orchestrator')`: chart URL, pinned non-empty version, namespace, `needs`, the exact whitelist and timeout annotations, host, TLS, absence of any auth annotation (`auth-url`, `auth-signin`, `oauth2`), the ORCH env values, the DB Secret reference, and that no plain values file holds a token or master key.

#### Acceptance conditions

- AC0: the ingress denies the cluster node IPs (chart value ingress.denySourceRanges = [192.168.1.26/32, 192.168.1.27/32, 192.168.1.28/32, 192.168.1.29/32, 192.168.1.65/32], read with `kubectl get nodes -o wide` at build time) and allows 192.168.1.0/24 (ingress.allowSourceRanges), so agent pods SNATed to node IPs cannot reach the API through the ingress [evidence: command:uv run pytest tests/test_orchestrator_release.py -q]
- AC1: the release installs the harbor chart at a pinned version in namespace agents after the database [evidence: command:uv run pytest tests/test_orchestrator_release.py -q -k release_chart_version_and_needs]
- AC2: the ingress is nginx, letsencrypt-prod, host agents.szymonrichert.pl, whitelisted to 192.168.1.0/24 with a 3600s read timeout and no auth annotation [evidence: command:uv run pytest tests/test_orchestrator_release.py -q -k ingress_lan_only_no_auth]
- AC3: ORCH_ALLOWED_CIDRS and ORCH_AGENT_IMAGES are set to the specified values [evidence: command:uv run pytest tests/test_orchestrator_release.py -q -k orch_env_values]
- AC4: the database connection reads the CNPG app Secret and no plain value holds a password [evidence: command:uv run pytest tests/test_orchestrator_release.py -q -k database_from_cnpg_secret]
- AC5: the master key and the Claude token reach the release only through encrypted sources [evidence: command:uv run pytest tests/test_orchestrator_release.py -q -k secrets_only_via_encrypted_files]
- AC6: new sessions are configured to start with any-mcp installed [evidence: command:uv run pytest tests/test_orchestrator_release.py -q -k any_mcp_configured_for_new_sessions]
- AC7: helmfile build succeeds with both releases [evidence: command:mise exec -- helmfile -f helmfile.yaml.gotmpl build >/dev/null]

#### Files

- `helmfile.yaml.gotmpl`
- `values/agent-orchestrator/common.yaml`
- `tests/test_orchestrator_release.py`

#### Interfaces

Consumes contracts agent-orchestrator-chart, agent-orchestrator-settings-env, agent-orchestrator-image.

#### Expected outcome

`helmfile build` lists release agent-orchestrator with the LAN-only ingress, the ORCH env, the DB Secret reference and encrypted secrets only.

#### Steps

- Write tests/test_orchestrator_release.py; run it; expect failures.
- Run `helm show chart` and `helm show values` on the published chart (published by agent-orchestrator CI as oci://harbor.szymonrichert.pl/charts/agent-orchestrator version 0.1.0-main.ccb7c04 (appVersion ccb7c04, confirmed in Harbor); try anonymous first, else `helm registry login` with the Harbor robot credentials supplied by the orchestrator, never printed), then add the release and values/agent-orchestrator/common.yaml (and raw/ secrets manifests when the chart cannot create the Secrets).
- Rerun both release tests and `mise run lint`; expect `passed`.

#### Notes

Orchestrator ruling 2026-10-23: the source-range annotations are rendered by the chart from ingress.allowSourceRanges / ingress.denySourceRanges (verified with helmfile template: whitelist-source-range 192.168.1.0/24, denylist-source-range the five node IPs); the values must not set the annotations by hand.

Ingress precedent: ~/Documents/infrastructure/code/helmfile helmfiles/coding/values/argo-workflows/common.yaml:137-152. The settings contract names the exact ORCH_* variables; the image tags come from the agent-orchestrator CI. Pin versions and tags, never `latest`.

- 2026-10-23 run agents-helmfile: dependency-failed on db-release

### S8: smoke script

- Status: done
- Files: `scripts/smoke.sh`, `mise.toml`, `tests/test_smoke_script.py`
- Verify: `uv run pytest tests/test_smoke_script.py -q && mise run lint`
- Verified head: 6b8fa017763c2ea130a9a77556e7e14e88cdfb7e

#### Requirement

Add `scripts/smoke.sh` and the mise task `smoke` (`bash scripts/smoke.sh`) that proves a deployed orchestrator works end to end. bash, `set -euo pipefail`, shellcheck clean, no secret printed; parameters by env with defaults: `HOST=agents.szymonrichert.pl`, `NAMESPACE=agents`, `SMOKE_TIMEOUT_S=600`.

1. UI: `curl -fsS --max-time 20 https://$HOST/` from the LAN returns HTTP 200 and an HTML body; the API health or `openapi.json` path named by the agent-orchestrator API contract also returns 200.
2. Create a 1-replica cluster through the public API (`POST https://$HOST/api/v1/clusters` with the cluster spec of the API contract: name `smoke-<epoch>`, replicas 1, no special prompt); the body is built with `jq -n`.
3. Poll until the cluster's agent pod exists and is Ready (`kubectl -n $NAMESPACE wait --for=condition=Ready pod -l <cluster label> --timeout=...`), bounded by SMOKE_TIMEOUT_S; on timeout fail with the pod events.
4. `kubectl -n $NAMESPACE exec <pod> -- claude mcp list` output must contain `any-mcp`; otherwise fail printing the mcp list only.
5. Always, on exit (trap): discard the cluster through the API (`DELETE /api/v1/clusters/<id>`, which also removes its PVC) so the smoke leaves nothing behind; an unreachable API on cleanup prints the cluster name to delete manually.

`tests/test_smoke_script.py` (no cluster needed): shellcheck clean; the source has `set -euo pipefail`, a `trap` that issues the DELETE, the `claude mcp list` and `any-mcp` check and `--max-time` on every curl; the script runs against a local fake HTTP server and a fake `kubectl` on PATH (a test double in tmp_path) to prove the happy path exits 0, a missing `any-mcp` in the list exits non-zero, and the cleanup DELETE is sent in both cases.

#### Acceptance conditions

- AC1: the happy path against a fake API and fake kubectl exits 0 and deletes the cluster [evidence: command:uv run pytest tests/test_smoke_script.py -q -k happy_path_exits_zero_and_cleans_up]
- AC2: a missing any-mcp in claude mcp list fails the smoke and still cleans up [evidence: command:uv run pytest tests/test_smoke_script.py -q -k missing_any_mcp_fails_and_cleans_up]
- AC3: every curl is bounded and the script has the strict-mode header and the cleanup trap [evidence: command:uv run pytest tests/test_smoke_script.py -q -k script_is_strict_bounded_and_traps]
- AC4: the script is shellcheck clean [evidence: command:shellcheck --severity=error scripts/smoke.sh]
- AC5: mise exposes a smoke task [evidence: command:mise tasks ls | grep -q '^smoke']

#### Files

- `scripts/smoke.sh`
- `mise.toml`
- `tests/test_smoke_script.py`

#### Interfaces

none

#### Expected outcome

`mise run smoke` runs the end-to-end check; its offline tests pass with a fake API and fake kubectl.

#### Steps

- Write tests/test_smoke_script.py with the fake server and fake kubectl; run it; expect failures (script missing).
- Write scripts/smoke.sh and the `smoke` mise task.
- Rerun the test, `shellcheck --severity=error scripts/smoke.sh` and `mise run lint`; expect `passed`.

#### Notes

The real run happens after the orchestrator applies the namespace; this task only delivers the script and its offline tests. API paths and the cluster label come from the agent-orchestrator API contract (README of code/agent-orchestrator, or its openapi.json).

- 2026-10-23 run agents-helmfile: dependency-failed on orchestrator-release

### S9: apply guard and hygiene

- Status: done
- Files: `mise.toml`, `.gitignore`, `.hook.sh`, `tests/test_mise_tasks.py`, `tests/test_repo_hygiene.py`, `tests/test_helmfile_base.py`
- Verify: `uv run pytest tests/test_mise_tasks.py tests/test_repo_hygiene.py tests/test_helmfile_base.py -q -p no:cacheprovider && mise run lint`
- Verified head: cdc29e5562c37f5dcf2af56b8d35d46d3c1f3f11

#### Requirement

Security review findings: (medium) mise.toml apply/diff kube-context guard only checks that a context exists; compare the current context to EXPECTED_KUBE_CONTEXT (default kubernetes-admin@kubernetes, the homelab context) and fail on mismatch. (low) .gitignore adds kubeconfig*, *.kubeconfig, .kube/, *.pem, *.key, *.dec*, *.decrypted*. (low) .hook.sh run_hook_script drops bash -x so secret-handling hook scripts are never traced. (low) pin the 'latest' tools in mise.toml (uv, jq, gitleaks) to exact versions and pin the helm-diff plugin version.

#### Acceptance conditions

- AC1: apply and diff refuse a kube context other than EXPECTED_KUBE_CONTEXT [evidence: test:tests/test_mise_tasks.py::test_kube_context_guard_rejects_unexpected_context]
- AC2: .gitignore covers kube and decrypted material [evidence: test:tests/test_repo_hygiene.py::test_gitignore_covers_kube_and_decrypted_files]
- AC3: the hook never runs scripts with xtrace [evidence: test:tests/test_helmfile_base.py::test_hook_scripts_not_traced]
- AC4: no tool in mise.toml is latest and helm-diff is pinned [evidence: test:tests/test_mise_tasks.py::test_tools_pinned]

#### Files

- `mise.toml`
- `.gitignore`
- `.hook.sh`
- `tests/test_mise_tasks.py`
- `tests/test_repo_hygiene.py`
- `tests/test_helmfile_base.py`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

The security findings are closed and pinned by tests.

What is true and observable when the task is done.

#### Steps

- Write the failing tests; run red.
- Implement; run green.

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

#### Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.

### S10: db secret name from cnpg

- Status: done
- Files: `values/agent-orchestrator/common.yaml`, `values/agent-orchestrator-db/common.yaml`, `tests/test_orchestrator_release.py`, `scripts/smoke.sh`, `README.md`
- Verify: `uv run pytest tests/test_orchestrator_release.py tests/test_db_release.py -q -p no:cacheprovider && mise run lint`
- Verified head: 375635a217c2ade60efe6ebffee99dd121d70fa8

#### Requirement

Live apply failed: the orchestrator Deployments reference secret agent-orchestrator-db-app (values/agent-orchestrator/common.yaml database.existingSecret), but the cnpg/cluster chart names the cluster agent-orchestrator-db-cluster, so CNPG creates agent-orchestrator-db-cluster-app; pods failed with 'secret "agent-orchestrator-db-app" not found' and the release rolled back. Point every reference to the real secret name, and replace the hardcoded-name assertion with a test that renders the agent-orchestrator-db release (helmfile template) and derives the app secret name from the rendered CNPG Cluster's metadata.name + '-app', then asserts the orchestrator release references exactly that name. Update the smoke script and README if they name the secret.

#### Acceptance conditions

- AC1: the orchestrator release references the secret derived from the rendered CNPG Cluster name [evidence: test:tests/test_orchestrator_release.py::test_db_secret_matches_rendered_cnpg_cluster]
- AC2: no file references agent-orchestrator-db-app [evidence: command:! git grep -n 'agent-orchestrator-db-app' -- ':!docs']

#### Files

- `values/agent-orchestrator/common.yaml`
- `values/agent-orchestrator-db/common.yaml`
- `tests/test_orchestrator_release.py`
- `scripts/smoke.sh`
- `README.md`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

The orchestrator release starts against the CNPG database on the live cluster.

What is true and observable when the task is done.

#### Steps

- Red: write the render-derived test, see it fail on the wrong name.
- Fix the references; run green.

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

#### Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.

### S11: api allowlist pod gateways

- Status: done
- Files: `values/agent-orchestrator/common.yaml`, `tests/test_orchestrator_release.py`
- Verify: `uv run pytest tests/test_orchestrator_release.py -q -p no:cacheprovider && mise run lint`
- Verified head: 02b3cc90b1113e4c5b9e1840b2d206e1676c8b1e

#### Requirement

Live finding after apply: the API's direct-peer allowlist returns 403 to LAN clients. ingress-nginx is hostNetwork, but on this flannel cluster its connection to the api pod arrives from the node's pod-network gateway address (10.244.N.0 via flannel.1 from another node, 10.244.N.1 via cni0 on the same node), not from a 192.168.1.x node IP (api access log: peer 10.244.0.0). Set ORCH_ALLOWED_CIDRS to each node's podCIDR .0/31: 10.244.0.0/31,10.244.1.0/31,10.244.2.0/31,10.244.3.0/31,10.244.4.0/31 (from kubectl get nodes .spec.podCIDR), which admits host-network traffic (the ingress) while agent pods (.2 and up) stay refused; the ingress whitelist/denylist keeps LAN-only. Values comment documents how the list is derived and that it must be updated when nodes change. Test pins the value shape (five /31s on .0 of 10.244.N.0/24).

#### Acceptance conditions

- AC1: ORCH_ALLOWED_CIDRS lists each node pod-network gateway /31 and not the LAN /24 [evidence: test:tests/test_orchestrator_release.py::test_allowed_cidrs_are_node_pod_gateways]
- AC2: from a LAN host, GET https://agents.szymonrichert.pl/api/v1/meta returns 200 after apply [evidence: judgement]

#### Files

- `values/agent-orchestrator/common.yaml`
- `tests/test_orchestrator_release.py`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

The UI answers 200 from the LAN after apply.

What is true and observable when the task is done.

#### Steps

- Red: live 403 from 192.168.1.106; write the value test, see it fail.
- Set the value; run green.

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

#### Ruling

- 2026-10-23 accepted: gate-repeat on a parking-wording false positive: common.yaml:22 is the required note that the list tracks the node set; hand-verified on 02b3cc9: tests/test_orchestrator_release.py 9 passed, mise run lint exit 0 (the verifier's 2 ruff errors were on a stale base).

#### Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.

### S12: smoke session mcp check

- Status: done
- Files: `scripts/smoke.sh`, `tests/test_smoke_script.py`
- Verify: `uv run pytest tests/test_smoke_script.py -q -p no:cacheprovider && mise run lint`
- Verified head: c45fd6ee57ddfd48145a62a9651b5c3743f26fde

#### Requirement

Live smoke failed on a false check: scripts/smoke.sh runs a bare 'claude mcp list' via kubectl exec, which reads the container's default config and reports no servers. claude-code-wrapper writes MCP servers into each session's own config dir (/sessions/<session_id>/config). Verified live: CLAUDE_CONFIG_DIR=/sessions/<sid>/config claude mcp list shows 'any-mcp: /opt/any-mcp/bin/any-mcp --config /opt/any-mcp/etc/any-mcp.yaml - Connected'. Fix the smoke: find the session config dir in the agent pod (the session id from the orchestrator API agents endpoint for the cluster, or the single /sessions/*/config), run claude mcp list with CLAUDE_CONFIG_DIR set, and require the any-mcp line to say Connected; also assert /opt/any-mcp/bin/any-mcp --version reports 0.1.0. Ignore the ccw entry (its URL env exists only inside the session process).

#### Acceptance conditions

- AC1: the smoke checks any-mcp in the session's config dir and requires Connected [evidence: test:tests/test_smoke_script.py::test_smoke_checks_session_config_dir]
- AC2: mise run smoke passes against the live deployment [evidence: command:mise run smoke]

#### Files

- `scripts/smoke.sh`
- `tests/test_smoke_script.py`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

mise run smoke passes on the live deployment.

What is true and observable when the task is done.

#### Steps

- Red: live smoke FAIL any-mcp missing; write the test, see it fail.
- Check the session config dir; run green and the live smoke.

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

#### Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.

## Files to delete

none recorded in the epic format

## Final verify

none recorded in the epic format

## After merge

none

## Rulings (migrated)

- hook-missing-namespace: accept true, at 2026-10-23T06:58:11Z: round-cap only on AC3, which could not pass before the release tasks land (planning error by the orchestrator); AC3 moved to db-release AC5. AC1/AC2 verified on 1fcd489: tests/test_helmfile_base.py passed, lint and gitleaks clean.
- hook-missing-namespace: accept true, at 2026-10-23T06:58:27Z: round-cap only on AC3, which could not pass before the release tasks land (orchestrator planning error); AC3 moved to db-release AC5; AC1/AC2 verified on 1fcd489.
- api-allowlist-pod-gateways: accept true, at 2026-10-23T07:47:09Z: gate-repeat on a parking-wording false positive: common.yaml:22 is the required note that the list tracks the node set; hand-verified on 02b3cc9: tests/test_orchestrator_release.py 9 passed, mise run lint exit 0 (the verifier's 2 ruff errors were on a stale base).
