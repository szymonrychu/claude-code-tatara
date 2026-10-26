---
title: cache job render
status: done
repo: agents-orchestrator
value: "restore and save Jobs run hardened with no credential, and agent pods never see one"
files: [src/agents_orchestrator/reconciler/cache.py, tests/test_cache_jobs_render.py]
verify: "uv run pytest -q tests/test_cache_jobs_render.py tests/test_render.py && uv run ruff check . && uv run ruff format --check ."
depends_on: [cache-config]
model: opus
review: ""
verified_head: 75baef2
points: 3
expected_minutes: 14
expected_tokens: 895472
points_actual: 3
actual_minutes: 6
actual_tokens: 1208222
actual_roles: "impl 5, review 1"
actual_role_tokens: "impl 1097034, review 111188"
---

# cache job render

## Requirement

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

## Acceptance conditions

- AC1: the restore Job runs the cache image with orch cache restore, never the spec image [evidence: test:tests/test_cache_jobs_render.py::test_restore_job_image_and_command]
- AC2: the Job env is exactly the CACHE_* set and HOME, with no spec env, secretKeyRef or envFrom [evidence: test:tests/test_cache_jobs_render.py::test_job_env_has_no_credentials]
- AC3: the save Job mounts the workspace read-only and a scratch emptyDir sized to max bytes [evidence: test:tests/test_cache_jobs_render.py::test_save_job_volumes]
- AC4: the Job pod is hardened: no service account token, non-root, read-only root, no privilege escalation, all capabilities dropped [evidence: test:tests/test_cache_jobs_render.py::test_job_pod_hardened]
- AC5: backoffLimit 2 and activeDeadlineSeconds equal to the cache timeout [evidence: test:tests/test_cache_jobs_render.py::test_job_limits]
- AC6: the agent objects of a cache-enabled session reference no cache credential [evidence: test:tests/test_cache_jobs_render.py::test_agent_pods_carry_no_cache_credentials]
- AC7: the existing render golden tests stay green [evidence: command:uv run pytest -q tests/test_render.py]
- AC8: lint and format pass [evidence: command:uv run ruff check . && uv run ruff format --check .]

## Files

- `src/agents_orchestrator/reconciler/cache.py`
- `tests/test_cache_jobs_render.py`

## Interfaces

- `reconciler/cache.py:restore_job_name`, `save_job_name`, `CACHE_LABEL`, `render_cache_job(session, settings, action, url) -> Obj`.
- Reuses `k8s/render.py:workdir_mount`, `workdir_path`, `WORKSPACE_VOLUME`, `k8s/labels.py:session labels`, `prefix`.

## Expected outcome

`render_cache_job(s, settings, "save", url)` is a `batch/v1` Job `<prefix>-cache-save` running `orch cache save` in `settings.cache_image`, workspace mounted read-only, no credential anywhere in its spec.

## Steps

- Red: write `tests/test_cache_jobs_render.py` (the six named tests, sessions from `tests/factories.py`); run it: fails.
- Green: write the render part of `reconciler/cache.py`; run the verify command.

## Notes

- Mirror `reconciler/init.py:render_init_job` (pull secret, labels, PVC volume) but with the hardening and env rules of the requirement.
- `readOnlyRootFilesystem` needs the `/tmp` emptyDir and `HOME=/tmp`.
- The save Job mounts the same `workdir_mount` with `readOnly: true`.

- 2026-10-25 done
