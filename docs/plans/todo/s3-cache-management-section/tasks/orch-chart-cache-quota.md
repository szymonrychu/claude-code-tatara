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

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
