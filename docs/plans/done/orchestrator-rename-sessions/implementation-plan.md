# orchestrator-rename-sessions implementation plan

## Agreed rung

Rung 1 of plan.md, migrated from the epic format: the steps are the epic's tasks.

## Approach

Migrated from the epic format: one step per task file, in dependency order, each with its status, files, verify, verified head and every body section.

## Chunk 1: migrated tasks (model: opus)

### S1: anymcp plugin session

- Status: done
- Files: `src/any_mcp/orchestrator.py`, `tests/test_orchestrator_plugin.py`, `tests/test_nomenclature.py`, `README.md`
- Verify: `uv run pytest -q tests/test_orchestrator_plugin.py tests/test_nomenclature.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: 5cd9044

#### Requirement

Rename the orchestrator plugin's unit from cluster to session (design D2, D11, D12; user decision: cluster is renamed session throughout; contract `orch-agent-api-session-header`). Paths are in code/any-mcp.

- `src/any_mcp/orchestrator.py`: the plugin Config field `cluster` becomes `session` (extra keys are already refused, so a config carrying `cluster` now fails validation; no alias); the request header `X-Orch-Session: <session>` replaces `X-Orch-Cluster`; every tool description and docstring says session ("the agents of the session", "Scale this session to a number of agents...", "the init scripts this session was initialised with", "applies to the next session created from the spec"); the docstring names agents-orchestrator.
- Error codes and fields passed through from the orchestrator follow design D2: `static_session` (was `static_cluster`), init scripts `applies: next_session` (was `next_cluster`).
- `tests/test_orchestrator_plugin.py`: the fixture config uses `session`; tests `test_session_header_sent` (the header `x-orch-session` carries the configured session, and no `x-orch-cluster` header is sent), `test_cluster_key_refused` (a config with `cluster` fails), and the existing code and `applies` assertions on the new values.
- `README.md`: the plugin's config fields and the example (`session: s-1`), "The token is scoped to one session", agents-orchestrator as the API's name.
- `tests/test_nomenclature.py` (new, written first): `git ls-files` over `src/any_mcp/orchestrator.py`, `tests/test_orchestrator_plugin.py` and `README.md` finds no line matching `/cluster/i` or `agent[-_]orchestrator`.
- CHANGELOG and the version belong to anymcp-release-v0-3-0.

#### Acceptance conditions

- AC1: the plugin sends X-Orch-Session with the configured session and never X-Orch-Cluster [evidence: test:tests/test_orchestrator_plugin.py::test_session_header_sent]
- AC2: a plugin config carrying the old cluster key is refused [evidence: test:tests/test_orchestrator_plugin.py::test_cluster_key_refused]
- AC3: the plugin source, its tests and the README no longer name the unit cluster or the old project name [evidence: command:uv run pytest -q tests/test_nomenclature.py]
- AC4: the plugin tests and lint pass [evidence: command:uv run pytest -q tests/test_orchestrator_plugin.py && uv run ruff check . && uv run ruff format --check .]

#### Files

- `src/any_mcp/orchestrator.py`
- `tests/test_orchestrator_plugin.py`
- `tests/test_nomenclature.py`
- `README.md`

#### Interfaces

- `any_mcp.orchestrator.OrchestratorPlugin` Config: `base_url, token, session, agent, slug, max_replicas, static, hive, ...` (extra keys refused); header `X-Orch-Session`. Must agree with orch-agent-api-sessions (contract `orch-agent-api-session-header`).

#### Expected outcome

The plugin addresses the orchestrator's session by key `session` and header `X-Orch-Session`; `cluster` is refused.

#### Steps

- Red: write `tests/test_nomenclature.py` and the two new plugin tests; `uv run pytest -q tests/test_orchestrator_plugin.py tests/test_nomenclature.py` fails on the old key, header and texts.
- Green: rename in `orchestrator.py` and README; the verify passes, lint clean.

#### Notes

- design.md D2 is the vocabulary; error codes come from the orchestrator (`static_session`).
- Do not touch CHANGELOG or the version (anymcp-release-v0-3-0).

- 2026-10-25 done

### S2: common client sessions

- Status: done
- Files: `src/agents_common/orchestrator.py`, `src/agents_common/fake_orchestrator.py`, `src/agents_common/runs.py`, `README.md`, `tests/`
- Verify: `uv run pytest -q tests/test_orchestrator_client.py tests/test_runs.py tests/test_reuse.py tests/test_nomenclature.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: a7b12ed

#### Requirement

Rename the orchestrator client, its fake and the run tracker from cluster to session (design D2, D12; user decision: cluster is renamed session throughout; contract `orch-sessions-api` as consumer, supersedes `preset-mapping-model`'s RunRef.cluster_id). Paths are in code/agents-common.

- `src/agents_common/orchestrator.py`: model `Session` (was `Cluster`), `create_session(preset_id, slug)` (idempotent on slug as today), `get_session(session_id)`, `list_messages(session_id)`, `post_message(session_id, text)`; routes `/api/v1/sessions`, `/api/v1/sessions/{id}`, `/api/v1/sessions/{id}/messages`; message model field `session_id`; error code `session_deleting`; every docstring says session and agents-orchestrator.
- `src/agents_common/fake_orchestrator.py`: serves the same `/api/v1/sessions` routes; `sessions` store, `discard_session(session_id)`, `remove_session(session_id)`, route labels `list_sessions`/`create_session`/`get_session`; messages carry `session_id`; 409 `session_deleting`.
- `src/agents_common/runs.py`: `RunRef.session_id`, `RunStore.set_session`, `running_session(client, session_id)`, failure reason `session_not_found`; every docstring.
- `README.md`: public names and examples on the new names.
- tests/: `test_orchestrator_client.py`, `test_runs.py`, `test_reuse.py` follow the rename; tests first: `tests/test_orchestrator_client.py::test_session_routes` (the client calls `/api/v1/sessions...` against the fake and never `/clusters`), `tests/test_runs.py::test_missing_session_fails_run` (reason `session_not_found`); new `tests/test_nomenclature.py` (D12) guarding every tracked file except the dated-history files.
- Version and tag belong to common-release-v0-3-0. No alias names.

#### Acceptance conditions

- AC1: the client and the fake use /api/v1/sessions routes only [evidence: test:tests/test_orchestrator_client.py::test_session_routes]
- AC2: a missing session fails the run with session_not_found [evidence: test:tests/test_runs.py::test_missing_session_fails_run]
- AC3: no tracked file names the unit cluster or the project agent-orchestrator outside dated history [evidence: command:uv run pytest -q tests/test_nomenclature.py]
- AC4: the touched suites and lint pass [evidence: command:uv run pytest -q tests/test_orchestrator_client.py tests/test_runs.py tests/test_reuse.py && uv run ruff check . && uv run ruff format --check .]

#### Files

- `src/agents_common/orchestrator.py`
- `src/agents_common/fake_orchestrator.py`
- `src/agents_common/runs.py`
- `README.md`
- `tests/`

#### Interfaces

- `OrchestratorClient.create_session/get_session/list_messages/post_message`, `Session`; fake `discard_session/remove_session`; `RunRef.session_id`, `RunStore.set_session`, `running_session`, reason `session_not_found` (consumes `orch-sessions-api`; supersedes `preset-mapping-model`'s RunRef.cluster_id for agents-schedule-microservice).

#### Expected outcome

agents-common speaks only the session API; its guard passes.

#### Steps

- Red: write `test_session_routes`, `test_missing_session_fails_run` and `tests/test_nomenclature.py`; run them: they fail.
- Green: rename client, fake, tracker, README and the touched tests; the verify passes.

#### Notes

- Routes and codes follow design.md D2 exactly; the fake must not answer `/clusters`.

- 2026-10-25 done

### S3: helmfile orch db import

- Status: done
- Files: `helmfile.yaml.gotmpl`, `values/agents-orchestrator-db/common.yaml`, `values/agents-orchestrator-db/default.secrets.yaml`, `tests/test_db_release.py`
- Verify: `uv run pytest -q tests/test_db_release.py && mise run lint`
- Verified head: c1f72b5

#### Requirement

Declare the new orchestrator database release, imported from the old one (design D1, D5; gate Q2; contract `agents-orchestrator-db-release`). Paths are in code/agents-helmfile. The old release `agent-orchestrator-db` and its values stay exactly as they are.

- `helmfile.yaml.gotmpl`: release `agents-orchestrator-db` (chart `cnpg/cluster` 0.9.0, namespace `agents`, `force: false`, timeout 600, labels `purpose: agents`, `application: agents-orchestrator`, the default template).
- `values/agents-orchestrator-db/common.yaml`: same shape as the old db values (postgresql 16, 1 instance, storage 5Gi and WAL 2Gi on rook-ceph, resources, monitoring off) plus `mode: recovery`, `recovery.method: import`, `recovery.database: agents_orchestrator`, `recovery.owner: agents_orchestrator`, `recovery.import.type: microservice`, `recovery.import.databases: [agent_orchestrator]`, `recovery.import.source` host `agent-orchestrator-db-cluster-rw`, port 5432, username `agent_orchestrator`, database `agent_orchestrator`, `sslMode: verify-full`, `passwordSecret` name `agent-orchestrator-db-cluster-app` key `password` (create false), `sslRootCertSecret` name `agent-orchestrator-db-cluster-ca` key `ca.crt`; backups enabled with S3 path `/agents-orchestrator-db/` (same bucket, region, 30d retention, daily 03:00 scheduled backup, `backupOwnerReference: self`). The builder checks every key against `helm show values cnpg/cluster --version 0.9.0` and `helmfile -l name=agents-orchestrator-db template`, and names any key that differs from this list in the task notes.
- `values/agents-orchestrator-db/default.secrets.yaml`: the S3 backup credentials, encrypted with the repo's SOPS rules through the workbench-secrets secret helper skill (never decrypted to the transcript, never committed in plain text); the values are the old db release's backup keys.
- `tests/test_db_release.py` (test first): tests for `agents-orchestrator-db` (`test_new_release_chart_and_labels`, `test_import_from_old_cluster`, `test_new_backups_own_path`, `test_new_db_secrets_encrypted`) next to the unchanged tests of the old release; the hook tests stay.

#### Acceptance conditions

- AC1: the new release imports database agent_orchestrator from the old cluster into agents_orchestrator over verified TLS [evidence: test:tests/test_db_release.py::test_import_from_old_cluster]
- AC2: the new database backs up to its own S3 path [evidence: test:tests/test_db_release.py::test_new_backups_own_path]
- AC3: the new secrets file is encrypted and the old release is unchanged [evidence: command:uv run pytest -q tests/test_db_release.py]
- AC4: the release renders with the cnpg chart [evidence: judgement:the task notes quote helmfile -l name=agents-orchestrator-db template showing spec.bootstrap.initdb.import and externalClusters]
- AC5: lint passes [evidence: command:mise run lint]

#### Files

- `helmfile.yaml.gotmpl`
- `values/agents-orchestrator-db/common.yaml`
- `values/agents-orchestrator-db/default.secrets.yaml`
- `tests/test_db_release.py`

#### Interfaces

- Release `agents-orchestrator-db`; CNPG Cluster `agents-orchestrator-db-cluster`; its app Secret `agents-orchestrator-db-cluster-app` (key `uri`) is what helmfile-orch-release-rename wires (contract `agents-orchestrator-db-release`).

#### Expected outcome

The new database release is declared as an import of the old one; nothing about the old release changes; nothing is applied here.

#### Steps

- Red: write the four new tests in `tests/test_db_release.py`; `uv run pytest -q tests/test_db_release.py` fails.
- Green: add the release, the values and the encrypted secrets file; run `helmfile -f helmfile.yaml.gotmpl -l name=agents-orchestrator-db template` and quote the bootstrap and externalClusters part; the verify passes.

#### Notes

- Never apply: deploy-cutover runs the import after the old app is uninstalled (design D7).
- Encrypted files go through the workbench-secrets secret helper skill, never a raw decrypt to the transcript.

- 2026-10-25 done

### S4: orch package rename

- Status: done
- Files: `pyproject.toml`, `uv.lock`, `src/`, `tests/`, `Dockerfile`, `.dockerignore`, `openapi.json`
- Verify: `uv run pytest -q && uv run ruff check . && uv run ruff format --check .`
- Verified head: 8ec5071

#### Requirement

Rename the Python project from agent-orchestrator to agents-orchestrator (design D1, D10; user decision: agent-orchestrator becomes agents-orchestrator for consistency). Paths are in code/agents-orchestrator (the submodule after orchestrator step O2; the GitHub repo is szymonrychu/agents-orchestrator).

- `pyproject.toml`: `name = "agents-orchestrator"`, packages `src/agents_orchestrator`, console script `orch = "agents_orchestrator.cli:main"` (the `orch` name stays, D10); `uv.lock` refreshed with `uv lock`.
- `git mv src/agent_orchestrator src/agents_orchestrator`; every import, module path and string `agent_orchestrator` in src/ and tests/ becomes `agents_orchestrator`.
- The hyphenated name inside src/: `k8s/labels.py` `MANAGED_BY = "agents-orchestrator"`; `settings.py` default `claude_secret_name = "agents-orchestrator-claude"`; any other default, log line or docstring in src/ naming agent-orchestrator.
- `Dockerfile` and `.dockerignore`: package paths.
- `openapi.json`: regenerated with `uv run python -m agents_orchestrator.api.openapi > openapi.json` (never hand-edited).
- `tests/test_project_name.py` (new, written first): `git ls-files src/agent_orchestrator` prints nothing (retirement); the pyproject name is agents-orchestrator; `git grep -n -E 'agent[-_]orchestrator'` over `src/`, `pyproject.toml`, `Dockerfile` and `openapi.json` finds nothing.
- Out of this task: the chart directory, CI, mise, scripts and e2e (orch-chart-ci-rename) and the docs (orch-docs-e2e-sessions). Only names change; the cluster vocabulary is later tasks' work.

#### Acceptance conditions

- AC1: the old package path is gone from git [evidence: test:tests/test_project_name.py::test_old_package_retired]
- AC2: the distribution, package, managed-by label value and default Secret names say agents-orchestrator [evidence: test:tests/test_project_name.py::test_package_named_agents_orchestrator]
- AC3: the committed openapi.json matches the app [evidence: test:tests/test_readme_api.py::test_openapi_json_matches_app]
- AC4: the component suite and lint pass [evidence: command:uv run pytest -q && uv run ruff check . && uv run ruff format --check .]

#### Files

- `pyproject.toml`
- `uv.lock`
- `src/`
- `tests/`
- `Dockerfile`
- `.dockerignore`
- `openapi.json`

#### Interfaces

- Distribution `agents-orchestrator`, import package `agents_orchestrator`, console script `orch`; `k8s.labels.MANAGED_BY == "agents-orchestrator"`; `Settings.claude_secret_name` default `agents-orchestrator-claude`.

#### Expected outcome

The repo builds and tests as agents-orchestrator; `src/agent_orchestrator` no longer exists in git.

#### Steps

- Red: write `tests/test_project_name.py` (`test_old_package_retired`, `test_package_named_agents_orchestrator`); `uv run pytest -q tests/test_project_name.py` fails.
- Green: `git mv src/agent_orchestrator src/agents_orchestrator`, rewrite imports and names in src/ and tests/, pyproject, `uv lock`, Dockerfile, `.dockerignore`, regenerate openapi.json; `uv run pytest -q` passes, lint clean.

#### Notes

- Runs after orchestrator step O2 (submodule at code/agents-orchestrator, GitHub repo renamed).
- Leave `chart/agent-orchestrator` paths in tests/ (helm_render.py, chart tests) to orch-chart-ci-rename; this task renames only the underscore form everywhere and the hyphen form inside src/.
- Retirement check is `git ls-files`, never the filesystem.

- 2026-10-25 done

### S5: webhook session columns

- Status: done
- Files: `src/agents_webhook/migrations/0005_sessions.sql`, `src/agents_webhook/db/events.py`, `src/agents_webhook/api/schemas.py`, `src/agents_webhook/worker.py`, `openapi.json`, `README.md`, `tests/`
- Verify: `uv run pytest -q tests/test_event_store.py tests/test_api.py tests/test_worker.py tests/test_worker_reuse.py tests/test_readme_api.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: 7c630a9

#### Requirement

Rename the webhook run's cluster columns and API fields to session (design D2, D4, D14; user decision: cluster is renamed session throughout; contract `webhook-events-session-fields`). Paths are in code/agents-webhook. Starts from main after webhook-event-filters merged (gate Q6), whose migration is 0004.

- New `src/agents_webhook/migrations/0005_sessions.sql`: `events.cluster_id` to `session_id`, `events.cluster_slug` to `session_slug`, every index or constraint naming them renamed to match; `ALTER ... RENAME` only, no row changed.
- `src/agents_webhook/db/events.py`: every SQL string, the row model fields `session_id`/`session_slug`, `set_session(run_id, session_id, *, slug=None)` (was `set_cluster`), docstrings and comments.
- `src/agents_webhook/api/schemas.py`: `EventView` and `EventDetail` fields `session_id`, `session_slug`; `openapi.json` regenerated with the repo's export (the README/openapi test names the command).
- `src/agents_webhook/worker.py`: reads the renamed row fields; it still hands them to agents-common v0.2.0 (`RunRef(cluster_id=event.session_id)`) until webhook-worker-sessions pins v0.3.0.
- `README.md`: the event fields in the API reference.
- tests/: `test_event_store.py`, `test_api.py`, `test_worker.py`, `test_worker_reuse.py` and `tests/e2e/` follow the renamed fields; tests first: `tests/test_event_store.py::test_0005_renames_cluster_columns` (seed a row with cluster_id and cluster_slug at 0004, migrate, read them back as session_id and session_slug; no column named cluster remains) and `tests/test_api.py::test_event_view_session_fields`.

#### Acceptance conditions

- AC1: migration 0005 keeps every row and leaves no events column named cluster [evidence: test:tests/test_event_store.py::test_0005_renames_cluster_columns]
- AC2: the events API serves session_id and session_slug [evidence: test:tests/test_api.py::test_event_view_session_fields]
- AC3: openapi.json and the README match the app [evidence: command:uv run pytest -q tests/test_readme_api.py]
- AC4: the touched suites and lint pass [evidence: command:uv run pytest -q tests/test_event_store.py tests/test_api.py tests/test_worker.py tests/test_worker_reuse.py && uv run ruff check . && uv run ruff format --check .]

#### Files

- `src/agents_webhook/migrations/0005_sessions.sql`
- `src/agents_webhook/db/events.py`
- `src/agents_webhook/api/schemas.py`
- `src/agents_webhook/worker.py`
- `openapi.json`
- `README.md`
- `tests/`

#### Interfaces

- `events.session_id`, `events.session_slug`; `EventView`/`EventDetail` fields `session_id`, `session_slug` (contract `webhook-events-session-fields`, consumed by web-webhooks-session-fields).

#### Expected outcome

Webhook runs store and serve their session; migration 0005 keeps every row.

#### Steps

- Red: write `test_0005_renames_cluster_columns` and `test_event_view_session_fields`; run them: they fail.
- Green: 0005, events store, schemas, worker field reads, openapi.json, README fields; the verify passes.

#### Notes

- 0004 belongs to webhook-event-filters (merged first, the epic's blocker); never renumber it.
- The worker still calls agents-common v0.2.0 here; keep its call shapes.

- 2026-10-25 done

### S6: anymcp release v0.3.0

- Status: done
- Files: `pyproject.toml`, `uv.lock`, `CHANGELOG.md`, `README.md`, `tests/test_release.py`
- Verify: `uv run pytest -q tests/test_release.py -k "versions_agree or pinned_install_line" && uv run ruff check . && uv run ruff format --check .`
- Verified head: 53b7a66

#### Requirement

Release any-mcp v0.3.0 carrying the session plugin (design D11; contract `any-mcp-release-v0-3-0`). Paths are in code/any-mcp.

- `pyproject.toml`: `version = "0.3.0"`; `uv.lock` refreshed with `uv lock`.
- `CHANGELOG.md`: `## v0.3.0` on top, a Breaking entry: the orchestrator plugin's config key `cluster` is now `session`, the header is `X-Orch-Session`, codes `static_session` and `next_session`; requires agents-orchestrator with the session agent API.
- `README.md` and `tests/test_release.py`: every pinned install line names `@v0.3.0` (`PINNED_LINE` included); `test_versions_agree` and `test_pinned_install_line_documented` pass on 0.3.0.
- Release step, run by the orchestrator (main session) once this epic's any-mcp PR is merged to main: push tag `v0.3.0` on the merge commit (irreversible, listed in design.md), confirm the tag's CI is green and `uv pip install "any-mcp @ git+https://github.com/szymonrychu/any-mcp@v0.3.0"` installs in a fresh venv. Until then orch-agent-api-sessions stays blocked.

#### Acceptance conditions

- AC1: pyproject, package metadata and the CHANGELOG top entry agree on 0.3.0 [evidence: test:tests/test_release.py::test_versions_agree]
- AC2: the README documents the v0.3.0 pinned install line [evidence: test:tests/test_release.py::test_pinned_install_line_documented]
- AC3: tag v0.3.0 exists on origin on the main merge commit and installs [evidence: judgement:the task notes quote git ls-remote --tags origin v0.3.0 and the install output]
- AC4: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

#### Files

- `pyproject.toml`
- `uv.lock`
- `CHANGELOG.md`
- `README.md`
- `tests/test_release.py`

#### Interfaces

- Tag `v0.3.0` (contract `any-mcp-release-v0-3-0`): `any-mcp @ git+https://github.com/szymonrychu/any-mcp@v0.3.0`.

#### Expected outcome

any-mcp 0.3.0 is documented, versioned and, after the orchestrator's release step, tagged on origin.

#### Steps

- Red: set the expected version and `PINNED_LINE` in `tests/test_release.py` to 0.3.0; `uv run pytest -q tests/test_release.py -k "versions_agree or pinned_install_line"` fails.
- Green: bump pyproject, `uv lock`, CHANGELOG and README; the verify passes.
- End the round "ready for tag": the orchestrator tags after the PR merges and pastes the `git ls-remote` line into the notes.

#### Notes

- Tags are never re-pointed; a wrong tag means v0.3.1.

- 2026-10-25 done

### S7: common release v0.3.0

- Status: done
- Files: `pyproject.toml`, `uv.lock`, `CHANGELOG.md`, `README.md`, `tests/test_release.py`
- Verify: `uv run pytest -q tests/test_release.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: 931b1de

#### Requirement

Release agents-common v0.3.0 with the session client (design D11; contract `agents-common-release-v0-3-0`). Paths are in code/agents-common.

- `pyproject.toml` `version = "0.3.0"`; `uv.lock` refreshed.
- `CHANGELOG.md`: `## v0.3.0` on top, Breaking: `Cluster` is `Session`, `create_cluster`/`get_cluster`/`running_cluster`/`set_cluster`/`discard_cluster`/`remove_cluster` are `create_session`/`get_session`/`running_session`/`set_session`/`discard_session`/`remove_session`, `RunRef.session_id`, reason `session_not_found`, routes `/api/v1/sessions` (needs agents-orchestrator with the session API).
- `README.md` install line `agents-common @ git+https://github.com/szymonrychu/agents-common@v0.3.0`; `tests/test_release.py` `INSTALL` and the expected version 0.3.0.
- Release step, run by the orchestrator once this epic's agents-common PR is merged to main: push tag `v0.3.0` on the merge commit (irreversible, listed in design.md), confirm the tag's CI and `uv pip install "agents-common @ git+https://github.com/szymonrychu/agents-common@v0.3.0"` in a fresh venv. Until then webhook-worker-sessions stays blocked.

#### Acceptance conditions

- AC1: version, CHANGELOG, README install line and package metadata agree on 0.3.0 [evidence: test:tests/test_release.py::test_versions_agree]
- AC2: tag v0.3.0 exists on origin on the main merge commit and installs [evidence: judgement:the task notes quote git ls-remote --tags origin v0.3.0 and the install output]
- AC3: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

#### Files

- `pyproject.toml`
- `uv.lock`
- `CHANGELOG.md`
- `README.md`
- `tests/test_release.py`

#### Interfaces

- Tag `v0.3.0` (contract `agents-common-release-v0-3-0`).

#### Expected outcome

agents-common 0.3.0 is documented, versioned and, after the release step, tagged on origin.

#### Steps

- Red: set `INSTALL` and the expected version in `tests/test_release.py` to 0.3.0; it fails.
- Green: bump, `uv lock`, CHANGELOG, README; the verify passes. End "ready for tag".

#### Notes

- Tags are never re-pointed.

- 2026-10-25 done

### S8: orch chart ci rename

- Status: done
- Files: `chart/`, `.github/workflows/ci.yaml`, `mise.toml`, `scripts/`, `e2e/`, `tests/`
- Verify: `uv run pytest -q tests/test_project_name.py tests/test_chart_ci.py tests/test_chart_config.py tests/test_chart_deployments.py tests/test_chart_rbac_ingress.py tests/test_chart_scaffold.py tests/test_chart_services_port.py && mise run lint:chart && uv run ruff check . && uv run ruff format --check .`
- Verified head: b6e79b8

#### Requirement

Rename the chart, the image and the CI from agent-orchestrator to agents-orchestrator (design D1, D11; contract `agents-orchestrator-chart` / `-image`). Paths are in code/agents-orchestrator.

- `git mv chart/agent-orchestrator chart/agents-orchestrator`; `Chart.yaml` `name: agents-orchestrator`; every helper define `agent-orchestrator.*` becomes `agents-orchestrator.*` with every `include`, every `fail` message, NOTES.txt and `ci/lint-values.yaml`.
- `.github/workflows/ci.yaml`: image `harbor.szymonrichert.pl/containers/agents-orchestrator`, local tags `agents-orchestrator:ci`, `helm package chart/agents-orchestrator`, `helm push "agents-orchestrator-$VERSION.tgz"`, the published-version check `"$CHART_REPO/agents-orchestrator"` and every message naming the chart (OCI `oci://harbor.szymonrichert.pl/charts/agents-orchestrator`).
- `mise.toml`: `lint:chart` path, test image `agents-orchestrator-agent-test:e2e`; `scripts/chart-version.sh`; `scripts/e2e.sh` (release `agents-orchestrator`, images `agents-orchestrator:e2e` and `agents-orchestrator-agent-test:e2e`, the kind cluster name `agents-orchestrator-e2e`, the managed-by selector `app.kubernetes.io/managed-by=agents-orchestrator`); `e2e/` values and manifests.
- tests/: `tests/helm_render.py` and the chart tests use `chart/agents-orchestrator`; `tests/test_project_name.py` gains `test_old_chart_retired` (`git ls-files chart/agent-orchestrator` prints nothing) and `test_chart_and_ci_named` (Chart.yaml name, the CI image and chart names, and `git grep -n -E 'agent[-_]orchestrator'` over `chart/`, `.github/`, `mise.toml`, `scripts/`, `e2e/` and `tests/` finds nothing outside `tests/test_project_name.py` itself).
- No other behaviour change. Harbor creates the new repositories on the first push from main (D11).

#### Acceptance conditions

- AC1: the old chart directory is gone from git [evidence: test:tests/test_project_name.py::test_old_chart_retired]
- AC2: chart, image, CI, mise, scripts and e2e carry the new name only [evidence: test:tests/test_project_name.py::test_chart_and_ci_named]
- AC3: the chart renders and lints under the new name [evidence: command:uv run pytest -q tests/test_chart_ci.py tests/test_chart_config.py tests/test_chart_deployments.py tests/test_chart_rbac_ingress.py tests/test_chart_scaffold.py tests/test_chart_services_port.py && mise run lint:chart]
- AC4: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

#### Files

- `chart/`
- `.github/workflows/ci.yaml`
- `mise.toml`
- `scripts/`
- `e2e/`
- `tests/`

#### Interfaces

- Chart `chart/agents-orchestrator`, name `agents-orchestrator`, defines `agents-orchestrator.*` (fullname drives every Service, Secret and Deployment name); OCI `oci://harbor.szymonrichert.pl/charts/agents-orchestrator`; image `harbor.szymonrichert.pl/containers/agents-orchestrator:<sha7>` (contracts `agents-orchestrator-chart`, `-image`).

#### Expected outcome

Main CI publishes the chart and image under the new names; the chart renders and lints.

#### Steps

- Red: add `test_old_chart_retired` and `test_chart_and_ci_named` to `tests/test_project_name.py`; they fail.
- Green: `git mv` the chart, rename defines and includes, CI, mise, scripts, e2e, tests' chart paths; the verify passes.

#### Notes

- The CI's published-version check and image digest check must name the new repositories, or the first main build fails.
- `CLUSTER=` in scripts/e2e.sh is the kind cluster's name: keep the variable, change only its value.

- 2026-10-25 done

### S9: orch wrapper session id

- Status: done
- Files: `src/agents_orchestrator/db/migrations/0004_wrapper_session_id.sql`, `src/agents_orchestrator/`, `tests/`, `openapi.json`, `README.md`
- Verify: `uv run pytest -q tests/test_migrations.py tests/test_events_store.py tests/test_api_streams.py tests/test_ingester.py tests/test_wrapper_session_bootstrap.py tests/test_workspace_proxy.py tests/test_readme_api.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: 59d20d6

#### Requirement

The claude-code-wrapper's session id becomes `wrapper_session_id` in the orchestrator (design D3, D4; gate Q7), so "session" is free for the orchestrator's unit. Paths are in code/agents-orchestrator.

- New `src/agents_orchestrator/db/migrations/0004_wrapper_session_id.sql`: `agents.session_id` to `wrapper_session_id`, `agents.session_created_at` to `wrapper_session_created_at`, `events.session_id` to `wrapper_session_id`; the events unique constraint over `(agent_id, session_id, seq)` and any other index or constraint naming the wrapper session renamed to match. `ALTER ... RENAME` only: no row is dropped or rewritten. 0001-0003 stay byte-identical (the runner tracks versions).
- Every SQL string, row key and attribute for these columns in src/ (db/agents.py, db/events.py, ingester/loop.py, reconciler/, dispatcher/verify.py, api/workspace.py, api/streams.py and any other the builder finds with `git grep -n session_id`) uses the new names; `reconciler/sessions.py` becomes `reconciler/wrapper_sessions.py` (`git mv`) with its importers, and `tests/test_session_bootstrap.py` becomes `tests/test_wrapper_session_bootstrap.py`.
- API: `EventView.session_id` becomes `wrapper_session_id`; `openapi.json` regenerated with `uv run python -m agents_orchestrator.api.openapi > openapi.json`; README's event fields and SSE payload docs updated.
- The `wrapper/` client keeps the wrapper's own `/v1/sessions` vocabulary (its URL paths and method names mirror the wrapper API).
- Tests first: `tests/test_migrations.py::test_0004_renames_wrapper_session_columns` (apply 0001-0003 to an empty DB from a tmp migrations dir, insert a cluster, an agent with a session id and an event, run the full migrations, read the same values from the `wrapper_session_*` columns; `information_schema.columns` lists no `session_id` or `session_created_at` on agents or events); `tests/test_api_streams.py::test_event_view_wrapper_session_id` (an event row is served with `wrapper_session_id` and without `session_id`).

#### Acceptance conditions

- AC1: migration 0004 keeps every row and renames the wrapper session columns, indexes and constraints [evidence: test:tests/test_migrations.py::test_0004_renames_wrapper_session_columns]
- AC2: the events API serves wrapper_session_id and no session_id [evidence: test:tests/test_api_streams.py::test_event_view_wrapper_session_id]
- AC3: no src file outside the wrapper client and migrations 0001-0003 uses a bare session_id or session_created_at [evidence: command:! git grep -n -E '\bsession_(id|created_at)\b' -- src/agents_orchestrator ':!src/agents_orchestrator/wrapper' ':!src/agents_orchestrator/db/migrations/0001_init.sql' ':!src/agents_orchestrator/db/migrations/0002_presets.sql' ':!src/agents_orchestrator/db/migrations/0003_hive.sql']
- AC4: openapi.json and README match the app [evidence: command:uv run pytest -q tests/test_readme_api.py]
- AC5: the touched suites and lint pass [evidence: command:uv run pytest -q tests/test_migrations.py tests/test_events_store.py tests/test_api_streams.py tests/test_ingester.py tests/test_wrapper_session_bootstrap.py tests/test_workspace_proxy.py && uv run ruff check . && uv run ruff format --check .]

#### Files

- `src/agents_orchestrator/db/migrations/0004_wrapper_session_id.sql`
- `src/agents_orchestrator/`
- `tests/`
- `openapi.json`
- `README.md`

#### Interfaces

- Columns `agents.wrapper_session_id`, `agents.wrapper_session_created_at`, `events.wrapper_session_id`; `EventView.wrapper_session_id`; module `reconciler/wrapper_sessions.py`.

#### Expected outcome

The orchestrator never uses a bare `session_id` for the wrapper's session; migration 0004 keeps every row.

#### Steps

- Red: write `test_0004_renames_wrapper_session_columns` and `test_event_view_wrapper_session_id`; run them: they fail (no 0004, field missing).
- Green: write 0004, rename SQL, row keys, attributes, the module and EventView, regenerate openapi.json, update README; the verify passes.

#### Notes

- Reuse the tmp-migrations-dir pattern of `test_presets_migration_on_existing_clusters` in tests/test_migrations.py.
- The live database gets 0004 only on the imported copy (design D5); the old database is never migrated.

- 2026-10-25 done

### S10: webhook worker sessions

- Status: done
- Files: `pyproject.toml`, `uv.lock`, `src/agents_webhook/worker.py`, `README.md`, `tests/`
- Verify: `uv run pytest -q tests/test_worker.py tests/test_worker_reuse.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: 58b0a18

#### Requirement

Move agents-webhook onto agents-common v0.3.0 and the session vocabulary in the worker (design D2, D11; contract `agents-common-release-v0-3-0`). Paths are in code/agents-webhook.

- `pyproject.toml`: both `agents-common @ git+https://github.com/szymonrychu/agents-common@v0.3.0` lines (runtime and `[testing]`); `uv.lock` refreshed.
- `src/agents_webhook/worker.py`: `create_session`, `running_session`, `RunRef(session_id=...)`, `set_session`; every log line, docstring and comment says session ("the run's session", "falls back once to a new session `wh-<id>`"); failure reason `session_not_found`.
- `README.md`: the worker behaviour and the failure reasons table (`session_not_found`), session for the unit.
- tests/: `test_worker.py`, `test_worker_reuse.py`, `tests/e2e/` on the v0.3.0 fake orchestrator (`discard_session`, `remove_session`, `/api/v1/sessions`); tests first: `tests/test_worker_reuse.py::test_gone_session_falls_back_to_new_session` and `tests/test_worker.py::test_missing_session_reason`.
- Confirm by reading worker.py that `OrchestratorUnavailable` leaves the row queued for a retry (design Assumptions, needed for the cutover window); when no test pins it, add `tests/test_worker.py::test_orchestrator_unavailable_retries`.


Orchestrator ruling 2026-10-25 (review of webhook-session-columns): task webhook-session-columns added a temporary `_RunStore` adapter in worker.py (its `set_cluster` forwards to `EventStore.set_session`) and a `RunRef(cluster_id=event.session_id)` shim, because agents-common v0.2.0 still names clusters. With agents-common v0.3.0 pinned, delete `_RunStore`, make `_FallbackStore` a direct store wrapper over `set_session` that keeps the `reuse_fallback` prefix, and drop the shim; no adapter or cluster-named call remains.

#### Acceptance conditions

- AC1: a gone session falls back once to a new session [evidence: test:tests/test_worker_reuse.py::test_gone_session_falls_back_to_new_session]
- AC2: a missing session fails the event with session_not_found [evidence: test:tests/test_worker.py::test_missing_session_reason]
- AC3: an unreachable orchestrator leaves the event for a retry [evidence: judgement:the task notes name the test that pins OrchestratorUnavailable retry, existing or added]
- AC4: the worker suites and lint pass on agents-common v0.3.0 [evidence: command:uv run pytest -q tests/test_worker.py tests/test_worker_reuse.py && uv run ruff check . && uv run ruff format --check .]
- AC-adapter: the temporary _RunStore adapter and the RunRef shim are gone [evidence: command:! grep -nE "_RunStore|cluster_id=" src/agents_webhook/worker.py]

#### Files

- `pyproject.toml`
- `uv.lock`
- `src/agents_webhook/worker.py`
- `README.md`
- `tests/`

#### Interfaces

- Consumes agents-common v0.3.0 (`create_session`, `running_session`, `RunRef.session_id`, `set_session`).

#### Expected outcome

The worker creates, reuses and falls back on sessions through agents-common v0.3.0.

#### Steps

- Precondition: tag agents-common v0.3.0 exists; else end `blocked`, whoCanClear "orchestrator: tag agents-common v0.3.0".
- Red: bump both pins, `uv lock`, write the two named tests; run them: they fail.
- Green: rename the worker calls, logs and README reasons; the verify passes.

#### Notes

- Read worker.py for the `OrchestratorUnavailable` path and record in the notes which test pins the retry (design Assumptions).

- 2026-10-25 amended: review of webhook-session-columns: remove the temporary _RunStore adapter

- 2026-10-25 done: AC3 pinned by tests/test_worker.py::test_failed_create_unavailable_leaves_the_row_in_progress and ::test_failed_orchestrator_down_leaves_rows_then_recovers

### S11: orch sessions sweep

- Status: done
- Files: `src/agents_orchestrator/db/migrations/0005_sessions.sql`, `src/agents_orchestrator/`, `tests/`, `openapi.json`, `README.md`, `examples/bench.yaml`
- Verify: `uv run pytest -q && uv run ruff check . && uv run ruff format --check .`
- Verified head: 0079f7c

#### Requirement

Rename the orchestrator's unit from cluster to session in the database, the Python code, the public HTTP API and the Kubernetes label, in one atomic sweep (design D2, D4, D8, D15; user decision: cluster is renamed session throughout (API, UI, docs); gate Q1; contract `orch-sessions-api`). Paths are in code/agents-orchestrator. Apply the design D2 table exactly; no alias, no old route, no compatibility view.

- Database: new `src/agents_orchestrator/db/migrations/0005_sessions.sql`: table `clusters` to `sessions`, `cluster_leaders` to `session_leaders`; column `cluster_id` to `session_id` in every table that has it (agents, messages, events, checks, leadership_requests, session_leaders, file_locks and any other `\d` shows); every index, primary key, unique, foreign-key and check constraint whose name contains `cluster` renamed to the matching `session` name (for example `messages_cluster_status_id` to `messages_session_status_id`, `events_cluster_id_desc` to `events_session_id_desc`). `ALTER ... RENAME` only. 0001-0004 stay byte-identical. NOTIFY channel `cluster_changed` becomes `session_changed`.
- Python: every identifier, module, docstring, comment and log line naming the unit: `db/clusters.py` to `db/sessions.py` (`git mv`; `Cluster`, `ClusterExists`, `ClusterNotFound`, `ClusterBeingDeleted` to `Session...`), `spec.ClusterSpec` to `SessionSpec`, `tokens.ClusterTokens` to `SessionTokens`, `render_cluster` to `render_session`, `list_clusters`, `cluster_max_attempts`, `cluster_aggregates`, `export_cluster_history`, `hive_clusters` and every other `*cluster*` name to its `session` form; `api/clusters.py` to `api/sessions.py`.
- Settings: `max_clusters` to `max_sessions` (`ORCH_MAX_SESSIONS`); any other setting naming the unit likewise; `cluster_domain` (`ORCH_CLUSTER_DOMAIN`, Kubernetes DNS) stays.
- Public API: `/api/v1/clusters...` to `/api/v1/sessions...` (every sub-route, path parameter `session_id`); schemas `SessionSpec`, `SessionSummary`, `SessionView`, `CreateSession`; every `cluster_id` field to `session_id`; `MetaCaps.max_clusters` to `max_sessions`; error codes `session_deleting`, `static_session`, `session_limit`; init scripts `applies: next_session`; SSE event types `session_status`, `session_removed`; `api/service_auth.py` allowlist routes; `openapi.json` regenerated (`uv run python -m agents_orchestrator.api.openapi > openapi.json`); README.md API reference sections (routes, schemas, codes, SSE types) rewritten to match (`tests/test_readme_api.py` pins them).
- Kubernetes label: `k8s/labels.py` `SESSION_LABEL = "agents.szymonrichert.pl/session"` (constant renamed), used by `session_labels`, selectors and `kube.owns`; `tests/golden/cluster_*.yaml` to `tests/golden/session_*.yaml` with the new label. The `agent-<slug>` object prefix stays (D10). No relabel code (D8).
- Not in this task (orch-agent-api-sessions): the agent API header `X-Orch-Cluster`, the pod env `ORCH_CLUSTER_ID`, the rendered any-mcp plugin key `cluster` and `api/agent.py`'s `Me.cluster_id`; they stay until any-mcp v0.3.0 exists. Not in this task (orch-docs-e2e-sessions): README prose outside the API reference, AGENTS.md, MEMORY.md, chart comments and e2e scripts.
- `examples/bench.yaml`: the bench spec key that names the unit follows the bench spec rename.
- tests/: every test follows the rename; files named after the unit are renamed with `git mv` (`test_clusters_repo.py` to `test_sessions_repo.py`, `test_api_clusters.py` to `test_api_sessions.py`).
- Tests first: `tests/test_migrations.py::test_0005_renames_clusters_to_sessions` (apply 0001-0004 from a tmp dir, seed a cluster with an agent, message, event, check, leader, lock and preset link, run all migrations, read every row back under the new names; `information_schema` and `pg_indexes`/`pg_constraint` show no name containing `cluster`); `tests/test_api_sessions.py::test_old_cluster_routes_gone` (`/api/v1/clusters` answers 404); `tests/test_nomenclature.py` (new, D12): `git ls-files src/agents_orchestrator tests openapi.json` lines matching `/cluster/i`, minus the D12 Kubernetes/CNPG/kind allowlist, are none, except in `api/agent.py`, `k8s/render.py` and `k8s/on_start.py` and their tests (`tests/test_api_agent.py`, `tests/test_agent_*.py`, `tests/test_on_start.py`, `tests/test_render.py`), which orch-agent-api-sessions adds to the guard.

#### Acceptance conditions

- AC1: migration 0005 keeps every row and leaves no table, column, index or constraint named cluster [evidence: test:tests/test_migrations.py::test_0005_renames_clusters_to_sessions]
- AC2: the public API serves /api/v1/sessions and the old routes answer 404 [evidence: test:tests/test_api_sessions.py::test_old_cluster_routes_gone]
- AC3: src, tests and openapi.json name the unit session only, outside the agent-API files left to orch-agent-api-sessions [evidence: command:uv run pytest -q tests/test_nomenclature.py]
- AC4: README API reference and openapi.json match the app [evidence: command:uv run pytest -q tests/test_readme_api.py]
- AC5: objects carry the agents.szymonrichert.pl/session label and ownership checks use it [evidence: command:uv run pytest -q tests/test_render.py tests/test_reconciler.py]
- AC6: the component suite and lint pass [evidence: command:uv run pytest -q && uv run ruff check . && uv run ruff format --check .]

#### Files

- `src/agents_orchestrator/db/migrations/0005_sessions.sql`
- `src/agents_orchestrator/`
- `tests/`
- `openapi.json`
- `README.md`
- `examples/bench.yaml`

#### Interfaces

- design.md D2 table, exactly: routes `/api/v1/sessions...`, schemas `SessionSpec`/`SessionSummary`/`SessionView`/`CreateSession`, `session_id` fields, `max_sessions`, codes `session_deleting`/`static_session`/`session_limit`, `next_session`, SSE `session_status`/`session_removed`, channel `session_changed`, label `agents.szymonrichert.pl/session`, tables `sessions`/`session_leaders`, settings `ORCH_MAX_SESSIONS` (contract `orch-sessions-api`, consumed by agents-common, agents-web and the helmfile smoke).

#### Expected outcome

The orchestrator's database, code, public API, label and README API reference call the unit a session; `/api/v1/clusters` is 404; migration 0005 keeps every row.

#### Steps

- Red: write `test_0005_renames_clusters_to_sessions`, `test_old_cluster_routes_gone` and `tests/test_nomenclature.py`; run them: they fail.
- Green, layer by layer, running `uv run pytest -q` once at the end of each layer: (1) 0005 and every SQL string, row key and channel; (2) Python identifiers and module renames (`git mv`); (3) public API routes, schemas, codes, SSE, service_auth allowlist, openapi.json, README API reference; (4) label constant and golden files. Final: the verify passes, lint clean.

#### Notes

- design.md D15: one atomic task on purpose; never add a temporary alias between layers.
- Rows travel as `dict_row` into API views (db/views.py), so a column, its field and its API field rename together.
- Keep Kubernetes words: `cluster_domain`, `ClusterIP`, `clusterIP: None`, `cluster.local`, `in-cluster` (D12 allowlist).
- Leave `api/agent.py`, the `X-Orch-Cluster` header, `ORCH_CLUSTER_ID` and the any-mcp plugin key to orch-agent-api-sessions; the guard excludes exactly those files until then.
- Tests named after the unit are renamed with `git mv`; never delete a test to make the sweep pass.

- 2026-10-25 done

### S12: webhook docs sessions

- Status: done
- Files: `README.md`, `AGENTS.md`, `MEMORY.md`, `chart/agents-webhook/values.yaml`, `chart/agents-webhook/ci/lint-values.yaml`, `tests/test_nomenclature.py`
- Verify: `uv run pytest -q tests/test_nomenclature.py tests/test_readme_config.py tests/test_readme_api.py tests/test_chart_workloads.py tests/test_chart_network.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: 8e579ba

#### Requirement

Finish the rename in agents-webhook's docs and chart and guard the whole repo (design D1, D2, D12). Paths are in code/agents-webhook.

- `README.md`, `AGENTS.md`: session for the unit, agents-orchestrator for the orchestrator (`WEBHOOK_ORCHESTRATOR_URL` is "the agents-orchestrator base URL").
- `chart/agents-webhook/values.yaml` comments (the agents-orchestrator the worker and api talk to) and `chart/agents-webhook/ci/lint-values.yaml` (`url: http://agents-orchestrator.agents.svc`).
- `MEMORY.md`: a dated 2026-10-25 line: run columns are session_id/session_slug (migration 0005), agents-common v0.3.0, no aliases.
- New `tests/test_nomenclature.py` (D12): every tracked file, allowlisting only the Kubernetes/CNPG/kind phrases and dated history, has no `/cluster/i` naming the unit and no `agent[-_]orchestrator`.

#### Acceptance conditions

- AC1: no tracked file names the unit cluster or the project agent-orchestrator outside the allowlist and dated history [evidence: command:uv run pytest -q tests/test_nomenclature.py]
- AC2: the README config docs stay pinned [evidence: command:uv run pytest -q tests/test_readme_config.py tests/test_readme_api.py]
- AC3: the chart lints and renders [evidence: command:uv run pytest -q tests/test_chart_workloads.py tests/test_chart_network.py && helm lint chart/agents-webhook -f chart/agents-webhook/ci/lint-values.yaml]
- AC4: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

#### Files

- `README.md`
- `AGENTS.md`
- `MEMORY.md`
- `chart/agents-webhook/values.yaml`
- `chart/agents-webhook/ci/lint-values.yaml`
- `tests/test_nomenclature.py`

#### Interfaces

- None new.

#### Expected outcome

Every tracked agents-webhook file passes the guard; MEMORY.md records the rename.

#### Steps

- Red: write `tests/test_nomenclature.py` over all tracked files; it fails on docs and chart.
- Green: rewrite README, AGENTS.md, chart comments and lint values, add the MEMORY.md line; the verify passes.

#### Notes

- Allowlist only Kubernetes/CNPG phrases (`db-cluster`, `cluster-issuer`, `in-cluster`, `cluster node IPs`) and dated history, each with a comment.

- 2026-10-25 done

### S13: orch agent api sessions

- Status: done
- Files: `src/agents_orchestrator/api/agent.py`, `src/agents_orchestrator/k8s/render.py`, `src/agents_orchestrator/k8s/on_start.py`, `src/agents_orchestrator/settings.py`, `pyproject.toml`, `uv.lock`, `openapi.json`, `tests/`
- Verify: `uv run pytest -q tests/test_api_agent.py tests/test_agent_port.py tests/test_agent_scale.py tests/test_agent_init_scripts.py tests/test_on_start.py tests/test_render.py tests/test_nomenclature.py tests/test_readme_api.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: 4811b4a

#### Requirement

Rename the agent API's unit to session and pin any-mcp v0.3.0 (design D2, D11; contracts `orch-agent-api-session-header`, `any-mcp-release-v0-3-0`). Paths are in code/agents-orchestrator.

- `api/agent.py`: `require_agent()` reads `X-Orch-Session` (no `X-Orch-Cluster` fallback: a request carrying only the old header is refused like a missing header); `Me.session_id` replaces `Me.cluster_id`; every docstring and message says session. The token binding (Bearer token derived for the session id, caller IP equals `agents.pod_ip`) is unchanged.
- `k8s/render.py`: the agent pod env `ORCH_SESSION_ID` replaces `ORCH_CLUSTER_ID` (in `AGENT_PASSTHROUGH_ENV` too); the wrapper hook header renders `X-Orch-Session: ${ORCH_SESSION_ID}`.
- `k8s/on_start.py`: the rendered any-mcp orchestrator plugin entry uses key `session: ${ORCH_SESSION_ID}`.
- any-mcp pin: `pyproject.toml` `any-mcp @ git+https://github.com/szymonrychu/any-mcp@v0.3.0`, `uv.lock` refreshed, `settings.any_mcp_ref` default `v0.3.0`.
- `openapi.json` regenerated; README agent API section (header, `Me`, env names).
- `tests/test_nomenclature.py`: drop the agent-API exceptions so the guard covers all of `src/agents_orchestrator`, `tests` and `openapi.json`.
- Tests first: `tests/test_api_agent.py::test_old_cluster_header_refused`, `tests/test_render.py::test_agent_env_session_id`, `tests/test_on_start.py::test_plugin_entry_session_key` (validated with any-mcp v0.3.0's `AnyMcpConfig`), and `tests/test_agent_scale.py` running the real v0.3.0 `OrchestratorPlugin` against the agent API.

#### Acceptance conditions

- AC1: the agent API accepts X-Orch-Session and refuses a request carrying only X-Orch-Cluster [evidence: test:tests/test_api_agent.py::test_old_cluster_header_refused]
- AC2: agent pods get ORCH_SESSION_ID and the hook header renders X-Orch-Session [evidence: test:tests/test_render.py::test_agent_env_session_id]
- AC3: the rendered any-mcp plugin entry uses the session key and validates under any-mcp v0.3.0 [evidence: test:tests/test_on_start.py::test_plugin_entry_session_key]
- AC4: the whole of src, tests and openapi.json names the unit session only [evidence: command:uv run pytest -q tests/test_nomenclature.py tests/test_readme_api.py]
- AC5: the agent API suites and lint pass [evidence: command:uv run pytest -q tests/test_api_agent.py tests/test_agent_port.py tests/test_agent_scale.py tests/test_agent_init_scripts.py tests/test_on_start.py tests/test_render.py && uv run ruff check . && uv run ruff format --check .]

#### Files

- `src/agents_orchestrator/api/agent.py`
- `src/agents_orchestrator/k8s/render.py`
- `src/agents_orchestrator/k8s/on_start.py`
- `src/agents_orchestrator/settings.py`
- `pyproject.toml`
- `uv.lock`
- `openapi.json`
- `tests/`

#### Interfaces

- `require_agent()`: `Authorization: Bearer <agent token>` plus `X-Orch-Session: <session id>`, caller IP = `agents.pod_ip`; `Me.session_id`; pod env `ORCH_SESSION_ID`; rendered plugin entry `{..., session: ${ORCH_SESSION_ID}, ...}` (contract `orch-agent-api-session-header`, matches any-mcp v0.3.0).

#### Expected outcome

Agents reach their session's agent API with any-mcp v0.3.0; the old header is refused; the whole repo's src, tests and openapi.json pass the nomenclature guard.

#### Steps

- Precondition: tag any-mcp v0.3.0 exists (`git ls-remote --tags https://github.com/szymonrychu/any-mcp v0.3.0`); else end `blocked`, whoCanClear "orchestrator: tag any-mcp v0.3.0".
- Red: bump the pin, `uv lock`, write the three named tests; run them: they fail.
- Green: rename header, env, field and plugin key; regenerate openapi.json; widen the guard; the verify passes.

#### Notes

- The token derivation input (`purpose:session id`) is unchanged, so live tokens stay valid across the rename.

- 2026-10-25 done

### S14: orch docs e2e sessions

- Status: done
- Files: `README.md`, `AGENTS.md`, `MEMORY.md`, `chart/agents-orchestrator/`, `e2e/`, `scripts/e2e.sh`, `tests/`
- Verify: `uv run pytest -q tests/test_nomenclature.py tests/test_project_name.py tests/test_readme_api.py && mise run lint:chart && uv run ruff check . && uv run ruff format --check .`
- Verified head: c27b228

#### Requirement

Finish the rename in the orchestrator's docs, chart comments and e2e, and guard the whole repo (design D1, D2, D10, D12; user decision: cluster is renamed session throughout (API, UI, docs)). Paths are in code/agents-orchestrator.

- `README.md` (all prose), `AGENTS.md` (CLAUDE.md only imports it), `chart/agents-orchestrator/README.md`, `chart/agents-orchestrator/values.yaml` and template comments ("per-session tokens", "session Secrets"), `e2e/agent-test.config.yaml`, `scripts/e2e.sh` messages, `tests/e2e/`: session for the unit, agents-orchestrator for the project; Kubernetes, CNPG and kind clusters keep their word.
- `MEMORY.md`: dated 2026-10-25 lines: renamed to agents-orchestrator and cluster to session (D1, D2), wrapper session id is `wrapper_session_id` (D3), no aliases; earlier dated lines keep their history.
- `tests/test_nomenclature.py` and `tests/test_project_name.py`: guard every tracked file of the repo (`git ls-files`), allowlisting only the D12 Kubernetes/CNPG/kind phrases and the dated-history files (MEMORY.md, ROADMAP.md, CHANGELOG.md, docs/plans/).
- The kind e2e passes on the renamed chart, images, routes and labels: `mise run test:e2e`.

#### Acceptance conditions

- AC1: no tracked file names the unit cluster or the project agent-orchestrator outside the allowlist and dated history [evidence: command:uv run pytest -q tests/test_nomenclature.py tests/test_project_name.py]
- AC2: MEMORY.md records the rename decisions [evidence: command:grep -q 'wrapper_session_id' MEMORY.md && grep -q 'agents-orchestrator' MEMORY.md]
- AC3: the kind e2e passes on the renamed chart, routes and labels [evidence: command:mise run test:e2e]
- AC4: README and openapi stay in sync and lint passes [evidence: command:uv run pytest -q tests/test_readme_api.py && uv run ruff check . && uv run ruff format --check . && mise run lint:chart]

#### Files

- `README.md`
- `AGENTS.md`
- `MEMORY.md`
- `chart/agents-orchestrator/`
- `e2e/`
- `scripts/e2e.sh`
- `tests/`

#### Interfaces

- None new; consumes every earlier orchestrator task.

#### Expected outcome

Every tracked file of agents-orchestrator passes both guards, MEMORY.md records the decisions, and the kind e2e is green.

#### Steps

- Red: widen `tests/test_nomenclature.py` and `tests/test_project_name.py` to all tracked files; run them: they fail on docs, chart comments and e2e.
- Green: rewrite the prose, add the MEMORY.md lines; the verify passes; then `mise run test:e2e` (quote its summary line).

#### Notes

- MEMORY.md, ROADMAP.md and CHANGELOG.md keep their dated history (allowlisted); ROADMAP.md is human-owned, never edited.
- Kind and Kubernetes clusters keep their word (D12).

- 2026-10-25 done

### S15: web api layer sessions

- Status: done
- Files: `scripts/sync-api.mjs`, `scripts/sync-api.test.mjs`, `openapi/orchestrator.json`, `openapi/orchestrator.source`, `src/`
- Verify: `npx tsc -b && npx vitest run && node --test scripts/sync-api.test.mjs && npm run check:api && npm run lint`
- Verified head: c4b7edb

#### Requirement

Re-vendor the orchestrator API from agents-orchestrator and rename the UI's API layer to sessions (design D2, D11, D15; user decision: cluster is renamed session throughout (API, UI, docs), with the web UI fixed to match; contract `orch-sessions-api` and `agents-web-openapi-vendor`). Paths are in code/agents-web.

- `scripts/sync-api.mjs`: backend `orchestrator` reads repo `agents-orchestrator` from sibling `../agents-orchestrator`; `scripts/sync-api.test.mjs` expects `openapi/orchestrator.source` to read `agents-orchestrator <sha>`.
- `npm run sync:api -- orchestrator` against the orchestrator integration tree after orch-agent-api-sessions: `openapi/orchestrator.json`, `openapi/orchestrator.source`; `npm run gen:api` regenerates `src/api/schema.d.ts` (never hand-edited).
- `src/api/client.ts`: types `SessionView`, `SessionSummary`, `SessionSpec`, `CreateSession`; `listSessions`, `getSession`, `createSession`, `deleteSession` and every `/sessions/...` path; every `clusterId` parameter `sessionId`. `src/api/stream.ts`: SSE types `session_status`, `session_removed`. `src/api/files.ts`, `src/api/terminals.ts`: `session_id`, `sessionId`. Error code `session_deleting`.
- Every importer in src/ updated mechanically to the renamed types, functions and fields so `tsc -b` passes; visible labels and component names are the next tasks' work (web-sessions-pages, web-workspace-sessions).
- Tests first: `src/api/client.test.ts` "session routes" (every call uses `/api/v1/sessions...`, none `/clusters`), `src/api/stream.test.ts` "session events" (session_status and session_removed are handled), and the other tests touched by the type rename.

#### Acceptance conditions

- AC1: the client calls only /api/v1/sessions routes [evidence: test:src/api/client.test.ts::session routes]
- AC2: the stream handles session_status and session_removed [evidence: test:src/api/stream.test.ts::session events]
- AC3: the vendored openapi comes from agents-orchestrator and the generated types match it [evidence: command:node --test scripts/sync-api.test.mjs && grep -q '^agents-orchestrator ' openapi/orchestrator.source && npm run check:api]
- AC4: the UI type-checks, its tests and lint pass [evidence: command:npx tsc -b && npx vitest run && npm run lint]

#### Files

- `scripts/sync-api.mjs`
- `scripts/sync-api.test.mjs`
- `openapi/orchestrator.json`
- `openapi/orchestrator.source`
- `src/`

#### Interfaces

- `openapi/orchestrator.json` byte-identical to agents-orchestrator's `openapi.json`, `openapi/orchestrator.source` `agents-orchestrator <sha>` (contract `agents-web-openapi-vendor`); `src/api/client.ts` exports `listSessions`, `getSession`, `createSession`, `deleteSession` and the Session types (contract `orch-sessions-api`).

#### Expected outcome

The UI compiles and passes its tests against the session API; no client call names `/clusters`.

#### Steps

- Red: update `scripts/sync-api.test.mjs` and write the "session routes" and "session events" tests; run `node --test scripts/sync-api.test.mjs` and `npx vitest run src/api`: they fail.
- Green: sync-api repo map, `npm run sync:api -- orchestrator` (sibling `../agents-orchestrator` is the orchestrator's integration tree), `npm run gen:api`, rename the API layer, fix every importer until `npx tsc -b` passes; the verify passes.

#### Notes

- design.md D15: types and every importer move together; never keep an alias type.
- Visible texts and component names are the next two tasks; rename identifiers only here.

- 2026-10-25 done

### S16: helmfile orch release rename

- Status: done
- Files: `helmfile.yaml.gotmpl`, `values/agent-orchestrator/`, `values/agents-orchestrator/`, `scripts/bootstrap-secrets.sh`, `tests/test_orchestrator_release.py`, `tests/test_secrets.py`
- Verify: `uv run pytest -q tests/test_orchestrator_release.py tests/test_secrets.py && mise run lint`
- Verified head: 6361a57

#### Requirement

Declare the orchestrator under its new release name and retire the old app release (design D1, D7, D9, D11; contracts `agents-orchestrator-chart` / `-image`, `any-mcp-release-v0-3-0`). Paths are in code/agents-helmfile.

Precondition, checked first: this epic's agents-orchestrator PR is merged to main and its CI published chart `0.1.0-main.<sha7>` and image `<sha7>` under the new names (`helm show chart oci://harbor.szymonrichert.pl/charts/agents-orchestrator --version 0.1.0-main.<sha7>`). The orchestrator writes `<sha7>` into this task with `ticket.py amend` once the PR merges; otherwise end `blocked`, whoCanClear "orchestrator: merge the agents-orchestrator PR and wait for its main CI".

- `helmfile.yaml.gotmpl`: the old `agent-orchestrator` release keeps only name, namespace, chart and `installed: false` (helmfile uninstalls it on apply; no values or secrets listed); new release `agents-orchestrator` (chart `oci://harbor.szymonrichert.pl/charts/agents-orchestrator`, version `0.1.0-main.<sha7>`, timeout 600, `needs: [agents/agents-orchestrator-db]`, labels `application: agents-orchestrator`, the default template, `secrets:` `values/agents-orchestrator/default.secrets.yaml` then `values/agents-orchestrator/service-token-agents-webhook.secrets.yaml`).
- `git mv values/agent-orchestrator values/agents-orchestrator` (the encrypted files move byte-identical: the master key, Claude token and service token hashes keep their values, so derived tokens do not change).
- `values/agents-orchestrator/common.yaml`: image `harbor.szymonrichert.pl/containers/agents-orchestrator` tag `<sha7>`; `postgres.existingSecret: agents-orchestrator-db-cluster-app`; `ORCH_ANY_MCP_REF: v0.3.0`; any ORCH_* name renamed by D2 (none set today: confirm); podAnnotations `oauth2-proxy-admission/secret-name: agents-orchestrator-proxy` (D9, created by user step U1); ingress TLS `secretName: agents-orchestrator-tls` with the cert-manager annotations kept (this ingress owns the certificate); comments name agents-orchestrator.
- `scripts/bootstrap-secrets.sh`: the moved paths and new names.
- tests/: `tests/test_orchestrator_release.py` (`REL = "agents-orchestrator"`, every assertion on the new names, the db template test on `agents-orchestrator-db`; new `test_old_release_uninstalled` and `test_values_dir_moved` (`git ls-files values/agent-orchestrator` prints nothing)); `tests/test_secrets.py` paths. Tests first.

#### Acceptance conditions

- AC1: the old app release is declared installed false with nothing else [evidence: test:tests/test_orchestrator_release.py::test_old_release_uninstalled]
- AC2: the values directory moved and the old path is gone from git [evidence: test:tests/test_orchestrator_release.py::test_values_dir_moved]
- AC3: chart version and image tag agree on the merged agents-orchestrator sha [evidence: test:tests/test_orchestrator_release.py::test_orchestrator_pin_matches_image]
- AC4: the release reads the new DB, SSO and TLS Secret names and any-mcp v0.3.0 [evidence: command:uv run pytest -q tests/test_orchestrator_release.py tests/test_secrets.py]
- AC5: the pinned chart and image exist in Harbor [evidence: judgement:the task notes quote helm show chart and docker manifest inspect for the pinned sha]
- AC6: lint passes [evidence: command:mise run lint]

#### Files

- `helmfile.yaml.gotmpl`
- `values/agent-orchestrator/`
- `values/agents-orchestrator/`
- `scripts/bootstrap-secrets.sh`
- `tests/test_orchestrator_release.py`
- `tests/test_secrets.py`

#### Interfaces

- Release `agents-orchestrator` values (Services `agents-orchestrator`, `-agents`, `-services:8002`; Secrets `agents-orchestrator-{claude,master-key,services}`); old release `agent-orchestrator` `installed: false`.

#### Expected outcome

The helmfile declares the renamed orchestrator release and the old app release as uninstalled; nothing is applied here.

#### Steps

- Check the precondition (merged sha and Harbor artefacts) first.
- Red: update `tests/test_orchestrator_release.py` and `tests/test_secrets.py` to the new names and add the two new tests; they fail.
- Green: helmfile release blocks, `git mv` the values dir, values and bootstrap script; the verify passes.

#### Notes

- `git mv` keeps the encrypted files byte-identical; never re-encrypt them (the master key value must not change).
- Never apply: deploy-cutover sequences the applies (design D7).

- 2026-10-25 done

### S17: web sessions pages

- Status: done
- Files: `src/clusters/`, `src/sessions/`, `src/backends/registry.ts`, `src/backends/registry.test.ts`, `src/App.tsx`, `src/App.test.tsx`, `src/nomenclature.test.ts`
- Verify: `npx tsc -b && npx vitest run src/sessions src/backends src/App.test.tsx src/nomenclature.test.ts && npm run lint`
- Verified head: c891770

#### Requirement

Rename the sessions settings page and its dialogs (design D2, D12; user decision: cluster is renamed session throughout, with the web UI fixed to match). Paths are in code/agents-web.

- `git mv src/clusters src/sessions`: `SessionsPage` (title "Sessions", button "New session", empty state "No sessions yet"), `NewSessionDialog` (title and aria-label "New session"), `DiscardSessionDialog` (body: "Everything is deleted: the agents, the workspace PVC and its files, and the session's whole chat history ..."), `InitScriptsDialog` ("No run recorded for this session.", "Saved. Applies to the next session"), `sessionSpecForm.ts`; each `*.test.tsx` renamed with its component and asserting the new texts.
- `src/backends/registry.ts`: menu entry id `sessions`, label "Sessions", order 10, `openSession`; `src/backends/registry.test.ts`.
- `src/App.tsx`, `src/App.test.tsx`: the settings route to the sessions page, "No sessions yet"; test names that name the unit say session.
- New `src/nomenclature.test.ts` (D12): `git ls-files` over `src/sessions`, `src/backends`, `src/App.tsx` and `src/App.test.tsx` has no line matching `/cluster/i`; web-workspace-sessions and web-docs-names widen the guarded list.
- Tests first: the renamed page and dialog tests fail on the old texts before the rename.


Orchestrator ruling 2026-10-25 (review of this task): src/App.tsx and src/App.test.tsx keep their cluster identifiers until web-workspace-sessions renames useClusters, TopBar and the cluster props they import; they compile only together. This task guards src/sessions and src/backends only; the App.tsx and App.test.tsx renames and their guard move to web-workspace-sessions.

#### Acceptance conditions

- AC1: the sessions page shows Sessions, New session and No sessions yet [evidence: test:src/sessions/SessionsPage.test.tsx::lists sessions]
- AC2: the menu entry is sessions / Sessions [evidence: test:src/backends/registry.test.ts::sessions entry]
- AC3: the old directory is gone from git [evidence: command:test -z "$(git ls-files src/clusters)"]
- AC4: the guarded paths name the unit session only [evidence: command:npx vitest run src/nomenclature.test.ts]
- AC5: the UI type-checks, the touched tests and lint pass [evidence: command:npx tsc -b && npx vitest run src/sessions src/backends src/App.test.tsx && npm run lint]

#### Files

- `src/clusters/`
- `src/sessions/`
- `src/backends/registry.ts`
- `src/backends/registry.test.ts`
- `src/App.tsx`
- `src/App.test.tsx`
- `src/nomenclature.test.ts`

#### Interfaces

- Menu entry `{id: 'sessions', label: 'Sessions', order: 10, backend: 'orchestrator'}` (supersedes `web-settings-menu-order`'s Clusters entry for agents-schedule-microservice, which inserts between Sessions and Presets).

#### Expected outcome

Settings > Sessions lists sessions with New session and discard; every text says session; `src/clusters` is gone from git.

#### Steps

- Red: rename the test files with their components (`git mv`), change their expected texts, write `src/nomenclature.test.ts` over the guarded paths; `npx vitest run src/sessions src/backends src/App.test.tsx src/nomenclature.test.ts` fails.
- Green: `git mv src/clusters src/sessions`, rename components and texts, registry, App; the verify passes.

#### Notes

- Test titles used as AC refs: "lists sessions" in SessionsPage.test.tsx, "sessions entry" in registry.test.ts.

- 2026-10-25 amended: App.tsx/App.test.tsx renames move to web-workspace-sessions (compile dependency)

- 2026-10-25 done

### S18: web workspace sessions

- Status: done
- Files: `src/App.tsx`, `src/App.test.tsx`, `src/chat/`, `src/ribbon/`, `src/layout/`, `src/files/`, `src/terminal/`, `src/presets/`, `src/nomenclature.test.ts`
- Verify: `npx tsc -b && npx vitest run && npm run lint`
- Verified head: 020ff1a

#### Requirement

Rename the session workspace UI: chat, ribbon, top bar, menu, files, terminal and presets (design D2, D12; user decision: cluster is renamed session throughout, with the web UI fixed to match). Paths are in code/agents-web.

- `src/chat/`: `useClusterChat.ts` to `useSessionChat.ts`; Composer placeholder "Message the session"; ScaleControl tooltip "Static session: scaling is off"; AgentsStrip, ChatView, QueueStrip, ChatLog props and identifiers.
- `src/ribbon/`: `useClusters.ts` to `useSessions.ts` and its state (`sessions`, `session`).
- `src/layout/`: TopBar button "New session" and props; SessionsMenu empty state "No sessions yet" and props; Workspace `data-session` attribute; panel layout and storage keys that name the unit (saved layouts under the old key are dropped once, no migration, D2 no-compat); ConfirmDialog test texts.
- `src/files/`, `src/terminal/`: props, identifiers, comments (`sessionId`).
- `src/presets/`: PresetForm help texts "More than 1 makes the session a hive" and "Runs once when a session starts, in the shared workdir; agents can read and edit it; edits apply to the next session"; PresetsPage doc comment "the stored SessionSpec templates".
- Every test in these directories follows the rename, test names included.
- `src/nomenclature.test.ts`: guard all of `src/` except `src/webhooks/` and `src/api/webhooks-schema.d.ts` (web-webhooks-session-fields adds them).


Orchestrator ruling 2026-10-25 (moved from web-sessions-pages): also rename every cluster identifier, text, data attribute and test name in src/App.tsx and src/App.test.tsx (useClusters, clusters, clusterId, New cluster, Cluster actions, data-cluster, cluster-row-*), and the src-wide guard must cover both files.

#### Acceptance conditions

- AC1: the composer invites a message to the session [evidence: test:src/chat/Composer.test.tsx::placeholder names the session]
- AC2: the top bar offers New session and the menu says No sessions yet [evidence: test:src/layout/TopBar.test.tsx::new session button]
- AC3: preset help texts say session [evidence: test:src/presets/PresetForm.test.tsx::help texts name the session]
- AC4: src outside the webhooks UI names the unit session only [evidence: command:npx vitest run src/nomenclature.test.ts]
- AC5: the UI type-checks, its tests and lint pass [evidence: command:npx tsc -b && npx vitest run && npm run lint]

#### Files

- `src/chat/`
- `src/ribbon/`
- `src/layout/`
- `src/files/`
- `src/terminal/`
- `src/presets/`
- `src/nomenclature.test.ts`

#### Interfaces

- `useSessions()` (ribbon state) and `useSessionChat()` hooks; `data-session` on the workspace root.

#### Expected outcome

Every chat, top bar, menu, files, terminal and preset text says session; src outside the webhooks UI passes the guard.

#### Steps

- Red: change the expected texts in the touched tests and widen `src/nomenclature.test.ts`; `npx vitest run` fails.
- Green: rename hooks, props, texts, storage keys and comments; the verify passes.

#### Notes

- Test titles used as AC refs: "placeholder names the session" (Composer.test.tsx), "new session button" (TopBar.test.tsx), "help texts name the session" (PresetForm.test.tsx).
- Saved layouts under old storage keys are dropped once (no migration, no fallback).

- 2026-10-25 amended: receives the App.tsx/App.test.tsx renames from web-sessions-pages

- 2026-10-25 done

### S19: web webhooks session fields

- Status: done
- Files: `openapi/webhooks.json`, `openapi/webhooks.source`, `src/api/webhooks-schema.d.ts`, `src/webhooks/`, `src/nomenclature.test.ts`
- Verify: `npx tsc -b && npx vitest run src/webhooks src/nomenclature.test.ts && npm run check:api && npm run lint`
- Verified head: 811f1b7

#### Requirement

Show the webhook run's session in the Webhooks UI (design D2, D14; contract `webhook-events-session-fields`). Paths are in code/agents-web. Starts after webhook-event-filters merged (gate Q6).

- `npm run sync:api -- webhooks` against the agents-webhook integration tree after webhook-session-columns: `openapi/webhooks.json`, `openapi/webhooks.source`; `npm run gen:api` regenerates `src/api/webhooks-schema.d.ts`.
- `src/webhooks/EventsTable.tsx` (and any other file under `src/webhooks/` reading the run): column "Session" from `session_slug`/`session_id`; texts say session.
- `src/webhooks/WebhooksPage.test.tsx` (test first): the events table shows the Session column and slug.
- `src/nomenclature.test.ts`: guard all of `src/`.

#### Acceptance conditions

- AC1: the events table shows each run's session [evidence: test:src/webhooks/WebhooksPage.test.tsx::events show the session]
- AC2: the vendored webhooks openapi matches the generated types [evidence: command:npm run check:api]
- AC3: all of src names the unit session only [evidence: command:npx vitest run src/nomenclature.test.ts]
- AC4: the UI type-checks, the webhooks tests and lint pass [evidence: command:npx tsc -b && npx vitest run src/webhooks && npm run lint]

#### Files

- `openapi/webhooks.json`
- `openapi/webhooks.source`
- `src/api/webhooks-schema.d.ts`
- `src/webhooks/`
- `src/nomenclature.test.ts`

#### Interfaces

- Consumes `webhook-events-session-fields` (`session_id`, `session_slug`).

#### Expected outcome

The Webhooks events table shows each run's session; all of src passes the guard.

#### Steps

- Red: write "events show the session" in WebhooksPage.test.tsx and widen the guard; they fail.
- Green: `npm run sync:api -- webhooks` (sibling `../agents-webhook` is its integration tree), `npm run gen:api`, update the table; the verify passes.

#### Notes

- webhook-event-filters (the epic's blocker) already changed `src/webhooks/`; start from main.

- 2026-10-25 done

### S20: web docs names

- Status: done
- Files: `README.md`, `chart/agents-web/README.md`, `chart/agents-web/values.yaml`, `MEMORY.md`, `src/nomenclature.test.ts`
- Verify: `npx vitest run src/nomenclature.test.ts && npm run test:chart && npm run lint:chart && npm run lint`
- Verified head: aac9e39

#### Requirement

Finish the rename in agents-web's docs and chart and guard the whole repo (design D1, D2, D12). Paths are in code/agents-web.

- `README.md`, `chart/agents-web/README.md`, `chart/agents-web/values.yaml` comments: agents-orchestrator owns `/api`; `npm run sync:api -- orchestrator` reads `../agents-orchestrator`; session for the unit.
- `MEMORY.md`: a dated 2026-10-25 line: the UI says session everywhere, menu entry id `sessions`, saved layouts under old keys dropped once, no aliases; earlier dated lines keep their history.
- `src/nomenclature.test.ts`: guard every tracked file (`git ls-files`), allowlisting only the D12 Kubernetes phrases (for example "cluster-internal" in chart docs) and the dated-history files.

#### Acceptance conditions

- AC1: no tracked file names the unit cluster or the project agent-orchestrator outside the allowlist and dated history [evidence: command:npx vitest run src/nomenclature.test.ts]
- AC2: MEMORY.md records the UI rename [evidence: command:grep -q 'sessions' MEMORY.md]
- AC3: chart tests, chart lint and lint pass [evidence: command:npm run test:chart && npm run lint:chart && npm run lint]

#### Files

- `README.md`
- `chart/agents-web/README.md`
- `chart/agents-web/values.yaml`
- `MEMORY.md`
- `src/nomenclature.test.ts`

#### Interfaces

- None new.

#### Expected outcome

Every tracked agents-web file passes the guard; MEMORY.md records the rename.

#### Steps

- Red: widen `src/nomenclature.test.ts` to `git ls-files`; it fails on README and chart docs.
- Green: rewrite the docs, add the MEMORY.md line; the verify passes.

#### Notes

- "cluster-internal" in chart docs is Kubernetes: allowlisted with a comment.

- 2026-10-25 done

### S21: helmfile consumers rename

- Status: done
- Files: `helmfile.yaml.gotmpl`, `values/agents-webhook/common.yaml`, `values/agents-web/common.yaml`, `tests/test_webhook_release.py`, `tests/test_web_release.py`
- Verify: `uv run pytest -q tests/test_webhook_release.py tests/test_web_release.py && mise run lint`
- Verified head: 4fbd057

#### Requirement

Point agents-webhook and agents-web at the renamed orchestrator and pin their renamed builds (design D1, D9, D11). Paths are in code/agents-helmfile.

Precondition, checked first: this epic's agents-webhook and agents-web PRs are merged to main and their CI published `0.1.0-main.<sha7>` charts and images; the orchestrator writes both sha7 values into this task with `ticket.py amend`; otherwise end `blocked`, whoCanClear "orchestrator: merge the agents-webhook and agents-web PRs and wait for their main CI".

- `helmfile.yaml.gotmpl`: agents-webhook `needs` `agents/agents-orchestrator` (and its own db); chart versions of agents-webhook and agents-web pinned to the merged sha7s.
- `values/agents-webhook/common.yaml`: `orchestrator.url: http://agents-orchestrator-services:8002`; image tag; SSO `secret-name: agents-orchestrator-proxy`; ingress TLS `secretName: agents-orchestrator-tls`; comments.
- `values/agents-web/common.yaml`: image tag; SSO `secret-name: agents-orchestrator-proxy`; TLS `agents-orchestrator-tls`; comments ("one Certificate for agents-orchestrator-tls").
- Tests first: `tests/test_webhook_release.py` (`test_database_and_orchestrator_wiring` on the new URL, `test_webhook_pin_and_needs` on `agents/agents-orchestrator`, `test_sso_on_api_only` and `test_ingress_host_and_tls` on the new Secrets, `test_db_values_match_orchestrator_db_shape` against `agents-orchestrator-db`); `tests/test_web_release.py` (`test_web_behind_oauth2_proxy_with_orchestrator_secret`, `test_web_ingress_owns_root_without_cert_annotations`, `test_web_pin_matches_image`).

#### Acceptance conditions

- AC1: the webhook calls the orchestrator at agents-orchestrator-services:8002 [evidence: test:tests/test_webhook_release.py::test_database_and_orchestrator_wiring]
- AC2: the webhook release needs agents-orchestrator [evidence: test:tests/test_webhook_release.py::test_webhook_pin_and_needs]
- AC3: agents-web and agents-webhook use the agents-orchestrator-proxy and agents-orchestrator-tls Secrets [evidence: command:uv run pytest -q tests/test_web_release.py tests/test_webhook_release.py]
- AC4: the pinned charts and images exist in Harbor [evidence: judgement:the task notes quote helm show chart for both pinned sha7s]
- AC5: lint passes [evidence: command:mise run lint]

#### Files

- `helmfile.yaml.gotmpl`
- `values/agents-webhook/common.yaml`
- `values/agents-web/common.yaml`
- `tests/test_webhook_release.py`
- `tests/test_web_release.py`

#### Interfaces

- agents-webhook `orchestrator.url: http://agents-orchestrator-services:8002`; shared Secrets `agents-orchestrator-proxy`, `agents-orchestrator-tls`.

#### Expected outcome

agents-webhook and agents-web are declared against the renamed orchestrator, Secrets and their renamed builds; nothing is applied here.

#### Steps

- Check the precondition (both merged sha7s and Harbor charts) first.
- Red: update the named tests in `tests/test_webhook_release.py` and `tests/test_web_release.py`; they fail.
- Green: helmfile needs and pins, both values files; the verify passes.

#### Notes

- agents-web and agents-webhook ingresses carry no cert-manager annotation; the orchestrator ingress owns `agents-orchestrator-tls`.

- 2026-10-25 done

### S22: helmfile smoke sessions

- Status: done
- Files: `scripts/smoke.sh`, `mise.toml`, `tests/test_smoke_script.py`, `tests/test_nomenclature.py`, `README.md`, `AGENTS.md`
- Verify: `uv run pytest -q tests/test_smoke_script.py tests/test_mise_tasks.py tests/test_nomenclature.py && mise run lint`
- Verified head: acd8432

#### Requirement

Move the live smoke and the helmfile docs to the new names and guard the repo (design D1, D2, D12; contract `orch-sessions-api` as consumer). Paths are in code/agents-helmfile.

- `scripts/smoke.sh`: default release `agents-orchestrator` (port-forward `deploy/agents-orchestrator-api`, Services `agents-orchestrator`, `agents-orchestrator-agents`, `agents-orchestrator-services:8002`), routes `/api/v1/sessions...`, session wording in variables, logs and failure messages, label `agents.szymonrichert.pl/session=<slug>`, the leader and scale checks on the session routes; the wrapper's own session config dir check keeps its wording.
- `mise.toml`: the smoke task description says session.
- `tests/test_smoke_script.py` (test first): the fake API serves `/api/v1/sessions` only and the default routes name `agents-orchestrator`; every existing case keeps passing on the new names.
- `README.md`, `AGENTS.md`: releases, Secrets and the cutover in the new names; `MEMORY.md` is written by deploy-cutover.
- New `tests/test_nomenclature.py` (D12): every tracked file has no `/cluster/i` naming the orchestrator's unit and no `agent[-_]orchestrator`, allowlisting the Kubernetes/CNPG/kind phrases (the cnpg `cluster:` values key, `db-cluster`, `cluster-info`, `cluster-issuer`, `cluster.local`), the dated-history files, and the old db release kept hibernated (`agent-orchestrator-db` in helmfile.yaml.gotmpl, `values/agent-orchestrator-db/`, the import source names in `values/agents-orchestrator-db/common.yaml`, tests/test_db_release.py), each allowlist entry commented with its reason.

#### Acceptance conditions

- AC1: the smoke drives the session routes and the renamed releases [evidence: test:tests/test_smoke_script.py::test_happy_path_exits_zero_and_cleans_up]
- AC2: no tracked file names the unit cluster or the old project outside the commented allowlist [evidence: command:uv run pytest -q tests/test_nomenclature.py]
- AC3: the smoke suite and lint pass [evidence: command:uv run pytest -q tests/test_smoke_script.py tests/test_mise_tasks.py && mise run lint]

#### Files

- `scripts/smoke.sh`
- `mise.toml`
- `tests/test_smoke_script.py`
- `tests/test_nomenclature.py`
- `README.md`
- `AGENTS.md`

#### Interfaces

- `scripts/smoke.sh` env: `RELEASE` default `agents-orchestrator`, `WEB_RELEASE`, `HOST`, `NAMESPACE`, `SMOKE_TIMEOUT_S` (unchanged names).

#### Expected outcome

The offline smoke tests and the guard pass on the new names; the live smoke runs in deploy-cutover.

#### Steps

- Red: switch the fake API in `tests/test_smoke_script.py` to `/api/v1/sessions` and the default routes to `agents-orchestrator`, write `tests/test_nomenclature.py`; they fail.
- Green: rewrite smoke.sh, the mise description, README and AGENTS.md; the verify passes.

#### Notes

- The smoke's wrapper "session config dir" check is the wrapper's session: keep it, it is not the unit.
- Each allowlist entry gets a comment saying why (Kubernetes, CNPG, or the hibernated old db, design D6).

- 2026-10-25 done

### S23: deploy cutover

- Status: done
- Files: `MEMORY.md`
- Verify: `mise run diff && mise run smoke`
- Verified head: bfc675b

#### Requirement

Move the live namespace to the renamed releases and prove it (design D5, D7, D8, D9; gate Q2, Q4; the irreversible operations are listed in design.md). Paths are in code/agents-helmfile. Applies are run by the orchestrator in the main session, never by a subagent; the implementer runs the read-only probes, `mise run diff` and `mise run smoke`.

- Precondition probes (implementer, read-only; any failure ends the task `blocked` with the output, before any apply): (1) `kubectl -n agents exec agent-orchestrator-db-cluster-1 -c postgres -- psql -U postgres -d agent_orchestrator -Atc "select count(*) from clusters where desired = 'active'"` prints 0, and the preset count is recorded; (2) `kubectl -n agents get secret agents-orchestrator-proxy` exists (user step U1 done; whoCanClear "user: apply the Keycloak client agents-orchestrator, design D9"); (3) the pinned charts exist (`helm show chart` for agents-orchestrator, agents-webhook, agents-web); (4) `mise run diff` shows only the expected changes: old app release removed, the two new releases, agents-webhook and agents-web values and versions; anything else stops the task. End the round with "ready for step 2".
- Step 2 (orchestrator): `mise run apply -- --selector name=agent-orchestrator` (uninstalls the old app).
- Step 3 (orchestrator): `mise run apply -- --selector name=agents-orchestrator-db`; implementer waits until `kubectl -n agents get cluster.postgresql.cnpg.io agents-orchestrator-db-cluster` is healthy and `select count(*) from presets` in `agents_orchestrator` equals the recorded count; a mismatch stops the task (rollback: re-declare the old release, D7).
- Step 4 (orchestrator): `mise run apply`. Implementer: the new app's migrate applied 0004 and 0005 (`select version from schema_migrations` lists 0001-0005, tables `sessions` and `session_leaders` exist), the presets are listed by `GET /api/v1/presets`, `mise run diff` shows no drift, `mise run smoke` exits 0.
- Step 5 (orchestrator): once `kubectl -n agents get certificate agents-orchestrator-tls` is Ready, `kubectl -n agents delete secret agent-orchestrator-tls`.
- `MEMORY.md`: a dated line: cut over to agents-orchestrator `0.1.0-main.<sha7>` with database `agents-orchestrator-db` imported from `agent-orchestrator-db` (preset count), agents-webhook and agents-web pins, the old TLS Secret removed, smoke green (quote its last line). No other file changes.


Orchestrator ruling 2026-10-25 (review of webhook-session-columns): agents-webhook migration 0005 renames events.cluster_id/cluster_slug while old pods still run the old SQL under the default RollingUpdate. During the cutover, scale the agents-webhook Deployments (ingest, api, worker) to 0, or apply that release with a Recreate strategy, before upgrading it to the session-named build. Queued rows wait and nothing is lost. Record which option was used in the task notes.

#### Acceptance conditions

- AC1: the preconditions held before any apply [evidence: judgement:the task notes quote the four precondition probe outputs]
- AC2: the imported database keeps the presets and carries the session schema [evidence: judgement:the task notes quote the preset counts of both databases and schema_migrations 0001-0005]
- AC3: the live namespace has no drift from the helmfile after the cutover [evidence: command:mise run diff]
- AC4: the smoke passes on the renamed releases [evidence: command:mise run smoke]
- AC5: MEMORY.md records the cutover [evidence: command:grep -q 'agents-orchestrator-db' MEMORY.md && grep -q 'smoke' MEMORY.md]

#### Files

- `MEMORY.md`

#### Interfaces

- Consumes every release of this epic; writes only MEMORY.md.

#### Expected outcome

The live namespace runs agents-orchestrator on agents-orchestrator-db (presets carried over), agents-webhook and agents-web on the new names; no drift; smoke green; the old database is untouched.

#### Steps

- Precondition probes (read-only), then "ready for step 2".
- Orchestrator steps 2 to 5 in order (design D7); after each, the implementer runs the probe that step names and reports it before the next.
- `mise run diff` (no drift), `mise run smoke` (exit 0), the MEMORY.md line.

#### Notes

- No TDD cycle applies: a deploy check plus one MEMORY.md line (doc edit exception).
- If a step fails, stop: the old database is the rollback point; never retry an apply blindly, read the helm error and report its tail.
- User step U1 (Keycloak client agents-orchestrator) must be done before; U2 (remove the old client) comes after a green smoke and is the user's.

- 2026-10-25 amended: review of webhook-session-columns: stop agents-webhook during the column-rename upgrade

- 2026-10-25 done: Preconditions 2026-10-25: (1) active clusters query on old DB printed 0, presets 2; (2) secret/agents-orchestrator-proxy exists (U1 via terraform MR !259); (3) helm show chart found agents-orchestrator 0.1.0-main.bba074f, agents-webhook 0.1.0-main.838ba1f, agents-web 0.1.0-main.5a8d6c8; (4) mise run diff (.logs/rename-prediff.log): only old app release removed, agents-orchestrator and agents-orchestrator-db added, agents-webhook and agents-web changed. agents-webhook scaled to 0 by the orchestrator before step 2 (option used); after step 4 agents_webhook events has session_id/session_slug (0005 applied). Imported DB: 2 presets, schema_migrations 0001-0005. Smoke OK after the any-mcp pin fix f1cba73 (.logs/rename-smoke2.log).

### S24: hibernate old orch db

- Status: done
- Files: `values/agent-orchestrator-db/common.yaml`, `tests/test_db_release.py`, `MEMORY.md`
- Verify: `uv run pytest -q tests/test_db_release.py && mise run lint && mise run diff && mise run smoke`
- Verified head: 0f96c62

#### Requirement

Hibernate the old orchestrator database instead of deleting it (design D6; gate Q3; constraint: prefer a design that never deletes live data). Paths are in code/agents-helmfile.

- `values/agent-orchestrator-db/common.yaml`: `cluster.annotations: {cnpg.io/hibernation: "on"}` and the scheduled backups removed (`backups.scheduledBackups: []`, existing S3 backups untouched); a comment: kept hibernated as the pre-rename copy, delete only on a user decision; remove the annotation to wake it.
- `tests/test_db_release.py` (test first): `test_old_db_hibernated` (the annotation is set and no scheduled backup is declared for the old cluster); the old release stays declared and installed.
- Apply (orchestrator): `mise run apply -- --selector name=agent-orchestrator-db`. Implementer: `kubectl -n agents get pods -l cnpg.io/cluster=agent-orchestrator-db-cluster` lists none, `kubectl -n agents get pvc agent-orchestrator-db-cluster-1 agent-orchestrator-db-cluster-1-wal` both Bound, `mise run diff` shows no drift, `mise run smoke` still exits 0.
- `MEMORY.md`: a dated line: old database hibernated (PVCs and S3 backups kept), how to wake it.

#### Acceptance conditions

- AC1: the old cluster is declared hibernated with no scheduled backups [evidence: test:tests/test_db_release.py::test_old_db_hibernated]
- AC2: the old PVCs are still bound and no old database pod runs [evidence: judgement:the task notes quote the kubectl get pods and get pvc output]
- AC3: no drift and the smoke still passes [evidence: command:mise run diff && mise run smoke]
- AC4: MEMORY.md records the hibernation [evidence: command:grep -q 'hibernat' MEMORY.md]

#### Files

- `values/agent-orchestrator-db/common.yaml`
- `tests/test_db_release.py`
- `MEMORY.md`

#### Interfaces

- Old release `agent-orchestrator-db` values: `cluster.annotations`, `backups.scheduledBackups`.

#### Expected outcome

The old CNPG cluster runs no pods, keeps its PVCs and S3 backups, and can be woken by removing one annotation.

#### Steps

- Red: write `test_old_db_hibernated`; it fails.
- Green: the values change; the verify's pytest and lint pass; the orchestrator applies the selector; the implementer quotes pods and PVCs, then `mise run diff` and `mise run smoke`.

#### Notes

- Deleting the old cluster is out of scope (design D6, Non-goals).
- Check with `helm show values cnpg/cluster --version 0.9.0` that `cluster.annotations` reaches the Cluster metadata; if not, end `blocked` with the chart's key list.

- 2026-10-25 done

## Files to delete

none recorded in the epic format

## Final verify

none recorded in the epic format

## After merge

none
