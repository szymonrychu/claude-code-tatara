# agents-schedule deploy implementation plan

## Agreed rung

Rung 1 of plan.md, migrated from the epic format: the steps are the epic's tasks.

## Approach

Migrated from the epic format: one step per task file, in dependency order, each with its status, files, verify, verified head and every body section.

## Chunk 1: migrated tasks (model: sonnet)

### S1: helmfile schedule db release

- Status: done
- Files: `helmfile.yaml.gotmpl`, `values/agents-schedule-db/common.yaml`, `tests/test_schedule_db_release.py`
- Verify: `uv run --frozen pytest -q -p no:cacheprovider tests/test_schedule_db_release.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: 0ccc7146051842687fc017cb39992bb8d9a6c264

#### Requirement

Add release `agents-schedule-db` (design D14; approval A6), the pattern of `agents-orchestrator-db` in `helmfile.yaml.gotmpl`: namespace `agents`, chart `cnpg/cluster` 0.9.0, `force: false`, timeout 600, labels `purpose: agents`, `application: agents-schedule`, values `values/common.yaml` and `values/agents-schedule-db/common.yaml` (one instance, storage as the orchestrator db, initdb database `schedule` owner `schedule`). The CNPG app Secret is `agents-schedule-db-cluster-app` with key `uri`.

#### Acceptance conditions

- AC1: the release is declared with the pinned chart and labels [evidence: test:tests/test_schedule_db_release.py::test_release_declared]
- AC2: initdb names the schedule database and owner [evidence: test:tests/test_schedule_db_release.py::test_initdb]
- AC3: helmfile lint passes [evidence: command:mise run lint]

#### Files

- `helmfile.yaml.gotmpl`
- `values/agents-schedule-db/common.yaml`
- `tests/test_schedule_db_release.py`

#### Interfaces

- Part `agents-schedule-db-release`: Secret `agents-schedule-db-cluster-app` key `uri` in namespace `agents`.

#### Expected outcome

Applying the helmfile creates the schedule database next to the orchestrator's.

#### Steps

- Write tests/test_schedule_db_release.py; run: fails.
- Add the release and values; the test passes.
- `mise run lint` clean.

#### Notes

- Creating a database is additive; nothing existing changes. Listed at the gate with the apply.

- 2026-10-25 amended: align to released agents-common v0.3.0 session names and the reuse rule

- 2026-10-25 done

### S2: schedule service token

- Status: done
- Files: `scripts/bootstrap-secrets.sh`, `tests/test_secrets.py`, `values/agents-schedule/default.secrets.yaml`, `values/agents-orchestrator/service-token-agents-schedule.secrets.yaml`, `.sops.yaml`
- Verify: `uv run --frozen pytest -q -p no:cacheprovider tests/test_secrets.py && shellcheck --severity=error scripts/bootstrap-secrets.sh && uv run ruff check .`
- Verified head: fd8696fbcee140c7bf2338ba83ca06101cfb442c

#### Requirement

Secrets for agents-schedule (design D14; approval A6), the same shape as agents-webhook task helmfile-service-token (contracts `orch-service-tokens`, `orch-services-service`). Paths are in code/agents-helmfile.

- `scripts/bootstrap-secrets.sh` gains `bootstrap_schedule`: when neither `values/agents-schedule/default.secrets.yaml` nor `values/agents-orchestrator/service-token-agents-schedule.secrets.yaml` exists, generate one service token (`openssl rand -hex 32`) and write, SOPS-encrypted through the existing `encrypt_to`:
  - `values/agents-schedule/default.secrets.yaml`: `orchestrator.token` (chart values shape of task helm-chart).
  - `values/agents-orchestrator/service-token-agents-schedule.secrets.yaml`: `serviceApi.tokenHashes.agents-schedule: <sha256 hex of the token>` (orchestrator chart values of `orch-services-service`).
  When both exist it does nothing; when exactly one exists it exits 1 naming both (never rotates, never half-writes). Values only travel through pipes, as the script's header requires.
- `.sops.yaml` covers the new paths if its rules do not already.
- `tests/test_secrets.py`: the new files are encrypted with the expected keys; the script is idempotent; one-of-two existing exits 1; the hash in the orchestrator file is the sha256 of the token in the schedule file (checked in-process the way the existing tests read encrypted files, never printed); no value printed.

#### Acceptance conditions

- AC1: the script writes both encrypted files with the token and its hash [evidence: test:tests/test_secrets.py::test_schedule_service_token_bootstrapped]
- AC2: a second run changes nothing and one-of-two existing exits 1 [evidence: test:tests/test_secrets.py::test_schedule_service_token_idempotent]
- AC3: no token value is printed [evidence: test:tests/test_secrets.py::test_schedule_service_token_not_printed]
- AC4: shellcheck passes [evidence: command:shellcheck --severity=error scripts/bootstrap-secrets.sh]

#### Files

- `scripts/bootstrap-secrets.sh`
- `tests/test_secrets.py`
- `values/agents-schedule/default.secrets.yaml`
- `values/agents-orchestrator/service-token-agents-schedule.secrets.yaml`
- `.sops.yaml`

#### Interfaces

- `values/agents-schedule/default.secrets.yaml` `orchestrator.token` and `values/agents-orchestrator/service-token-agents-schedule.secrets.yaml` `serviceApi.tokenHashes.agents-schedule` (part `agents-schedule-token-bootstrap`).

#### Expected outcome

One bootstrap run gives the schedule service a working orchestrator credential.

#### Steps

- Add the three tests to tests/test_secrets.py the way the existing secret tests run the script; they fail.
- Extend the script; they pass.
- shellcheck clean.

#### Notes

- The webhook epic adds its own pair of files the same way; the two stay independent. The orchestrator release picks up `service-token-*.secrets.yaml` per `orch-services-service`.

- 2026-10-25 amended: align to released agents-common v0.3.0 session names and the reuse rule

- 2026-10-25 done

### S3: smoke schedule check

- Status: done
- Files: `scripts/smoke.sh`, `tests/test_smoke_script.py`
- Verify: `uv run --frozen pytest -q -p no:cacheprovider tests/test_smoke_script.py && shellcheck --severity=error scripts/smoke.sh && uv run ruff check .`
- Verified head: 392e1a3fc3081afe922ff450e0c4660c1160f952

#### Requirement

Add a schedule step to `scripts/smoke.sh` (design D14; approvals A5, A6): port-forward `deploy/agents-schedule-api` (port 8000, like the orchestrator step), then: `GET /readyz` 200; `POST /schedules/api/v1/schedules` a disabled schedule `smoke-<ts>` on the default preset with cron `0 3 * * *`; `POST /schedules/preview` returns 3 times; `POST /schedules/{id}/run` 202; poll `GET /runs/{run_id}` until `in-progress` with a `session_id` (bounded by `SMOKE_TIMEOUT_S`); the cleanup trap deletes that session through the orchestrator API and the schedule through the schedule API, and prints the manual cleanup line when either is unreachable. tests/test_smoke_script.py extends the fake server with the schedule routes and asserts the step passes, fails on a run that goes `failed`, and cleans up.

#### Acceptance conditions

- AC1: the smoke step passes against the fake server [evidence: test:tests/test_smoke_script.py::test_schedule_step_passes]
- AC2: a failed run fails the smoke with its reason [evidence: test:tests/test_smoke_script.py::test_schedule_step_failed_run]
- AC3: the cleanup trap deletes the session and the schedule [evidence: test:tests/test_smoke_script.py::test_schedule_step_cleans_up]
- AC4: shellcheck passes [evidence: command:shellcheck --severity=error scripts/smoke.sh]

#### Files

- `scripts/smoke.sh`
- `tests/test_smoke_script.py`

#### Interfaces

- `scripts/smoke.sh` schedule step; parameters by env as the existing steps (part `agents-schedule-smoke`).

#### Expected outcome

`mise run smoke` covers the schedule service end to end with the real orchestrator.

#### Steps

- Add the three tests; they fail.
- Add the step and cleanup; they pass.
- shellcheck clean.

#### Notes

- The schedule is created disabled so it never fires on its own; only run-now starts a session.
- The orchestrator step's cleanup pattern (`cleanup` trap with manual line) is reused.

- 2026-10-25 amended: align to released agents-common v0.3.0 session names and the reuse rule
- Split 2026-10-25: depends_on `api-docs-and-openapi` stays satisfied by the epic blocker agents-schedule-microservice, which owns that task.

- 2026-10-25 done

### S4: web config schedules backend

- Status: done
- Files: `values/agents-web/common.yaml`, `tests/test_web_release.py`
- Verify: `uv run --frozen pytest -q -p no:cacheprovider tests/test_web_release.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: ead1cde61c9924f44d54f8d9c43bb85a209a48c0

#### Requirement

Add the `schedules` backend to the agents-web release values (design D12; approval A4) in the shape of `agents-web-backends-config` (chart value `backends`): `{id: schedules, label: Schedules, basePath: /schedules/api/v1}`. tests/test_web_release.py `test_schedules_backend_configured` asserts the entry next to the orchestrator one.

#### Acceptance conditions

- AC1: config.json values list the schedules backend after webhooks [evidence: test:tests/test_web_release.py::test_schedules_backend_configured]

#### Files

- `values/agents-web/common.yaml`
- `tests/test_web_release.py`

#### Interfaces

- agents-web `config.json` backend entry `schedules` (part `agents-web-schedules-config`).

#### Expected outcome

The live UI shows the Schedules entry once deployed.

#### Steps

- Add the test to tests/test_web_release.py; it fails.
- Add the values entry; it passes.
- Lint clean.

#### Notes

- `values/agents-web/common.yaml` and `tests/test_web_release.py` are created by frontend-decoupling; this task only adds the entry.

- 2026-10-25 done

### S5: web schedules api client

- Status: done
- Files: `openapi/schedules.json`, `openapi/schedules.source`, `scripts/sync-api.mjs`, `scripts/sync-api.test.mjs`, `package.json`, `src/api/schedules-schema.d.ts`, `src/schedules/api.ts`, `src/schedules/api.test.ts`
- Verify: `npm ci --no-audit --no-fund && node --test scripts/sync-api.test.mjs && npx vitest run src/schedules/api.test.ts && npm run check:api && npm run lint`
- Verified head: 10581e41777795dc1c87e1832e488881d897f0a3

#### Requirement

Add the schedule API client in agents-web (design D12; approval A4), following the frontend-decoupling contracts `agents-web-openapi-vendor` (vendored `openapi/<id>.json` plus `openapi/<id>.source` `<repo> <sha40>`, `npm run sync:api -- <backend-id> [--from <checkout>]`) and `agents-web-backends-config` (runtime `config.json` backends `{id, label, basePath}`, `src/config/backends.ts:backendBase(id)`, `isConfigured(id)`).

- `scripts/sync-api.mjs` maps backend id `schedules` to the `agents-schedule` repo (default `--from ../agents-schedule`); `scripts/sync-api.test.mjs` covers it.
- Run `npm run sync:api -- schedules` to vendor `openapi/schedules.json` and `openapi/schedules.source`; `package.json` `gen:api` and `check:api` also generate and check `src/api/schedules-schema.d.ts` from it.
- `src/schedules/api.ts`: base path `backendBase('schedules')` at call time (relative URL, never absolute); `listSchedules`, `getSchedule`, `createSchedule`, `updateSchedule`, `deleteSchedule`, `previewSchedule`, `runScheduleNow`, `listScheduleRuns`, `listRuns`, `getRun`; errors surface `{code, message}` from the error envelope; `schedulesEnabled()` is `isConfigured('schedules')`.

#### Acceptance conditions

- AC1: every client function calls the documented method and relative path under the configured base [evidence: command:npx vitest run src/schedules/api.test.ts -t 'routes']
- AC2: API errors surface code and message [evidence: command:npx vitest run src/schedules/api.test.ts -t 'errors']
- AC3: without a schedules backend the client reports disabled [evidence: command:npx vitest run src/schedules/api.test.ts -t 'disabled']
- AC4: sync:api knows the schedules backend [evidence: command:node --test scripts/sync-api.test.mjs]
- AC5: the vendored schema, its source line and the generated types agree [evidence: command:npm run check:api && grep -Eq '^agents-schedule [0-9a-f]{40}$' openapi/schedules.source]

#### Files

- `openapi/schedules.json`
- `openapi/schedules.source`
- `scripts/sync-api.mjs`
- `scripts/sync-api.test.mjs`
- `package.json`
- `src/api/schedules-schema.d.ts`
- `src/schedules/api.ts`
- `src/schedules/api.test.ts`

#### Interfaces

- `src/schedules/api.ts` exports above, typed from `src/api/schedules-schema.d.ts` (part `web-schedules-client`).

#### Expected outcome

The UI has a typed client for every schedule route, configured at runtime.

#### Steps

- Write src/schedules/api.test.ts and the sync-api case; both fail.
- Extend sync-api.mjs, run `npm run sync:api -- schedules --from ../agents-schedule`, write api.ts; the tests pass.
- `npm run lint` and `npm run check:api` clean.

#### Notes

- Layout per agents-webhook's `src/webhooks/api.ts` (contract `web-webhook-client`): one folder per backend.
- No CORS: the API is same-origin under its path prefix.
- Split 2026-10-25: depends_on `api-docs-and-openapi` stays satisfied by the epic blocker agents-schedule-microservice, which owns that task.

- 2026-10-25 done

### S6: helmfile schedule release

- Status: done
- Files: `helmfile.yaml.gotmpl`, `values/agents-schedule/common.yaml`, `tests/test_schedule_release.py`
- Verify: `uv run --frozen pytest -q -p no:cacheprovider tests/test_schedule_release.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: 0c4b1f67a5709610556cd185e2efe06ac658865b

#### Requirement

Add release `agents-schedule` (design D13, D14; approval A6): chart `oci://harbor.szymonrichert.pl/charts/agents-schedule` (version pinned by `deploy-schedule`; `0.1.0` here), `needs: [agents/agents-schedule-db]`, labels as the db. `values/agents-schedule/common.yaml`:

- `postgres.existingSecret: agents-schedule-db-cluster-app`, `existingSecretKey: uri`.
- `orchestrator.url: http://agents-orchestrator-services:8002` (the orchestrator's service port, contract `orch-services-service`); `orchestrator.token` comes from SOPS `values/agents-schedule/default.secrets.yaml` (task schedule-service-token).
- `env.SCHED_ALLOWED_CIDRS: 127.0.0.1/32` (only the sidecar).
- `components.api.podAnnotations`: the oauth2-proxy injector annotations with the shared secret `agents-orchestrator-proxy` (as `values/agents-orchestrator/common.yaml`).
- `ingress`: host `lab.szymonrichert.pl`, path `/schedules` Prefix, TLS secret `agents-orchestrator-tls`, no cert-manager annotation (contract `agents-web-url-layout`), the node-IP `denySourceRanges` the orchestrator uses.

#### Acceptance conditions

- AC1: the release needs the db release and pins the OCI chart [evidence: test:tests/test_schedule_release.py::test_release_declared]
- AC2: database and orchestrator token come from their Secrets and the URL is the service port [evidence: test:tests/test_schedule_release.py::test_secrets_wired]
- AC3: the ingress routes /schedules on the lab host with the shared TLS secret and no cert-manager annotation [evidence: test:tests/test_schedule_release.py::test_ingress_path]
- AC4: the api pod carries the SSO annotations and the allowlist admits only the sidecar [evidence: test:tests/test_schedule_release.py::test_sso_and_allowlist]

#### Files

- `helmfile.yaml.gotmpl`
- `values/agents-schedule/common.yaml`
- `tests/test_schedule_release.py`

#### Interfaces

- Release `agents-schedule` values (part `agents-schedule-release-values`).

#### Expected outcome

The schedule service is declared behind the shared SSO under `/schedules` on the lab host.

#### Steps

- Write tests/test_schedule_release.py; run: fails.
- Add the release and values; the test passes.
- `mise run lint` clean.

#### Notes

- Never the orchestrator's port 8000 (403 from its CIDR allowlist); port 8002 takes bearer service tokens (`orch-service-tokens`).

- 2026-10-25 amended: align to released agents-common v0.3.0 session names and the reuse rule
- Split 2026-10-25: depends_on `chart-ingress-and-test-hook` stays satisfied by the epic blocker agents-schedule-microservice, which owns that task.

- 2026-10-26 done

### S7: web schedule form

- Status: done
- Files: `src/schedules/ScheduleForm.tsx`, `src/schedules/ScheduleForm.test.tsx`
- Verify: `npm ci --no-audit --no-fund && npx vitest run src/schedules/ScheduleForm.test.tsx && npm run lint`
- Verified head: 79d015f10dbd55c935c064e6ff015a99060252c7

#### Requirement

Add `ScheduleForm` (design D4, D7, D12; approvals A2, A4) on the trigger UI kit agents-webhook-microservice puts in agents-web (contract `trigger-ui-page-pattern`, `src/triggers/index.ts`: `PresetSelect`, `RunStatusChip`, `usePoll`).

- Fields: name, cron (5 fields, with a one-line syntax hint), timezone (select over `Intl.supportedValuesOf('timeZone')`, default `Europe/Warsaw`), preset (`PresetSelect` over the orchestrator's `GET /api/v1/presets`), prompt (textarea, hint naming `{schedule_name}` and `{fired_at}`), enabled.
- Live preview: on cron or timezone change (debounced 300 ms) calls `previewSchedule` and lists the next 3 fire times in the chosen zone; a 422 shows the server's reason under the cron or timezone field.
- Save calls create or update; server errors (422 codes, 409 name conflict) appear on the matching field; success calls `onSaved(schedule)`.

#### Acceptance conditions

- AC1: the form shows the next 3 fire times for a valid cron and the reason for an invalid one [evidence: command:npx vitest run src/schedules/ScheduleForm.test.tsx -t 'preview']
- AC2: timezone defaults to Europe/Warsaw and presets come from the orchestrator [evidence: command:npx vitest run src/schedules/ScheduleForm.test.tsx -t 'defaults']
- AC3: server validation errors land on their fields [evidence: command:npx vitest run src/schedules/ScheduleForm.test.tsx -t 'errors']
- AC4: save creates or updates and reports the saved schedule [evidence: command:npx vitest run src/schedules/ScheduleForm.test.tsx -t 'save']

#### Files

- `src/schedules/ScheduleForm.tsx`
- `src/schedules/ScheduleForm.test.tsx`

#### Interfaces

- `ScheduleForm({schedule?: ScheduleView, onSaved, onCancel})` (part `web-schedule-form`).

#### Expected outcome

Schedules are created and edited in the UI with a preview of when they fire.

#### Steps

- Write ScheduleForm.test.tsx; `npx vitest run src/schedules/ScheduleForm.test.tsx` fails.
- Write ScheduleForm.tsx; the test passes.
- `npm run lint` clean.

#### Notes

- Reuse `PresetSelect` from the kit; do not write another preset picker.

- 2026-10-26 done

### S8: web schedule runs list

- Status: done
- Files: `src/schedules/ScheduleRuns.tsx`, `src/schedules/ScheduleRuns.test.tsx`
- Verify: `npm ci --no-audit --no-fund && npx vitest run src/schedules/ScheduleRuns.test.tsx && npm run lint`
- Verified head: 31166c920afe01eca9ea3d971264731a1a4ebc00

#### Requirement

Add `ScheduleRuns` (design D12; approval A4): the last 20 runs of one schedule (`listScheduleRuns`), newest first, each with fire time in the schedule's zone, trigger (scheduled or manual), `RunStatusChip` from the trigger UI kit (contract `trigger-ui-page-pattern`), the reason when present, and a link to the session in the orchestrator view when `session_id` is set. Refreshes with `usePoll` every 10 s while mounted and on `refreshKey` change.

#### Acceptance conditions

- AC1: runs render newest first with status, trigger and reason [evidence: command:npx vitest run src/schedules/ScheduleRuns.test.tsx -t 'renders']
- AC2: a run with a session links to that session [evidence: command:npx vitest run src/schedules/ScheduleRuns.test.tsx -t 'session link']
- AC3: the list refreshes on its interval and on refreshKey [evidence: command:npx vitest run src/schedules/ScheduleRuns.test.tsx -t 'refresh']

#### Files

- `src/schedules/ScheduleRuns.tsx`
- `src/schedules/ScheduleRuns.test.tsx`

#### Interfaces

- `ScheduleRuns({scheduleId, timezone, refreshKey})` (part `web-schedule-runs`).

#### Expected outcome

Run history and session links are visible per schedule.

#### Steps

- Write ScheduleRuns.test.tsx; it fails.
- Write ScheduleRuns.tsx; it passes.
- `npm run lint` clean.

#### Notes

- The session link uses the session view route agents-web already has for the orchestrator.

- 2026-10-25 amended: align to released agents-common v0.3.0 session names and the reuse rule

- 2026-10-26 done

### S9: web schedules page

- Status: done
- Files: `src/schedules/SchedulesPage.tsx`, `src/schedules/SchedulesPage.test.tsx`
- Verify: `npm ci --no-audit --no-fund && npx vitest run src/schedules/SchedulesPage.test.tsx && npm run lint`
- Verified head: c8fb37f17022a103f76c0183c9b88ea9bfa4d6f0

#### Requirement

Add `SchedulesPage` (design D12; approvals A2, A4, gate Q6): a list of schedules (name, cron, timezone, preset name, next fire time, last run status) with per-row controls: enable/disable toggle (PUT with `enabled` flipped), Run now (POST run; the new run appears in its runs list), Edit (opens `ScheduleForm`), Delete (confirm dialog, then DELETE). A New schedule button opens an empty form. Expanding a row shows `ScheduleRuns`. Errors show the server's message. Empty state explains what a schedule does.

#### Acceptance conditions

- AC1: the page lists schedules with next fire time and last run status [evidence: command:npx vitest run src/schedules/SchedulesPage.test.tsx -t 'lists']
- AC2: enable/disable and run now call the API and refresh the row [evidence: command:npx vitest run src/schedules/SchedulesPage.test.tsx -t 'controls']
- AC3: delete asks for confirmation before calling the API [evidence: command:npx vitest run src/schedules/SchedulesPage.test.tsx -t 'delete']
- AC4: new and edit open the form and the list updates on save [evidence: command:npx vitest run src/schedules/SchedulesPage.test.tsx -t 'form']

#### Files

- `src/schedules/SchedulesPage.tsx`
- `src/schedules/SchedulesPage.test.tsx`

#### Interfaces

- `SchedulesPage({onBack})` (part `web-schedules-page`); `onBack` comes from the registry `render(onBack)`.

#### Expected outcome

Schedules are fully managed from one page.

#### Steps

- Write SchedulesPage.test.tsx; it fails.
- Write SchedulesPage.tsx; it passes.
- `npm run lint` clean.

#### Notes

- Mirror the webhook pages' layout (contract `trigger-ui-page-pattern`) so both trigger pages look alike.

- 2026-10-26 done

### S10: web schedules menu entry

- Status: done
- Files: `src/schedules/menu.ts`, `src/backends/registry.ts`, `src/backends/registry.test.ts`
- Verify: `npm ci --no-audit --no-fund && npx vitest run src/backends/registry.test.ts src/App.test.tsx && npm run lint`
- Verified head: 41e62491e04f53d3bea7de396df81f8315ec57bc

#### Requirement

Register the Schedules entry (design D12; approval A4, gate Q7) in the frontend-decoupling backend registry (contract `agents-web-backend-registry`, `src/backends/registry.ts`; order rule `web-settings-menu-order` of configuration-improvements): `src/schedules/menu.ts` exports `schedulesMenu: MenuEntry = {id: 'schedules', label: 'Schedules', order: 30, backend: 'schedules', render: (onBack) => createElement(SchedulesPage, {onBack})}` (a `.ts` file, so no JSX), and `src/backends/registry.ts` sets `BACKEND_MENUS.schedules = [schedulesMenu]` (the agents-webhook web-webhook-menu-entry shape). `src/App.test.tsx` stays green. Order 30 is the slot the registry reserves for Schedules, between Webhooks (20) and Presets (40), giving Sessions, Webhooks, Schedules, Presets (gate Q7). The entry appears only when `config.json` lists the `schedules` backend.

#### Acceptance conditions

- AC1: with the schedules backend configured, Schedules sorts after Webhooks and before Presets [evidence: command:npx vitest run src/backends/registry.test.ts -t 'schedules order']
- AC2: without the schedules backend there is no Schedules entry [evidence: command:npx vitest run src/backends/registry.test.ts -t 'schedules hidden']
- AC3: the entry renders the schedules page [evidence: command:npx vitest run src/backends/registry.test.ts -t 'schedules render']

#### Files

- `src/schedules/menu.ts`
- `src/backends/registry.ts`
- `src/backends/registry.test.ts`

#### Interfaces

- `src/schedules/menu.ts:schedulesMenu`, `BACKEND_MENUS.schedules` in `src/backends/registry.ts` (part `web-schedules-menu`).

#### Expected outcome

The schedules UI lives in the hamburger menu.

#### Steps

- Add the three tests to src/backends/registry.test.ts; they fail.
- Register the entry; they pass.
- `npm run lint` clean.

#### Notes

- `SchedulesPage` accepts `onBack` per the registry's `render(onBack)`.

- 2026-10-25 amended: align to released agents-common v0.3.0 session names and the reuse rule

- 2026-10-26 done

### S11: deploy schedule

- Status: done
- Files: `helmfile.yaml.gotmpl`, `values/agents-schedule/common.yaml`, `values/agents-web/common.yaml`, `tests/test_schedule_release.py`, `tests/test_web_release.py`
- Verify: `uv run --frozen pytest -q -p no:cacheprovider tests/test_schedule_release.py tests/test_web_release.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: e16b726474aeac2a4d8521562fdc560006eecbf1

#### Requirement

Release and deploy this epic (design D14; approval A6). Pin release `agents-schedule` to chart `0.1.0` and `image.tag` to the sha7 of tag v0.1.0; pin the agents-web release to the main build that contains this epic's UI (chart `0.1.0-main.<sha7>` and image `<sha7>`, contracts `agents-web-chart` and `agents-web-image`). tests assert each chart version and image tag agree on their sha (offline, text read). Then run `bash scripts/bootstrap-secrets.sh` (schedule token), `mise run diff` (only the new releases and the agents-web pin change), `mise run apply` and `mise run smoke` against the expected kube context.

#### Acceptance conditions

- AC1: the schedule chart and image pins agree on the v0.1.0 sha [evidence: test:tests/test_schedule_release.py::test_schedule_pin_matches_release]
- AC2: the agents-web chart and image pins agree on one sha [evidence: test:tests/test_web_release.py::test_web_pin_matches_image]
- AC3: helmfile apply of the agents namespace succeeds [evidence: judgement:the apply output (helm revision and chart) quoted in the task notes; never run apply as AC evidence]
- AC4: the live smoke passes, including the schedule step [evidence: command:mise run smoke]
- AC5: the diff shows only the new schedule releases and the agents-web pin [evidence: judgement:the task diff and mise run diff output reviewed]

#### Files

- `helmfile.yaml.gotmpl`
- `values/agents-schedule/common.yaml`
- `values/agents-web/common.yaml`
- `tests/test_schedule_release.py`
- `tests/test_web_release.py`

#### Interfaces

- Consumes chart `oci://harbor.szymonrichert.pl/charts/agents-schedule` 0.1.0 and image `harbor.szymonrichert.pl/containers/agents-schedule:<sha7>` (contracts `agents-schedule-chart`, `agents-schedule-image`), and the agents-web main build.

#### Expected outcome

The schedule service and the UI with its Schedules entry run live and the smoke is green.

#### Steps

- Update the pin tests to the new shas; they fail.
- Change the pins; the verify passes.
- `bash scripts/bootstrap-secrets.sh`, `mise run diff`, `mise run apply`, `mise run smoke`: each exits 0.

#### Notes

- Runs after the agents-schedule and agents-web merges reach main; the shas are filled with `ticket.py amend` then (precedent `docs/plans/done/cluster-presets/tasks/deploy-pin-presets.md`, frontend-decoupling `deploy-pin-web`).
- `mise run apply` is guarded by lint, test and the kube-context check (`EXPECTED_KUBE_CONTEXT`).
- The orchestrator already runs the agents-webhook-microservice build with the service port; this task does not touch the orchestrator release.
- Split 2026-10-25: depends_on `release-v0-1-0` stays satisfied by the epic blocker agents-schedule-microservice, which owns that task.

- 2026-10-26 done: Applied by the main session at e16b726: agents-schedule rev 1 (chart 0.1.0), agents-schedule-db rev 1 (cnpg/cluster 0.9.0), agents-web rev 8 (0.1.0-main.586344d), agents-orchestrator rev 2 (services Secret token hash). First smoke 503 (orchestrator 401: api pods not restarted on services Secret change); after kubectl rollout restart deploy/agents-orchestrator-api, smoke: OK (.logs/sched-deploy-smoke2.log). Root fix tracked by the main session in agents-orchestrator.

## Files to delete

none recorded in the epic format

## Final verify

none recorded in the epic format

## After merge

none
