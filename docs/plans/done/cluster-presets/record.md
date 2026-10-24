# cluster presets record

## Summary

Asked (2026-10-23): named ClusterSpec presets (create, copy, edit, delete) with a seeded 1-pod Default, scheduling a cluster from a preset alone, live cluster edit removed, Presets as the first settings category in the hamburger menu, everything also usable headless.

Shipped: 13 tasks, all `done`. agent-orchestrator: `0002_presets.sql`, `/api/v1/presets` CRUD plus copy, `POST /api/v1/clusters` with `preset_id` (snapshot at create, generated slug, raw `spec` kept, exactly one of the two), `PATCH /api/v1/clusters/{id}` retired (405), `PresetForm`, `PresetsPage`, `NewClusterDialog`, kind e2e through the public API. agents-helmfile: pin to `9ab0d60`.

Verdict: delivered and merged. Orchestrator suite 528 passed, frontend 183 passed, PR CI green including kind e2e. Not deployed: `helmfile apply` and smoke are user-run. PR CI kind e2e caught a real bug the unit tests missed (PATCH answered 404, not 405, behind the SPA mount in the built image); fixed test-first in `spa-method-not-allowed`.

## Planned vs built

Sources: plan-execute first-run return (`presets-return.json`, 11 tasks), task files, `git show --stat` of each landed commit in `code/agent-orchestrator` and `code/agents-helmfile`, `presets-suite.log`. The return was not provided for the later runs (`presets-review-fixes`, `spa-method-not-allowed`, `deploy-pin-presets`); their rows use the task file `verified_head` and say so. Continuations per task: unknown (not in the return); the epic took 4 apply-run commits in the superrepo (`f97dc34`, `48ab361`, `5e4f223`, `550c518`).

Orchestrator commits are on `cluster-presets`, merged as `9ab0d60` (PR #5); helmfile pin `de32698`, merged as `8bf0b6b` (PR #7).

| Task | Status | Review rounds | Files (from the landed commit) | Verifier head | Verification tail and implementer red |
|---|---|---|---|---|---|
| slug-from-name | done | 1 | spec.py, bench/runner.py, tests/test_slugs.py | `eac3b59` | pytest test_slugs + test_bench, ruff clean. Red: `test_slugs.py` collection ImportError (slugify/generated_slug missing). Return `cannotVerify`: the red claim itself was not independently confirmed. |
| presets-table-and-repo | done | 1 | 0002_presets.sql, db/presets.py, test_migrations.py, test_presets_repo.py, README.md | `233ff92` | test_migrations + test_presets_repo, ruff clean (implementer: 17 passed). Red: 5 migration tests FAILED, `test_presets_repo.py` ImportError (no `db.presets`). |
| preset-routes | done | 1 | api/presets.py, api/app.py, api/schemas.py, api/clusters.py, spec.py, test_api_presets.py, README.md, openapi.json, schema.d.ts | `dde2170` | test_api_presets + test_api_clusters + test_readme_api, check:api, ruff clean (implementer: 90 passed). Red: 5 tests FAILED with the router registration temporarily disabled. |
| create-cluster-from-preset | done | 1 | api/clusters.py, api/schemas.py, db/clusters.py, test_api_create_from_preset.py, README.md, openapi.json, schema.d.ts | `de2e847` | test_api_create_from_preset + clusters + readme_api, check:api, ruff clean. Red: 9 tests FAILED in `test_api_create_from_preset.py`. |
| fe-new-cluster-dialog | done | 1 | client.ts, client.test.ts, NewClusterDialog.tsx(+test), App.tsx(+test), TopBar.tsx(+test) | `9a46092` | vitest (implementer 48 passed), lint, build, check:api. Red: TopBar/NewClusterDialog/client tests failed (3 files, 2 tests failed, load errors). |
| fe-preset-form | done | 2 | PresetForm.tsx (git mv of ClusterForm.tsx), PresetForm.test.tsx, clusterSpecForm.ts, DiscardClusterDialog.test.tsx, ClusterForm.test.tsx (deleted), client.ts, nodeModules.d.ts | `9fb81a8` | vitest PresetForm + DiscardClusterDialog + designRules, lint, build (verifier-reported 24 passed). Red: none recorded (`tests.red` null). Return `filesChanged` is `[]`; the commit changes 7 files, so the files win. |
| fe-presets-page | done | 0 | PresetsPage.tsx(+test), App.tsx(+test) | `477e2f5` | vitest PresetsPage + App + designRules, lint, build. Red: PresetsPage import failed and the Settings entry was not found (2 files failed). |
| retire-cluster-patch-route | done | 1 | api/clusters.py, api/schemas.py, test_api_clusters.py, README.md, MEMORY.md, openapi.json, schema.d.ts | `97af531` | test_api_clusters + presets + create_from_preset + readme_api, check:api, build, ruff clean (implementer 69 passed). Red: `assert 200 == 405`, `test_patch_cluster_retired_405` FAILED. |
| retire-spec-update-repo | done | 1 | db/clusters.py, spec.py, test_clusters_repo.py, test_reconciler.py | `79cc4d6` | test_clusters_repo + api_clusters + api_messages, ruff clean, grep for `update_spec|ClusterDeleting` empty. Red: `test_live_edit_code_retired` FAILED (`hasattr(clusters, "update_spec")`). I confirmed `update_spec`, `ClusterDeleting`, `PatchCluster`, `patchCluster` are gone from `src` and `frontend/src` (only the retirement test mentions them). |
| kind-e2e-presets | done (escalated in run 1, accepted by ruling) | 3, stopped `gate-repeat` | tests/e2e/test_e2e_kind.py (+160/-8); `e2e/values-kind.yaml` unchanged. Return `filesChanged` is `[]`; the commit `dbf8dc9` changes the one file, so the files win. | `a7b8b4a` (task-branch tip; landed as `dbf8dc9`) | Collection: 17 collected, ruff clean. The same verification text records the AC4 test run as exit 1 (no kind binary in the sandbox) while `passed: true`; contradiction, see Deviations. Red: none (`tests.red` null; process gap: test-only diff, no non-test file to revert). Executed only by PR CI e2e job: green. |
| presets-review-fixes | done | unknown (return not provided) | tests/test_migrations.py, PresetForm.tsx, PresetForm.test.tsx, README.md (`6e73ebb`, `27eeef9`) | `27eeef9` (task file `verified_head`) | Red shown by the orchestrator: early-edit PresetForm test fails against the pre-fix component (1 failed), passes on HEAD. The migration upgrade test is a characterization test of already-safe SQL (no red). AC3 doc-section check misfired; the note is at README.md:313 (ruling). |
| spa-method-not-allowed | done | unknown (return not provided) | api/spa.py, api/errors.py, tests/test_spa.py (`c979451`) | `c979451` (task file `verified_head`) | Test-first per the caller; the implementer's red output is not in the files I read. The red that matters is PR CI: `test_patch_cluster_retired` got 404. After the fix the orchestrator suite is 528 passed. |
| deploy-pin-presets | done | 0 in run 1 (`dependency-failed` on kind-e2e-presets, listed `unverified` there), re-run after the amend | helmfile.yaml.gotmpl, values/agent-orchestrator/common.yaml, tests/test_orchestrator_release.py (`de32698`, 3 lines) | `de32698` (task file `verified_head`; run-1 return has no head, so `unverified` in that return) | Release tests pass except `test_release_chart_version_and_needs` and `test_db_secret_matches_rendered_cnpg_cluster`, which pull charts and are blocked by the container network policy; `mise run apply` runs them. Ruff clean. Red: not in the files I read. |

No `tdd-revert` output is quoted anywhere above; the red column is the implementer's own `tests.red` or an orchestrator-run red.

Approvals ledger (`approvals.json`, all `approved`). The run-1 return column is its `approvals[].status`; the "Final" column is after the rulings, the CI results and the merges.

| Id | Text | Decisions | Tasks | Run-1 return | Final |
|---|---|---|---|---|---|
| A | Presets are named, stored templates with create, copy, edit, delete through /api/v1 and the UI; stores only what the user set; editor shows /meta defaults | D2 D3 D6 D17 D18 D21 | fe-new-cluster-dialog, fe-preset-form, fe-presets-page, preset-routes, presets-table-and-repo | delivered | delivered |
| B | Seeded 1-pod Default; editable and copyable, not renamable or deletable; last preset not deletable | D1 D3 D15 D16 | fe-presets-page, preset-routes, presets-table-and-repo | delivered | delivered |
| C | Schedule takes a preset and an optional slug; raw spec kept, exactly one of spec or preset_id | D4 D6 D11 D12 | create-cluster-from-preset, fe-new-cluster-dialog, slug-from-name | delivered | delivered |
| D | Cluster keeps the spec snapshotted at create plus its source preset; preset edit or delete never changes it | D1 D4 D13 D19 | create-cluster-from-preset, fe-new-cluster-dialog, kind-e2e-presets, presets-table-and-repo | escalated (kind-e2e-presets gate-repeat) | delivered: ruling accepted kind-e2e, PR CI kind e2e green |
| E | Live cluster edit removed: PATCH retired (405 test), schema, repository function, "the stored parameter of validate_spec", client call, form edit mode; documented exception | D5 D14 D22 | fe-preset-form, presets-table-and-repo, retire-cluster-patch-route, retire-spec-update-repo | delivered | delivered, except the `stored` parameter, which stays by builder-check ruling 2 (see Deviations); the ledger text was not amended |
| F | Presets first settings category in the hamburger menu, full main-area page with Back | D7 D20 | fe-presets-page | delivered | delivered |
| G | Headless parity: documented public API and an API-only e2e test per capability | D8 D10 | create-cluster-from-preset, kind-e2e-presets, preset-routes | escalated (kind-e2e-presets) | delivered: ASGI tests per route plus kind e2e through /api/v1, CI green |
| H | Chart and image pinned in agents-helmfile; helmfile apply and smoke run by the user | D9 | deploy-pin-presets | escalated (dependency-failed) | pin delivered and merged (helmfile#7); apply and smoke pending, user |

## Deviations and rulings

Each entry: what, why, cost if wrong.

Orchestrator rulings (`rulings.json`):
- kind-e2e-presets accepted (2026-10-24T03:00:28Z) although its verification text shows AC4 re-run exit 1 and tdd-skipped / ac-unmet findings stood. Why: the kind e2e cannot run in this container (no cluster/kind binary); verified by collection and lint, executed by the PR CI e2e job. Cost if wrong: an unrun e2e merged unproven; bounded because PR CI ran it (green after the SPA fix).
- presets-review-fixes accepted (2026-10-24T03:16:50Z). Why: the AC3 doc-section anchor check misfired (note present at README.md:313); red shown by the orchestrator for the PresetForm test; the migration upgrade test is characterization of safe SQL. Cost if wrong: the README note missing or the early-edit fix untested; both checked in the files.

Builder-check rulings (design.md, 2026-10-23):
1. Preset path fills `replicas` from `settings.default_replicas` when unset; raw-spec path unchanged. Why: Default stores replicas 1 explicitly, other presets may omit it. Cost: a raw-spec caller and a preset caller would differ on an unset replicas.
2. Preset PUT accepts an out-of-list model/effort/image only when unchanged; `validate_spec` and `check_spec` keep the `stored` parameter; scheduling validates fully. Why: the legacy PATCH rule, needed so an old preset stays editable. Cost: approval E text said the parameter would go (it stayed); dead-code claim in E is partly untrue, a later reader may delete it and break PUT.
3. 5th generated-slug clash answers 409 `conflict`, never 500. Cost: a rare 409 the user retries.
4. Leading or trailing spaces in names rejected, no trimming; copy name's source part cut to 40 characters. Cost: a user-visible 422 on pasted names.
5. Clearing a field in the editor means unset, never null. Cost: none beyond defaults applying.
6. Kind e2e tests delete every cluster they create; `ORCH_MAX_CLUSTERS` raised only if needed (`e2e/values-kind.yaml` was not changed). Cost: cluster-cap flake in CI; the return left "default is 20" unconfirmed, CI green.
7. Kind e2e never edits the Default; edits act on a copy. Cost: Default edit path covered only by ASGI tests.
8. fe-preset-form moves the discard-dialog tests from the web-ui `ClusterForm.test.tsx`. Cost: lost coverage if mis-moved; `DiscardClusterDialog.test.tsx` added (68 lines).
9. `createCluster` typed on the regenerated `CreateCluster`; every task keeps `npm run build` and `check:api` green. Cost: red main between tasks; none observed.
10. deploy-pin-presets excluded from the build run, runs after the orchestrator PR merges, sha filled with `ticket.py amend`. Cost: the pin lags the merge; it did (run 1 returned `dependency-failed`, run after the amend delivered).

Epic review rulings (2026-10-24): acted on three minor findings in presets-review-fixes (upgrade-path migration test, PresetForm early edits, README writers table). Declined: `getPreset`/`copyPreset` used only by tests (the `fe-preset-client` contract lists them); no "copy 2" naming on a UI name collision (the 409 is shown, as designed). Cost: dead client functions; a manual rename after a collision. Security review skipped: no authz, secrets, ingress or privilege surface; migration additive and idempotent. Cost if wrong: an unreviewed surface; the diff adds only CRUD and a migration.

Other deviations from the files:
- Run-1 declined (fe-preset-form): "edits typed before /meta arrives are dropped" judged a narrow race and not a requirement. The epic review then found it as a real minor finding and presets-review-fixes fixed it. Cost: one extra task (11 min).
- Run-1 declined (fe-preset-form): "Worktree not clean at verification" note; `git status --short` was empty. Not verifiable from the files now.
- The run-1 return has `audit: "off"` and `scopeAudit: null`; the scope audit (sonnet, every item A-G landed, 17 e2e collected) ran later per the README Review section. I did not see its output.
- `forwardMerged`: none.

## Duplicates reconciled

None (return `duplicates` is empty; `misattributed` is empty).

## Discovered and blocked

- Real bug, fixed: `SpaStaticFiles` answered every `api/` path with 404 before any method check, so retired `PATCH` returned 404 in the built image; unit tests never mounted the SPA. Found by PR CI kind e2e `test_patch_cluster_retired`. Fixed by `spa-method-not-allowed` (`c979451`, 405 with `Allow: GET, HEAD`). Cleared.
- Kind e2e cannot run in this container (no cluster, no kind binary). Run by the PR CI `e2e` job only: green. Cleared by CI.
- Two agents-helmfile tests (`test_release_chart_version_and_needs`, `test_db_secret_matches_rendered_cnpg_cluster`) pull charts over the network and fail here under the container network policy. Run by `mise run apply`. Who can clear: the user (runs apply).
- `helmfile apply` and `mise run smoke`: not run. Who can clear: the user.
- First full orchestrator suite: 524 passed; `test_frontend_schema_matches_openapi` fails until `npm --prefix frontend ci` has run (needs `node_modules`). Passes after. Cleared; the verify commands now run `npm ci` first.
- tatara and magic-trainer (named API consumers in the orchestrator README) were not checked for PATCH or slug-only POST use; the README and MEMORY.md carry the dated exception. Who can clear: the owner of those repos (user).
- Return `cannotVerify` items still unconfirmed by the files I read: whether the server's real `PresetView.spec` shape (sparse, no explicit nulls) matches the form's assumption (CI e2e creates presets through the API and passed); concurrent-delete safety beyond the one two-connection test; `slug-from-name` implementer's test-first claim.
- Process gap: kind-e2e-presets has no red/green evidence (test-only diff). The verifier gate repeated on it for 3 rounds on an environment failure, not a code defect (5 fix minutes plus 1 false-finding minute in `actual_roles`).
- The run-1 return contradicts the files in three places: `filesChanged` is `[]` for fe-preset-form and kind-e2e-presets; kind-e2e-presets has `verification.passed: true` while its evidence says the AC4 run exited 1; `finished: false` with `undelivered: []`. The files above are what I used.

## Research that changed the plan

- `research.md` 1 (PATCH callers: only the UI and tests; `bench/runner.py:115` and `smoke.sh:46` only POST and DELETE) -> `retire-cluster-patch-route` is safe in tree; `smoke.sh` unchanged (Q2); tatara and magic-trainer left as a named risk.
- `research.md` 3 (EC2 launch templates are immutable, https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/manage-launch-template-versions.html; Kubernetes template change rolls pods, `k8s/render.py:189`, `:254`) -> snapshot at create, versioned presets rejected (D4, D13, Non-goals).
- `research.md` 3 (validation depends on settings) -> validate at save and again at schedule (D2, D4); this produced builder ruling 2.
- `research.md` 2 (`valuesFromSpec` / `blankValues(meta)` reuse; PVC editable again) -> `fe-preset-form` reuses `clusterSpecForm.ts` in place (D6).
- `research.md` 4 (MUI temporary Drawer, https://mui.com/material-ui/react-drawer/) -> no new dependency; Presets via the `settingsCategories` contract `orch-settings-menu` (D7).
- discovery `reuse.md` fix-as-ac (private `_check_spec`) -> `preset-routes` owns the public `check-spec-public`; `arm_slug` sanitising -> `slug-from-name` task (`slugify`, `generated_slug`, also used by `orch bench`); idempotent seed -> `INSERT ... ON CONFLICT DO NOTHING` in `0002_presets.sql`.

## Cost

Agents by role are `actual_roles` minutes summed over the 13 task files: impl 35, verify 33, review 12, fix 9, land 11, false-finding 2 (total 102). The per-task `actual` values sum to 90; the role minutes exceed `actual` on 6 tasks (kind-e2e-presets 9 vs 8, presets-review-fixes 12 vs 11, deploy-pin-presets 4 vs 1, retire-cluster-patch-route 9 vs 8, presets-table-and-repo 7 vs 5, slug-from-name 4 vs 2). Agent counts and tokens: unknown, except run-1 triage usage: 7 calls, 14 input and 5565 output tokens. Continuations: unknown per task; 4 plan-execute runs. Audits: whole-diff review (sonnet), scope audit (sonnet), security review skipped; run-1 `audit` was `off`. Wall-clock: superrepo `move in-progress` 2026-10-24 02:00:10 UTC to pointer bump 03:50:02 UTC, about 110 min including both merges (PR #5 03:41 UTC, PR #7 03:48 UTC).

README Time: Estimate 73 agent-min, Critical path 47 min, Expected wall at P=1.5 1.6 h (k=2.0), Actual 90 min, Remaining 0 min.

| Task | Estimate (min) | Actual (min) | actual_roles |
|---|---|---|---|
| slug-from-name | 5 | 2 | impl 1, verify 1, review 1, land 1 |
| presets-table-and-repo | 6 | 5 | impl 3, verify 2, review 1, land 1 |
| preset-routes | 6 | 9 | impl 4, verify 3, review 1, land 1 |
| create-cluster-from-preset | 6 | 10 | impl 4, verify 4, review 1, land 1 |
| fe-new-cluster-dialog | 6 | 6 | impl 3, verify 3, review 1, land 1 |
| fe-preset-form | 6 | 12 | impl 4, verify 5, review 1, fix 1, land 1 |
| fe-presets-page | 6 | 6 | impl 3, verify 2, land 1 |
| retire-cluster-patch-route | 6 | 8 | impl 3, verify 4, review 1, land 1 |
| retire-spec-update-repo | 5 | 7 | impl 4, verify 1, review 1, land 1 |
| kind-e2e-presets | 5 | 8 | impl 1, verify 1, review 1, fix 5, false-finding 1 |
| deploy-pin-presets | 5 | 1 | impl 1, verify 1, review 1, land 1 |
| presets-review-fixes | 6 | 11 | impl 2, verify 5, review 1, fix 3, false-finding 1 |
| spa-method-not-allowed | 5 | 5 | impl 2, verify 1, review 1, land 1 |
| Total | 73 | 90 | |

## MRs and deploy

- agent-orchestrator PR #5, https://github.com/szymonrychu/agent-orchestrator/pull/5: PR CI all green including kind e2e (after `c979451`); merged as `9ab0d60`. Orchestrator 528 passed, frontend 183 passed (`presets-suite.log`: 22 files, build and check:api clean).
- agents-helmfile PR #7, https://github.com/szymonrychu/agents-helmfile/pull/7: pin chart `0.1.0-main.9ab0d60` and image `9ab0d60` (`de32698`); merged as `8bf0b6b`. Release tests pass except the two chart-pull tests blocked by the container network policy (run by `mise run apply`); ruff clean.
- Superrepo: pointers bumped in `d440c21` on `claude/nifty-davinci-0z8a2v`; ticket moved to done in `c2a6d1d`.
- Deploy: not done. The user runs `helmfile apply` and `mise run smoke`. The orchestrator runs migration 0002 on start (additive, idempotent, existing clusters keep their spec). No deploy confirmation exists.

## Lessons routed to

Mechanical (add a check):
- Status-code contract tests passed in-process but failed in the built image (SPA mount shadowed the 405). Add a test fixture that builds the app with `static_dir` set and run the retirement and method tests (`PATCH` 405, unknown `api/` 404) against it; `tests/test_spa.py` now holds the two cases, extend the pattern to every retired route.
- The verifier gate flagged `tdd-skipped` on a test-only diff and `ac-unmet` on a missing `kind` binary, burning 3 rounds. Change `verify-task.py` to skip the `tdd-skipped` gate when the diff has no non-test file, and to report a missing-binary exit as `cannotVerify` instead of an unmet AC; test both cases in the script's tests.
- The run-1 return gave `filesChanged: []` for two landed tasks and `verification.passed: true` beside an exit-1 AC re-run. Add a plan-execute self-check that `filesChanged` equals `git diff --name-only` of the landed commit and that `passed` is false when any AC evidence line records a nonzero exit.
- The `doc-section:README.md#data-model` evidence check misfired though the note existed. Add a test for the doc-section anchor resolver with this README heading.

Judgement call (edit a skill or rule):
- fe-preset-form declined "edits typed before /meta arrives are dropped" as a narrow race; the epic review kept it as a real finding. Edit the review/triage rubric in `plan-execute` guidance: a finding that loses user input is not declinable as a narrow race.
- Builder-check ruling 2 changed the scope of approval E (the `stored` parameter stays) but `approvals.json` text was not amended, so the ledger overstates what was delivered. Edit the `start-development` builder-check step: a ruling that changes an approved item's scope amends that approval text with `ticket.py`.
