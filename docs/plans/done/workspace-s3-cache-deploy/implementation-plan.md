# workspace s3 cache deploy implementation plan

## Agreed rung

Rung 1 of plan.md, migrated from the epic format: the steps are the epic's tasks.

## Approach

Migrated from the epic format: one step per task file, in dependency order, each with its status, files, verify, verified head and every body section.

## Chunk 1: migrated tasks (model: opus)

### S1: cache put signs content type

- Status: done
- Files: `src/agents_orchestrator/cache/presign.py`, `src/agents_orchestrator/cache/transfer.py`, `tests/test_cache_presign.py`, `tests/test_cache_cli.py`
- Verify: `uv run pytest -q -o addopts='-m "not integration and not e2e"' tests/test_cache_presign.py tests/test_cache_cli.py && uv run ruff check .`
- Verified head: 9c8bb44

#### Requirement

Live apply 2026-10-26 (diagnosis in the task notes): the workspace cache save fails with upload_failed: HTTP 403 AccessDenied on Ceph RGW 20.2.4. cache/transfer.py save() sends `Content-Type: application/zstd` on the presigned PUT, while cache/presign.py signs only `host` (X-Amz-SignedHeaders=host); RGW then treats the request as anonymous. Probes from the reconciler pod: the same URL without the header returns 200, and a URL presigned with ContentType=application/zstd and sent with that header returns 200. Fix in agents-orchestrator: presign signs the content type for PUT (botocore Params ContentType) from one shared constant that the CLI also sends, so the two cannot drift; GET is unchanged. Update the presign docstring, whose claim that Content-Type need not match does not hold on RGW. Tests: the PUT URL's SignedHeaders include content-type, the CLI sends exactly that value, and a moto round trip still passes.

#### Acceptance conditions

- AC1: a PUT URL signs content-type and the CLI sends the same constant [evidence: test:tests/test_cache_presign.py::test_put_signs_content_type]
- AC2: the suite and lint pass [evidence: command:mise run lint]

#### Files

- `src/agents_orchestrator/cache/presign.py`
- `src/agents_orchestrator/cache/transfer.py`
- `tests/test_cache_presign.py`
- `tests/test_cache_cli.py`

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

### S2: helmfile cache bucket

- Status: done
- Files: `raw/workspace-cache-bucket.pre.yaml`, `values/agents-orchestrator/common.yaml`, `tests/test_workspace_cache.py`
- Verify: `uv run pytest -q -p no:cacheprovider tests/test_workspace_cache.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: 8ebfff6

#### Requirement

Provision the cache bucket on rook-ceph and wire it into the orchestrator release (design D9). Runs after the epic orchestrator-rename-sessions lands: the release is `agents-orchestrator` and its values live in `values/agents-orchestrator/` (if that epic chose other names, the orchestrator amends this file list first). Paths are in code/agents-helmfile. Rook-ceph specifics live only here.

- `raw/workspace-cache-bucket.pre.yaml`: `apiVersion: objectbucket.io/v1alpha1`, `kind: ObjectBucketClaim`, name `agents-workspace-cache`, namespace `agents`, `spec {bucketName: agents-workspace-cache, storageClassName: rook-ceph-bucket}`; a comment that the StorageClass `reclaimPolicy` is `Delete`, so deleting this claim deletes the bucket and every cache. `.hook.sh` applies it at presync.
- `values/agents-orchestrator/common.yaml`: `cache.s3 {endpoint: http://rook-ceph-rgw-ceph-objectstore.rook-ceph.svc:80, region: us-east-1, bucket: agents-workspace-cache, pathStyle: true, existingSecret: agents-workspace-cache}` (rook creates Secret `agents-workspace-cache` with `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`, the chart's default key names), with a comment naming the claim.
- `tests/test_workspace_cache.py`.

Core tasks in epic workspace-s3-cache that this task depends on (covered by the epic blocker): cache-chart-values.


Orchestrator ruling 2026-10-26 (epic security review, medium): nothing bounds the bucket total (5 GiB per key, unbounded keys), so set a bucket quota on the ObjectBucketClaim (rook additionalConfig maxSize in the rook-documented unit form, for example "100G", and maxObjects; rook v1.21 documents both as default-allowed OBC additionalConfig), set in the raw ObjectBucketClaim file (the established pattern for raw resources, applied at presync without templating; edit the file to change it), and test the file.

#### Acceptance conditions

- AC1: the claim is an ObjectBucketClaim in agents with the fixed bucket name and the rook-ceph-bucket StorageClass [evidence: test:tests/test_workspace_cache.py::test_bucket_claim_shape]
- AC2: the raw file is picked up at presync (name ends in .pre.yaml, under raw/) [evidence: test:tests/test_workspace_cache.py::test_bucket_claim_applied_at_presync]
- AC3: the orchestrator values point the cache at the rgw endpoint, path style, the claim's bucket and Secret [evidence: test:tests/test_workspace_cache.py::test_orchestrator_cache_values]
- AC4: no access key or secret literal appears in any plain values file [evidence: test:tests/test_workspace_cache.py::test_no_cache_credentials_in_values]
- AC5: lint and format pass [evidence: command:uv run ruff check . && uv run ruff format --check .]
- AC-quota: the bucket claim sets a size and object quota [evidence: test:tests/test_cache_bucket.py::test_bucket_quota_set]

#### Files

- `raw/workspace-cache-bucket.pre.yaml`
- `values/agents-orchestrator/common.yaml`
- `tests/test_workspace_cache.py`

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

- 2026-10-26 amended: epic security review: bucket quota

- 2026-10-26 amended: review: the quota lives in the raw OBC file (raw resources are not templated); maxSize in rook's documented G unit

- 2026-10-26 done

### S3: smoke workspace cache

- Status: done
- Files: `scripts/smoke.sh`, `tests/test_smoke_script.py`, `README.md`
- Verify: `uv run pytest -q -p no:cacheprovider tests/test_smoke_script.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: 9308871

#### Requirement

Prove the workspace cache in the deployed smoke (design D9, D12; goal G8). Paths are in code/agents-helmfile; post-rename API paths (`/api/v1/sessions`; if the rename epic chose other paths, the orchestrator amends this task first).

`scripts/smoke.sh`, after the existing checks, a workspace cache check:
- `GET /api/v1/meta`: `cache.available` must be true, else fail "workspace cache is not configured".
- A random run id `RUN_ID`. Session A: raw spec, 1 replica, `cache: {key: "smoke-workspace-cache"}`, init script `printf '%s\n' "$RUN_ID" > cache-marker`. Wait (bounded by `SMOKE_TIMEOUT_S`) for its init to succeed and `status.cache.restore.state` to be `restored` or `miss`. Delete A and wait until `GET` returns 404 (its save ran in the discard).
- Session B: the same cache key, init script `grep -qx "$RUN_ID" cache-marker`. Wait for `status.cache.restore.state` `restored` and the init `succeeded`; a failed init fails the smoke with "workspace cache did not carry the marker" and the init log tail. Delete B and wait for 404.
- The object `workspace-cache/smoke-workspace-cache.tar.zst` stays and is overwritten on each run (one fixed key). Both sessions are deleted by the existing cleanup trap on any failure.
- `tests/test_smoke_script.py` (fake API): the happy path passes; an unavailable cache fails; a B init failure fails with the marker message; both sessions are deleted on failure. `README.md`: the smoke list names the cache check.

#### Acceptance conditions

- AC1: the smoke happy path including the cache check exits 0 against the fake API [evidence: test:tests/test_smoke_script.py::test_workspace_cache_round_trip_passes]
- AC2: an orchestrator without the cache fails the smoke [evidence: test:tests/test_smoke_script.py::test_workspace_cache_unavailable_fails]
- AC3: a second session without the marker fails with the marker message [evidence: test:tests/test_smoke_script.py::test_workspace_cache_marker_missing_fails]
- AC4: both cache sessions are deleted when the check fails [evidence: test:tests/test_smoke_script.py::test_workspace_cache_sessions_cleaned_up]
- AC5: the existing smoke tests stay green [evidence: command:uv run pytest -q -p no:cacheprovider tests/test_smoke_script.py]
- AC6: lint and format pass [evidence: command:uv run ruff check . && uv run ruff format --check .]

#### Files

- `scripts/smoke.sh`
- `tests/test_smoke_script.py`
- `README.md`

#### Interfaces

- `scripts/smoke.sh`; API `POST /api/v1/sessions`, `GET /api/v1/sessions/{id}`, `GET /api/v1/meta`, `DELETE /api/v1/sessions/{id}` (post-rename paths).

#### Expected outcome

`mise run smoke` ends with a passing workspace cache check that proves a marker written by session A's init is present for session B.

#### Steps

- Red: add the four named tests to `tests/test_smoke_script.py` (its fake API grows `cache` in meta and `status.cache` on sessions); run it: fails.
- Green: the smoke check and the README line; run the verify command.

#### Notes

- Reuse the existing init-scripts wait loop and the cleanup trap; bound every wait by `SMOKE_TIMEOUT_S`.
- The marker check relies on restore running before init (design D3).

- 2026-10-26 done

### S4: web preset cache fields

- Status: done
- Files: `src/sessions/sessionSpecForm.ts`, `src/presets/PresetForm.tsx`, `src/presets/PresetForm.test.tsx`, `openapi/orchestrator.json`, `openapi/orchestrator.source`, `src/api/schema.d.ts`
- Verify: `npx vitest run src/presets/PresetForm.test.tsx && npm run lint && npm run check:api`
- Verified head: 5c7f9d1

#### Requirement

Add the workspace cache to the preset form (design D10; consumes contracts orch-session-spec-cache and orch-meta-cache). Runs after the epic orchestrator-rename-sessions lands and after task cache-key-on-create. Paths are in code/agents-web under the post-rename names (today's `src/clusters/clusterSpecForm.ts` is `src/sessions/sessionSpecForm.ts`; if that epic chose another name, the same symbols `stateFromPreset`, `validate`, `toPresetSpec` apply and the orchestrator amends this file list first).

- Sync the orchestrator API: `openapi/orchestrator.json` copied from `openapi.json` of the agents-orchestrator commit that carries task cache-key-on-create, `openapi/orchestrator.source` set to `agents-orchestrator <that sha>`, `npm run gen:api` regenerates `src/api/schema.d.ts`.
- `sessionSpecForm.ts`: form values `cacheEnabled` (boolean), `cacheKey` (string), `cacheExclude` (string, one glob per line); set key `cache`; `stateFromPreset` reads `spec.cache`; `validate`: the key matches `^[a-z0-9][a-z0-9._-]{0,62}$` (message "Cache key: lowercase letters, digits, '.', '_' and '-', at most 63"), at most 50 exclude lines, each at most 256 characters, not starting with `/`, no `..` segment; `toPresetSpec` writes `cache: {}` plus `key` when non-empty and `exclude` when non-empty, only when the set key `cache` is present and `cacheEnabled` is true; an untouched preset writes no `cache`, and switching the cache off on a stored preset removes it.
- `src/presets/PresetForm.tsx`: a "Workspace cache" section: a Switch "Cache the workspace in S3", a TextField "Cache key" with placeholder "derived from the preset" and helper "Same key, same cache: sessions sharing a key share the workspace (last save wins)", a multiline TextField "Exclude (one glob per line)". When `meta.cache.available` is false the section is disabled with the helper "Workspace cache is not configured on the orchestrator".
- Tests in `src/presets/PresetForm.test.tsx`.

Core tasks in epic workspace-s3-cache that this task depends on (covered by the epic blocker): cache-key-on-create.

#### Acceptance conditions

- AC1: enabling the cache with an empty key saves cache {} [evidence: command:npx vitest run src/presets/PresetForm.test.tsx -t "saves an empty cache when enabled without a key"]
- AC2: a key and exclude lines are saved as cache.key and cache.exclude [evidence: command:npx vitest run src/presets/PresetForm.test.tsx -t "saves the cache key and excludes"]
- AC3: an invalid key or exclude line shows an inline error and blocks saving [evidence: command:npx vitest run src/presets/PresetForm.test.tsx -t "rejects an invalid cache key"]
- AC4: the section is disabled with its note when meta.cache.available is false [evidence: command:npx vitest run src/presets/PresetForm.test.tsx -t "disables the cache section when the orchestrator has no cache"]
- AC5: editing a preset loads its stored cache [evidence: command:npx vitest run src/presets/PresetForm.test.tsx -t "loads a stored cache"]
- AC6: a preset saved without touching the cache carries no cache key [evidence: command:npx vitest run src/presets/PresetForm.test.tsx -t "keeps presets without a cache sparse"]
- AC7: the generated API types match the synced spec [evidence: command:npm run check:api]
- AC8: lint passes [evidence: command:npm run lint]

#### Files

- `src/sessions/sessionSpecForm.ts`
- `src/presets/PresetForm.tsx`
- `src/presets/PresetForm.test.tsx`
- `openapi/orchestrator.json`
- `openapi/orchestrator.source`
- `src/api/schema.d.ts`

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

### S5: deploy pin workspace cache

- Status: done
- Files: `helmfile.yaml.gotmpl`, `values/agents-orchestrator/common.yaml`, `values/agents-web/common.yaml`, `tests/test_orchestrator_release.py`, `tests/test_web_release.py`
- Verify: `uv run pytest -q -p no:cacheprovider tests/test_orchestrator_release.py tests/test_web_release.py tests/test_workspace_cache.py -k "not test_release_chart_version_and_needs and not test_db_secret_matches_rendered_cnpg_cluster and not test_web_release_chart" && uv run ruff check . && uv run ruff format --check .`
- Verified head: 9893b65

#### Requirement

Pin agents-helmfile to the agents-orchestrator and agents-web builds that carry the workspace cache (design D9; precedent docs/plans/done/agent-init-scripts/tasks/deploy-pin-init-scripts.md). Runs after the epic orchestrator-rename-sessions lands (release `agents-orchestrator`, values in `values/agents-orchestrator/`). Paths are in code/agents-helmfile.

Precondition, checked first: this epic's agents-orchestrator PR and agents-web PR are merged to main and their CI published chart `0.1.0-main.<sha7>` and image `<sha7>` for each (`helm show chart oci://harbor.szymonrichert.pl/charts/agents-orchestrator --version 0.1.0-main.<sha7>`, the same for `agents-web`). The orchestrator writes both `<sha7>` values into this task with `ticket.py amend` once the PRs merge; otherwise end `blocked`, whoCanClear "orchestrator: merge the agents-orchestrator and agents-web PRs of workspace-s3-cache and wait for their main CI".

- `helmfile.yaml.gotmpl`: release `agents-orchestrator` version `0.1.0-main.<orchestrator sha7>`; release `agents-web` version `0.1.0-main.<web sha7>`.
- `values/agents-orchestrator/common.yaml`: `image.tag` `<orchestrator sha7>`.
- `values/agents-web/common.yaml`: `image.tag` `<web sha7>`.
- `tests/test_orchestrator_release.py::test_orchestrator_pin_matches_image` and `tests/test_web_release.py::test_web_pin_matches_image` stay the pin checks (update them only if they hard-code a sha).

Core task in epic workspace-s3-cache that this task depends on (covered by the epic blocker): cache-docs.

#### Acceptance conditions

- AC1: the orchestrator chart version and image tag agree on the merge sha [evidence: test:tests/test_orchestrator_release.py::test_orchestrator_pin_matches_image]
- AC2: the agents-web chart version and image tag agree on the merge sha [evidence: test:tests/test_web_release.py::test_web_pin_matches_image]
- AC3: the pinned charts and images exist in Harbor [evidence: judgement:the task notes quote helm show chart for both pinned versions]
- AC4: the offline release tests and lint pass [evidence: command:uv run pytest -q -p no:cacheprovider tests/test_orchestrator_release.py tests/test_web_release.py tests/test_workspace_cache.py -k "not test_release_chart_version_and_needs and not test_db_secret_matches_rendered_cnpg_cluster and not test_web_release_chart" && uv run ruff check . && uv run ruff format --check .]

#### Files

- `helmfile.yaml.gotmpl`
- `values/agents-orchestrator/common.yaml`
- `values/agents-web/common.yaml`
- `tests/test_orchestrator_release.py`
- `tests/test_web_release.py`

#### Interfaces

- Releases `agents-orchestrator` and `agents-web` in `helmfile.yaml.gotmpl`.

#### Expected outcome

agents-helmfile pins the orchestrator and web builds that carry the workspace cache.

#### Steps

- Check the precondition (both charts exist in Harbor); quote `helm show chart` output in the notes.
- Red: run the pin tests after changing only the helmfile versions: they fail on the mismatch.
- Green: the image tags; run the verify command.

#### Notes

- webhook-event-filters (a blocker of this epic) also pins agents-web; take the latest main merge that contains both epics.

- 2026-10-26 done

### S6: apply smoke workspace cache

- Status: done
- Files: `MEMORY.md`
- Verify: `mise run diff && mise run smoke`
- Verified head: 23054c0

#### Requirement

Apply the pinned releases and the bucket claim to the live `agents` namespace and prove the cache with the smoke (design D9; user decision: deployed on rook-ceph). Paths are in code/agents-helmfile. Runs only after tasks deploy-pin-workspace-cache, helmfile-cache-bucket and smoke-workspace-cache are done. The orchestrator runs `mise run apply` itself (live applies are refused in subagents); the apply is never acceptance evidence.

- Implementer, before the apply: `mise run diff`; keep its output in the task notes. Expected: the agents-orchestrator chart version, image tag and cache settings; the agents-web chart version and image tag; the new ObjectBucketClaim `agents-workspace-cache` (raw/ drift). Anything else stops the task `blocked` with the diff, whoCanClear "user". Then end the implementer round with "ready for apply".
- Orchestrator: `mise run apply` (lint, test and the kube-context guard run first; never bypass the guard or set EXPECTED_KUBE_CONTEXT). A failing apply is not retried blindly: read the helm error and report its tail.
- After the apply, implementer: `kubectl -n agents get obc agents-workspace-cache` shows `Bound`; `mise run diff` exits 0 (no drift); `mise run smoke` exits 0 including the workspace cache check.
- `MEMORY.md`: a dated line: applied agents-orchestrator `0.1.0-main.<sha7>` and agents-web `0.1.0-main.<sha7>` with the workspace cache, bucket `agents-workspace-cache` on rook-ceph, smoke green (quote its last log line).
- No other file changes.


Orchestrator ruling 2026-10-26 (the core reviews could not prove these against moto): after the apply, run a one-off read-only probe from inside the reconciler pod, which already holds the S3 credentials, without printing any credential or URL. (1) Presign a PUT URL for a throwaway key `probe-<random>` with the app's own presign and send a GET with it: expect 403 (method is part of the signature). (2) Presign a GET for that key, which does not exist: expect 404, not 403, so a first restore is a cache miss. Run it with `kubectl exec deploy/agents-orchestrator-reconciler -- python -c ...`. No object is created. Quote both status codes in the task notes; any other result stops the task blocked.

#### Acceptance conditions

- AC1: the bucket claim is bound [evidence: command:kubectl -n agents get obc agents-workspace-cache -o jsonpath='{.status.phase}' | grep -qx Bound]
- AC2: the live namespace has no drift from the pinned helmfile after the apply [evidence: command:mise run diff]
- AC3: the smoke passes against the live orchestrator, including the workspace cache check [evidence: command:mise run smoke]
- AC4: MEMORY.md records the applied versions, the bucket and the smoke result [evidence: command:grep -q "agents-workspace-cache" MEMORY.md && grep -q "0.1.0-main" MEMORY.md]
- AC5: the pre-apply diff showed only the expected changes [evidence: judgement:the diff output quoted in the task notes]
- AC-probe: a presigned PUT URL is refused for GET (403) and a GET on a missing key returns 404 [evidence: judgement:the task notes quote both status codes from the one-off reconciler-pod probe]

#### Files

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

- 2026-10-26 amended: live presign proofs as a one-off probe instead of permanent smoke steps

- 2026-10-26 done: Probe from the reconciler pod: PUT-presigned URL used for GET 403, GET on a missing key 404. First smoke failed: RGW 20.2.4 rejects a presigned PUT carrying an unsigned Content-Type (AccessDenied, anonymous); fixed by cache-put-signs-content-type (ea1fac7). A 7-byte object left by the diagnosis probe was verified and deleted. Final smoke OK (.logs/cache-smoke3.log): session B restored session A's marker. Post-apply diff: No affected releases.

## Files to delete

none recorded in the epic format

## Final verify

none recorded in the epic format

## After merge

none
