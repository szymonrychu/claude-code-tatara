# agents matrix connector deploy implementation plan

## Agreed rung

Rung 1 of plan.md, migrated from the epic format: the steps are the epic's tasks.

## Approach

Migrated from the epic format: one step per task file, in dependency order, each with its status, files, verify, verified head and every body section.

## Chunk 1: migrated tasks (model: sonnet)

### S1: helmfile matrix secrets

- Status: done
- Files: `scripts/bootstrap-secrets.sh`, `tests/test_secrets.py`, `values/agents-matrix-connector/default.secrets.yaml`, `values/agents-orchestrator/service-token-agents-matrix-connector.secrets.yaml`, `.sops.yaml`
- Verify: `uv run --frozen pytest -q -p no:cacheprovider tests/test_secrets.py && shellcheck --severity=error scripts/bootstrap-secrets.sh && uv run ruff check .`
- Verified head: f09b2a46b8f0b8bc0d6b7f49075e20391d6db70a

#### Requirement

Secrets for the connector (design D2, D13, revision R1). Paths are in code/agents-helmfile.

Precondition, checked first: Secret `hermes-agent-matrix` in namespace `ai` has a non-empty key `MATRIX_ACCESS_TOKEN` (read-only kubectl, never printed) and `GET /_matrix/client/v3/account/whoami` with it answers `@hermes:szymonrichert.pl` (the token only through a file or a pipe; only the returned user id is shown). Otherwise end `blocked`, whoCanClear "user: Secret ai/hermes-agent-matrix has no working MATRIX_ACCESS_TOKEN".

- `scripts/bootstrap-secrets.sh` gains `bootstrap_matrix_connector`: when neither `values/agents-matrix-connector/default.secrets.yaml` nor `values/agents-orchestrator/service-token-agents-matrix-connector.secrets.yaml` exists, it requires `MATRIX_CONNECTOR_TOKEN_FILE` (path to a file holding the Matrix access token; missing or empty exits 1 naming the variable), generates one service token (`openssl rand -hex 32`) and writes, SOPS-encrypted through the existing `encrypt_to`:
  - `values/agents-matrix-connector/default.secrets.yaml`: `orchestrator.token` and `matrix.accessToken` (chart values of task mxc-chart-workloads).
  - `values/agents-orchestrator/service-token-agents-matrix-connector.secrets.yaml`: `serviceApi.tokenHashes.agents-matrix-connector: <sha256 hex of the service token>` (contract `orch-service-tokens`).
  When both exist it does nothing; when exactly one exists it exits 1 naming both (never rotates, never half-writes). Values only travel through pipes and files, as the script's header requires; nothing is printed.
- Pipe Secret `ai/hermes-agent-matrix` key `MATRIX_ACCESS_TOKEN` into a mode-600 file under `/Users/szymonri/Documents/claude-code-tatara/.scratchpad/agents-matrix-connector/` (never printed), run the script with `MATRIX_CONNECTOR_TOKEN_FILE` set to it, delete the file afterwards, writing the two files; `.sops.yaml` covers the new paths if its rules do not already.
- `tests/test_secrets.py`: the new files are SOPS-encrypted with the expected keys; the orchestrator hash is the sha256 of the connector's service token (checked in-process as the existing tests read encrypted files, never printed); re-running never rotates; one-of-two exits 1; a missing token file exits 1; no value is printed.

User request 2026-10-25, verbatim: 'agents-matrix-connector New microservice- is meant to connect with existing matrix deployment and allow for talking to agents through facebook. Must support user/chat/room auto discovery and white/blacklosting. Hermes already uses working bridge.'

#### Acceptance conditions

- AC1: the two secret files exist, are SOPS-encrypted and hold the expected keys [evidence: test:tests/test_secrets.py::test_matrix_connector_secrets_encrypted_with_expected_keys]
- AC2: the orchestrator hash matches the connector's service token [evidence: test:tests/test_secrets.py::test_matrix_connector_token_hash_matches]
- AC3: re-running never rotates, a half-present pair exits 1 and a missing token file exits 1 [evidence: test:tests/test_secrets.py::test_matrix_connector_secrets_never_rotate]
- AC4: the script never prints a value, and shellcheck and lint pass [evidence: command:uv run --frozen pytest -q -p no:cacheprovider tests/test_secrets.py -k never_prints && shellcheck --severity=error scripts/bootstrap-secrets.sh && uv run ruff check .]

#### Files

- `scripts/bootstrap-secrets.sh`
- `tests/test_secrets.py`
- `values/agents-matrix-connector/default.secrets.yaml`
- `values/agents-orchestrator/service-token-agents-matrix-connector.secrets.yaml`
- `.sops.yaml`

#### Interfaces

- `values/agents-matrix-connector/default.secrets.yaml` (`orchestrator.token`, `matrix.accessToken`), read by the release of helmfile-matrix-releases through the `values/{{ .Release.Name }}/default.secrets.yaml` convention.
- `values/agents-orchestrator/service-token-agents-matrix-connector.secrets.yaml`, wired into the agents-orchestrator release by helmfile-matrix-releases.

#### Expected outcome

Both files are committed encrypted; the orchestrator will accept the connector's bearer token on port 8002 after the apply.

#### Steps

- Red: extend `tests/test_secrets.py` with the four tests (a temp token file for the script tests). Fails: no bootstrap function, no files.
- Green: write `bootstrap_matrix_connector`, run it with the real U2 file, commit the encrypted files. Run the verify.

#### Notes

- Same shape as agents-webhook-microservice task helmfile-service-token (`bootstrap_webhook`).
- After this task is done the orchestrator deletes the U2 token file (design U2).
- The values dir is `values/agents-orchestrator/` after orchestrator-rename-sessions (design D15).

- 2026-10-25 amended: revision R1 (user 2026-10-25): the connector takes over Hermes' Matrix user and Facebook account, Hermes scaled to 0; only the Hermes home-channel owner DM is allowed

- 2026-10-26 done

### S2: web matrix api client

- Status: done
- Files: `openapi/matrix.json`, `openapi/matrix.source`, `scripts/sync-api.mjs`, `scripts/sync-api.test.mjs`, `package.json`, `src/api/matrix-schema.d.ts`, `src/matrix/api.ts`, `src/matrix/api.test.ts`
- Verify: `npm ci --no-audit --no-fund && node --test scripts/sync-api.test.mjs && npx vitest run src/matrix/api.test.ts && npm run check:api && npm run lint`
- Verified head: e679002beb6fb5e1d769896760d972ffa00f11a2

#### Requirement

Vendor the connector API and write its client (design D11, D12; contract `agents-web-openapi-vendor`). Paths are in code/agents-web.

- `scripts/sync-api.mjs`: backend id `matrix` maps to the `agents-matrix-connector` repo (default `--from ../agents-matrix-connector`); `scripts/sync-api.test.mjs` covers it.
- `openapi/matrix.json` and `openapi/matrix.source` (`agents-matrix-connector <sha40>`) from `npm run sync:api -- matrix` against the agents-matrix-connector checkout of this epic.
- `package.json`: `gen:api` and `check:api` also generate and check `src/api/matrix-schema.d.ts` from `openapi/matrix.json`.
- `src/matrix/api.ts`: functions over the `matrix` backend's `basePath` from the runtime config (never an absolute URL), typed from `matrix-schema.d.ts`: `getMeta()`, `listRooms({kind?, access?})`, `getRoom(roomId)`, `setRoomSettings(roomId, {preset_id, trigger})`, `listRoomMessages(roomId, {limit?, beforeId?})`, `listUsers({q?, limit?})`, `listRules()`, `addRule({list, kind, value, note?})`, `deleteRule(id)`, `getSettings()`, `setSettings({default_preset_id})`, `listMessages({status?, roomId?, limit?, beforeId?})`; room ids are URL-encoded in paths; errors surface the backend's `{error: {code, message}}`.
- `src/matrix/api.test.ts`: each call hits the right method, path (encoded room id), query and body; errors parse.

User request 2026-10-25, verbatim: 'agents-matrix-connector New microservice- is meant to connect with existing matrix deployment and allow for talking to agents through facebook. Must support user/chat/room auto discovery and white/blacklosting. Hermes already uses working bridge.'

#### Acceptance conditions

- AC1: sync-api maps the matrix backend to the agents-matrix-connector repo [evidence: command:node --test scripts/sync-api.test.mjs]
- AC2: every client call hits the matrix basePath with the right method, encoded path, query and body [evidence: command:npx vitest run src/matrix/api.test.ts -t "calls the matrix API under the configured basePath"]
- AC3: backend errors surface their code and message [evidence: command:npx vitest run src/matrix/api.test.ts -t "surfaces backend error codes"]
- AC4: the generated schema matches the vendored openapi and lint passes [evidence: command:npm run check:api && npm run lint]

#### Files

- `openapi/matrix.json`
- `openapi/matrix.source`
- `scripts/sync-api.mjs`
- `scripts/sync-api.test.mjs`
- `package.json`
- `src/api/matrix-schema.d.ts`
- `src/matrix/api.ts`
- `src/matrix/api.test.ts`

#### Interfaces

- `src/matrix/api.ts` (used by web-chats-rooms-page and web-chats-access-panels); `openapi/matrix.json` vendored from contract `matrix-connector-api`.

#### Expected outcome

The UI can call every connector route with generated types.

#### Steps

- Red: extend `scripts/sync-api.test.mjs`; write `src/matrix/api.test.ts` (describe/it names as in the ACs). Both fail.
- Green: map the backend, vendor the schema, generate types, write `api.ts`. Run the verify.

#### Notes

- Same shape as agents-webhook-microservice task web-webhook-api-client and `src/webhooks/api.ts`.
- 2026-10-25 split: depends_on mxc-openapi-and-readme live in epic agents-matrix-connector; that epic is a blocker of this one, so they are done before this task runs.

- 2026-10-26 done

### S3: helmfile matrix releases

- Status: done
- Files: `helmfile.yaml.gotmpl`, `values/agents-matrix-connector/common.yaml`, `values/agents-matrix-connector-db/common.yaml`, `tests/test_matrix_connector_release.py`
- Verify: `uv run --frozen pytest -q -p no:cacheprovider tests/test_matrix_connector_release.py -k "not helmfile_build" && uv run ruff check . && uv run ruff format --check .`
- Verified head: 20589c35949fe4779fe943118de4eb569919acf5

#### Requirement

The release pair for the connector (design D13, D15, revision R1). Paths are in code/agents-helmfile.

Preconditions, checked first: (a) this epic's agents-matrix-connector PR is merged to main and chart `oci://harbor.szymonrichert.pl/charts/agents-matrix-connector` `0.1.0-main.<sha7>` and image `<sha7>` exist (the orchestrator amends `<sha7>` in); otherwise end `blocked`, whoCanClear "orchestrator: merge the agents-matrix-connector PR and wait for its main CI". (b) Hermes runs 0 replicas (read-only `kubectl -n ai get deploy hermes-agent`, after the infrastructure helmfile MR that scales Hermes to 0 is merged); otherwise end `blocked`, whoCanClear "orchestrator: merge the Hermes scale-to-0 MR in the infrastructure helmfile".

- `helmfile.yaml.gotmpl`: `agents-matrix-connector-db` (`cnpg/cluster`, the version and options of `agents-webhook-db`) and `agents-matrix-connector` (OCI chart pinned `0.1.0-main.<sha7>`, `needs: [agents/agents-matrix-connector-db, agents/agents-orchestrator]`), namespace `agents`, labels `application: agents-matrix-connector`; the agents-orchestrator release's values gain `values/agents-orchestrator/service-token-agents-matrix-connector.secrets.yaml`.
- `values/agents-matrix-connector-db/common.yaml`: initdb database and owner `agents_matrix_connector`, storage and backups as `agents-webhook-db` with its own backup path.
- `values/agents-matrix-connector/common.yaml`: `image.tag <sha7>`; `postgres.existingSecret: agents-matrix-connector-db-cluster-app`, key `uri`; `orchestrator.url: http://agents-orchestrator-services:8002`; `matrix.homeserverUrl: http://matrix-synapse.messaging.svc.cluster.local:8008`; `matrix.userId: "@hermes:szymonrichert.pl"`; `matrix.deviceId: hermes-agent`; `matrix.selfIdentities: ["@facebook_61594633049360:szymonrichert.pl"]`; `matrix.bridgeBots: ["@facebookbot:szymonrichert.pl"]`; `policy.default: deny`; `components.api.podAnnotations`: the same oauth2-proxy annotations as the agents-webhook api; `components.bot.podAnnotations: {}`; `ingress`: enabled, host `lab.szymonrichert.pl`, the shared TLS secret the agents-webhook api ingress uses, no cert-manager annotation, the same node-IP `denySourceRanges` as the agents-webhook api ingress.
- `tests/test_matrix_connector_release.py` (offline, reading the layered values as the existing release tests do): pins agree; the DB secret name matches the CNPG release; SSO annotations on the api pod only; the orchestrator URL is the services Service; the homeserver URL, user id, self identities and bridge bots are set; the policy is deny; the ingress host, TLS secret and source ranges match the agents-webhook api's; the orchestrator release reads the connector's token-hash file; no plaintext secret in common values; a test that needs `helmfile build` is named `test_*_helmfile_build`.

User request 2026-10-25, verbatim: 'agents-matrix-connector New microservice- is meant to connect with existing matrix deployment and allow for talking to agents through facebook. Must support user/chat/room auto discovery and white/blacklosting. Hermes already uses working bridge.'

#### Acceptance conditions

- AC1: the connector and its database are declared with the pinned chart and needs [evidence: test:tests/test_matrix_connector_release.py::test_matrix_connector_pin_and_needs]
- AC2: database, orchestrator and homeserver wiring, the bot identity and default deny are set [evidence: test:tests/test_matrix_connector_release.py::test_wiring_identity_and_policy]
- AC3: SSO annotations are on the api pod only and the ingress matches the webhook api's host, TLS and source ranges [evidence: test:tests/test_matrix_connector_release.py::test_sso_and_ingress]
- AC4: the orchestrator release reads the connector's token-hash file and no plaintext secret is in common values [evidence: test:tests/test_matrix_connector_release.py::test_token_hash_wired_and_no_plaintext]
- AC5: the offline release tests and lint pass [evidence: command:uv run --frozen pytest -q -p no:cacheprovider tests/test_matrix_connector_release.py -k "not helmfile_build" && uv run ruff check . && uv run ruff format --check .]

#### Files

- `helmfile.yaml.gotmpl`
- `values/agents-matrix-connector/common.yaml`
- `values/agents-matrix-connector-db/common.yaml`
- `tests/test_matrix_connector_release.py`

#### Interfaces

- Consumes contracts `agents-matrix-connector-chart`, `agents-matrix-connector-image`, `matrix-connector-settings-env`, `orch-service-tokens`, `orch-services-service`.

#### Expected outcome

`mise run diff` (run later by apply-smoke-matrix) shows the two new releases and the orchestrator's added token hash.

#### Steps

- Red: `tests/test_matrix_connector_release.py` with the four tests. Fails: no releases.
- Green: edit the helmfile and write the values. Run the verify.

#### Notes

- Same shape as agents-webhook-microservice task helmfile-webhook-releases; copy the oauth2-proxy annotations and source ranges from `values/agents-webhook/common.yaml` rather than retyping them.
- No NetworkPolicy exists in `agents` or `messaging` (probed 2026-10-25); none is added.
- 2026-10-25 split: depends_on mxc-dockerfile-and-ci, mxc-chart-network, mxc-e2e-api, mxc-operations-docs live in epic agents-matrix-connector; that epic is a blocker of this one, so they are done before this task runs.

- 2026-10-25 amended: revision R1 (user 2026-10-25): the connector takes over Hermes' Matrix user and Facebook account, Hermes scaled to 0; only the Hermes home-channel owner DM is allowed

- 2026-10-26 done

### S4: web chats rooms page

- Status: done
- Files: `src/matrix/ChatsPage.tsx`, `src/matrix/RoomsTable.tsx`, `src/matrix/RoomDrawer.tsx`, `src/matrix/RoomMessages.tsx`, `src/matrix/ChatsPage.test.tsx`
- Verify: `npm ci --no-audit --no-fund && npx vitest run src/matrix/ChatsPage.test.tsx && npm run lint`
- Verified head: 5fd77da5edd2960557ecd9e38e052204a932fb30

#### Requirement

The Chats page: rooms table, room drawer and recent messages (design D12). Paths are in code/agents-web.

- `src/matrix/ChatsPage.tsx`: `ChatsPage({onBack, onOpenSession})` with a header showing the bot user id and sync health from `getMeta()` (a warning when `sync.healthy` is false) and a Rooms section; polls rooms every 5 s with `usePoll` (trigger UI kit).
- `src/matrix/RoomsTable.tsx`: columns name, kind (DM, Group, Matrix, Infrastructure), flags (message request, encrypted), members, access chip (allowed, denied, default with the reason), preset name, effective trigger, session slug (clicking calls `onOpenSession(sessionId)`), last activity, queued; a kind filter and an access filter; a row click opens the drawer.
- `src/matrix/RoomDrawer.tsx`: members (display name, Matrix id, Facebook id, access chip); preset (`PresetSelect`, with "Default preset" as the empty choice) and trigger (Default, All messages, Only when mentioned) saved through `setRoomSettings` with `FormError` on 422; Allow room and Deny room buttons (`addRule` with kind `room`), disabled for infrastructure and encrypted rooms, each after a `ConfirmDialog`; when a room rule exists, a Remove rule action instead.
- `src/matrix/RoomMessages.tsx`: the room's recent messages (`listRoomMessages`, polled every 5 s while the drawer is open): direction, time, sender name, body (or "not stored" when the body is null), status via `RunStatusChip` and reason; Load older through `beforeId`.
- `src/matrix/ChatsPage.test.tsx`: the table renders rooms with their access and session; filters work; the drawer saves preset and trigger and shows a 422 message; Allow and Deny create the right rule after confirming and are disabled for encrypted and infrastructure rooms; messages render including "not stored".

User request 2026-10-25, verbatim: 'agents-matrix-connector New microservice- is meant to connect with existing matrix deployment and allow for talking to agents through facebook. Must support user/chat/room auto discovery and white/blacklosting. Hermes already uses working bridge.'

#### Acceptance conditions

- AC1: the rooms table shows kind, flags, access, preset, trigger, session and queued, and filters by kind and access [evidence: command:npx vitest run src/matrix/ChatsPage.test.tsx -t "lists rooms with access and session"]
- AC2: the drawer saves the preset and trigger and shows a 422 error [evidence: command:npx vitest run src/matrix/ChatsPage.test.tsx -t "saves room settings"]
- AC3: Allow room and Deny room create the room rule after a confirm and are disabled for encrypted and infrastructure rooms [evidence: command:npx vitest run src/matrix/ChatsPage.test.tsx -t "allows and denies a room"]
- AC4: recent messages show both directions, status and reason, and "not stored" for a null body [evidence: command:npx vitest run src/matrix/ChatsPage.test.tsx -t "shows recent messages"]
- AC5: the header warns when sync is unhealthy [evidence: command:npx vitest run src/matrix/ChatsPage.test.tsx -t "warns on unhealthy sync"]
- AC6: lint passes [evidence: command:npm run lint]

#### Files

- `src/matrix/ChatsPage.tsx`
- `src/matrix/RoomsTable.tsx`
- `src/matrix/RoomDrawer.tsx`
- `src/matrix/RoomMessages.tsx`
- `src/matrix/ChatsPage.test.tsx`

#### Interfaces

- `src/matrix/ChatsPage.tsx`: `ChatsPage({onBack, onOpenSession})`, extended by web-chats-access-panels and rendered by web-chats-menu-entry.
- Uses `src/triggers/index.ts` (`usePoll`, `PresetSelect`, `RunStatusChip`, `FormError`; contract `trigger-ui-page-pattern`) and `src/layout/ConfirmDialog.tsx`.

#### Expected outcome

An operator sees every discovered chat, opens one, sets its preset and allows it.

#### Steps

- Red: `src/matrix/ChatsPage.test.tsx` with the five cases (mock `src/matrix/api.ts`). Fails: no components.
- Green: write the four components. Run the verify.

#### Notes

- Follow `src/webhooks/WebhooksPage.tsx` and `EventsTable.tsx` for layout and polling; MUI components as elsewhere.
- `RunStatusChip` statuses are new, in-progress, handled, ignored, failed, which match the inbound statuses.

- 2026-10-26 done

### S5: smoke matrix check

- Status: done
- Files: `scripts/smoke.sh`, `tests/test_smoke_script.py`, `README.md`
- Verify: `uv run --frozen pytest -q -p no:cacheprovider tests/test_smoke_script.py && shellcheck --severity=error scripts/smoke.sh && uv run ruff check . && uv run ruff format --check .`
- Verified head: b0b7a61a10f4626167e5cdc7a3bc785582ecff84

#### Requirement

Extend the live smoke with connector checks that never send a Matrix message (design D13). Paths are in code/agents-helmfile.

- `scripts/smoke.sh`, new steps after the webhook steps (release name `MATRIX_RELEASE`, default `agents-matrix-connector`): the `-api` and `-bot` Deployments are Available; through a port-forward to the api Deployment (bypassing its SSO sidecar, as the webhook steps do): `GET /matrix/api/v1/meta` answers `user_id` `@hermes:szymonrichert.pl` and `sync.healthy` true (proves the token, the homeserver path and the sync loop); `POST /rules` a deny rule `{list: deny, kind: user, value: "@smoke-<random>:invalid.example"}`, `GET /rules` lists it, `DELETE /rules/{id}` removes it (the trap deletes it on failure, as the webhook endpoint cleanup does); `GET /rooms` answers 200. The UI `config.json` lists the `matrix` backend.
- The header comment documents the new steps and env.
- `tests/test_smoke_script.py`: the script contains the meta, rules round-trip and rooms checks, cleans the rule up in its trap, and never calls a Matrix send or the homeserver directly.
- `README.md` (helmfile) smoke section mentions the connector checks.

User request 2026-10-25, verbatim: 'agents-matrix-connector New microservice- is meant to connect with existing matrix deployment and allow for talking to agents through facebook. Must support user/chat/room auto discovery and white/blacklosting. Hermes already uses working bridge.'

#### Acceptance conditions

- AC1: the smoke checks meta identity and sync health, a rule round trip with cleanup, the rooms list and the UI backend [evidence: test:tests/test_smoke_script.py::test_matrix_connector_checks]
- AC2: the smoke never sends a Matrix message nor calls the homeserver [evidence: test:tests/test_smoke_script.py::test_matrix_smoke_sends_nothing]
- AC3: shellcheck and lint pass [evidence: command:shellcheck --severity=error scripts/smoke.sh && uv run ruff check . && uv run ruff format --check .]

#### Files

- `scripts/smoke.sh`
- `tests/test_smoke_script.py`
- `README.md`

#### Interfaces

- `scripts/smoke.sh` (run by `mise run smoke`), consumed by apply-smoke-matrix.

#### Expected outcome

`mise run smoke` after the apply proves the connector is logged in, syncing and its API works, without touching any chat.

#### Steps

- Red: add the two tests to `tests/test_smoke_script.py`. Fails: no matrix steps.
- Green: extend the script and README. Run the verify.

#### Notes

- Follow the webhook steps' port-forward and trap pattern in the same script.

- 2026-10-25 amended: revision R1 (user 2026-10-25): the connector takes over Hermes' Matrix user and Facebook account, Hermes scaled to 0; only the Hermes home-channel owner DM is allowed

- 2026-10-26 done

### S6: web chats access panels

- Status: done
- Files: `src/matrix/UsersTable.tsx`, `src/matrix/RulesPanel.tsx`, `src/matrix/DefaultPreset.tsx`, `src/matrix/ChatsPage.tsx`, `src/matrix/Access.test.tsx`
- Verify: `npm ci --no-audit --no-fund && npx vitest run src/matrix/Access.test.tsx src/matrix/ChatsPage.test.tsx && npm run lint`
- Verified head: 716ac9b09028d4c938394bb2ac1f37e3cc6f5ba6

#### Requirement

Users, rules and default preset on the Chats page (design D6, D12). Paths are in code/agents-web.

- `src/matrix/UsersTable.tsx`: discovered users (display name, Matrix id, Facebook id, rooms count, access chip), a search box (`listUsers({q})`), Allow and Deny actions per user (`addRule` kind `facebook` when the user has a Facebook id, else `user`), each after a `ConfirmDialog`.
- `src/matrix/RulesPanel.tsx`: the allow and deny lists (`listRules`), each rule with kind, value, note, created time and a Delete action after a confirm; an Add rule form (list, kind from `meta.rule_kinds[list]` so `display_name` only appears under deny, value, note) with `FormError` for 422 and 409.
- `src/matrix/DefaultPreset.tsx`: the default preset (`getSettings`, `setSettings`) with `PresetSelect` and a note that rooms without their own preset use it, and that the default policy (from `meta.default_policy`) applies to rooms and users no rule covers.
- `src/matrix/ChatsPage.tsx`: Rooms, Users and Rules as tabs, the default preset above them.
- `src/matrix/Access.test.tsx`: users search and allow/deny create the right rule; the rules panel lists, adds (display_name offered only under deny) and deletes rules and shows a 409; the default preset saves.

User request 2026-10-25, verbatim: 'agents-matrix-connector New microservice- is meant to connect with existing matrix deployment and allow for talking to agents through facebook. Must support user/chat/room auto discovery and white/blacklosting. Hermes already uses working bridge.'

#### Acceptance conditions

- AC1: users can be searched and allowed or denied by Facebook id or Matrix id after a confirm [evidence: command:npx vitest run src/matrix/Access.test.tsx -t "allows and denies a user"]
- AC2: the rules panel lists both lists, adds with display_name offered only under deny, shows a 409 and deletes after a confirm [evidence: command:npx vitest run src/matrix/Access.test.tsx -t "manages rules"]
- AC3: the default preset is shown and saved [evidence: command:npx vitest run src/matrix/Access.test.tsx -t "saves the default preset"]
- AC4: lint passes [evidence: command:npm run lint]

#### Files

- `src/matrix/UsersTable.tsx`
- `src/matrix/RulesPanel.tsx`
- `src/matrix/DefaultPreset.tsx`
- `src/matrix/ChatsPage.tsx`
- `src/matrix/Access.test.tsx`

#### Interfaces

- `src/matrix/UsersTable.tsx`, `RulesPanel.tsx`, `DefaultPreset.tsx`; `ChatsPage` tabs.

#### Expected outcome

An operator allows a person by their Facebook id, sees the rule, and removes it again.

#### Steps

- Red: `src/matrix/Access.test.tsx` with the three cases. Fails: no components.
- Green: write the components and the tabs. Run the verify (also re-runs `ChatsPage.test.tsx`).

#### Notes

- The UI never decides access itself; it shows the API's access views.

- 2026-10-26 done

### S7: orchestrator repin ab37f1e

- Status: done
- Files: `helmfile.yaml.gotmpl`, `values/agents-orchestrator/common.yaml`, `tests/test_orchestrator_release.py`
- Verify: `uv run --frozen pytest -q -p no:cacheprovider tests/test_orchestrator_release.py -k "not helmfile_build" && uv run ruff check . && uv run ruff format --check .`
- Verified head: 2a8376b2336d83a7d270bfe5e1b44a168c7324c5

#### Requirement

Re-pin agents-orchestrator to ab37f1e (the cache self-repair, agents-orchestrator PR #20) so it ships with this epic's apply. Request from the main orchestrator session 2026-10-26: it cannot take the task itself because this epic holds helmfile.yaml.gotmpl. Paths are in code/agents-helmfile. Same 3-line shape as helmfile commit 98faa23:

- `helmfile.yaml.gotmpl`: the agents-orchestrator chart version `0.1.0-main.ea1fac7` becomes `0.1.0-main.ab37f1e`.
- `values/agents-orchestrator/common.yaml`: image tag `ea1fac7` becomes `ab37f1e`.
- `tests/test_orchestrator_release.py`: the expected pin is updated first (red), then the two files (green).

One separate commit: `chore(deploy): re-pin orchestrator to ab37f1e (cache self-repair)`. The main session checks the chart is published before it applies.

#### Acceptance conditions

- AC1: the orchestrator chart and image are pinned to ab37f1e and the release test expects it [evidence: command:grep -q '0.1.0-main.ab37f1e' helmfile.yaml.gotmpl && grep -q 'ab37f1e' values/agents-orchestrator/common.yaml && uv run --frozen pytest -q -p no:cacheprovider tests/test_orchestrator_release.py -k "not helmfile_build"]
- AC2: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

#### Files

- `helmfile.yaml.gotmpl`
- `values/agents-orchestrator/common.yaml`
- `tests/test_orchestrator_release.py`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

What is true and observable when the task is done.

#### Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

#### Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.

- 2026-10-26 done

### S8: web chats menu entry

- Status: done
- Files: `src/matrix/menu.tsx`, `src/backends/registry.ts`, `src/backends/registry.test.ts`
- Verify: `npm ci --no-audit --no-fund && npx vitest run src/backends/registry.test.ts src/App.test.tsx && npm run lint`
- Verified head: 162770e3207614d19913e7c6426cb40b9b5390db

#### Requirement

Make the Chats page reachable from the menu (design D12; contract `agents-web-backend-registry`). Paths are in code/agents-web.

- `src/matrix/menu.tsx`: `chatsMenu: MenuEntry = {id: 'chats', label: 'Chats', order: 35, backend: 'matrix', render}` rendering `ChatsPage` with `onBack` and `openSession`, the session opener `MenuEntry.render` passes after orchestrator-rename-sessions task web-sessions-pages.
- `src/backends/registry.ts`: `BACKEND_MENUS.matrix = [chatsMenu]`; the reserved-slots comment gains `35 Chats (agents-matrix-connector)`.
- `src/backends/registry.test.ts`: with the matrix backend configured the entry is listed between Schedules (30) and Presets (40); without it, it is absent.

User request 2026-10-25, verbatim: 'agents-matrix-connector New microservice- is meant to connect with existing matrix deployment and allow for talking to agents through facebook. Must support user/chat/room auto discovery and white/blacklosting. Hermes already uses working bridge.'

#### Acceptance conditions

- AC1: the Chats entry appears at order 35 only when the matrix backend is configured [evidence: command:npx vitest run src/backends/registry.test.ts -t "lists Chats only with the matrix backend"]
- AC2: the app tests and lint pass [evidence: command:npx vitest run src/backends/registry.test.ts src/App.test.tsx && npm run lint]

#### Files

- `src/matrix/menu.tsx`
- `src/backends/registry.ts`
- `src/backends/registry.test.ts`

#### Interfaces

- `BACKEND_MENUS.matrix` (contract `agents-web-backend-registry`, slot 35).

#### Expected outcome

With `config.json` listing `{id: matrix, label: Chats, basePath: /matrix/api/v1}`, the menu shows Chats.

#### Steps

- Red: add the registry test case. Fails: no entry.
- Green: write `menu.tsx` and register it. Run the verify.

#### Notes

- Same shape as agents-webhook-microservice task web-webhook-menu-entry.

- 2026-10-26 done

### S9: helmfile web chats entry

- Status: done
- Files: `helmfile.yaml.gotmpl`, `values/agents-web/common.yaml`, `tests/test_web_release.py`
- Verify: `uv run --frozen pytest -q -p no:cacheprovider tests/test_web_release.py -k "not helmfile_build" && uv run ruff check . && uv run ruff format --check .`
- Verified head: 72b381eacc60f7e69aad8fe14cdac586e90bb639

#### Requirement

Configure the matrix backend in agents-web and pin its build (design D12, D13; contracts `agents-web-backends-config`, `agents-web-chart`). Paths are in code/agents-helmfile.

Precondition, checked first: this epic's agents-web PR is merged to main and chart `oci://harbor.szymonrichert.pl/charts/agents-web` `0.1.0-main.<sha7>` and its image exist; the orchestrator amends `<sha7>` in. Otherwise end `blocked`, whoCanClear "orchestrator: merge the agents-web PR of agents-matrix-connector and wait for its main CI".

- `values/agents-web/common.yaml`: `backends` gains `{id: matrix, label: Chats, basePath: /matrix/api/v1}` after the existing entries; `image.tag <sha7>`.
- `helmfile.yaml.gotmpl`: release `agents-web` version `0.1.0-main.<sha7>`; `needs` includes `agents/agents-matrix-connector`.
- `tests/test_web_release.py`: the matrix backend is configured with that basePath and label; the agents-web pin and image tag agree.

User request 2026-10-25, verbatim: 'agents-matrix-connector New microservice- is meant to connect with existing matrix deployment and allow for talking to agents through facebook. Must support user/chat/room auto discovery and white/blacklosting. Hermes already uses working bridge.'

#### Acceptance conditions

- AC1: agents-web lists the matrix backend at /matrix/api/v1 labelled Chats [evidence: test:tests/test_web_release.py::test_matrix_backend_configured]
- AC2: the agents-web chart and image pins agree on the merge sha [evidence: test:tests/test_web_release.py::test_web_pin_matches_image]
- AC3: the offline release tests and lint pass [evidence: command:uv run --frozen pytest -q -p no:cacheprovider tests/test_web_release.py -k "not helmfile_build" && uv run ruff check . && uv run ruff format --check .]

#### Files

- `helmfile.yaml.gotmpl`
- `values/agents-web/common.yaml`
- `tests/test_web_release.py`

#### Interfaces

- `values/agents-web/common.yaml` `backends` (contract `agents-web-backends-config`).

#### Expected outcome

The live UI shows the Chats entry once applied.

#### Steps

- Red: add `test_matrix_backend_configured` (and adjust the pin test only if it names the old sha). Fails: no backend.
- Green: edit values and helmfile. Run the verify.

#### Notes

- Same shape as agents-webhook-microservice task helmfile-web-webhooks-entry.

- 2026-10-26 done

### S10: apply smoke matrix

- Status: done
- Files: `MEMORY.md`
- Verify: `mise run diff && mise run smoke`
- Verified head: 8bce546bf6fe3f4e1e9f196cb56676d967c31b9c

#### Requirement

Apply to the live `agents` namespace and prove it (design D13; live-deploy rule: the orchestrator runs live applies itself, never a subagent). Paths are in code/agents-helmfile.

- Implementer, before the apply: `mise run diff`; keep its output in the task notes. Expected: new releases `agents-matrix-connector-db` and `agents-matrix-connector`; the agents-orchestrator token-hash addition; agents-web version, image tag and the matrix backend. Anything else stops the task `blocked` with the diff, whoCanClear "user". Then end the implementer round with "ready for apply".
- Orchestrator (main session, never a subagent): `mise run apply` in code/agents-helmfile (lint, test and the kube-context guard run first; never bypass the guard); a failing apply is not retried blindly: read the helm error and report its tail.
- After the apply, implementer: `mise run diff` again (no drift) and `mise run smoke` (exit 0, including the connector checks); read-only `kubectl -n agents logs deploy/agents-matrix-connector-bot --tail=50` shows the first sync and no token in the output; `MEMORY.md`: a dated line: applied agents-matrix-connector `0.1.0-main.<sha7>` with its CNPG database as `@hermes:szymonrichert.pl` (Hermes at 0 replicas), agents-web `0.1.0-main.<sha7>` with Chats; default deny; smoke green (quote its last log line).
- After the smoke, implementer: create the one allow rule the user asked for (2026-10-25, verbatim: 'Whitelist only 1 channel for now- the one where Hermess sends "Hermess is shutting down..." messages (Szymon Richert to Szymon Richert)'; that is Hermes' home channel, the owner DM portal `!iLWrAwaTMYnINJsyNv:szymonrichert.pl`): `POST /matrix/api/v1/rules` with `{"list": "allow", "kind": "room", "value": "!iLWrAwaTMYnINJsyNv:szymonrichert.pl", "note": "owner DM, Hermes home channel"}` through the port-forward the smoke uses (bypassing the SSO sidecar); then `GET /matrix/api/v1/rules` lists exactly that allow rule and no deny rule, and `GET /matrix/api/v1/rooms/{room_id}` for it shows the decision allowed (a 404 because the room is not yet discovered stops the task `blocked` with the `/rooms` listing, whoCanClear "orchestrator"). The default policy stays deny.
- Last, once the allow rule is in place and the smoke is green: send the user one Messenger message, a short joke chosen then, into `!iLWrAwaTMYnINJsyNv:szymonrichert.pl` as the bot (user request 2026-10-25, verbatim: 'Once it's deployed, ping me with a message (a joke, don't tell me now).'). Send it through the bot's own Matrix client in the bot pod (for example a one-off `kubectl exec` running the connector's MatrixClient with the mounted token file), never printing the token; quote the returned event id in the task notes. This is the only Matrix message the deploy sends.
- No other file changes.

User request 2026-10-25, verbatim: 'agents-matrix-connector New microservice- is meant to connect with existing matrix deployment and allow for talking to agents through facebook. Must support user/chat/room auto discovery and white/blacklosting. Hermes already uses working bridge.'

#### Acceptance conditions

- AC1: the live namespace has no drift from the pinned helmfile after the apply [evidence: command:mise run diff]
- AC2: the smoke passes, including the connector checks [evidence: command:mise run smoke]
- AC3: MEMORY.md records the applied versions and the smoke result [evidence: command:grep -q "agents-matrix-connector" MEMORY.md && grep -q "smoke" MEMORY.md]
- AC4: the pre-apply diff showed only the expected changes and the bot log shows a sync without the token [evidence: judgement:the diff output and the log tail quoted in the task notes]
- AC5: the only access rule is the allow rule for `!iLWrAwaTMYnINJsyNv:szymonrichert.pl` and that room's decision is allowed [evidence: judgement:the GET /rules and GET /rooms/{room_id} output quoted in the task notes]
- AC6: the joke message was sent once to the allowed room and its event id is recorded [evidence: judgement:the event id quoted in the task notes]

#### Files

- `MEMORY.md`

#### Interfaces

- The live releases; nothing new.

#### Expected outcome

The connector runs in namespace `agents`, logged in and syncing; the Chats page is live; the smoke is green. A first Messenger chat then shows up in Chats as default-deny until the user allows it.

#### Steps

- `mise run diff` (expected changes only), "ready for apply"; orchestrator applies; `mise run diff` (no drift); `mise run smoke` (exit 0); MEMORY line.

#### Notes

- Same shape as agents-webhook-microservice task apply-smoke-webhook. Deploy tasks never use apply as AC evidence.

- 2026-10-25 amended: revision R1 (user 2026-10-25): the connector takes over Hermes' Matrix user and Facebook account, Hermes scaled to 0; only the Hermes home-channel owner DM is allowed

- 2026-10-25 amended: user 2026-10-25: once deployed, ping the user with a joke message

- 2026-10-26 done

### S11: live reply proof

- Status: done
- Files: `MEMORY.md`
- Verify: `mise run diff`
- Verified head: 8bce546bf6fe3f4e1e9f196cb56676d967c31b9c

#### Requirement

Live proof of goal G1 (scope audit 2026-10-26): "a Messenger message to the connected Facebook account in an allowed chat gets the agent's reply in the same chat". Read-only; no file changes.

Precondition: the connector's default preset is set (user chose 'Default', 00000000-0000-0000-0000-000000000001, set 2026-10-26) and the user has sent one new Messenger message in the allowed owner DM `!iLWrAwaTMYnINJsyNv:szymonrichert.pl` after that. Otherwise end `blocked`, whoCanClear "user: send one Messenger message in the owner DM".

- Through the smoke's 127.0.0.1 port-forward to the api (port 8000): `GET /matrix/api/v1/rooms/{room_id}/messages` shows the new inbound message dispatched (not ignored) with a session, and an outbound reply; `GET /matrix/api/v1/rooms/{room_id}` shows the session.
- Read-only bot log tail shows the dispatch and the reply send, with no token in the output.
- Quote the evidence (statuses, session id, event ids; no message bodies) in /Users/szymonri/Documents/claude-code-tatara/.scratchpad/agents-matrix-connector/g1-proof.md.
- Never send a Matrix message, never change rules or settings, never apply.

#### Acceptance conditions

- AC1: a new inbound message in the allowed owner DM was dispatched to a session and the agent's reply was posted back in the same room [evidence: judgement:the /rooms/{id}/messages and /rooms/{id} output quoted in g1-proof.md]
- AC2: the bot log shows the dispatch and reply without the token [evidence: judgement:the sanitized log excerpt in g1-proof.md]

#### Files

- `MEMORY.md`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

What is true and observable when the task is done.

#### Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

#### Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.

- 2026-10-26 done

## Files to delete

none recorded in the epic format

## Final verify

none recorded in the epic format

## After merge

none
