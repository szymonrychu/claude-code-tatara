# Decouple S3 session cache from presets implementation plan

## Agreed rung

Not agreed yet: a draft migrated from the epic's tasks; the plan-writer revises it after the gate.

## Approach

Migrated from the epic format: one step per task file, in dependency order, each with its status, files, verify, verified head and every body section.

## Chunk 1: migrated tasks (model: opus)

### S1: orch cache copy if absent

- Status: todo
- Files: `src/agents_orchestrator/cache/copy.py`, `tests/test_cache_copy.py`
- Verify: `uv run --frozen pytest -q -p no:cacheprovider tests/test_cache_copy.py && mise run lint`
- Verified head: none

#### Requirement

User request (2026-10-29 04:52Z, mx-34 #343), verbatim: "I also want to decouple s3 cache from preset. There must be a way to define S3 backup name with jonja2 template with default as preset-sessionname. This must also copy caches of existing sessions, so after rotation everything will work properly." (jonja2 = Jinja2)

Leader constraint: the migration copies only, never moves or deletes S3 objects.

This task delivers design D8 in agents-orchestrator: a new module `src/agents_orchestrator/cache/copy.py` with `copy_if_absent(settings, source: str, dest: str) -> Literal["copied", "exists", "source_missing"]`, a synchronous server-side copy of one object key to another in `settings.cache_s3_bucket` through the one `presign._client` (no second credential path).

Recipe (brief-docs section 3): `head_object(dest)`: 200 answers `exists` and nothing is written (never overwrite). 404, then `head_object(source)`: 404 answers `source_missing`. 200, then `copy_object(Bucket, Key=dest, CopySource={"Bucket": ..., "Key": source}, CopySourceIfMatch=<the source ETag>)` with the default `MetadataDirective=COPY`, answering `copied`. Any other status (403 on a HEAD, 412 from a source rewritten meanwhile, 5xx) raises `CopyError`, whose message carries the operation and the status code and never a credential or a URL query.

The module never calls `delete_object`, `delete_objects` or `put_object` (copy only: the leader constraint). It is a single CopyObject (every object is at most `CACHE_MAX_BYTES_LIMIT`, 5 GiB); no multipart copy. Destination `If-None-Match` is not relied on (Ceph RGW and moto 5.2.4 ignore it on copy).

#### Acceptance conditions

- AC1: a present source is copied to an absent destination; the source is unchanged and the destination holds the same bytes [evidence: test:tests/test_cache_copy.py::test_copies_when_dest_absent]
- AC2: an existing destination answers exists and keeps its bytes [evidence: test:tests/test_cache_copy.py::test_existing_dest_is_never_overwritten]
- AC3: an absent source answers source_missing and writes nothing [evidence: test:tests/test_cache_copy.py::test_missing_source_writes_nothing]
- AC4: a 403 on a HEAD raises CopyError and is never read as absent [evidence: test:tests/test_cache_copy.py::test_forbidden_head_raises]
- AC5: a 412 from CopySourceIfMatch raises CopyError [evidence: test:tests/test_cache_copy.py::test_source_changed_raises]
- AC6: a CopyError message carries the operation and status and no access key, secret or signature [evidence: test:tests/test_cache_copy.py::test_error_carries_no_secret]
- AC7: the copy module calls no delete or put [evidence: command:! grep -nE "delete_object|delete_objects|put_object" src/agents_orchestrator/cache/copy.py]
- AC8: lint passes [evidence: command:mise run lint]

#### Files

- `src/agents_orchestrator/cache/copy.py`
- `tests/test_cache_copy.py`

#### Interfaces

- `src/agents_orchestrator/cache/copy.py` (new): `CopyOutcome = Literal["copied", "exists", "source_missing"]`, `class CopyError(Exception)`, `copy_if_absent(settings: Settings, source: str, dest: str) -> CopyOutcome` (synchronous; callers run it with `asyncio.to_thread`).
- Uses `presign._client(settings.cache_s3_endpoint, settings.cache_s3_region, settings.cache_s3_path_style, settings.cache_s3_verify_tls, settings.cache_s3_access_key_id, settings.cache_s3_secret_access_key)`; no second client or credential path (MEMORY 2026-10-28, one `_client`).

#### Expected outcome

`copy_if_absent(s, "workspace-cache/preset-x.tar.zst", "workspace-cache/my-repo-alpha.tar.zst")` copies once and answers `copied`, answers `exists` on a second call without writing, answers `source_missing` when the source is absent, and raises `CopyError` on any other S3 answer.

#### Steps

- Read cache/presign.py, settings.py (cache fields) and tests/test_cache_presign.py (its ThreadedMotoServer fixture and `_no_ambient_aws`) in one pass.
- Red: write tests/test_cache_copy.py with the tests named in the acceptance conditions (moto server for AC1-AC3, `botocore.stub.Stubber` on the client for the 403 and 412 cases); run `uv run --frozen pytest -q -p no:cacheprovider tests/test_cache_copy.py`; expect failure on the missing module.
- Green: write cache/copy.py; rerun; expect all passed.
- `mise run lint`; expect exit 0.

#### Notes

- brief-docs section 3 holds the recipe and citations: RGW does not read destination `If-None-Match` on CopyObject and moto 5.2.4 ignores it, so never-overwrite is HEAD-then-copy, safe because the reconciler is the single writer.
- `head_object` raises `botocore.exceptions.ClientError`; read `error.response["Error"]["Code"]` and `ResponseMetadata.HTTPStatusCode`; 404 is `"404"`/`NoSuchKey`. HEAD answers 403 instead of 404 without `s3:ListBucket`; that must raise, never read as absent.
- Pass `CopySource` as a dict so botocore URL-encodes the key; keep the default `MetadataDirective=COPY` (the stored Content-Type is the one the presigned PUT signed).
- These tests need no Postgres, so they run locally.
- Tree state (pictures baseline, 2026-10-28): `mise run lint` green; the full suite is red-env only. Tests that use the `pool`/`dsn` fixtures need Postgres through testcontainers, and agent pods have no Docker, so they error locally (`DockerException`) and run in CI on the PR: the reviewer reads the CI job for them and quotes its summary line. `tests/test_reconciler.py::test_lightkube_default_client_uses_env_config` fails in-cluster for an unrelated reason (KUBERNETES_SERVICE_HOST).
- If a verify run fails, save the failing test name and the output tail before any rerun (retro, markdown-rendering-in-chat).
- Per-task security check (retro, recurring): user input reaching S3 keys or a template engine is the high-risk surface here; check size bounds, refusal paths and that no credential or presigned query reaches a log, a status reason or an error message.
- Before working read the repo's AGENTS.md, MEMORY.md and ROADMAP.md. No em dashes. No backward-compatibility shims.

- 2026-10-29 amended: planner filled Interfaces, Expected outcome, Steps and Notes before the gate (retro: no empty Steps)

### S2: orch cache name template

- Status: todo
- Files: `src/agents_orchestrator/cache/naming.py`, `tests/test_cache_naming.py`, `pyproject.toml`, `uv.lock`
- Verify: `uv run --frozen pytest -q -p no:cacheprovider tests/test_cache_naming.py && mise run lint`
- Verified head: none

#### Requirement

User request (2026-10-29 04:52Z, mx-34 #343), verbatim: "I also want to decouple s3 cache from preset. There must be a way to define S3 backup name with jonja2 template with default as preset-sessionname. This must also copy caches of existing sessions, so after rotation everything will work properly." (jonja2 = Jinja2)

Leader constraint: the migration copies only, never moves or deletes S3 objects.

This task delivers design D2 and D3 in agents-orchestrator: a new module `src/agents_orchestrator/cache/naming.py`, importable by the api and the reconciler (it imports neither `reconciler` nor `k8s`), that renders a cache name template in the Jinja2 3.1.6 sandbox, and the runtime dependency `jinja2>=3.1.6` (`uv add "jinja2>=3.1.6"`).

- `DEFAULT_CACHE_NAME_TEMPLATE`: the default template, rendering `<preset>-<session>`. The preset part is shortened so the rendered name always matches `spec.CACHE_KEY_RE` (`^[a-z0-9][a-z0-9._-]{0,62}$`) for every valid preset name (including one that slugifies to an empty string) and every valid session slug (at most 40 characters).
- `CACHE_NAME_VARIABLES = ("preset", "preset_id", "session", "created_by")`: `preset` is `spec.slugify(<preset name>)`, `preset_id` the preset uuid as a string, `session` the session slug, `created_by` the creating service's token name or the empty string for a user.
- `check_template(template: str) -> None` raises `ValueError` with a message naming the problem when the template is longer than 256 characters; does not parse; uses anything beyond output expressions (no `for`, `if` block, `macro`, `call`, `set`, `include`, `import`, `extends`, `with` or `filter` block, no function or method call, no attribute access); uses a filter outside `lower`, `upper`, `replace`, `trim`, `truncate`; or refers to a variable outside `CACHE_NAME_VARIABLES` (`jinja2.meta.find_undeclared_variables`).
- `render_cache_name(template: str, **variables: str) -> str` checks the template, renders it in one module-level `ImmutableSandboxedEnvironment` (`undefined=StrictUndefined`, `autoescape=False`, no loader, no extensions, `globals` emptied before any template is loaded, `*` and `**` intercepted and refused), strips the output and raises `ValueError` unless the output matches `spec.CACHE_KEY_RE`. A variable the template uses but the caller did not pass raises `ValueError` naming it. Every exception from Jinja2 or the render is caught and re-raised as `ValueError`.

Amendment 2026-10-29 (interrogate verdict `/workdir/workdir/.scratchpad/s3-cache/interrogate.md` Act on 1; builder check `/workdir/workdir/.scratchpad/s3-cache/builder-check.md` Q4 and Q5; design D3 amendment), verbatim from design D3: the earlier rationale "the allowlist bounds the work by template length" was false. `"%0999999999d" % 1` allocates about 1 GB (`%` is not intercepted by the sandbox) and chained `replace("", X)` grows multiplicatively, and the key rule runs only after the render. So:
- The AST allowlist is exact (my call, builder-check Q4): `Template`, `Output`, `TemplateData`, `Name` (an allowed variable), `Const` string literals, integer `Const` only as slice bounds and filter arguments, `Getitem` only with a `Slice`, `CondExpr`, `Concat` (`~`), and `Filter` nodes of the five allowed filters with literal arguments. Every other node is refused, so every `BinOp` (`+`, `-`, `*`, `/`, `//`, `%`, `**`) is refused; `~` is a `Concat` node and stays allowed. The `*` and `**` interception stays as a second line.
- `replace` is a module filter that refuses an empty `old` with `ValueError`.
- Every filter refuses an input and an output longer than 256 characters, and a rendered output longer than 256 characters is refused, each with `ValueError`, before the key rule runs.
- A template that does not parse (a Jinja2 `TemplateSyntaxError`) is re-raised as `ValueError` (my call, builder-check Q5).

#### Acceptance conditions

- AC1: jinja2>=3.1.6 is a runtime dependency in pyproject.toml and uv.lock is current [evidence: command:grep -q '"jinja2>=3.1.6"' pyproject.toml && uv lock --locked]
- AC2: the default renders `<preset>-<session>` for a short preset name and slug, e.g. preset `my-repo` and session `alpha` give `my-repo-alpha` [evidence: test:tests/test_cache_naming.py::test_default_renders_preset_dash_session]
- AC3: the default renders a name matching CACHE_KEY_RE for a 40-character preset slug with a 40-character session slug, and for a preset that slugifies to an empty string [evidence: test:tests/test_cache_naming.py::test_default_always_fits_the_key_rule]
- AC4: a literal key without template syntax renders to itself [evidence: test:tests/test_cache_naming.py::test_literal_key_renders_to_itself]
- AC5: check_template raises ValueError for a template over 256 characters, a syntax error (a Jinja2 TemplateSyntaxError wrapped in ValueError), a for loop, an if block, a set, a function or method call, attribute access, a filter outside the allowlist and an unknown variable [evidence: test:tests/test_cache_naming.py::test_check_template_refusals]
- AC6: `*` and `**` are refused, so a template cannot inflate its output by multiplication or power [evidence: test:tests/test_cache_naming.py::test_multiplication_and_power_refused]
- AC7: a rendered value that breaks CACHE_KEY_RE (uppercase, a slash, longer than 63 characters, empty) raises ValueError [evidence: test:tests/test_cache_naming.py::test_rendered_name_must_match_key_rule]
- AC8: a variable the template uses but the caller did not pass raises ValueError naming it, never renders an empty string [evidence: test:tests/test_cache_naming.py::test_missing_variable_is_an_error]
- AC9: the naming module imports neither agents_orchestrator.reconciler nor agents_orchestrator.k8s [evidence: test:tests/test_cache_naming.py::test_naming_imports_no_reconciler_or_k8s]
- AC10: lint passes [evidence: command:mise run lint]
- AC11: every BinOp is refused by check_template and render_cache_name, including `%` string formatting (`{{ "%060d" % 1 }}`, `{{ "%0999999999d" % 1 }}`) and `+`, while `~` concatenation renders [evidence: test:tests/test_cache_naming.py::test_binops_refused_concat_allowed]
- AC12: `replace` with an empty `old` raises ValueError, and a chain of non-empty replaces whose intermediate grows past 256 characters raises ValueError instead of rendering [evidence: test:tests/test_cache_naming.py::test_replace_empty_old_and_chain_capped]
- AC13: a filter input or output longer than 256 characters and a rendered output longer than 256 characters each raise ValueError before the key rule runs; a slice (`preset[:22]`), a conditional expression and filter literal arguments are accepted, a non-slice subscript is refused [evidence: test:tests/test_cache_naming.py::test_per_step_cap_and_allowed_nodes]

#### Files

- `src/agents_orchestrator/cache/naming.py`
- `tests/test_cache_naming.py`
- `pyproject.toml`
- `uv.lock`

#### Interfaces

- `src/agents_orchestrator/cache/naming.py` (new): `DEFAULT_CACHE_NAME_TEMPLATE: str`, `CACHE_NAME_VARIABLES: tuple[str, ...] = ("preset", "preset_id", "session", "created_by")`, `TEMPLATE_MAX = 256`, `check_template(template: str) -> None` (raises `ValueError`), `render_cache_name(template: str, **variables: str) -> str` (raises `ValueError`).
- Reuses `spec.CACHE_KEY_RE` and `spec.slugify`; callers (task orch-cache-name-on-create, orch-cache-name-migration) pass `preset=slugify(name)` themselves.
- No import cycle: `spec.py` will call `naming.check_template` from the `WorkspaceCache.key` validator in the next task, so `naming` must import from `spec` only inside functions, or `spec` imports `naming` lazily; pick one and keep `python -c "import agents_orchestrator.spec, agents_orchestrator.cache.naming"` working.
- `pyproject.toml` `[project].dependencies` gains `"jinja2>=3.1.6"`; `uv.lock` updated by `uv add`.
- The environment's `filters` hold exactly `lower`, `upper`, `replace`, `trim`, `truncate`, each wrapped so it refuses an input or output over `TEMPLATE_MAX` (256) characters; `replace` is the module's own and refuses an empty `old` (design D3 amendment, 2026-10-29).

#### Expected outcome

`render_cache_name(DEFAULT_CACHE_NAME_TEMPLATE, preset="my-repo", preset_id="...", session="alpha", created_by="")` returns `my-repo-alpha`; any template beyond plain output expressions with the five allowed filters is refused with a `ValueError`; every rendered name matches `CACHE_KEY_RE`.

#### Steps

- Read `src/agents_orchestrator/spec.py` (CACHE_KEY_RE, slugify, SLUG_MAX), `pyproject.toml`, and agents-webhook's `src/agents_webhook/prompt.py` (`_BoundedEnvironment`) for the sandbox shape, in one pass.
- `uv add "jinja2>=3.1.6"`; expect pyproject.toml and uv.lock to change, `uv lock --locked` exits 0.
- Red: write tests/test_cache_naming.py with every test named in the acceptance conditions; run `uv run --frozen pytest -q -p no:cacheprovider tests/test_cache_naming.py`; expect collection to fail on the missing module.
- Green: write `cache/naming.py` (environment, exact AST node allowlist walk over `env.parse(...)` refusing every `BinOp`, capped filter wrappers and the own `replace`, `meta.find_undeclared_variables`, render, output cap, strip, key rule); rerun; expect all passed.
- `mise run lint`; expect `files already formatted` and exit 0.

#### Notes

- Sandbox recipe and citations: brief-docs section 1 (`/workdir/workdir/.scratchpad/s3-cache/brief-docs.md`). The sandbox alone does not bound output size, and neither does the allowlist by template length alone (interrogate 2026-10-29: `"%060d" % 1` renders 60 characters, two `replace("","xyz")` links take `ab` to 47); the exact node allowlist with no `BinOp`, the own `replace`, the per-filter and output 256-character caps and the post-render key rule do.
- Default shape is the builder's within the boundary: it must render `<preset>-<session>` when both are short and always match CACHE_KEY_RE (a 40-character preset slug plus `-` plus a 40-character slug is 81 > 63, and a preset name such as `...` slugifies to an empty string). Slicing (`preset[:22]`) and a conditional expression are allowed node types if the default needs them; document the chosen text in the module docstring.
- `meta.find_undeclared_variables` can raise `TemplateAssertionError`; map it to `ValueError`.
- Rejected: rendering in a forkserver child with time and memory limits (agents-webhook `prompt.py`), because the allowlist already bounds the work and the api and reconciler would each need a child process (design D3).
- Tree state (pictures baseline, 2026-10-28): `mise run lint` green; the full suite is red-env only. Tests that use the `pool`/`dsn` fixtures need Postgres through testcontainers, and agent pods have no Docker, so they error locally (`DockerException`) and run in CI on the PR: the reviewer reads the CI job for them and quotes its summary line. `tests/test_reconciler.py::test_lightkube_default_client_uses_env_config` fails in-cluster for an unrelated reason (KUBERNETES_SERVICE_HOST).
- If a verify run fails, save the failing test name and the output tail before any rerun (retro, markdown-rendering-in-chat).
- Per-task security check (retro, recurring): user input reaching S3 keys or a template engine is the high-risk surface here; check size bounds, refusal paths and that no credential or presigned query reaches a log, a status reason or an error message.
- Before working read the repo's AGENTS.md, MEMORY.md and ROADMAP.md. No em dashes. No backward-compatibility shims.

- 2026-10-29 amended: planner filled Interfaces, Expected outcome, Steps and Notes before the gate (retro: no empty Steps)

- 2026-10-29 amended: interrogate Act on 1 (/workdir/workdir/.scratchpad/s3-cache/interrogate.md) and builder-check Q4, Q5: every BinOp refused, own replace refuses empty old, 256-character per-step cap, exact node allowlist, syntax error as ValueError; AC5 clarified, AC11-AC13 added; Interfaces, Steps and Notes edited directly

### S3: orch preset legacy key strip

- Status: todo
- Files: `src/agents_orchestrator/db/migrations`, `tests/test_migrations.py`
- Verify: `uv run --frozen pytest -q -p no:cacheprovider tests/test_migrations.py && mise run lint`
- Verified head: none

#### Requirement

User request (2026-10-29 04:52Z, mx-34 #343), verbatim: "I also want to decouple s3 cache from preset. There must be a way to define S3 backup name with jonja2 template with default as preset-sessionname. This must also copy caches of existing sessions, so after rotation everything will work properly." (jonja2 = Jinja2)

Leader constraint: the migration copies only, never moves or deletes S3 objects.

This task delivers design D10 in agents-orchestrator: a new SQL migration `src/agents_orchestrator/db/migrations/<NNNN>_preset_cache_default_name.sql`, where `<NNNN>` is the next free number on the base branch when the task is built (expected 0015, after 0014 of immediate-message-delivery-w; main ends at 0011_drop_feed_cursor, slash adds 0010 and 0012, session-orchestration-mcp 0013), removes `cache.key` from every preset whose stored key equals its own pre-epic derived key (`'preset-' || left(encode(sha256(convert_to('workspace-cache:', 'UTF8') || uuid_send(id)), 'hex'), 16)`), so that preset gets the default cache name. Every other preset, including other literal keys, is unchanged. Idempotent and safe to re-run, like the earlier migrations.

Tests no longer accurate because they pin the migration list and a new migration exists; each gains the new version: tests/test_migrations.py::test_fresh_database_gets_all_tables, ::test_presets_migration_on_existing_sessions, ::test_concurrent_migrate_serialises and ::test_0005_renames_clusters_to_sessions.

#### Acceptance conditions

- AC1: a preset storing its own derived key loses cache.key and keeps cache.exclude; a preset with key `mine` and a preset storing another preset's derived key are unchanged [evidence: test:tests/test_migrations.py::test_preset_cache_default_name_strips_own_derived_key]
- AC2: re-running the migration changes nothing [evidence: test:tests/test_migrations.py::test_preset_cache_default_name_idempotent]
- AC3: the SQL formula gives `preset-4660fe5f5bc805e5` for the preset id uuid int 1, the value the removed Python default_cache_key pinned [evidence: test:tests/test_migrations.py::test_preset_cache_default_name_matches_pinned_key]
- AC4: a fresh database gets every migration including the new one [evidence: test:tests/test_migrations.py::test_fresh_database_gets_all_tables]
- AC5: lint passes [evidence: command:mise run lint]

#### Files

- `src/agents_orchestrator/db/migrations`
- `tests/test_migrations.py`

#### Interfaces

- `src/agents_orchestrator/db/migrations/<NNNN>_preset_cache_default_name.sql` (new; `<NNNN>` the next free number on the base branch at build time).
- Writes only `presets.spec` of presets whose `spec->'cache'->>'key'` equals their own pre-epic derived key; `jsonb` edit `spec #- '{cache,key}'` (or equivalent) keeps the rest of `cache`.

#### Expected outcome

After `orch migrate`, a preset that stored `preset-<its own hash>` has `spec.cache` without `key` (so its sessions get the default `<preset>-<session>`); every other preset is byte-for-byte unchanged; a second run changes nothing.

#### Steps

- Read db/migrate.py, db/migrations/0002_presets.sql and 0009_created_by_service.sql, and tests/test_migrations.py (`run_migrations`, `empty_dsn`, the tmp_path copy pattern of `test_0009_created_by_service_column`) in one pass; check the base branch for the highest migration number.
- Red: add the three new tests named in the acceptance conditions and add the new version to the four list-pinning tests named in the Requirement; run `uv run --frozen pytest -q -p no:cacheprovider tests/test_migrations.py`; expect failures on the missing migration (DB tests: on CI or a local Postgres).
- Green: write the SQL file; rerun; expect passed.
- `mise run lint`; expect exit 0.

#### Notes

- `sha256(bytea)` exists in Postgres 11 and later; `uuid_send(id)` gives the 16 bytes Python's `uuid.UUID.bytes` gives. AC3 pins the formula against `preset-4660fe5f5bc805e5` for `uuid.UUID(int=1)`, the value tests/test_api_cache.py pinned before this epic.
- Whether any live preset stores its own derived key is unknown (no DB read was made); the migration is correct either way.
- Expected number 0015 (negotiated 2026-10-29, mx-34 #469/#470): this lands after immediate-message-delivery-w's 0014, which follows session-orchestration-mcp's 0013, slash's 0010 and 0012 and main's 0011_drop_feed_cursor, not right after 0011. Rebase onto the base branch first and take the next free number then.
- Tree state (pictures baseline, 2026-10-28): `mise run lint` green; the full suite is red-env only. Tests that use the `pool`/`dsn` fixtures need Postgres through testcontainers, and agent pods have no Docker, so they error locally (`DockerException`) and run in CI on the PR: the reviewer reads the CI job for them and quotes its summary line. `tests/test_reconciler.py::test_lightkube_default_client_uses_env_config` fails in-cluster for an unrelated reason (KUBERNETES_SERVICE_HOST).
- If a verify run fails, save the failing test name and the output tail before any rerun (retro, markdown-rendering-in-chat).
- Per-task security check (retro, recurring): user input reaching S3 keys or a template engine is the high-risk surface here; check size bounds, refusal paths and that no credential or presigned query reaches a log, a status reason or an error message.
- Before working read the repo's AGENTS.md, MEMORY.md and ROADMAP.md. No em dashes. No backward-compatibility shims.

- 2026-10-29 amended: planner filled Interfaces, Expected outcome, Steps and Notes before the gate (retro: no empty Steps)

- 2026-10-29 amended: migration number is 0015, after immediate delivery's 0014 (mx-34 #469/#470)

### S4: orch transcripts follow name

- Status: todo
- Files: `src/agents_orchestrator/cache/presign.py`, `src/agents_orchestrator/reconciler/cache.py`, `tests/test_sessions_restore.py`, `tests/test_sessions_backup.py`, `MEMORY.md`
- Verify: `uv run --frozen pytest -q -p no:cacheprovider tests/test_sessions_restore.py tests/test_sessions_backup.py tests/test_cache_restore.py tests/test_cache_save.py && mise run lint`
- Verified head: none

#### Requirement

User request (2026-10-29 04:52Z, mx-34 #343), verbatim: "I also want to decouple s3 cache from preset. There must be a way to define S3 backup name with jonja2 template with default as preset-sessionname. This must also copy caches of existing sessions, so after rotation everything will work properly." (jonja2 = Jinja2)

Leader constraint: the migration copies only, never moves or deletes S3 objects.

This task delivers design D5 in agents-orchestrator: one cache name per session names both of its S3 objects. The workspace archive stays `<prefix><name>.tar.zst`; the Claude transcripts object becomes `<prefix>sessions/<name>.tar.zst` (it was `<prefix>sessions/<slug>.tar.zst`).

- The first restore of either target (`reconciler/cache.py:CacheRunner._begin`; the transcripts restore runs first) pins `status.cache.key` (the session's `spec.cache.key`), `status.cache.object` and the new `status.cache.sessions_object`. Every later restore and save of both targets presigns from the pinned `status.cache.key`.
- `presign.sessions_object_name(settings, name)` and `presign.target_object_name(settings, target, name)` take the cache name for both targets; `CacheRunner._start` passes the pinned name for the sessions target instead of the slug.
- `_begin` pins the name for every run (restore or save, either target) when `status.cache.key` is absent, so no restore or save of the transcripts ever uses the slug.
- MEMORY.md records the decision (dated, with the why).

Tests no longer accurate and rewritten, because the transcripts object now follows the cache name (design D5): tests/test_sessions_restore.py::test_sessions_restore_job_render and tests/test_sessions_backup.py::test_discard_saves_sessions_after_workdir (both assert `/workspace-cache/sessions/alpha.tar.zst`, the slug), and tests/test_sessions_backup.py::test_sessions_save_job_render and ::test_sessions_object_name_distinct_from_cache_keys where they pass the slug as the name.

#### Acceptance conditions

- AC1: the transcripts restore Job presigns a GET of `<prefix>sessions/<spec.cache.key>.tar.zst`, and the first restore pins status.cache key, object and sessions_object [evidence: test:tests/test_sessions_restore.py::test_sessions_restore_uses_cache_name]
- AC2: the transcripts save Job presigns a PUT of `<prefix>sessions/<status.cache.key>.tar.zst` [evidence: test:tests/test_sessions_backup.py::test_sessions_save_uses_cache_name]
- AC3: once pinned, a different spec.cache.key moves neither object: restore and save of both targets use status.cache.key [evidence: test:tests/test_sessions_backup.py::test_pinned_name_wins_over_spec]
- AC4: sessions_object_name(settings, "my-repo-alpha") is `workspace-cache/sessions/my-repo-alpha.tar.zst` and never equals object_name of any valid key [evidence: test:tests/test_sessions_backup.py::test_sessions_object_name_distinct_from_cache_keys]
- AC5: MEMORY.md records that the transcripts object follows the cache name [evidence: command:grep -q "sessions_object" MEMORY.md]
- AC6: lint passes [evidence: command:mise run lint]

#### Files

- `src/agents_orchestrator/cache/presign.py`
- `src/agents_orchestrator/reconciler/cache.py`
- `tests/test_sessions_restore.py`
- `tests/test_sessions_backup.py`
- `MEMORY.md`

#### Interfaces

- `cache/presign.py`: `sessions_object_name(settings, name: str) -> str` returns `<prefix>sessions/<name>.tar.zst`; `target_object_name(settings, target, name)` and `presign(settings, method, name, target)` take the cache name for both targets.
- `reconciler/cache.py:CacheRunner._begin` pins `status.cache.key`, `object` and `sessions_object` for every run when `key` is absent; `_start` presigns the sessions target from `cache["key"]`; a run without a key fails `no_cache_key` for both targets.
- Contract change (docs/plans/contracts.json, updated by the orchestrator): `orch-session-status-cache` gains `sessions_object`.

#### Expected outcome

A new cache-enabled session with cache name `my-repo-alpha` restores and saves its transcripts at `workspace-cache/sessions/my-repo-alpha.tar.zst`, and `status.cache` carries `key`, `object` and `sessions_object` from its first restore on.

#### Steps

- Read cache/presign.py, reconciler/cache.py (`_begin`, `_start`, `sessions_restore_step`, `save_step`), cache/save_rule.py, tests/test_sessions_restore.py, tests/test_sessions_backup.py and the MEMORY.md 2026-10-28 transcript entries in one pass.
- Red: add the tests named in the acceptance conditions and rewrite the tests named in the Requirement to expect `sessions/<cache name>`; run `uv run --frozen pytest -q -p no:cacheprovider tests/test_sessions_restore.py tests/test_sessions_backup.py`; expect the new assertions to fail (DB tests: on CI or a local Postgres).
- Green: change presign.py and reconciler/cache.py; rerun the verify; expect passed.
- Add the MEMORY.md entry (dated, why: one name per session covers its whole backup, user Q1); `mise run lint`; expect exit 0.

#### Notes

- The test fixtures use slug `alpha` and a cache key different from the slug, so a test that still passes with the slug proves nothing; assert the key path.
- `SESSIONS_EXCLUDE`, the save rule and the Job rendering do not change; only the object name and the pinned fields do.
- Sessions sharing a cache name now share their transcripts too (design D5, open question Q1); the bootstrapper resumes a stopped session with a transcript, so a recreated session resumes the last conversation saved under that name.
- Tree state (pictures baseline, 2026-10-28): `mise run lint` green; the full suite is red-env only. Tests that use the `pool`/`dsn` fixtures need Postgres through testcontainers, and agent pods have no Docker, so they error locally (`DockerException`) and run in CI on the PR: the reviewer reads the CI job for them and quotes its summary line. `tests/test_reconciler.py::test_lightkube_default_client_uses_env_config` fails in-cluster for an unrelated reason (KUBERNETES_SERVICE_HOST).
- If a verify run fails, save the failing test name and the output tail before any rerun (retro, markdown-rendering-in-chat).
- Per-task security check (retro, recurring): user input reaching S3 keys or a template engine is the high-risk surface here; check size bounds, refusal paths and that no credential or presigned query reaches a log, a status reason or an error message.
- Before working read the repo's AGENTS.md, MEMORY.md and ROADMAP.md. No em dashes. No backward-compatibility shims.

- 2026-10-29 amended: planner filled Interfaces, Expected outcome, Steps and Notes before the gate (retro: no empty Steps)

### S5: web discard effective name

- Status: todo
- Files: `src/sessions/DiscardSessionDialog.tsx`, `src/sessions/DiscardSessionDialog.test.tsx`
- Verify: `npm ci --no-audit --no-fund && npx vitest run src/sessions/DiscardSessionDialog.test.tsx && npm run lint`
- Verified head: none

#### Requirement

User request (2026-10-29 04:52Z, mx-34 #343), verbatim: "I also want to decouple s3 cache from preset. There must be a way to define S3 backup name with jonja2 template with default as preset-sessionname. This must also copy caches of existing sessions, so after rotation everything will work properly." (jonja2 = Jinja2)

Leader constraint: the migration copies only, never moves or deletes S3 objects.

This task delivers design D12 (session side) in agents-web: the discard dialog names the session's effective cache name, `status.cache.key` (pinned by the reconciler at the first restore), falling back to `spec.cache.key` before that, for both the workspace files and the Claude transcripts, and says they are restored by the next session whose cache name is the same (by default a session from the same preset with the same slug). This replaces the wrong `restored when a session with the same slug is created`.

Test no longer accurate, rewritten: src/sessions/DiscardSessionDialog.test.tsx `states what is backed up when the session cache is configured` (it pins the removed wording).

#### Acceptance conditions

- AC1: with status.cache.key `my-repo-alpha` and spec.cache.key `preset-0123456789abcdef` the dialog names `my-repo-alpha` for the workspace files and the transcripts, with the new restore wording [evidence: command:npx vitest run src/sessions/DiscardSessionDialog.test.tsx -t "names the effective cache name"]
- AC2: without status.cache.key the dialog names spec.cache.key [evidence: command:npx vitest run src/sessions/DiscardSessionDialog.test.tsx -t "falls back to the spec cache name before the first restore"]
- AC3: the old wording is gone from src [evidence: command:! grep -rn "restored when a session with the same slug is created" src]
- AC4: the whole dialog suite and lint pass [evidence: command:npx vitest run src/sessions/DiscardSessionDialog.test.tsx && npm run lint]

#### Files

- `src/sessions/DiscardSessionDialog.tsx`
- `src/sessions/DiscardSessionDialog.test.tsx`

#### Interfaces

- `src/sessions/DiscardSessionDialog.tsx`: the effective name is `session.status.cache?.key` when it is a non-empty string, else `session.spec.cache?.key`; `status` is `Record<string, unknown>` in the schema, so narrow the type before use.

#### Expected outcome

Discarding a migrated session whose spec still says `preset-0123456789abcdef` and whose `status.cache.key` is `my-repo-alpha` shows that both the workspace files and the Claude transcripts are saved under `my-repo-alpha` and restored by the next session with the same cache name (by default the same preset and slug).

#### Steps

- Read src/sessions/DiscardSessionDialog.tsx and src/sessions/DiscardSessionDialog.test.tsx (`existing`, `wrap`) in one pass.
- `npm ci --no-audit --no-fund`.
- Red: rewrite `states what is backed up when the session cache is configured` for the new wording and add the two tests named in the acceptance conditions; run `npx vitest run src/sessions/DiscardSessionDialog.test.tsx`; expect them to fail.
- Green: change DiscardSessionDialog.tsx; rerun; expect all passed.
- `npm run lint`; expect exit 0.

#### Notes

- The orchestrator pins `status.cache.key` at the first restore and the migration repoints it for pre-epic sessions (tasks orch-transcripts-follow-name, orch-cache-name-migration); the spec key of a pre-epic session stays the old `preset-*` literal because the api owns `spec`.
- No schema sync is needed: `status` is free-form.
- Tree state (pictures baseline, 2026-10-28): `mise run lint` green; `npm test` had 6 test files failing to import `@codemirror/*` because node_modules was stale, so the verify runs `npm ci --no-audit --no-fund` first.
- If a verify run fails, save the failing test name and the output tail before any rerun (retro, recurring vitest load flake in PresetForm).
- Before working read the repo's AGENTS.md, MEMORY.md and ROADMAP.md. No em dashes. No backward-compatibility shims.

- 2026-10-29 amended: planner filled Interfaces, Expected outcome, Steps and Notes before the gate (retro: no empty Steps)

### S6: orch cache name on create

- Status: todo
- Files: `src/agents_orchestrator/spec.py`, `src/agents_orchestrator/api/sessions.py`, `src/agents_orchestrator/api/presets.py`, `src/agents_orchestrator/api/schemas.py`, `openapi.json`, `README.md`, `MEMORY.md`, `tests/test_api_cache.py`
- Verify: `uv run --frozen pytest -q -p no:cacheprovider tests/test_api_cache.py tests/test_readme_api.py tests/test_cache_naming.py && mise run lint`
- Verified head: none

#### Requirement

User request (2026-10-29 04:52Z, mx-34 #343), verbatim: "I also want to decouple s3 cache from preset. There must be a way to define S3 backup name with jonja2 template with default as preset-sessionname. This must also copy caches of existing sessions, so after rotation everything will work properly." (jonja2 = Jinja2)

Leader constraint: the migration copies only, never moves or deletes S3 objects.

This task delivers design D1, D4, D6 and D13 in agents-orchestrator.

- `spec.cache.key` is a cache name template (Jinja2, `cache.naming`): `WorkspaceCache.key` accepts any string that passes `naming.check_template` (at most 256 characters). A literal key such as `mine` keeps working and names one shared cache, as today.
- Session create from a preset (`api/sessions.py:_create_from_preset`) renders the preset's `spec.cache.key`, or `naming.DEFAULT_CACHE_NAME_TEMPLATE` when it is empty, with `preset` = `slugify(preset.name)`, `preset_id`, `session` = the session's slug (the caller's, or each generated slug attempt) and `created_by` = the calling service or `""`, and stores the rendered name as the session's `spec.cache.key`. A render error answers 422 `invalid_request` naming the preset.
- A raw-spec session (`POST /api/v1/sessions` with `spec`) still needs `cache.key` (422 without it, as today). It is rendered with `session` and `created_by` only, so a template that refers to `preset` or `preset_id` answers 422.
- Preset create and replace (`api/presets.py:_validated`) answer 422 `invalid_request` when `naming.check_template` refuses the key or a trial render fails with this preset's name, a sample preset id, a 40-character sample slug and an empty `created_by`. The preset stores the template as sent.
- Removed with no replacement (no backward compatibility): `spec.default_cache_key`, `spec.CACHE_KEY_RESERVED_PREFIX`, `spec.check_caller_cache_key`, `check_spec`'s `derived_cache_key` parameter and `api/presets.py:_without_derived_key`. A preset copy keeps the source's `cache` as it is.
- `GET /api/v1/meta` `cache` gains `default_name_template` (the text of `DEFAULT_CACHE_NAME_TEMPLATE`). `openapi.json` is regenerated (`uv run python -m agents_orchestrator.api.openapi > openapi.json`).
- README `### Spec and key` describes the cache name template, its variables, the default, the 256-character and key-rule limits and the render points. MEMORY.md records the decisions (dated, with the why).

Tests no longer accurate, removed or rewritten in tests/test_api_cache.py, because the user asked to decouple the cache from the preset: `test_default_cache_key` and `test_default_cache_key_is_pinned` (the preset-id-derived key no longer exists), `test_create_from_preset_derives_key` (the default is now the rendered `<preset>-<session>`), `test_preset_prefix_reserved` and `test_copy_drops_source_derived_key` (the reserved prefix and the derived key are removed, design D6), `test_meta_cache` (its exact dict gains `default_name_template`).

#### Acceptance conditions

- AC1: two sessions created from a keyless cache preset named `My Repo` with slugs `alpha` and `beta` get cache keys `my-repo-alpha` and `my-repo-beta` [evidence: test:tests/test_api_cache.py::test_create_from_preset_renders_default_name]
- AC2: a session created from a preset without a slug gets the default rendered with its generated slug [evidence: test:tests/test_api_cache.py::test_generated_slug_renders_into_name]
- AC3: a preset template `{{ preset }}-shared` gives every session of that preset the same key, and a literal preset key `mine` is kept as is [evidence: test:tests/test_api_cache.py::test_preset_template_and_literal_key]
- AC4: preset create and replace answer 422 for a template with an unknown variable, a for loop, a syntax error, or one whose trial render with a 40-character slug breaks the key rule [evidence: test:tests/test_api_cache.py::test_preset_template_validated_on_save]
- AC5: a raw-spec session renders `{{ session }}-x` into `<slug>-x`, answers 422 for a template using `preset`, and still answers 422 without `cache.key` [evidence: test:tests/test_api_cache.py::test_raw_spec_key_template]
- AC6: keys starting with `preset-` are accepted like any other key on presets and raw specs, and a preset copy keeps the source cache unchanged [evidence: test:tests/test_api_cache.py::test_no_reserved_prefix_and_copy_keeps_cache]
- AC7: default_cache_key, CACHE_KEY_RESERVED_PREFIX, check_caller_cache_key, derived_cache_key and _without_derived_key are gone from src [evidence: command:! grep -rnE "default_cache_key|CACHE_KEY_RESERVED_PREFIX|check_caller_cache_key|derived_cache_key|_without_derived_key" src]
- AC8: GET /api/v1/meta cache carries available, max_bytes and default_name_template equal to naming.DEFAULT_CACHE_NAME_TEMPLATE [evidence: test:tests/test_api_cache.py::test_meta_cache]
- AC9: the committed openapi.json matches the app [evidence: test:tests/test_readme_api.py::test_openapi_json_matches_app]
- AC10: README and MEMORY.md describe the cache name template [evidence: command:grep -qi "cache name template" README.md && grep -qi "cache name template" MEMORY.md]
- AC11: lint passes [evidence: command:mise run lint]

#### Files

- `src/agents_orchestrator/spec.py`
- `src/agents_orchestrator/api/sessions.py`
- `src/agents_orchestrator/api/presets.py`
- `src/agents_orchestrator/api/schemas.py`
- `openapi.json`
- `README.md`
- `MEMORY.md`
- `tests/test_api_cache.py`

#### Interfaces

- `spec.WorkspaceCache.key: str | None` validated by `naming.check_template` (was `CACHE_KEY_RE`); `spec.CACHE_KEY_RE` stays the rule for a rendered name.
- `api/sessions.py:check_spec(spec, settings, stored=None)` (no `derived_cache_key`); `_create_from_preset` renders inside the slug loop; `create_session` renders a raw-spec key.
- `api/presets.py:_validated` trial-renders; `copy_preset` copies `source.spec` unchanged.
- `api/schemas.py:MetaCache` gains `default_name_template: str`; `openapi.json` regenerated.
- Contract change (docs/plans/contracts.json, updated by the orchestrator, not this task): `orch-session-spec-cache` key is a template on presets and raw specs and the rendered name on stored sessions; `orch-meta-cache` gains `default_name_template`.

#### Expected outcome

`POST /api/v1/sessions {"preset_id": <My Repo>, "slug": "alpha"}` answers a session whose `spec.cache.key` is `my-repo-alpha`; a preset with an unsafe template is refused with 422; `/meta` shows the default template; nothing in `src` mentions the preset-derived key.

#### Steps

- Read spec.py (WorkspaceCache, default_cache_key, check_caller_cache_key), api/sessions.py, api/presets.py, api/schemas.py (MetaCache), README.md `## Workspace cache`, tests/test_api_cache.py and tests/test_api_sessions.py helpers (`client_for`, `make_settings`, `assert_error`) in one pass.
- Red: rewrite tests/test_api_cache.py: drop the five tests named in the Requirement, add the tests named in the acceptance conditions, extend `test_meta_cache`; run `uv run --frozen pytest -q -p no:cacheprovider tests/test_api_cache.py`; DB tests error locally without Docker, so confirm red on CI or with a local Postgres; the non-DB tests must fail on the missing behaviour.
- Green: change spec.py, api/sessions.py, api/presets.py, api/schemas.py; regenerate `uv run python -m agents_orchestrator.api.openapi > openapi.json`; rerun the verify; expect the non-DB tests and `tests/test_readme_api.py::test_openapi_json_matches_app` passed.
- Update README `### Spec and key` and add the MEMORY.md entry; `mise run lint`; expect exit 0.

#### Notes

- Render in `_create_from_preset` per slug attempt (`generated_slug` changes each retry, `api/sessions.py` around l.288-293); the session id is not available there and is not a variable.
- `created_by` is `calling_service(request)` or `""`; `preset` is `slugify(preset.name)` (preset names allow uppercase, spaces, `.`, `_`, 40 characters, `db/presets.py:19-20`).
- Trial render at preset save uses a 40-character sample slug (worst case) so a template that can break the key rule is caught at save, not at session create.
- Security: dropping the reserved prefix is design D6 (open question Q6): any API caller can already create a session from any preset with any free slug and so reach that cache; the prefix protected nothing once names are `<preset>-<session>`.
- Do not touch tests/test_api_create_from_preset.py or tests/test_api_presets.py unless a test there fails because of the removed derived key; then name it as no longer accurate in the report.
- Tree state (pictures baseline, 2026-10-28): `mise run lint` green; the full suite is red-env only. Tests that use the `pool`/`dsn` fixtures need Postgres through testcontainers, and agent pods have no Docker, so they error locally (`DockerException`) and run in CI on the PR: the reviewer reads the CI job for them and quotes its summary line. `tests/test_reconciler.py::test_lightkube_default_client_uses_env_config` fails in-cluster for an unrelated reason (KUBERNETES_SERVICE_HOST).
- If a verify run fails, save the failing test name and the output tail before any rerun (retro, markdown-rendering-in-chat).
- Per-task security check (retro, recurring): user input reaching S3 keys or a template engine is the high-risk surface here; check size bounds, refusal paths and that no credential or presigned query reaches a log, a status reason or an error message.
- Before working read the repo's AGENTS.md, MEMORY.md and ROADMAP.md. No em dashes. No backward-compatibility shims.

- 2026-10-29 amended: planner filled Interfaces, Expected outcome, Steps and Notes before the gate (retro: no empty Steps)

### S7: orch cache name migration

- Status: todo
- Files: `src/agents_orchestrator/reconciler/cache_migration.py`, `src/agents_orchestrator/reconciler/loop.py`, `src/agents_orchestrator/reconciler/cache.py`, `src/agents_orchestrator/cache/presign.py`, `tests/test_cache_migration.py`, `README.md`, `MEMORY.md`
- Verify: `uv run --frozen pytest -q -p no:cacheprovider tests/test_cache_migration.py tests/test_cache_presign.py tests/test_cache_restore.py tests/test_cache_save.py tests/test_sessions_restore.py tests/test_sessions_backup.py && mise run lint`
- Verified head: none

#### Requirement

User request (2026-10-29 04:52Z, mx-34 #343), verbatim: "I also want to decouple s3 cache from preset. There must be a way to define S3 backup name with jonja2 template with default as preset-sessionname. This must also copy caches of existing sessions, so after rotation everything will work properly." (jonja2 = Jinja2)

Leader constraint: the migration copies only, never moves or deletes S3 objects.

This task delivers design D7 and D9 in agents-orchestrator: the reconciler copies the caches of the sessions that existed before this epic to their new names and repoints them, so a session discarded and recreated with the same slug from the same preset (rotation) restores its workspace and transcripts. New module `src/agents_orchestrator/reconciler/cache_migration.py`, called from `reconciler/loop.py` once per tick per session: in `_converge` before the transcripts restore step, and in `_discard` before the workdir save.

- Which sessions: `spec.cache` set, the cache configured (`settings.cache_available`), no `status.cache.migration` record or one in state `failed` (amended 2026-10-29, item 2 below), and either `status.cache.key` set without `status.cache.sessions_object` (pinned before this epic) or `spec.cache.key` equal to the pre-epic preset key of `preset_id` (`preset-` plus the first 16 hex digits of sha256(`workspace-cache:` + the preset id's 16 bytes)), a formula kept in this module only to recognise old sessions; or `preset_id` NULL with `preset_name` set and a key matching `preset-[0-9a-f]{16}` (amended 2026-10-29, item 6 below).
- New name: for a session on its pre-epic preset key, what a session created now from its source preset with its slug would get: the preset's current `spec.cache.key` template, or `naming.DEFAULT_CACHE_NAME_TEMPLATE` when it is empty, rendered with the preset's current name, `preset_id`, the slug and `created_by_service` (`""` when null); when the preset was deleted, the default rendered with the stored `preset_name`. Every other session keeps its current name (`status.cache.key`, else `spec.cache.key`).
- Copy (`cache.copy.copy_if_absent`, run off the event loop with `asyncio.to_thread`): the workspace object `<prefix><old name>.tar.zst` to `<prefix><new name>.tar.zst` when the names differ, and the transcripts object `<prefix>sessions/<slug>.tar.zst` to `<prefix>sessions/<new name>.tar.zst` when they differ. Copy only: nothing is moved, deleted or overwritten.
- Then repoint: `status.cache.key`, `status.cache.object` and `status.cache.sessions_object` take the new name, and `status.cache.migration` records `{state: done, from_key, workdir, sessions, finished_at}`, where `workdir` and `sessions` are each `copied`, `exists`, `source_missing` or `unchanged`.
- Failure: a render error records `migration` `{state: failed, reason}` once and keeps the old names (not retried in `_converge`; retried in `_discard`, amended 2026-10-29, item 2 below). A `CopyError` in `_converge` records `{state: failed, reason, failures, next_at}` (backoff `settings.retry_delay_seconds(failures)`, database clock), keeps the old names and retries after `next_at`. In `_discard` it repoints per target as in item 5 below (amended 2026-10-29; was: repoints anyway), records the failure and never holds the discard.
- README documents the migration and the `status.cache` fields (`key`, `object`, `sessions_object`, `migration`). MEMORY.md records the decisions (dated, with the why).

Amendment 2026-10-29 (interrogate verdict `/workdir/workdir/.scratchpad/s3-cache/interrogate.md` Act on 2-6; design D7 and D9 amendments), verbatim from design D7 and D9:

1. Eligibility (item 2): "no `status.cache.migration` yet" becomes "no `status.cache.migration` record, or one in state `failed`"; a `done` record is final. Otherwise a converge failure followed by a discard could skip the migration, save under the old name, and the recreated session would restore nothing: the timing trap this decision exists to close.
2. Discard retries (item 2): in `_discard` every record that is not `done` (none, or `failed` from a render or a copy) is retried at once, regardless of `next_at`, and then repointed or kept per target as below; the discard is still never held.
3. Transcripts while pending (item 3): "the old name has the same content" holds for the workspace only; before the migration a pre-epic session's transcripts live at `sessions/<slug>`, never at `sessions/<legacy key>`. While a session's migration is pending (eligible under D7 with no `done` record, including `failed`), the transcripts restore and save presign the legacy `<prefix>sessions/<slug>.tar.zst` and `status.cache.sessions_object` is not pinned; it is pinned only by the migration's repoint or, for a session that is not pre-epic, by the first restore. Once `sessions_object` is pinned, the sessions target presigns exactly that object.
4. Save in flight at deploy (item 4): the migration does nothing while a save run of either target is `running` (the save step advances it); when a save of a target has finished, the copy runs after it, from the object that save just wrote, so the new name never carries a stale or half-overwritten copy.
5. Repoint after a failed copy (item 5): in `_discard` the repoint is per target. The workspace target (`key`, `object`) and the transcripts target (`sessions_object`) each take the new name when their copy succeeded (`copied`, `exists`, `source_missing`, `unchanged`) or when `save_skip(settings.cache_available, status, target)` (`cache/save_rule.py`) is None, so their save lands under the new name; a target whose copy failed and whose save is skipped (`never_converged`, a failed restore, `not_configured`) keeps its old object, and the record is `failed` naming that target.
6. Deleted presets (item 6): `sessions.preset_id` is `ON DELETE SET NULL` (`0002_presets.sql:19`), so the pre-epic preset key of a deleted preset cannot be computed. A session with `preset_id` NULL, `preset_name` set and a key (`status.cache.key`, else `spec.cache.key`) matching `preset-[0-9a-f]{16}` counts as being on its pre-epic preset key; its new name is the default rendered with `slugify(preset_name)`.

#### Acceptance conditions

- AC1: a live pre-epic session from preset `My Repo` (slug alpha, status.cache.key the pre-epic preset key, no sessions_object) gets `<prefix><old key>.tar.zst` copied to `<prefix>my-repo-alpha.tar.zst` and `<prefix>sessions/alpha.tar.zst` to `<prefix>sessions/my-repo-alpha.tar.zst`; status.cache key, object and sessions_object are repointed and migration is done [evidence: test:tests/test_cache_migration.py::test_live_preset_session_copied_and_repointed]
- AC2: after the migration the discard saves presign PUTs of the new workspace and transcripts objects, and a session created again from the same preset with the same slug restores those same objects (rotation) [evidence: test:tests/test_cache_migration.py::test_rotation_restores_the_migrated_cache]
- AC3: an existing destination object is never overwritten, the old objects still exist after the migration, and no delete or put request reaches S3 [evidence: test:tests/test_cache_migration.py::test_copy_only_never_overwrites_or_deletes]
- AC4: a missing source records source_missing for that object and the session is still repointed [evidence: test:tests/test_cache_migration.py::test_missing_source_repoints]
- AC5: the preset's current template decides the new name (template `{{ preset }}` gives `my-repo`), and a deleted preset falls back to the default with the stored preset name [evidence: test:tests/test_cache_migration.py::test_new_name_follows_current_preset_template]
- AC6: a raw-spec session with a literal key keeps its workspace name and only its transcripts are copied from sessions/<slug> to sessions/<key> [evidence: test:tests/test_cache_migration.py::test_raw_spec_session_copies_transcripts_only]
- AC7: a session whose sessions_object was pinned after this epic, and a session with a `done` migration record, are never migrated again [evidence: test:tests/test_cache_migration.py::test_new_and_migrated_sessions_skipped]
- AC8: a CopyError during converge records failed with failures and next_at, keeps the old names, and the migration retries once next_at has passed [evidence: test:tests/test_cache_migration.py::test_copy_error_in_converge_retries_with_backoff]
- AC9: a CopyError during discard on a target whose save_skip is None repoints that target to the new name, records failed, and the saves (under the new name) and the discard still complete [evidence: test:tests/test_cache_migration.py::test_copy_error_in_discard_never_holds]
- AC10: a pre-epic session that never converged (spec key the pre-epic preset key, no status.cache) is migrated before its first restore, which then reads the new names [evidence: test:tests/test_cache_migration.py::test_unconverged_pre_epic_session_migrated_before_restore]
- AC11: the migration module calls no delete or put [evidence: command:! grep -nE "delete_object|delete_objects|put_object" src/agents_orchestrator/reconciler/cache_migration.py]
- AC12: README documents status.cache.migration and MEMORY.md records the migration [evidence: command:grep -q "status.cache.migration" README.md && grep -q "cache.migration" MEMORY.md]
- AC13: lint passes [evidence: command:mise run lint]
- AC14: a pre-epic session whose preset was deleted (preset_id NULL, preset_name `My Repo`, key matching `preset-[0-9a-f]{16}`, both pinned and unconverged variants) is migrated to `my-repo-alpha` via the default rendered with the stored preset name [evidence: test:tests/test_cache_migration.py::test_deleted_preset_session_migrated_by_preset_name]
- AC15: converge failed, then discard: a session whose migration record is `failed` (a CopyError with next_at in the future, and a render failure) is retried at the discard regardless of next_at, its saves land under the new name, and a session recreated from the same preset with the same slug restores them [evidence: test:tests/test_cache_migration.py::test_failed_then_discard_migrates]
- AC16: while a save run of either target is `running` the migration copies and repoints nothing [evidence: test:tests/test_cache_migration.py::test_migration_waits_for_running_save]
- AC17: a discard whose workdir save finished under the old name before the migration ran copies that just-saved object, and the recreated session restores the saved content, never an older copy [evidence: test:tests/test_cache_migration.py::test_finished_save_copied_after_it]
- AC18: a CopyError during discard on a target whose save_skip returns a reason (never_converged, a failed restore) keeps that target's old object, records failed naming the target, and the discard completes [evidence: test:tests/test_cache_migration.py::test_copy_error_with_skipped_save_keeps_old_name]
- AC19: while a pre-epic session's migration is pending or failed, the transcripts restore and save presign `<prefix>sessions/<slug>.tar.zst` and status.cache.sessions_object stays unset; after a successful retry sessions_object is the new name and later runs presign it [evidence: test:tests/test_cache_migration.py::test_pending_migration_transcripts_use_legacy_slug]

#### Files

- `src/agents_orchestrator/reconciler/cache_migration.py`
- `src/agents_orchestrator/reconciler/loop.py`
- `src/agents_orchestrator/reconciler/cache.py`
- `src/agents_orchestrator/cache/presign.py`
- `tests/test_cache_migration.py`
- `README.md`
- `MEMORY.md`

#### Interfaces

- `src/agents_orchestrator/reconciler/cache_migration.py` (new): a class or function the `Reconciler` calls with the session and a `during_discard: bool`, writing through the reconciler's `_write_status` (the reconciler is the only writer of `sessions.status`); `legacy_preset_key(preset_id: uuid.UUID) -> str` lives here only.
- `reconciler/loop.py`: `_converge` calls it before `self.cache.sessions_restore_step`; `_discard` calls it after `_quiesce` and before the workdir `save_step`; the session is reloaded after a repoint so the next step reads the new `status.cache`.
- Reads the source preset with `db/presets.get(conn, preset_id)` (read only; the api stays the only writer of `presets`).
- Uses `cache.naming.render_cache_name`, `cache.naming.DEFAULT_CACHE_NAME_TEMPLATE`, `spec.slugify`, `cache.copy.copy_if_absent`, `presign.object_name`, `presign.sessions_object_name`.
- `status.cache.migration`: `{state: "done"|"failed", from_key, workdir, sessions, finished_at, reason, failures, next_at}` (absent keys omitted). Contract change for `orch-session-status-cache` recorded by the orchestrator.
- Amended 2026-10-29 (interrogate Act on 3, 5): a sync predicate in `cache_migration` (for example `pending(session) -> bool`: eligible under the amended rule with no `done` record) needs no DB read, so `reconciler/cache.py` can call it. `CacheRunner._begin` does not pin `sessions_object` while it is true, and `_start` presigns the sessions target from the pinned `sessions_object` when set, else the legacy `<prefix>sessions/<slug>.tar.zst` while pending, else `sessions/<status.cache.key>` (pinning it). `presign.py` gains an entry point that presigns an exact object path (the builder's shape), so a per-target repoint (`object` and `sessions_object` independent) is honoured by both save steps.
- Amended 2026-10-29 (interrogate Act on 4): the migration reads `status.cache.save` and `status.cache.sessions_save` and returns without copying while either is `running`; in `_discard` the call stays before the workdir `save_step` and runs again before the sessions `save_step` until a record exists, so a finished save is copied after it.

#### Expected outcome

After deploy, each live session that existed before the epic has its `preset-<hash>.tar.zst` object copied to `<preset>-<slug>.tar.zst` (and any `sessions/<slug>.tar.zst` to `sessions/<preset>-<slug>.tar.zst`), its `status.cache` repointed and a `migration` record; its discard saves under the new names and a session recreated from the same preset with the same slug restores them. No S3 object is moved, deleted or overwritten.

#### Steps

- Read reconciler/loop.py (`_converge`, `_discard`, `_write_status`, `_reload`), reconciler/cache.py (`_begin`, `_start`, `save_step`, `_write`), cache/presign.py, cache/save_rule.py (`save_skip`), db/migrations/0002_presets.sql, cache/copy.py, cache/naming.py, db/presets.py, db/sessions.py (`Session` fields), settings.py (`retry_delay_seconds`), tests/test_cache_restore.py (`Env`) and tests/test_cache_save.py (`SaveEnv`) in one pass.
- Red: write tests/test_cache_migration.py with the tests named in the acceptance conditions (moto server for the bucket as in tests/test_cache_presign.py, the `Env` helpers for sessions and Jobs); run `uv run --frozen pytest -q -p no:cacheprovider tests/test_cache_migration.py`; expect failure on the missing module (DB tests: on CI or a local Postgres).
- Green: write cache_migration.py, wire it into loop.py, add the pending rule and the pinned `sessions_object` presign to reconciler/cache.py and presign.py; rerun the verify; expect passed, and the existing cache, presign and sessions suites unchanged.
- Document the migration and the `status.cache` fields in README `## Workspace cache`; add the MEMORY.md entry; `mise run lint`; expect exit 0.

#### Notes

- Live facts (cartographer brief section 4, read-only probe 2026-10-29): 3 live sessions (cct2, claude-code-tatara, mx-34); bucket objects `preset-00f3b4fa52bbda02.tar.zst` 8.5 KB, `preset-55ab25edd7a675ed.tar.zst` 434 MB, `preset-5aa1667ff178f9ae.tar.zst` 18 B, `smoke-workspace-cache.tar.zst`, 14 `sessions/smoke-*` objects; no transcripts object of a live session. Which live session holds which key is unknown (no DB read was made).
- Timing trap the repoint closes: a live session saves to `status.cache.key`; copying without repointing would leave the fresh save under the old name and a recreated session restoring a stale copy.
- The copy is a blocking server-side CopyObject inside the reconciler tick (the largest object today is 434 MB); it runs once per pre-epic session. Run it with `asyncio.to_thread` so the event loop stays free.
- Copy only (leader constraint): grep the diff for `delete_object`, `delete_objects` and `put_object`; AC3 proves it against moto.
- Headline promise end to end (retro, recurring): AC2 must exercise migrate, discard save, recreate and restore in one test, not separate pieces; AC15 and AC17 do the same for the failed-then-discarded and save-in-flight paths.
- Deploy order (design Constraints): this task and orch-transcripts-follow-name ship in one release; the epic lands as one close.
- Sizing (2026-10-29): points raised from 8 to 13 and expected minutes and tokens refilled from calibration by hand (`ticket.py` has no points update), because the interrogate amendments add the pending transcripts rule, the per-target repoint, the save-in-flight wait and the deleted-preset rule.
- Tree state (pictures baseline, 2026-10-28): `mise run lint` green; the full suite is red-env only. Tests that use the `pool`/`dsn` fixtures need Postgres through testcontainers, and agent pods have no Docker, so they error locally (`DockerException`) and run in CI on the PR: the reviewer reads the CI job for them and quotes its summary line. `tests/test_reconciler.py::test_lightkube_default_client_uses_env_config` fails in-cluster for an unrelated reason (KUBERNETES_SERVICE_HOST).
- If a verify run fails, save the failing test name and the output tail before any rerun (retro, markdown-rendering-in-chat).
- Per-task security check (retro, recurring): user input reaching S3 keys or a template engine is the high-risk surface here; check size bounds, refusal paths and that no credential or presigned query reaches a log, a status reason or an error message.
- Before working read the repo's AGENTS.md, MEMORY.md and ROADMAP.md. No em dashes. No backward-compatibility shims.

- 2026-10-29 amended: planner filled Interfaces, Expected outcome, Steps and Notes before the gate (retro: no empty Steps)

- 2026-10-29 amended: interrogate Act on 2-6 (/workdir/workdir/.scratchpad/s3-cache/interrogate.md): failed records eligible and retried at discard, legacy sessions/<slug> while pending, wait for a running save and copy after a finished one, per-target repoint gated by save_skip, deleted-preset rule; AC7 and AC9 changed, AC14-AC19 added; files (reconciler/cache.py, cache/presign.py), verify, points 8 to 13, Interfaces, Steps and Notes edited directly

### S8: web preset cache name field

- Status: todo
- Files: `src/sessions/sessionSpecForm.ts`, `src/presets/PresetForm.tsx`, `src/presets/PresetForm.test.tsx`, `src/api/schema.d.ts`, `openapi/orchestrator.json`, `openapi/orchestrator.source`
- Verify: `npm ci --no-audit --no-fund && npx vitest run src/presets/PresetForm.test.tsx && npm run check:api && npm run lint`
- Verified head: none

#### Requirement

User request (2026-10-29 04:52Z, mx-34 #343), verbatim: "I also want to decouple s3 cache from preset. There must be a way to define S3 backup name with jonja2 template with default as preset-sessionname. This must also copy caches of existing sessions, so after rotation everything will work properly." (jonja2 = Jinja2)

Leader constraint: the migration copies only, never moves or deletes S3 objects.

This task delivers design D12 (preset side) in agents-web.

- The preset form's cache field is labelled `Cache name template` and takes a Jinja2 template. Its placeholder is the orchestrator's default from `GET /api/v1/meta` `cache.default_name_template`; its helper text names the variables `preset`, `preset_id`, `session` and `created_by` and says that sessions whose names render the same share one cache (last save wins). Empty sends no `key` (the orchestrator renders the default).
- Client checks: at most 256 characters, nothing else; the orchestrator validates the template and its 422 message is shown under the field, as today. Removed: the client cache key regex (`CACHE_KEY`), the reserved `preset-` rule (`CACHE_KEY_RESERVED_PREFIX`, `cacheKeyError`'s stored-key parameter, `validate`'s `storedCacheKey`) and `PresetForm.tsx`'s copy rule that drops a `preset-` key: a copy keeps the source cache as it is.
- `openapi/orchestrator.json`, `openapi/orchestrator.source` and `src/api/schema.d.ts` are synced to the agents-orchestrator commit that adds `cache.default_name_template` (`npm run sync:api -- orchestrator`), and `npm run check:api` passes.

Tests no longer accurate, rewritten in src/presets/PresetForm.test.tsx because the field now takes a template under a new label and the reserved prefix is removed (design D6, D12): `saves an empty cache when enabled without a key`, `saves the cache key and excludes`, `rejects an invalid cache key`, `shows the server message for a reserved cache key`, `disables the cache section when the orchestrator has no cache`, `loads a stored cache`, `a copy drops a preset-derived cache key`.

#### Acceptance conditions

- AC1: the field is labelled Cache name template, shows the meta default_name_template as its placeholder, and an empty field saves `cache: {}` [evidence: command:npx vitest run src/presets/PresetForm.test.tsx -t "cache name template defaults to the orchestrator default"]
- AC2: a template such as `{{ preset }}-shared` is saved verbatim as cache.key [evidence: command:npx vitest run src/presets/PresetForm.test.tsx -t "saves a cache name template verbatim"]
- AC3: more than 256 characters blocks submit, while template syntax and names starting with `preset-` are not refused client side [evidence: command:npx vitest run src/presets/PresetForm.test.tsx -t "cache name template client checks"]
- AC4: the orchestrator's 422 message for an invalid template shows under the field [evidence: command:npx vitest run src/presets/PresetForm.test.tsx -t "shows the server message for an invalid cache name template"]
- AC5: a copy keeps the source cache, including a key starting with `preset-` [evidence: command:npx vitest run src/presets/PresetForm.test.tsx -t "a copy keeps the source cache"]
- AC6: the reserved prefix rule is gone from src [evidence: command:! grep -rnE "CACHE_KEY_RESERVED_PREFIX|reserved for preset-derived" src]
- AC7: the vendored orchestrator schema is in sync [evidence: command:npm run check:api]
- AC8: the whole PresetForm suite and lint pass [evidence: command:npx vitest run src/presets/PresetForm.test.tsx && npm run lint]

#### Files

- `src/sessions/sessionSpecForm.ts`
- `src/presets/PresetForm.tsx`
- `src/presets/PresetForm.test.tsx`
- `src/api/schema.d.ts`
- `openapi/orchestrator.json`
- `openapi/orchestrator.source`

#### Interfaces

- `src/sessions/sessionSpecForm.ts`: `FormValues.cacheKey` keeps its name (it now holds a template); `cacheKeyError(key: string): string | undefined` checks only the 256-character cap (`MAX_CACHE_NAME_TEMPLATE_CHARS = 256`); `validate(v, meta)` loses `storedCacheKey`; `CACHE_KEY` and `CACHE_KEY_RESERVED_PREFIX` removed; `toPresetSpec` still sends `cache: {}` for an empty field.
- `src/presets/PresetForm.tsx`: field label `Cache name template`, placeholder `meta.cache.default_name_template`, helper text naming the variables; the copy keeps `spec.cache` unchanged.
- `src/api/schema.d.ts`, `openapi/orchestrator.json`, `openapi/orchestrator.source`: synced by `npm run sync:api -- orchestrator` (`--from <agents-orchestrator checkout>` when the commit is only on the epic branch).

#### Expected outcome

Opening a preset with the cache on shows a `Cache name template` field whose placeholder is the orchestrator default; typing `{{ preset }}-shared` saves it verbatim; a template the orchestrator refuses shows its 422 message under the field; copying a preset keeps its cache settings.

#### Steps

- Read src/sessions/sessionSpecForm.ts (cache parts, `validate`, `toPresetSpec`, `stateFromPreset`), src/presets/PresetForm.tsx, src/presets/PresetForm.test.tsx (helpers `field`, `paste`, `replace`, `meta`, `preset`), scripts/sync-api.mjs and openapi/orchestrator.source in one pass.
- `npm ci --no-audit --no-fund`; then `npm run sync:api -- orchestrator --from <agents-orchestrator tree at the commit of orch-cache-name-on-create>`; expect the three vendored files to change and `npm run check:api` to exit 0.
- Red: rewrite the seven tests named in the Requirement and add the tests named in the acceptance conditions; run `npx vitest run src/presets/PresetForm.test.tsx`; expect the new tests to fail.
- Green: change sessionSpecForm.ts and PresetForm.tsx; rerun; expect all passed.
- `npm run lint`; expect exit 0.

#### Notes

- The client cannot render Jinja2; it checks only the length. The orchestrator validates and answers 422 `invalid_request` with the reason; the form already shows server messages under the field (see the existing reserved-key server test being rewritten).
- `openapi/orchestrator.source` pins `<repo> <sha40>`; the pinned commit must stay reachable after the orchestrator PR merges (retro, matrix-connector-agent-initi: merge that PR with a merge commit, or re-sync to the merged main commit before the web PR merges).
- Tree state (pictures baseline, 2026-10-28): `mise run lint` green; `npm test` had 6 test files failing to import `@codemirror/*` because node_modules was stale, so the verify runs `npm ci --no-audit --no-fund` first.
- If a verify run fails, save the failing test name and the output tail before any rerun (retro, recurring vitest load flake in PresetForm).
- Before working read the repo's AGENTS.md, MEMORY.md and ROADMAP.md. No em dashes. No backward-compatibility shims.

- 2026-10-29 amended: planner filled Interfaces, Expected outcome, Steps and Notes before the gate (retro: no empty Steps)

## Files to delete

none recorded in the epic format

## Final verify

none recorded in the epic format

## After merge

none
