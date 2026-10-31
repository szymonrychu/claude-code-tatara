# workspace s3 cache implementation plan

## Agreed rung

Rung 1 of plan.md, migrated from the epic format: the steps are the epic's tasks.

## Approach

Migrated from the epic format: one step per task file, in dependency order, each with its status, files, verify, verified head and every body section.

## Chunk 1: migrated tasks (model: opus)

### S1: cache archive

- Status: done
- Files: `src/agents_orchestrator/cache/__init__.py`, `src/agents_orchestrator/cache/archive.py`, `pyproject.toml`, `uv.lock`, `tests/test_cache_archive.py`
- Verify: `uv run pytest -q tests/test_cache_archive.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: 8dfe3f0

#### Requirement

Add the archive layer of the workspace cache (design D5, D6). Runs after the epic orchestrator-rename-sessions lands. Paths are in code/agents-orchestrator under the post-rename names (design Constraints: if that epic chose other module names, the same symbols apply and the orchestrator amends this file list first).

New package `src/agents_orchestrator/cache/`; `cache/archive.py`:
- `pack(workdir: Path, out: BinaryIO, *, exclude: list[str], max_bytes: int) -> int`: a tar stream compressed with `zstandard` written to `out`; returns the compressed bytes written. Members are paths relative to `workdir`. Symlinks are stored as symlinks and never followed; sockets, FIFOs, block and character devices are skipped. `.agent-init` (`spec.CACHE_ALWAYS_EXCLUDE`) is always excluded, plus each `exclude` glob (fnmatch on the workdir-relative POSIX path; a matching directory prunes its whole subtree). Raises `TooLarge` as soon as the compressed output passes `max_bytes`.
- `unpack(src: BinaryIO, workdir: Path) -> int`: streaming zstd decompression and `tarfile` extraction with `filter="data"` into `workdir` (created when missing); returns the number of members extracted. It never deletes or empties anything already in `workdir`. A corrupt stream or a refused member (absolute path, `..`, a link escaping `workdir`, a device node) raises `ExtractError`.
- Both refuse a `workdir` that is empty or `/` with `ValueError` before touching the filesystem (retro: a computed path that came out empty must not be written into).
- `pyproject.toml`: dependency `zstandard`; `uv.lock` refreshed with `uv lock`.

#### Acceptance conditions

- AC1: pack then unpack restores files, directories, modes and symlinks [evidence: test:tests/test_cache_archive.py::test_round_trip_keeps_files_modes_symlinks]
- AC2: .agent-init and the exclude globs are left out, and an excluded directory prunes its subtree [evidence: test:tests/test_cache_archive.py::test_excludes]
- AC3: a symlink to a file outside the workdir is stored as a link, never its content, and FIFOs are skipped [evidence: test:tests/test_cache_archive.py::test_symlinks_not_followed_specials_skipped]
- AC4: pack raises TooLarge once the compressed output passes max_bytes [evidence: test:tests/test_cache_archive.py::test_too_large]
- AC5: unpack refuses absolute, dot-dot and escaping-link members with ExtractError and writes nothing outside the workdir [evidence: test:tests/test_cache_archive.py::test_unpack_refuses_unsafe_members]
- AC6: unpack keeps existing files that are not in the archive [evidence: test:tests/test_cache_archive.py::test_unpack_keeps_existing_files]
- AC7: a corrupt stream raises ExtractError [evidence: test:tests/test_cache_archive.py::test_corrupt_stream]
- AC8: an empty or root workdir is refused before any filesystem access [evidence: test:tests/test_cache_archive.py::test_refuses_empty_or_root_workdir]
- AC9: lint and format pass [evidence: command:uv run ruff check . && uv run ruff format --check .]

#### Files

- `src/agents_orchestrator/cache/__init__.py`
- `src/agents_orchestrator/cache/archive.py`
- `pyproject.toml`
- `uv.lock`
- `tests/test_cache_archive.py`

#### Interfaces

- `cache/archive.py:pack(workdir, out, *, exclude, max_bytes) -> int`, `unpack(src, workdir) -> int`, `TooLarge`, `ExtractError`.

#### Expected outcome

A workdir with files, a symlink and an excluded `node_modules/` packs to a `.tar.zst` stream and unpacks to the same tree without `node_modules/` and `.agent-init/`; a crafted archive with `../escape` raises `ExtractError` and writes nothing outside.

#### Steps

- `uv add zstandard` (writes pyproject.toml and uv.lock).
- Red: write `tests/test_cache_archive.py` with the eight named tests (craft unsafe archives with `tarfile` directly); run it: fails on the missing module.
- Green: write `archive.py`; run the verify command.

#### Notes

- Python 3.12: `tarfile` `filter="data"` exists; open with `tarfile.open(fileobj=..., mode="r|")` over a `zstandard.ZstdDecompressor().stream_reader(src)`; write with `mode="w|"` over `ZstdCompressor().stream_writer(counting_out)`.
- Count compressed bytes in a small writer wrapper and raise `TooLarge` there.
- Walk with `os.scandir`/`os.walk(followlinks=False)`; use `lstat` to skip sockets, FIFOs and devices.
- Never `rmtree` or clear the workdir (retro: computed-path writes).

- 2026-10-25 done: Review medium finding (no member-count cap) dropped: archives come only from this session's own save and unpack onto the same session PVC, so a member flood is no more than the agent could create directly.

### S2: cache config

- Status: done
- Files: `src/agents_orchestrator/settings.py`, `src/agents_orchestrator/spec.py`, `tests/test_cache_config.py`
- Verify: `uv run pytest -q tests/test_cache_config.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: de8fe0a

#### Requirement

Add the workspace cache configuration surface (design D6, D7, D8). Runs after the epic orchestrator-rename-sessions lands. Paths are in code/agents-orchestrator under the post-rename names (design Constraints: if that epic chose other module names, the same symbols apply and the orchestrator amends this file list first).

- `src/agents_orchestrator/settings.py`: fields `cache_s3_endpoint: str = ""` (an http or https URL when set), `cache_s3_region: str = "us-east-1"`, `cache_s3_bucket: str = ""`, `cache_s3_prefix: str = "workspace-cache/"`, `cache_s3_path_style: bool = False`, `cache_s3_verify_tls: bool = True`, `cache_s3_access_key_id: str = ""`, `cache_s3_secret_access_key: str = ""` (never in repr or logs), `cache_image: str = ""`, `cache_max_bytes: int = 5368709120` (1 to 5368709120: the single-PUT limit), `cache_timeout_seconds: int = 1800` (60 to 86400). Env names `ORCH_CACHE_S3_ENDPOINT`, `ORCH_CACHE_S3_REGION`, `ORCH_CACHE_S3_BUCKET`, `ORCH_CACHE_S3_PREFIX`, `ORCH_CACHE_S3_PATH_STYLE`, `ORCH_CACHE_S3_VERIFY_TLS`, `ORCH_CACHE_S3_ACCESS_KEY_ID`, `ORCH_CACHE_S3_SECRET_ACCESS_KEY`, `ORCH_CACHE_IMAGE`, `ORCH_CACHE_MAX_BYTES`, `ORCH_CACHE_TIMEOUT_SECONDS` (contract orch-cache-settings-env). A bad value raises `SettingsError` naming the variable.
- Property `cache_available` = `bool(cache_s3_bucket)`. Method `require_cache()`: when the bucket is set and any of `cache_s3_access_key_id`, `cache_s3_secret_access_key`, `cache_image` is empty, raise `SettingsError` naming each missing variable (the api, dispatcher and ingester never call it; the reconciler does, task cache-restore-runner).
- `src/agents_orchestrator/spec.py`: `WorkspaceCache` (strict) with `key: str | None = None` matching `^[a-z0-9][a-z0-9._-]{0,62}$` and `exclude: list[str] = []` (at most 50 entries, each non-empty, at most 256 characters, not absolute, no `..` segment); constants `CACHE_KEY_RE`, `CACHE_EXCLUDE_MAX = 50`, `CACHE_ALWAYS_EXCLUDE = (INIT_DIR,)`; `SessionSpec.cache: WorkspaceCache | None = None`, sparse: unset is not stored or dumped in a preset (contract orch-session-spec-cache).
- `validate_spec`: `spec.cache` set while `not settings.cache_available` adds the error "workspace cache is not configured (ORCH_CACHE_S3_BUCKET is unset)", except when `stored` is given and `stored.cache == spec.cache` (the preset PUT rule the image, model and effort checks use).

#### Acceptance conditions

- AC1: the cache settings load from their ORCH_CACHE_* names with the stated defaults [evidence: test:tests/test_cache_config.py::test_cache_settings_defaults_and_env]
- AC2: max bytes above 5368709120, a non-http endpoint and a timeout out of range are refused naming the variable [evidence: test:tests/test_cache_config.py::test_cache_settings_refused]
- AC3: require_cache names each missing credential or image when a bucket is set, and passes with no bucket [evidence: test:tests/test_cache_config.py::test_require_cache_names_missing]
- AC4: the secret access key never appears in the settings repr [evidence: test:tests/test_cache_config.py::test_secret_key_not_in_repr]
- AC5: WorkspaceCache enforces the key pattern and the exclude limits [evidence: test:tests/test_cache_config.py::test_workspace_cache_validation]
- AC6: a spec without cache dumps no cache key (sparse presets) [evidence: test:tests/test_cache_config.py::test_cache_sparse_dump]
- AC7: validate_spec refuses a cache while unavailable and accepts an unchanged stored cache [evidence: test:tests/test_cache_config.py::test_validate_spec_cache_unavailable]
- AC8: lint and format pass [evidence: command:uv run ruff check . && uv run ruff format --check .]

#### Files

- `src/agents_orchestrator/settings.py`
- `src/agents_orchestrator/spec.py`
- `tests/test_cache_config.py`

#### Interfaces

- `settings.py:Settings` cache fields, `cache_available`, `require_cache()` (contract `orch-cache-settings-env`).
- `spec.py:WorkspaceCache`, `SessionSpec.cache`, `CACHE_KEY_RE`, `CACHE_EXCLUDE_MAX`, `CACHE_ALWAYS_EXCLUDE` (contract `orch-session-spec-cache`).
- `spec.py:validate_spec` keeps its signature.

#### Expected outcome

`Settings(cache_s3_bucket="b")` loads with `cache_available` true and `require_cache()` naming the three missing variables; `SessionSpec.model_validate({"cache": {"key": "Bad Key"}})` fails; a preset spec without cache dumps no `cache` key.

#### Steps

- Red: write `tests/test_cache_config.py` with the seven named tests; run `uv run pytest -q tests/test_cache_config.py`: they fail (no fields).
- Green: add the settings fields and validators, `WorkspaceCache`, the spec field and the validate_spec rule; run the verify command: all pass, lint clean.

#### Notes

- Follow the existing settings validators (`_Bad`, `SettingsError` naming the variable) and `require_agent_image()`.
- Use `_Strict` for `WorkspaceCache` so unknown keys are refused; keep the field sparse the way `reuse_running_agent` and `max_replicas` are (unset not dumped).
- `cache_s3_secret_access_key`: `Field(repr=False)` or `SecretStr`; never log it.

- 2026-10-25 done

### S3: cache key reserved prefix

- Status: done
- Files: `src/agents_orchestrator/spec.py`, `src/agents_orchestrator/api/sessions.py`, `src/agents_orchestrator/api/presets.py`, `tests/test_api_cache.py`, `README.md`
- Verify: `uv run pytest -q -o addopts='-m "not integration and not e2e"' tests/test_api_cache.py && uv run ruff check .`
- Verified head: 8d8b2c3

#### Requirement

Epic security review 2026-10-26 (medium): without a preset, spec.cache.key is caller-supplied and only regex-checked, so an SSO user can set key to another preset's derived key (visible in that preset's session status) and read that preset's cached workspace on restore or overwrite it on save, planting hooks (.claude/settings.json, .git/hooks) that the victim preset's next session runs. Fix in agents-orchestrator: the `preset-` prefix is reserved for derived keys. A caller-supplied cache.key (raw spec, preset create/update, session create) that starts with `preset-` is rejected with 422 invalid_request "cache.key prefix preset- is reserved for preset-derived keys"; a stored spec whose key equals default_cache_key(its preset) stays valid. User slugs outside the prefix keep working (user requirement: optional user-provided slug). Document it in the README Workspace cache section.

#### Acceptance conditions

- AC1: a caller-supplied cache.key starting with preset- is rejected with 422 on session create, raw spec and preset create/update [evidence: test:tests/test_api_cache.py::test_preset_prefix_reserved]
- AC2: the preset-derived key still resolves and other user slugs still work [evidence: test:tests/test_api_cache.py::test_create_from_preset_derives_key]
- AC3: the suite and lint pass [evidence: command:mise run lint]

#### Files

- `src/agents_orchestrator/spec.py`
- `src/agents_orchestrator/api/sessions.py`
- `src/agents_orchestrator/api/presets.py`
- `tests/test_api_cache.py`
- `README.md`

#### Interfaces

See the Requirement; no new cross-repo contract.

#### Expected outcome

Every acceptance condition holds on the committed HEAD.

#### Steps

- Red: write the AC tests; run the task verify: they fail.
- Green: implement the Requirement; rerun the verify: they pass.
- Run the repo's full suite and lint: green.

#### Notes

- See the Requirement and the epic design.md.

- 2026-10-26 done

### S4: cache chart values

- Status: done
- Files: `chart/agents-orchestrator/values.yaml`, `chart/agents-orchestrator/templates/configmap.yaml`, `chart/agents-orchestrator/templates/deployment.yaml`, `chart/agents-orchestrator/README.md`, `chart/agents-orchestrator/ci/lint-values.yaml`, `tests/test_chart_cache.py`
- Verify: `uv run pytest -q tests/test_chart_cache.py tests/test_chart_config.py tests/test_chart_deployments.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: d4d5d57

#### Requirement

Expose the cache configuration in the chart, credentials on the reconciler only (design D2, D8; extends contract agents-orchestrator-chart). Runs after the epic orchestrator-rename-sessions lands. Paths are in code/agents-orchestrator under the post-rename names (design Constraints: if that epic chose other module names, the same symbols apply and the orchestrator amends this file list first).

Chart `chart/agents-orchestrator`:
- `values.yaml`: `cache.s3 {endpoint: "", region: us-east-1, bucket: "", prefix: workspace-cache/, pathStyle: false, verifyTls: true, existingSecret: "", accessKeyIdKey: AWS_ACCESS_KEY_ID, secretAccessKeyKey: AWS_SECRET_ACCESS_KEY}`, `cache.image: ""` (empty: the chart's own `image.repository:image.tag`, tag defaulting to the appVersion), `cache.maxBytes: 5368709120`, `cache.timeoutSeconds: 1800`; each commented.
- `templates/configmap.yaml`: with `cache.s3.bucket` set: `ORCH_CACHE_S3_ENDPOINT`, `ORCH_CACHE_S3_REGION`, `ORCH_CACHE_S3_BUCKET`, `ORCH_CACHE_S3_PREFIX`, `ORCH_CACHE_S3_PATH_STYLE`, `ORCH_CACHE_S3_VERIFY_TLS`, `ORCH_CACHE_IMAGE`, `ORCH_CACHE_MAX_BYTES`, `ORCH_CACHE_TIMEOUT_SECONDS`; none of them when it is empty.
- `templates/deployment.yaml`: the reconciler container only gets `ORCH_CACHE_S3_ACCESS_KEY_ID` and `ORCH_CACHE_S3_SECRET_ACCESS_KEY` as `secretKeyRef` to `cache.s3.existingSecret` with the two key names; `fail` when `cache.s3.bucket` is set without `existingSecret`. The api, dispatcher and ingester containers get no cache credential.
- `README.md` (chart): the `cache` values. `ci/lint-values.yaml`: a cache block so `helm lint` renders it.

#### Acceptance conditions

- AC1: with a bucket set the settings ConfigMap carries every non-secret ORCH_CACHE_* value [evidence: test:tests/test_chart_cache.py::test_configmap_cache_env]
- AC2: with no bucket the ConfigMap has no ORCH_CACHE_* key [evidence: test:tests/test_chart_cache.py::test_no_cache_no_env]
- AC3: only the reconciler container gets the credential env, from the existing Secret's keys [evidence: test:tests/test_chart_cache.py::test_credentials_only_on_reconciler]
- AC4: a bucket without existingSecret fails the render [evidence: test:tests/test_chart_cache.py::test_bucket_requires_secret]
- AC5: the cache image defaults to the chart's own image [evidence: test:tests/test_chart_cache.py::test_cache_image_defaults_to_chart_image]
- AC6: the existing chart tests stay green [evidence: command:uv run pytest -q tests/test_chart_config.py tests/test_chart_deployments.py tests/test_chart_ci.py]
- AC7: lint and format pass [evidence: command:uv run ruff check . && uv run ruff format --check .]

#### Files

- `chart/agents-orchestrator/values.yaml`
- `chart/agents-orchestrator/templates/configmap.yaml`
- `chart/agents-orchestrator/templates/deployment.yaml`
- `chart/agents-orchestrator/README.md`
- `chart/agents-orchestrator/ci/lint-values.yaml`
- `tests/test_chart_cache.py`

#### Interfaces

- Chart values `cache.*` (extends contract `agents-orchestrator-chart`); env names from contract `orch-cache-settings-env`.

#### Expected outcome

`helm template` with `cache.s3.bucket=b, cache.s3.existingSecret=s` renders the ORCH_CACHE_* ConfigMap keys and the two credential `secretKeyRef`s on the reconciler container only.

#### Steps

- Red: write `tests/test_chart_cache.py` with `tests/helm_render.py` (the five named tests); run it: fails.
- Green: values, templates, chart README and `ci/lint-values.yaml`; run the verify command.

#### Notes

- The reconciler-only block already exists in `templates/deployment.yaml` (`if eq $component "reconciler"`).
- The image default follows the chart's existing image tag helper (appVersion when `image.tag` is empty).

- 2026-10-25 done

### S5: cache job render

- Status: done
- Files: `src/agents_orchestrator/reconciler/cache.py`, `tests/test_cache_jobs_render.py`
- Verify: `uv run pytest -q tests/test_cache_jobs_render.py tests/test_render.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: 75baef2

#### Requirement

Render the cache restore and save Jobs with no credential in any pod (design D1, D2, D6). Runs after the epic orchestrator-rename-sessions lands. Paths are in code/agents-orchestrator under the post-rename names (design Constraints: if that epic chose other module names, the same symbols apply and the orchestrator amends this file list first).

New module `src/agents_orchestrator/reconciler/cache.py` (render part):
- `restore_job_name(slug)` = `f"{prefix(slug)}-cache-restore"`, `save_job_name(slug)` = `f"{prefix(slug)}-cache-save"`; labels: the session labels plus `agents.szymonrichert.pl/cache: restore|save`.
- `render_cache_job(session, settings, action: Literal["restore", "save"], url: str) -> Obj`:
  - image `settings.cache_image`, never `spec.image`; command `["orch", "cache", action]`;
  - env exactly `CACHE_URL` (url), `CACHE_DIR` (`workdir_path(spec)`), `CACHE_MAX_BYTES`, `CACHE_EXCLUDE` (JSON of `spec.cache.exclude`), `CACHE_SCRATCH=/scratch`, `HOME=/tmp`; no `spec.env`, no `secretKeyRef`, no `envFrom`;
  - volumes: the session PVC through `workdir_mount(spec)` (read-only for save), an `emptyDir` `tmp` at `/tmp`, and for save an `emptyDir` `scratch` at `/scratch` with `sizeLimit` = `cache_max_bytes`;
  - pod: `restartPolicy: Never`, `automountServiceAccountToken: false`, `securityContext {runAsUser: 1000, runAsNonRoot: true, fsGroup: 1000}`; container `securityContext {readOnlyRootFilesystem: true, allowPrivilegeEscalation: false, capabilities: {drop: [ALL]}}`; `imagePullSecrets` as the agent pods;
  - Job: `backoffLimit: 2`, `activeDeadlineSeconds: settings.cache_timeout_seconds`, no TTL.
- The agent objects rendered for a cache-enabled session (`render_session`, today `render_cluster`) carry no reference to cache credentials: no env name starting `AWS_`, `CACHE_` or `ORCH_CACHE_`, and no `secretKeyRef` beyond the session Secret and the Claude Secret.

#### Acceptance conditions

- AC1: the restore Job runs the cache image with orch cache restore, never the spec image [evidence: test:tests/test_cache_jobs_render.py::test_restore_job_image_and_command]
- AC2: the Job env is exactly the CACHE_* set and HOME, with no spec env, secretKeyRef or envFrom [evidence: test:tests/test_cache_jobs_render.py::test_job_env_has_no_credentials]
- AC3: the save Job mounts the workspace read-only and a scratch emptyDir sized to max bytes [evidence: test:tests/test_cache_jobs_render.py::test_save_job_volumes]
- AC4: the Job pod is hardened: no service account token, non-root, read-only root, no privilege escalation, all capabilities dropped [evidence: test:tests/test_cache_jobs_render.py::test_job_pod_hardened]
- AC5: backoffLimit 2 and activeDeadlineSeconds equal to the cache timeout [evidence: test:tests/test_cache_jobs_render.py::test_job_limits]
- AC6: the agent objects of a cache-enabled session reference no cache credential [evidence: test:tests/test_cache_jobs_render.py::test_agent_pods_carry_no_cache_credentials]
- AC7: the existing render golden tests stay green [evidence: command:uv run pytest -q tests/test_render.py]
- AC8: lint and format pass [evidence: command:uv run ruff check . && uv run ruff format --check .]

#### Files

- `src/agents_orchestrator/reconciler/cache.py`
- `tests/test_cache_jobs_render.py`

#### Interfaces

- `reconciler/cache.py:restore_job_name`, `save_job_name`, `CACHE_LABEL`, `render_cache_job(session, settings, action, url) -> Obj`.
- Reuses `k8s/render.py:workdir_mount`, `workdir_path`, `WORKSPACE_VOLUME`, `k8s/labels.py:session labels`, `prefix`.

#### Expected outcome

`render_cache_job(s, settings, "save", url)` is a `batch/v1` Job `<prefix>-cache-save` running `orch cache save` in `settings.cache_image`, workspace mounted read-only, no credential anywhere in its spec.

#### Steps

- Red: write `tests/test_cache_jobs_render.py` (the six named tests, sessions from `tests/factories.py`); run it: fails.
- Green: write the render part of `reconciler/cache.py`; run the verify command.

#### Notes

- Mirror `reconciler/init.py:render_init_job` (pull secret, labels, PVC volume) but with the hardening and env rules of the requirement.
- `readOnlyRootFilesystem` needs the `/tmp` emptyDir and `HOME=/tmp`.
- The save Job mounts the same `workdir_mount` with `readOnly: true`.

- 2026-10-25 done

### S6: cache key on create

- Status: done
- Files: `src/agents_orchestrator/spec.py`, `src/agents_orchestrator/api/sessions.py`, `src/agents_orchestrator/api/schemas.py`, `openapi.json`, `tests/test_api_cache.py`
- Verify: `uv run pytest -q tests/test_api_cache.py tests/test_readme_api.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: 2bf9fa9

#### Requirement

Resolve the cache key at session create and expose cache availability (design D7, D8). Runs after the epic orchestrator-rename-sessions lands. Paths are in code/agents-orchestrator under the post-rename names (design Constraints: if that epic chose other module names, the same symbols apply and the orchestrator amends this file list first).

- `src/agents_orchestrator/spec.py`: `default_cache_key(preset_id: UUID) -> str` = `"preset-" + sha256(b"workspace-cache:" + preset_id.bytes).hexdigest()[:16]` (pseudorandom, derived from the immutable preset id, so a preset rename keeps the cache and a copy gets a new one).
- `src/agents_orchestrator/api/sessions.py`: `POST /api/v1/sessions` with `preset_id`: when the snapshotted spec has `cache` with `key` None, set `key` to `default_cache_key(preset.id)` before the insert, so the stored session spec always carries the key. With a raw `spec`, a `cache` without `key` is a 422 `invalid_request` "cache.key is required without a preset". Preset POST and PUT store `cache` sparse, without resolving the key.
- `GET /api/v1/meta` gains `cache: {available: settings.cache_available, max_bytes: settings.cache_max_bytes}` (`api/schemas.py`: `MetaCache`, `Meta.cache`; contract orch-meta-cache).
- `openapi.json` regenerated with `uv run python -m agents_orchestrator.api.openapi > openapi.json` (the command `tests/test_readme_api.py::test_openapi_json_matches_app` names).

#### Acceptance conditions

- AC1: default_cache_key is stable for one preset id, differs between ids and matches the key pattern [evidence: test:tests/test_api_cache.py::test_default_cache_key]
- AC2: a session from a preset with a keyless cache stores the derived key in its spec [evidence: test:tests/test_api_cache.py::test_create_from_preset_derives_key]
- AC3: a session from a preset with a key keeps that key [evidence: test:tests/test_api_cache.py::test_create_from_preset_keeps_user_key]
- AC4: a raw spec with a keyless cache is a 422 naming cache.key [evidence: test:tests/test_api_cache.py::test_raw_spec_needs_key]
- AC5: a preset stores its cache sparse and unresolved [evidence: test:tests/test_api_cache.py::test_preset_cache_stored_sparse]
- AC6: meta reports cache availability and max bytes [evidence: test:tests/test_api_cache.py::test_meta_cache]
- AC7: the committed openapi.json matches the app [evidence: test:tests/test_readme_api.py::test_openapi_json_matches_app]
- AC8: lint and format pass [evidence: command:uv run ruff check . && uv run ruff format --check .]

#### Files

- `src/agents_orchestrator/spec.py`
- `src/agents_orchestrator/api/sessions.py`
- `src/agents_orchestrator/api/schemas.py`
- `openapi.json`
- `tests/test_api_cache.py`

#### Interfaces

- `spec.py:default_cache_key(preset_id: UUID) -> str`.
- `POST /api/v1/sessions` behaviour (contract `orch-session-spec-cache`); `GET /api/v1/meta` `cache {available, max_bytes}` (contract `orch-meta-cache`); `api/schemas.py:MetaCache`.

#### Expected outcome

A session created from a preset whose spec is `{"cache": {}}` returns `spec.cache.key` = `preset-<16 hex>`, the same for every session of that preset; `/meta` shows `cache.available`.

#### Steps

- Red: write `tests/test_api_cache.py` (the six named tests, using the existing API test fixtures of `tests/test_api_create_from_preset.py`); run it: fails.
- Green: implement; regenerate `openapi.json` with `uv run python -m agents_orchestrator.api.openapi > openapi.json`; run the verify command.

#### Notes

- Resolve the key in `_create_from_preset` after `check_spec`, with `spec.model_copy(update=...)` on the `cache` sub-model, before the insert.
- The derivation uses the preset id, not the name: a renamed preset keeps its cache (design D7).

- 2026-10-25 done

### S7: cache save allowlist

- Status: done
- Files: `src/agents_orchestrator/reconciler/cache.py`, `tests/test_cache_save.py`, `README.md`, `MEMORY.md`
- Verify: `uv run pytest -q -o addopts='-m "not integration and not e2e"' tests/test_cache_save.py && uv run ruff check .`
- Verified head: 45c221c

#### Requirement

Epic whole-diff review 2026-10-26 (medium, .scratchpad/cache-epic-review.md): the save skip rule in reconciler/cache.py (SAVE_SKIP_RESTORE_REASONS) is a deny-list that omits restore failures able to leave a partial workdir: `exit <code>` (an OOM kill mid-extract), `bad_output`, `no_cache_key`, and `extract_failed` also still saves. A save then replaces a good archive with a partial tree, the design's anti-goal. Orchestrator ruling: invert to an allow-list. A save Job runs only when the session's restore outcome is a success: restored, or the archive did not exist yet (a cache miss on first use). It is skipped on every other restore state or reason, present or future, and on the cache being unavailable. Keep the skip recorded with its reason as now. Update the README Workspace cache section and the MEMORY.md D11 line to the allow-list rule.

Also check how a missing archive is reported. A presigned GET for a missing key returns 404 when the bucket owner can list the bucket, else 403. Make sure the restore maps 404 to the cache-miss outcome. If the CLI cannot tell a 403-missing from a 403-denied, record that in the README; the live smoke checks it.

#### Acceptance conditions

- AC1: a save runs only after a successful restore or a cache miss, and is skipped for every other restore outcome [evidence: test:tests/test_cache_save.py::test_save_only_after_successful_restore]
- AC2: a restore of a missing archive is a cache miss and is followed by a save [evidence: test:tests/test_cache_save.py::test_cache_miss_then_save]
- AC3: the suite and lint pass [evidence: command:mise run lint]

#### Files

- `src/agents_orchestrator/reconciler/cache.py`
- `tests/test_cache_save.py`
- `README.md`
- `MEMORY.md`

#### Interfaces

See the Requirement; no new cross-repo contract.

#### Expected outcome

Every acceptance condition holds on the committed HEAD.

#### Steps

- Red: write the AC tests; run the task verify: they fail.
- Green: implement the Requirement; rerun the verify: they pass.
- Run the repo's full suite and lint: green.

#### Notes

- See the Requirement and the epic design.md.

- 2026-10-26 done

### S8: cache transfer cli

- Status: done
- Files: `src/agents_orchestrator/cache/transfer.py`, `src/agents_orchestrator/cli.py`, `tests/test_cache_cli.py`
- Verify: `uv run pytest -q tests/test_cache_cli.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: 53a14e9

#### Requirement

Add the Job-side transfer CLI `orch cache restore|save` (contract orch-cache-job-cli; design D1, D5, D11). Runs after the epic orchestrator-rename-sessions lands. Paths are in code/agents-orchestrator under the post-rename names (design Constraints: if that epic chose other module names, the same symbols apply and the orchestrator amends this file list first).

`src/agents_orchestrator/cache/transfer.py` and `cli.py` (register `cache` with a positional `restore` or `save`). The command reads only these env variables and never constructs `Settings()` or reads `ORCH_*`: `CACHE_URL` (a presigned URL), `CACHE_DIR` (the workdir), `CACHE_MAX_BYTES`, `CACHE_EXCLUDE` (a JSON list of globs, default `[]`), `CACHE_SCRATCH` (directory for the save archive, default `/scratch`). Its last stdout line is one JSON object `{"outcome", "bytes", "reason"}`.

- `restore`: GET `CACHE_URL` streamed with httpx into `archive.unpack`. 200: `{"outcome": "restored", "bytes": <n>}`, exit 0. 404: `{"outcome": "miss", "bytes": 0}`, exit 0, the workdir untouched. An HTTP status other than 200 or 404, or a network error, before any byte was extracted: `{"outcome": "failed", "reason": "download_failed: <detail>"}`, exit 1. `ExtractError` or any failure after extraction began: `{"outcome": "failed", "reason": "extract_failed: <detail>"}`, exit 1.
- `save`: `CACHE_DIR` missing: `{"outcome": "skipped", "reason": "no_workdir"}`, exit 0, no request. Else `archive.pack` into `<CACHE_SCRATCH>/archive.tar.zst`; `TooLarge`: `{"outcome": "failed", "reason": "too_large"}`, exit 1, no request. Else one PUT of the file with `Content-Length` and `Content-Type: application/zstd`; 2xx: `{"outcome": "saved", "bytes": <n>}`, exit 0; anything else: `{"outcome": "failed", "reason": "upload_failed: <status or error>"}`, exit 1. The archive file is removed afterwards.
- No output line, reason or log contains the URL's query string (the signature).

#### Acceptance conditions

- AC1: restore of a 200 body extracts into CACHE_DIR and prints restored with the byte count [evidence: test:tests/test_cache_cli.py::test_restore_restored]
- AC2: restore of a 404 prints miss, exits 0 and leaves the workdir untouched [evidence: test:tests/test_cache_cli.py::test_restore_miss]
- AC3: a 500 or a connection error before extraction prints download_failed and exits 1 [evidence: test:tests/test_cache_cli.py::test_restore_download_failed]
- AC4: a corrupt body prints extract_failed and exits 1 [evidence: test:tests/test_cache_cli.py::test_restore_extract_failed]
- AC5: save PUTs one archive with Content-Length and prints saved [evidence: test:tests/test_cache_cli.py::test_save_saved]
- AC6: save with no workdir prints skipped no_workdir and sends no request [evidence: test:tests/test_cache_cli.py::test_save_no_workdir]
- AC7: save over CACHE_MAX_BYTES prints too_large, exits 1 and sends no request [evidence: test:tests/test_cache_cli.py::test_save_too_large_no_put]
- AC8: an upload failure reason never contains the URL query string [evidence: test:tests/test_cache_cli.py::test_save_upload_failed_hides_signature]
- AC9: orch cache runs with no ORCH_* variable set [evidence: test:tests/test_cache_cli.py::test_cli_needs_no_settings]
- AC10: lint and format pass [evidence: command:uv run ruff check . && uv run ruff format --check .]

#### Files

- `src/agents_orchestrator/cache/transfer.py`
- `src/agents_orchestrator/cli.py`
- `tests/test_cache_cli.py`

#### Interfaces

- `orch cache restore|save` env and JSON outcome line (contract `orch-cache-job-cli`); `cache/transfer.py:restore(env) -> int`, `save(env) -> int`.
- Consumes `cache/archive.py` from cache-archive.

#### Expected outcome

`CACHE_URL=http://127.0.0.1:<port>/o CACHE_DIR=/tmp/w orch cache save` PUTs one zstd body and prints `{"outcome": "saved", "bytes": N, "reason": null}` last; `restore` of the same URL recreates the tree.

#### Steps

- Red: write `tests/test_cache_cli.py` (the nine named tests) against a local HTTP fake (stdlib `http.server` in a thread, or `httpx.MockTransport` injected into the transfer functions); run it: fails.
- Green: write `transfer.py` and register the command in `cli.py`; run the verify command.

#### Notes

- Keep the import of `transfer` lazy inside the command, like the other subcommands, so `orch --help` stays light.
- Strip the query string from any URL in errors (`httpx.URL(url).copy_with(query=None)`).
- httpx is already a dependency; no new one here.

- 2026-10-26 done

### S9: cache presign

- Status: done
- Files: `src/agents_orchestrator/cache/presign.py`, `pyproject.toml`, `uv.lock`, `tests/test_cache_presign.py`
- Verify: `uv run pytest -q tests/test_cache_presign.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: 781151a

#### Requirement

Presign the cache object URLs in the reconciler (design D2, D8). Runs after the epic orchestrator-rename-sessions lands. Paths are in code/agents-orchestrator under the post-rename names (design Constraints: if that epic chose other module names, the same symbols apply and the orchestrator amends this file list first).

`src/agents_orchestrator/cache/presign.py`:
- `object_name(settings, key) -> str` = `f"{settings.cache_s3_prefix}{key}.tar.zst"` (one object per key, reused on every save).
- `presign(settings, method: Literal["GET", "PUT"], key: str) -> str`: a boto3 S3 client with `endpoint_url` (None when `cache_s3_endpoint` is empty), `region_name`, signature version `s3v4`, addressing style `path` when `cache_s3_path_style` else `virtual`, `verify=cache_s3_verify_tls`, and the credentials from `cache_s3_access_key_id` and `cache_s3_secret_access_key`; `ExpiresIn = cache_timeout_seconds + 600`. Presigning makes no network call.
- `pyproject.toml`: dependency `boto3`; dev dependency `moto[server]`; `uv.lock` refreshed with `uv lock`.
- A round trip proves the URLs work with the CLI of task cache-transfer-cli: moto's `ThreadedMotoServer` as the endpoint (path style), a bucket created in the test, presign PUT then `orch cache save`, presign GET then `orch cache restore` into a fresh directory.

#### Acceptance conditions

- AC1: with path style on, the URL host is the endpoint host and the path starts with the bucket [evidence: test:tests/test_cache_presign.py::test_path_style_url]
- AC2: with path style off, the bucket is in the host [evidence: test:tests/test_cache_presign.py::test_virtual_style_url]
- AC3: the URL expires after the cache timeout plus 600 seconds [evidence: test:tests/test_cache_presign.py::test_expiry]
- AC4: the object name is prefix, key and .tar.zst [evidence: test:tests/test_cache_presign.py::test_object_name]
- AC5: save through a presigned PUT then restore through a presigned GET round-trips the workdir on a moto server [evidence: test:tests/test_cache_presign.py::test_round_trip_through_moto]
- AC6: a presigned GET of a missing key restores as a miss [evidence: test:tests/test_cache_presign.py::test_missing_object_is_miss]
- AC7: lint and format pass [evidence: command:uv run ruff check . && uv run ruff format --check .]

#### Files

- `src/agents_orchestrator/cache/presign.py`
- `pyproject.toml`
- `uv.lock`
- `tests/test_cache_presign.py`

#### Interfaces

- `cache/presign.py:object_name(settings, key) -> str`, `presign(settings, method, key) -> str`.
- Consumes the settings of cache-config and the CLI of cache-transfer-cli.

#### Expected outcome

With endpoint `http://rgw:80`, path style on and bucket `b`, `presign(s, "PUT", "k")` returns `http://rgw:80/b/workspace-cache/k.tar.zst?X-Amz-...&X-Amz-Expires=2400`; the moto round trip restores the saved tree.

#### Steps

- `uv add boto3` and `uv add --dev 'moto[server]'`.
- Red: write `tests/test_cache_presign.py` (the six named tests; moto `ThreadedMotoServer(port=0)` fixture, bucket made with a boto3 client); run it: fails.
- Green: write `presign.py`; run the verify command.

#### Notes

- `boto3.client("s3", endpoint_url=..., region_name=..., aws_access_key_id=..., aws_secret_access_key=..., verify=..., config=botocore.config.Config(signature_version="s3v4", s3={"addressing_style": ...}))`, then `generate_presigned_url("get_object"|"put_object", Params={"Bucket", "Key"}, ExpiresIn=...)`.
- For the PUT, do not sign a ContentType the CLI does not send; if signing it, the CLI's `application/zstd` must match.
- Build the client per call or cache it on the settings identity; presigning is local.

- 2026-10-26 done: Moto does not enforce SigV4, so single-method and single-object scoping is unproven against real RGW; check it in the live smoke (workspace-s3-cache-deploy).

### S10: orch services secret checksum

- Status: done
- Files: `chart/agents-orchestrator/templates/deployment.yaml`, `tests/test_chart_deployments.py`
- Verify: `uv run pytest -q -o addopts='-m "not integration and not e2e"' tests/test_chart_deployments.py && uv run ruff check .`
- Verified head: 2290dbb

#### Requirement

Discovered in the agents-schedule-deploy apply 2026-10-26: adding a service token hash changed only the agents-orchestrator-services Secret, the api pods did not restart, and the orchestrator kept answering 401 to the new token until a manual `kubectl rollout restart deploy/agents-orchestrator-api`. In the agents-orchestrator chart, every Deployment whose container reads ORCH_SERVICE_TOKENS (or any other value from the services Secret) carries a pod-template annotation with the checksum of that Secret's rendered data (the same pattern the chart already uses for the settings ConfigMap, if it does), so a token change rolls those pods on apply. Test the render: the annotation exists and changes when serviceApi.tokenHashes changes.

#### Acceptance conditions

- AC1: the pods reading the services Secret carry a checksum annotation that changes with the token hashes [evidence: test:tests/test_chart_deployments.py::test_services_secret_checksum_rolls_api]
- AC2: chart lint and tests pass [evidence: command:mise run lint]

#### Files

- `chart/agents-orchestrator/templates/deployment.yaml`
- `tests/test_chart_deployments.py`

#### Interfaces

See the Requirement; no new cross-repo contract.

#### Expected outcome

Every acceptance condition holds on the committed HEAD.

#### Steps

- Red: write the AC tests; run the task verify: they fail.
- Green: implement the Requirement; rerun the verify: they pass.
- Run the repo's full suite and lint: green.

#### Notes

- See the Requirement and the epic design.md.

- 2026-10-26 done

### S11: cache restore runner

- Status: done
- Files: `src/agents_orchestrator/reconciler/cache.py`, `src/agents_orchestrator/reconciler/loop.py`, `tests/test_cache_restore.py`, `tests/fakes/fake_kube.py`
- Verify: `uv run pytest -q tests/test_cache_restore.py tests/test_init_runner.py tests/test_reconciler.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: bf58295

#### Requirement

Restore the workspace at session start, before init and the Claude sessions (design D1, D3, D11; contract orch-session-status-cache). Runs after the epic orchestrator-rename-sessions lands. Paths are in code/agents-orchestrator under the post-rename names (design Constraints: if that epic chose other module names, the same symbols apply and the orchestrator amends this file list first).

- `src/agents_orchestrator/reconciler/cache.py`: `CacheRunner(pool, kube, settings, *, write_status)` with `restore_step(session) -> CacheGate`, the same crash-safe shape as `InitRunner` (`reconciler/init.py`). No `spec.cache`: no status, gate clear. First step: write `status.cache = {key, object, restore: {state: "running", started_at (database clock), finished_at: null, bytes: null, reason: null, job: null}}`; when `not settings.cache_available`, finish `failed` with reason `not_configured`; else create the restore Job (task cache-job-render) with `presign(settings, "GET", key)` and then write `job`. Observe: Complete: read the last JSON line of the pod log tail (`checks.log_tail`): `restored` with `bytes`, or `miss`. Failed: `failed` with the JSON line's `reason`, else `exit <code>`. DeadlineExceeded, or older than the cache timeout plus `DEADLINE_GRACE_SECONDS`: `failed` `timeout`. A Job that vanished after its create: `failed` `job_missing`; a crash between the running write and the create: create it. A foreign Job: `failed` `foreign_object`. A create error: `failed` `job_create_failed: <error>`. The Job is deleted after the outcome is written; a later tick deletes a leftover one.
- `CacheGate {hold, degraded, message}`: `running` holds with "cache restore running"; `failed` is degraded with "cache restore failed: <reason>"; `restored` and `miss` are clear.
- `src/agents_orchestrator/reconciler/loop.py`: `_converge` runs `restore_step` before `init.step`; while the restore holds, `init.step` is not called and no Claude session is bootstrapped (phase pending); a failed restore lets init and the sessions run, phase degraded, its message joined. `_rebootstrap` holds while the restore holds. The Reconciler calls `settings.require_cache()` at construction when `settings.cache_available`.

#### Acceptance conditions

- AC1: a session without cache gets no status.cache and no cache Job [evidence: test:tests/test_cache_restore.py::test_no_cache_no_job]
- AC2: the first converge writes restore running, creates the restore Job with a presigned GET URL, and starts no init Job [evidence: test:tests/test_cache_restore.py::test_restore_job_created_before_init]
- AC3: a restored outcome records bytes, deletes the Job, and the next converge starts the init Job [evidence: test:tests/test_cache_restore.py::test_restored_then_init_runs]
- AC4: a miss lets init and the sessions start without degrading the phase [evidence: test:tests/test_cache_restore.py::test_miss_is_not_degraded]
- AC5: a failed restore records the CLI reason and the sessions start with phase degraded [evidence: test:tests/test_cache_restore.py::test_failed_restore_degrades]
- AC6: timeout, job_missing and foreign_object are recorded as failed with that reason [evidence: test:tests/test_cache_restore.py::test_restore_timeout_missing_foreign]
- AC7: a cache spec while the cache is unavailable records failed not_configured and creates no Job [evidence: test:tests/test_cache_restore.py::test_not_configured]
- AC8: a crash between the running write and the create creates the Job exactly once on the next tick [evidence: test:tests/test_cache_restore.py::test_crash_safety]
- AC9: a rebootstrap command is held while the restore runs [evidence: test:tests/test_cache_restore.py::test_rebootstrap_held_during_restore]
- AC10: the reconciler refuses to start with a bucket but no credentials [evidence: test:tests/test_cache_restore.py::test_reconciler_requires_cache_credentials]
- AC11: the existing init and reconciler tests stay green [evidence: command:uv run pytest -q tests/test_init_runner.py tests/test_reconciler.py tests/test_agent_init_scripts.py]
- AC12: lint and format pass [evidence: command:uv run ruff check . && uv run ruff format --check .]

#### Files

- `src/agents_orchestrator/reconciler/cache.py`
- `src/agents_orchestrator/reconciler/loop.py`
- `tests/test_cache_restore.py`
- `tests/fakes/fake_kube.py`

#### Interfaces

- `reconciler/cache.py:CacheRunner.restore_step(session) -> CacheGate`, `CacheGate`.
- `status.cache` (contract `orch-session-status-cache`): `{key, object, restore {state, started_at, finished_at, bytes, reason, job}, save {...}}`.
- `reconciler/loop.py:Reconciler._converge`, `_rebootstrap`, `__init__`.

#### Expected outcome

A new cached session shows `status.cache.restore.state` running, then restored or miss, and only then the init Job and the Claude sessions start; a failed restore shows phase degraded with the reason.

#### Steps

- Red: write `tests/test_cache_restore.py` (the ten named tests, with `tests/fakes/fake_kube.py` `finish_job(..., log=...)` returning the CLI JSON line); run it: fails.
- Green: implement `CacheRunner.restore_step` and the loop wiring; run the verify command.

#### Notes

- Copy the state machine of `reconciler/init.py:InitRunner` (state before create, `job` after, `_observe`, `_outcome`, `_delete_job`); share `checks.log_tail`, `job_condition`, `container_exit_code`.
- `fake_kube.finish_job` hard-codes the container name `check`; generalise it only if a test needs the real name.
- Parse only the last non-empty log line as JSON; a non-JSON line on a Complete Job is `failed` with reason `bad_output`.

- 2026-10-26 done

### S12: cache save on discard

- Status: done
- Files: `src/agents_orchestrator/reconciler/cache.py`, `src/agents_orchestrator/reconciler/loop.py`, `tests/test_cache_save.py`, `tests/fakes/fake_kube.py`
- Verify: `uv run pytest -q tests/test_cache_save.py tests/test_discard_hook.py tests/test_reconciler.py tests/test_autoclose.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: 52b5a1a

#### Requirement

Save the workspace at session end, under the same object name, before the PVC is deleted (design D3, D4, D11). Runs after the epic orchestrator-rename-sessions lands. Paths are in code/agents-orchestrator under the post-rename names (design Constraints: if that epic chose other module names, the same symbols apply and the orchestrator amends this file list first).

- `CacheRunner.save_step(session) -> bool` in `src/agents_orchestrator/reconciler/cache.py` (True: the discard may go on). No `spec.cache`: True. Skip rules, each writing `status.cache.save = {state: "skipped", reason}` and returning True with no Job: the restore is absent or `running` (`restore_running`); the restore failed with a reason starting `download_failed`, `timeout`, `job_missing`, `foreign_object`, `job_create_failed` or `not_configured` (that reason's head word); the cache is unavailable now (`not_configured`). After `extract_failed` the save runs, so a corrupt archive is replaced.
- Otherwise: write `save {state: "running", ...}`, create the save Job (task cache-job-render) with `presign(settings, "PUT", key)` for the same `object` as the restore, return False; observe as the restore does: `saved` with `bytes`, `skipped` with the CLI reason (`no_workdir`), `failed` with `too_large`, `upload_failed: ...`, `timeout`, `job_missing`, `foreign_object` or `job_create_failed: ...`. After any outcome: delete the Job and return True. A failed save logs a warning naming the session slug, the key and the reason; it never holds the discard.
- `src/agents_orchestrator/reconciler/loop.py`: `_quiesce` scales the StatefulSet to zero and waits for the agent pods when a hook is owed or a save is owed (`spec.cache` set and no save outcome yet); after `discard_quiesce_timeout_seconds` it goes on with pods still running, logged. `_discard` order: cancel checks, quiesce, `save_step` (phase `deleting`, message "saving the workspace cache" while it returns False), `pre_discard`, prune. `DISCARD_ORDER` still deletes any leftover cache Job.
- Every deletion path goes through `_discard`: explicit delete, idle autoclose (`close_expired`), a trigger service's delete.

#### Acceptance conditions

- AC1: deleting a cached session scales the StatefulSet to zero, creates the save Job only after the agent pods are gone, and keeps the PVC until the save outcome [evidence: test:tests/test_cache_save.py::test_save_runs_after_quiesce_before_prune]
- AC2: a saved outcome records bytes, then the discard deletes the objects and purges the row [evidence: test:tests/test_cache_save.py::test_saved_then_purged]
- AC3: too_large, upload_failed and timeout are recorded, logged, and the discard still completes [evidence: test:tests/test_cache_save.py::test_failed_save_does_not_block_discard]
- AC4: a restore that is running, failed with download_failed or timeout, or a cache now unavailable skips the save with that reason and creates no Job [evidence: test:tests/test_cache_save.py::test_save_skipped_when_restore_did_not_finish]
- AC5: after an extract_failed restore the save runs [evidence: test:tests/test_cache_save.py::test_save_after_extract_failed]
- AC6: an idle autoclose saves the workspace [evidence: test:tests/test_cache_save.py::test_autoclose_saves]
- AC7: a quiesce timeout with pods still running saves anyway [evidence: test:tests/test_cache_save.py::test_quiesce_timeout_saves_anyway]
- AC8: a crash between the running write and the create creates the save Job exactly once [evidence: test:tests/test_cache_save.py::test_save_crash_safety]
- AC9: the save URL is a presigned PUT for the restore's object name [evidence: test:tests/test_cache_save.py::test_same_object_name]
- AC10: the discard hook, reconciler and autoclose tests stay green [evidence: command:uv run pytest -q tests/test_discard_hook.py tests/test_reconciler.py tests/test_autoclose.py]
- AC11: lint and format pass [evidence: command:uv run ruff check . && uv run ruff format --check .]

#### Files

- `src/agents_orchestrator/reconciler/cache.py`
- `src/agents_orchestrator/reconciler/loop.py`
- `tests/test_cache_save.py`
- `tests/fakes/fake_kube.py`

#### Interfaces

- `reconciler/cache.py:CacheRunner.save_step(session) -> bool`.
- `reconciler/loop.py:Reconciler._quiesce`, `_discard`.

#### Expected outcome

Deleting a cached session shows phase deleting with "saving the workspace cache", then the objects go and the row is purged; the bucket holds `workspace-cache/<key>.tar.zst` with the latest workdir.

#### Steps

- Red: write `tests/test_cache_save.py` (the nine named tests); run it: fails.
- Green: implement `save_step`, the quiesce condition and the discard order; run the verify command.

#### Notes

- `_quiesce` today returns True at once when no hook is owed; the new condition is `hook owed or save owed`; the existing ingester drain wait (`discard_drain_seconds`) stays as it is for both (it only adds seconds).
- The save must run before `_prune(..., DISCARD_ORDER)`, which deletes the PVC.
- Retro: a save must never act on an empty workdir path; `render_cache_job` takes it from `workdir_path(spec)`.

- 2026-10-26 done

### S13: cache docs

- Status: done
- Files: `README.md`, `MEMORY.md`, `tests/test_readme_api.py`
- Verify: `uv run pytest -q tests/test_readme_api.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: 3015bc9

#### Requirement

Document the workspace cache (design D4, D11, D12). Runs after the epic orchestrator-rename-sessions lands. Paths are in code/agents-orchestrator under the post-rename names (design Constraints: if that epic chose other module names, the same symbols apply and the orchestrator amends this file list first).

- `README.md`: a `## Workspace cache` section: the `spec.cache` field and the key derivation (`default_cache_key`, raw spec needs a key); the lifecycle (restore Job before init and the sessions, save Job during the discard before the PVC goes; nothing on pod restart or node loss); `status.cache` with every restore and save state and the save skip rules; last writer wins for sessions sharing a key; credentials only in the reconciler, Jobs get one presigned URL; a table of every `ORCH_CACHE_*` setting; the Job CLI env (`CACHE_URL`, `CACHE_DIR`, `CACHE_MAX_BYTES`, `CACHE_EXCLUDE`, `CACHE_SCRATCH`) and its JSON outcome line; `GET /api/v1/meta` `cache`.
- `MEMORY.md`: dated 2026 lines for D1 (Jobs, not the agent pod), D2 (presigned URLs), D4 (last writer wins), D11 (save skip rules), each with the why.
- `tests/test_readme_api.py`: `test_readme_documents_workspace_cache` asserts the section and each `ORCH_CACHE_*` name the settings define.

#### Acceptance conditions

- AC1: the README section names every ORCH_CACHE_* setting the code defines [evidence: test:tests/test_readme_api.py::test_readme_documents_workspace_cache]
- AC2: the section exists [evidence: doc-section:README.md#Workspace cache]
- AC3: MEMORY.md records the cache decisions [evidence: command:grep -q "presigned" MEMORY.md && grep -q "last writer wins" MEMORY.md]
- AC4: the README route and openapi tests stay green [evidence: command:uv run pytest -q tests/test_readme_api.py]
- AC5: lint and format pass [evidence: command:uv run ruff check . && uv run ruff format --check .]

#### Files

- `README.md`
- `MEMORY.md`
- `tests/test_readme_api.py`

#### Interfaces

- `README.md#Workspace cache`; contracts `orch-session-spec-cache`, `orch-session-status-cache`, `orch-cache-settings-env`, `orch-cache-job-cli`, `orch-meta-cache` documented there.

#### Expected outcome

A reader of the README can enable the cache on a preset, configure any S3 store, and read `status.cache`.

#### Steps

- Red: add `test_readme_documents_workspace_cache` to `tests/test_readme_api.py` (collect the `ORCH_CACHE_*` names from `Settings.model_fields`); run it: fails.
- Green: write the README section and the MEMORY.md lines; run the verify command.

#### Notes

- Match the README's existing style for settings tables and status fields (see the init scripts section).

- 2026-10-26 done

## Files to delete

none recorded in the epic format

## Final verify

none recorded in the epic format

## After merge

none
