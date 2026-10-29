---
title: orch chart cache quota
status: todo
repo: agents-orchestrator
value: The bucket quota can be set through the orchestrator chart so the Cache section shows its gauge
files: [chart/agents-orchestrator/values.yaml, chart/agents-orchestrator/templates/configmap.yaml, chart/agents-orchestrator/README.md, tests/test_chart_cache.py]
verify: "uv run --frozen pytest -q -p no:cacheprovider tests/test_chart_cache.py && mise run lint:chart && mise run lint"
depends_on: [orch-cache-api]
model: sonnet
review: ""
verified_head: ""
points: 2
expected_minutes: 5
expected_tokens: 545296
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# orch chart cache quota

## Requirement

User request (2026-10-29 04:52Z, mx-34 #343), verbatim: "I want to have dedicated section (as presets, sessions, webhooks) for s3 cache management."

README Goal G5, verbatim: "a quota gauge shows bytes and objects against the bucket quota set in agents-helmfile; released and deployed, and proven live by listing the bucket and deleting one disposable object."

Design D7 (Quota settings), verbatim: "`ORCH_CACHE_QUOTA_BYTES` and `ORCH_CACHE_QUOTA_OBJECTS` (default unset, gauge hidden), set in agents-helmfile values from the OBC quota (100G, 100000). User Q4."

Architecture brief, verbatim: "Quota: settings `ORCH_CACHE_QUOTA_BYTES`, `ORCH_CACHE_QUOTA_OBJECTS` (chart default null, gauge hidden), set in agents-helmfile next to the OBC."

This task delivers the chart part of D7 in agents-orchestrator: chart values `cache.quota.bytes` and `cache.quota.objects` (default null); the settings ConfigMap renders `ORCH_CACHE_QUOTA_BYTES` and `ORCH_CACHE_QUOTA_OBJECTS` as exact integer strings only when each is set and the bucket is set (the ConfigMap reaches every component, so the api reads them); the chart README documents both values; the S3 credentials stay on the reconciler container only.

tests/test_chart_cache.py::test_readme_documents_cache_values lists every documented cache value, so it gains `cache.quota.bytes` and `cache.quota.objects` (extended, not weakened).

## Acceptance conditions

- AC1: with cache.quota.bytes and cache.quota.objects set, the settings ConfigMap carries ORCH_CACHE_QUOTA_BYTES and ORCH_CACHE_QUOTA_OBJECTS and the api Deployment reads that ConfigMap [evidence: test:tests/test_chart_cache.py::test_configmap_cache_quota_env]
- AC2: with the quota unset, or without a bucket, neither variable is rendered [evidence: test:tests/test_chart_cache.py::test_no_quota_no_env]
- AC3: a quota of 100000000000 bytes renders as the exact string "100000000000", never a float or an exponent [evidence: test:tests/test_chart_cache.py::test_quota_renders_large_integers]
- AC4: the S3 credentials are still on the reconciler container only [evidence: test:tests/test_chart_cache.py::test_credentials_only_on_reconciler]
- AC5: the chart README documents the cache values including cache.quota.bytes and cache.quota.objects [evidence: test:tests/test_chart_cache.py::test_readme_documents_cache_values]
- AC6: chart lint and lint pass [evidence: command:mise run lint:chart && mise run lint]

## Files

- `chart/agents-orchestrator/values.yaml`
- `chart/agents-orchestrator/templates/configmap.yaml`
- `chart/agents-orchestrator/README.md`
- `tests/test_chart_cache.py`

## Interfaces

- `chart/agents-orchestrator/values.yaml`: under `cache`, `quota: {bytes: null, objects: null}` with comments (bucket total quota shown by the web Cache section gauge; null hides the gauge).
- `chart/agents-orchestrator/templates/configmap.yaml`: inside the existing `cache.s3.bucket` block, `ORCH_CACHE_QUOTA_BYTES: {{ .quota.bytes | int64 | toString | quote }}` when set, same for objects.
- Settings consumed: `cache_quota_bytes`, `cache_quota_objects` (task orch-cache-api).

## Expected outcome

agents-helmfile can set the quota through `cache.quota` values, and the api's `GET /api/v1/cache` reports it; an unset quota renders nothing and the gauge stays hidden.

## Steps

- Read `chart/agents-orchestrator/values.yaml` (cache block), `templates/configmap.yaml`, `templates/deployment.yaml` (envFrom per component), the chart README and `tests/test_chart_cache.py` (`render`, `_settings`, `_deployments`) in one pass.
- Red: add `test_configmap_cache_quota_env`, `test_no_quota_no_env` and `test_quota_renders_large_integers`; run `uv run --frozen pytest -q -p no:cacheprovider tests/test_chart_cache.py`; expect the three to fail.
- Green: add the values, the template lines and the README rows; rerun; expect passed; `mise run lint:chart && mise run lint`; expect exit 0.

## Notes

- Retro (matrix-connector-agent-initi): a chart value that reaches only some containers passed every test and failed live; AC1 asserts the api Deployment actually reads the settings ConfigMap.
- Helm reads large YAML integers as float64; `int64 | toString` is the existing pattern (`ORCH_CACHE_MAX_BYTES`).
- These tests render with the local helm binary and need no Postgres, so they run locally.
- Builds after decouple-s3-session-cache-fr and live-session-transcript-back landed on main (README blockers). Use their names as landed: `cache/naming.py` (`render_cache_name`, `DEFAULT_CACHE_NAME_TEMPLATE`), `cache/copy.py`, `reconciler/cache_migration.py`, and `status.cache` `key`, `object`, `sessions_object`, `restore`, `save`, `sessions_restore`, `sessions_save`, `sessions_backup`, `migration`. Read the landed code first; where a landed name differs from this task's text, use the landed name and say so in the task Notes, never guess.
- Tree state: `mise run lint` green. Tests that use the `pool`/`dsn` fixtures need Postgres through testcontainers; agent pods have no Docker, so they error locally (`DockerException`) and run in CI on the PR: the reviewer reads the CI job for them and quotes its summary line. Pure and moto-only tests run locally. `tests/test_reconciler.py::test_lightkube_default_client_uses_env_config` fails in-cluster for an unrelated reason (KUBERNETES_SERVICE_HOST).
- If a verify run fails, save the failing test name and the output tail before any rerun (retro, recurring).
- Before working read the repo's AGENTS.md, MEMORY.md and ROADMAP.md. No em dashes. No backward-compatibility shims.

- 2026-10-29 amended: planner filled Interfaces, Expected outcome, Steps and Notes before the gate (retro: no empty Steps)
