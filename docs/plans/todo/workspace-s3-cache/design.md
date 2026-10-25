# Workspace S3 cache design

## Summary

Optional, per-preset workspace caching in S3, modelled on GitLab runner caches. When a session with
`spec.cache` starts, the reconciler runs a restore Job that downloads `<prefix><key>.tar.zst` and
unpacks it into the session workdir before the init scripts and the Claude sessions start; when the
session ends (delete, idle autoclose, trigger close) the reconciler stops the agent pods, runs a save
Job that archives the workdir and uploads it under the same object name, then discards the session.
The S3 credentials live only in the reconciler, which hands each Job one presigned, short-lived URL
for one object; agent pods and Job pods never hold a credential. Configuration is generic S3
(endpoint, region, bucket, credentials Secret, path-style flag); the rook-ceph ObjectBucketClaim lives
only in agents-helmfile. Written in post-rename names: this epic runs after orchestrator-rename-sessions
(agent-orchestrator becomes agents-orchestrator, cluster becomes session).

## Intent and why

User request 2026-10-25: "S3 based workspace caching similar to caching in gitlab runners- when
cluster/session starts, workspace is getting downloaded from S3, when it ends it's getting uploaded
back to S3 (use zip or something to prepare archive, reuse the same name). Deploy using rook-ceph s3,
but configuration must be generic and not assume anything about infra system will run on. Caching is
an optional feature, preset coupled with preset. Optionally user can provide cache slug, by default
it's pseudorandom (preset derived) string."

Every session starts from an empty RWX PVC today, so repeated sessions of one preset (webhook and
schedule triggers especially) re-clone repos and re-install dependencies each time. A cache keyed per
preset carries the workspace from one session to the next.

## Goals

- G1: A preset (and a session spec) can enable the workspace cache; it is off unless set.
- G2: The cache key is the user-supplied slug, or by default a pseudorandom string derived from the
  preset id, resolved into the session spec at create.
- G3: At session start the archive is downloaded and unpacked into the workdir before init scripts
  and Claude sessions run; a missing object is a cache miss, not an error.
- G4: At session end the workdir is archived and uploaded under the same object name before the PVC
  is deleted, on every deletion path that goes through the discard (explicit delete, idle autoclose,
  trigger close).
- G5: No S3 credential reaches an agent pod or a Job pod; only the reconciler holds it.
- G6: S3 configuration is generic (endpoint, region, bucket, prefix, path-style, TLS verify,
  credentials Secret); nothing in agents-orchestrator assumes rook-ceph.
- G7: agents-helmfile provisions the bucket on rook-ceph (ObjectBucketClaim) and wires it into the
  orchestrator release; agents-web exposes the cache in the preset form.
- G8: The live smoke proves a value written in one session is restored in the next.

## Non-goals

- Caching anything outside the session workdir (the per-pod `/sessions` transcripts, `/opt/mise`,
  `/opt/any-mcp`).
- Periodic or mid-session saves; saving on agent pod restart, crash or node loss (the PVC survives
  those; only the session end saves).
- A cache delete, list or eviction API, and S3 lifecycle rules; objects stay until removed by hand.
- Locking or merging between concurrent sessions sharing a key (D4: last writer wins).
- Showing `status.cache` in the web UI session views (it is in the API status).
- Any change to claude-code-wrapper.
- Uploading through the agent pod, the wrapper or a sidecar (D1).

## Anti-goals

- An S3 access key or secret key in any pod spec except the reconciler Deployment.
- A failed or timed-out restore followed by a save that replaces a good archive with a partial or
  empty workspace.
- A session deletion held forever by an unreachable S3 endpoint (the PVC must still be discarded).
- rook-ceph names, the rgw Service or ObjectBucketClaim types anywhere in agents-orchestrator.
- An archive member that writes outside the workdir on restore (absolute paths, `..`, escaping links,
  device nodes).

## Constraints

- Runs after orchestrator-rename-sessions lands: every task uses `code/agents-orchestrator`,
  `src/agents_orchestrator`, `SessionSpec`, `api/sessions.py`, `db/sessions.py` and the chart
  `chart/agents-orchestrator`. If that epic picked other module names, the same symbols apply
  (today: `ClusterSpec` in `spec.py`, `_create_from_preset` in `api/clusters.py`,
  `Reconciler._converge` and `_discard` in `reconciler/loop.py`); the orchestrator amends task file
  lists with `ticket.py amend` before claiming the epic.
- Python only (orchestrator, Job CLI); TypeScript only in agents-web.
- Services talk through HTTP APIs; the reconciler stays the only writer of `sessions.status`.
- Single-PUT upload: S3 and RGW cap one PUT at 5 GiB, so `ORCH_CACHE_MAX_BYTES` is at most
  5368709120.
- Deploy: the orchestrator runs `mise run apply` in agents-helmfile itself; it is never AC evidence.
  The live kube context is guarded by agents-helmfile's `kube-context` task.

## Decisions

### D1: Transfer runs in orchestrator-created Jobs

Decision: the reconciler creates a restore Job `<prefix>-cache-restore` on the first converge of a
session with `spec.cache`, and a save Job `<prefix>-cache-save` during the discard, both mounting the
session PVC (save read-only), running the orchestrator image (`ORCH_CACHE_IMAGE`, the chart sets it to
its own image) with the fixed command `orch cache restore|save`. Same crash-safe shape as the init
Job (`reconciler/init.py`: state written before create, `job` after, outcome from the pod log, Job
deleted after the outcome).

| Option | Credential exposure | Deletion paths | Upload time bound | Multi-replica |
|---|---|---|---|---|
| Init container + preStop hook in the agent pod | preStop runs in the agent container: the credential is in the agent's env | preStop does not run on node loss or OOM kill; scale-down of one replica also fires it | capped by terminationGracePeriodSeconds (90 s) | every replica uploads |
| Sidecar in the agent pod | separate env, but the Secret is in the agent pod spec | same as preStop | same grace cap | every replica uploads |
| claude-code-wrapper | the agent process's own runtime holds the credential | wrapper shutdown only | grace cap | every replica uploads |
| Orchestrator process itself | none in pods | all discard paths | none | once | 
| **Orchestrator-created Job (chosen)** | none (D2) | every path through `_discard` | own `activeDeadlineSeconds` | once per session |

The orchestrator process cannot mount per-session PVCs, so it cannot archive the workspace itself.
The Job keeps the upload off the agent pod's grace period and runs once per session, not per replica.

### D2: Presigned URLs; credentials only in the reconciler

Decision: the reconciler holds the S3 access key and secret (`ORCH_CACHE_S3_ACCESS_KEY_ID`,
`ORCH_CACHE_S3_SECRET_ACCESS_KEY`, set by the chart from a Secret only on the reconciler Deployment)
and presigns one GET (restore) or one PUT (save) URL per Job with botocore, expiring after
`ORCH_CACHE_TIMEOUT_SECONDS + 600`. The Job pod gets only `CACHE_URL`; no Secret is referenced by any
Job or agent pod. Alternative: credentials as Secret env in the Job pod (bucket-wide access in a pod
that reads agent-written data); rejected. This mirrors GitLab runner, which presigns and hands the
helper a URL (https://docs.gitlab.com/runner/configuration/advanced-configuration/#the-runnerscaches3-section).
Job pods: `automountServiceAccountToken: false`, uid 1000, `runAsNonRoot`, `readOnlyRootFilesystem`,
`allowPrivilegeEscalation: false`, capabilities drop ALL, no `spec.env`, never `spec.image`.

### D3: Lifecycle and deletion paths

Decision: restore once per session (like init), before init; save once per session, in `_discard`
after `_quiesce` and before the pre-discard hook and the prune. `_quiesce` scales the StatefulSet to
zero whenever a save is owed (today only when a hook is owed). Paths:
- explicit delete, idle autoclose (`close_expired`), trigger close: all set `desired=deleting`, so
  all save.
- agent pod crash, restart command, node loss of an agent pod: the PVC survives, nothing runs.
- quiesce timeout with pods still running: save anyway, logged (the archive may catch a live write).
- node loss or eviction of a Job pod: `backoffLimit: 2` retries; a single PUT is atomic, so a
  partial upload never replaces the object.
- reconciler crash mid-step: level-triggered from `status.cache`, as the init runner.
- namespace or release deletion without the reconciler: no save (out of scope).
(my call)

### D4: Concurrent sessions sharing a key: last writer wins

Decision: no locking; each save is one atomic PUT, so the last finished save wins and a restore reads
one whole object. The default key is per preset, so concurrent trigger sessions of one preset share
it, as GitLab jobs share a cache key. Alternatives: refuse a second session holding a key (breaks
concurrent trigger sessions); conditional PUT on the restored ETag (RGW support for `If-Match` on PUT
is not guaranteed across versions). (my call; gate question Q1)

### D5: Archive format tar + zstd, same object name

Decision: `tar` streamed through `zstandard` into `<ORCH_CACHE_S3_PREFIX><key>.tar.zst`
(prefix default `workspace-cache/`). tar keeps modes and symlinks and streams; Python's `zipfile`
restores neither permissions nor symlinks. Save never follows symlinks and skips sockets, FIFOs and
device files; restore uses `tarfile` filter `data` (no absolute paths, no `..`, no links out of the
workdir, no device nodes, setuid bits cleared) and never deletes anything already in the workdir.
Excludes: `.agent-init` always, plus `spec.cache.exclude` (fnmatch globs on the workdir-relative
POSIX path; a matching directory prunes its subtree). (my call)

### D6: Size cap and timeout

Decision: `ORCH_CACHE_MAX_BYTES` (default 5368709120, at most that) caps the compressed archive; the
save Job writes it to an `emptyDir` with that `sizeLimit` and stops with `too_large` when the cap is
passed, leaving the previous object untouched. `ORCH_CACHE_TIMEOUT_SECONDS` (default 1800) is each
Job's `activeDeadlineSeconds`. (my call; gate question Q2)

### D7: Spec field and cache key

Decision: `SessionSpec.cache: WorkspaceCache | None = None`, `WorkspaceCache {key: str | None,
exclude: list[str] = []}`, sparse (unset is not stored in a preset). Presence enables the cache.
`key` matches `^[a-z0-9][a-z0-9._-]{0,62}$`; `exclude` at most 50 entries, each non-empty, at most 256
characters, not absolute, no `..` segment. At `POST /api/v1/sessions` with `preset_id`, a cache without
a key gets `default_cache_key(preset.id)` = `"preset-" + sha256(b"workspace-cache:" +
preset_id.bytes).hexdigest()[:16]`, written into the session spec; with a raw `spec`, a cache without a
key is a 422 `cache.key is required without a preset`. A copied preset gets a new id and so a new
default key. Derived from the immutable id, not the name, so a rename keeps the cache. (my call)

### D8: Generic S3 configuration

Decision: settings `ORCH_CACHE_S3_ENDPOINT` (empty: the AWS default), `ORCH_CACHE_S3_REGION`
(default `us-east-1`), `ORCH_CACHE_S3_BUCKET` (empty: cache unavailable), `ORCH_CACHE_S3_PREFIX`,
`ORCH_CACHE_S3_PATH_STYLE` (bool), `ORCH_CACHE_S3_VERIFY_TLS` (bool, default true),
`ORCH_CACHE_S3_ACCESS_KEY_ID`, `ORCH_CACHE_S3_SECRET_ACCESS_KEY`, `ORCH_CACHE_IMAGE`,
`ORCH_CACHE_MAX_BYTES`, `ORCH_CACHE_TIMEOUT_SECONDS`. `Settings.cache_available` is
`bool(cache_s3_bucket)`; the reconciler refuses to start with a bucket but no credentials or image
(`require_cache()`, like `require_agent_image()`). A spec with `cache` while unavailable fails
validation, except an unchanged cache on a preset PUT (the `stored` rule). Chart values `cache.s3
{endpoint, region, bucket, prefix, pathStyle, verifyTls, existingSecret, accessKeyIdKey (default
AWS_ACCESS_KEY_ID), secretAccessKeyKey (default AWS_SECRET_ACCESS_KEY)}`, `cache.image` (default the
chart's own image), `cache.maxBytes`, `cache.timeoutSeconds`. `GET /api/v1/meta` gains `cache
{available, max_bytes}`.

### D9: Rook-ceph lives only in agents-helmfile

Decision: `raw/workspace-cache-bucket.pre.yaml` is an ObjectBucketClaim `agents-workspace-cache` in
namespace `agents`, `storageClassName: rook-ceph-bucket`, `bucketName: agents-workspace-cache`
(applied at presync by `.hook.sh`); rook creates Secret `agents-workspace-cache` with
`AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` (probed on live OBC `monitoring/loki-bucket`).
Orchestrator values: endpoint `http://rook-ceph-rgw-ceph-objectstore.rook-ceph.svc:80`, region
`us-east-1` (StorageClass parameter), bucket `agents-workspace-cache`, `pathStyle: true`,
`existingSecret: agents-workspace-cache`.

### D10: Web preset form

Decision: the preset form gets a "Workspace cache" section: an enable switch, a cache key field
(placeholder "derived from the preset", validated with the D7 pattern), and an exclude list (one glob
per line). Disabled with a note when `meta.cache.available` is false. Sparse save: `cache` only when
enabled.

### D11: Failure policy

Decision: `status.cache = {key, object, restore {state, started_at, finished_at, bytes, reason, job},
save {...}}`. Restore states `running | restored | miss | failed`; save states `running | saved |
skipped | failed`. Restore `running` holds init and the Claude sessions (phase pending); `failed`
lets them start with phase degraded and message `cache restore failed: <reason>`. Save is `skipped`
when the restore never finished (`restore_running`), failed before extracting (`download_failed`),
timed out (`timeout`), or the cache is unavailable (`not_configured`), or the workdir does not exist
(`no_workdir`); after `extract_failed` the save proceeds, so a corrupt archive is replaced. A failed
save (`too_large`, `upload_failed`, `timeout`, `job_missing`, `foreign_object`, `job_create_failed`, `bad_output`: a Complete Job whose last log line is not the JSON outcome) is logged and the discard continues. The
CLI prints its outcome as the last stdout line, one JSON object `{"outcome", "bytes", "reason"}`,
which the reconciler reads from the log tail. (my call)

### D12: Contracts

Decision: the epic owns contracts `orch-session-spec-cache` (schema), `orch-session-status-cache`
(schema), `orch-cache-settings-env` (schema), `orch-cache-job-cli` (interface), `orch-meta-cache`
(api) and `agents-orchestrator-chart-cache` (release, extends the rename epic's `agents-orchestrator-chart`
with `cache` values); consumers agents-web and agents-helmfile. Registered in `docs/plans/contracts.json`.

## Research

| Lens | Ran or skipped | Adopted | Rejected |
|---|---|---|---|
| research-code-internal | skipped: own recon of the init Job runner, the discard path and the render module covered the reuse (`reconciler/init.py`, `reconciler/loop.py:_discard`, `k8s/render.py`) | reuse the init Job state machine shape and `checks.log_tail` | a new controller loop |
| research-code-external | skipped as a lens; GitLab runner cache docs read directly | presigned URLs (https://docs.gitlab.com/runner/configuration/advanced-configuration/#the-runnerscaches3-section), last writer wins and one object per key (https://docs.gitlab.com/ci/caching/) | zip archives (GitLab's format; loses modes and symlinks in Python) |
| research-docs | skipped: OBC shape probed read-only on the live cluster (`kubectl get obc -A`, `monitoring/loki-bucket` Secret keys), botocore presign and tarfile `data` filter are documented stable APIs the builder exercises in tests | OBC with fixed `bucketName` | reading the OBC ConfigMap from the orchestrator |
| research-papers | skipped: no algorithmic core | none | none |

## Research inputs

- The init Job runner is the template for both cache Jobs (`code/agent-orchestrator/src/agent_orchestrator/reconciler/init.py`) - cache-restore-runner, cache-save-on-discard.
- `_quiesce` scales to zero only when a hook is owed (`reconciler/loop.py:_quiesce`) - cache-save-on-discard.
- Agent pods reference no ServiceAccount and the default SA has no RBAC; the cache Secret is not referenced by any pod (live probe 2026-10-25) - cache-job-render.
- rook OBC Secret keys are `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`; ConfigMap `BUCKET_REGION` is empty, StorageClass region `us-east-1` (live probe) - helmfile-cache-bucket.
- Raw manifests `raw/*.pre.yaml` are applied at presync by `.hook.sh` (`code/agents-helmfile/.hook.sh:apply_dir`) - helmfile-cache-bucket.
- Prior deploy tasks pin the orchestrator chart only after its main CI publishes (`docs/plans/done/agent-init-scripts/tasks/deploy-pin-init-scripts.md`) - deploy-pin-workspace-cache.
- Retro improvement (test-temp-dirs-outside-the-c): for any task that deletes or writes into a computed path, check what runs when the producing step fails or the variable is empty - cache-archive (restore never deletes, refuses an empty `CACHE_DIR`), cache-save-on-discard.

## Decision coverage

| Decision | Tasks |
|---|---|
| D1 Transfer runs in orchestrator-created Jobs | cache-job-render, cache-restore-runner, cache-save-on-discard, cache-transfer-cli |
| D2 Presigned URLs; credentials only in the reconciler | cache-presign, cache-job-render, cache-chart-values |
| D3 Lifecycle and deletion paths | cache-restore-runner, cache-save-on-discard |
| D4 Last writer wins | cache-transfer-cli, cache-docs |
| D5 Archive format tar + zstd | cache-archive |
| D6 Size cap and timeout | cache-config, cache-archive, cache-job-render |
| D7 Spec field and cache key | cache-config, cache-key-on-create |
| D8 Generic S3 configuration | cache-config, cache-key-on-create, cache-chart-values |
| D9 Rook-ceph lives only in agents-helmfile | helmfile-cache-bucket, deploy-pin-workspace-cache, apply-smoke-workspace-cache |
| D10 Web preset form | web-preset-cache-fields |
| D11 Failure policy | cache-restore-runner, cache-save-on-discard, cache-docs |
| D12 Contracts | cache-docs, smoke-workspace-cache |

## Review focus

- No Secret reference, `AWS_*` or `ORCH_CACHE_S3_*` credential env in the agent StatefulSet or the
  Job pods; credentials only on the reconciler Deployment.
- Restore extraction safety (filter `data`, no deletes, empty `CACHE_DIR` refused) and save never
  following symlinks.
- The save skip rules: no save after a restore that did not finish or failed before extracting.
- `_quiesce` and `_discard` ordering: the save Job runs before the prune deletes the PVC, and a failed
  save never blocks the discard.
- Crash safety of both runners (state before create, `job` after).

## Left to the builder

- Internal module layout under `src/agents_orchestrator/cache/` beyond the named entry points.
- The zstd compression level (fast levels, 1 to 6).
- The HTTP fake used to test the CLI, and moto's server mode for the presign round trip.

## Assumptions and unknown facts

- The rename epic keeps `prefix(slug)` object naming and the `status` JSON column; confirmed by
  reading its merged diff before claiming this epic (orchestrator).
- RGW accepts presigned SigV4 GET and PUT with path-style URLs: standard; proven live by
  smoke-workspace-cache.
- Harbor publishes the orchestrator chart `0.1.0-main.<sha7>` on main merge (previous epics); the pin
  task checks it.

## Open questions

- Q1: Concurrent sessions sharing one cache key (the default for every session of a preset): last finished save wins, with no locking, as GitLab runner caches do? [answer: yes, recommended answer (user: 'Go' on the combined gate, 2026-10-25)]
- Q2: Cap one cache archive at 5 GiB compressed (the single-PUT limit) by default, where a bigger save fails and keeps the previous archive? [recommended: yes, 5 GiB default, configurable lower]

## Irreversible operations in scope

- Each save overwrites the previous archive of its key (no bucket versioning): by design (user
  decision: same object name).
- The live apply creates bucket `agents-workspace-cache` through an ObjectBucketClaim on StorageClass
  `rook-ceph-bucket`, whose `reclaimPolicy` is `Delete`: deleting the OBC later deletes the bucket and
  every cache. The apply is covered by the gate; no task deletes the OBC.
