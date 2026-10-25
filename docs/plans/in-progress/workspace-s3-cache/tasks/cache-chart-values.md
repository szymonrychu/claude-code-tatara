---
title: cache chart values
status: in-progress
repo: agents-orchestrator
value: "operators configure any S3 store through chart values, with credentials on the reconciler only"
files: [chart/agents-orchestrator/values.yaml, chart/agents-orchestrator/templates/configmap.yaml, chart/agents-orchestrator/templates/deployment.yaml, chart/agents-orchestrator/README.md, chart/agents-orchestrator/ci/lint-values.yaml, tests/test_chart_cache.py]
verify: "uv run pytest -q tests/test_chart_cache.py tests/test_chart_config.py tests/test_chart_deployments.py && uv run ruff check . && uv run ruff format --check ."
depends_on: [cache-config]
model: opus
review: ""
verified_head: ""
points: 3
expected_minutes: 14
expected_tokens: 895472
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# cache chart values

## Requirement

Expose the cache configuration in the chart, credentials on the reconciler only (design D2, D8; extends contract agents-orchestrator-chart). Runs after the epic orchestrator-rename-sessions lands. Paths are in code/agents-orchestrator under the post-rename names (design Constraints: if that epic chose other module names, the same symbols apply and the orchestrator amends this file list first).

Chart `chart/agents-orchestrator`:
- `values.yaml`: `cache.s3 {endpoint: "", region: us-east-1, bucket: "", prefix: workspace-cache/, pathStyle: false, verifyTls: true, existingSecret: "", accessKeyIdKey: AWS_ACCESS_KEY_ID, secretAccessKeyKey: AWS_SECRET_ACCESS_KEY}`, `cache.image: ""` (empty: the chart's own `image.repository:image.tag`, tag defaulting to the appVersion), `cache.maxBytes: 5368709120`, `cache.timeoutSeconds: 1800`; each commented.
- `templates/configmap.yaml`: with `cache.s3.bucket` set: `ORCH_CACHE_S3_ENDPOINT`, `ORCH_CACHE_S3_REGION`, `ORCH_CACHE_S3_BUCKET`, `ORCH_CACHE_S3_PREFIX`, `ORCH_CACHE_S3_PATH_STYLE`, `ORCH_CACHE_S3_VERIFY_TLS`, `ORCH_CACHE_IMAGE`, `ORCH_CACHE_MAX_BYTES`, `ORCH_CACHE_TIMEOUT_SECONDS`; none of them when it is empty.
- `templates/deployment.yaml`: the reconciler container only gets `ORCH_CACHE_S3_ACCESS_KEY_ID` and `ORCH_CACHE_S3_SECRET_ACCESS_KEY` as `secretKeyRef` to `cache.s3.existingSecret` with the two key names; `fail` when `cache.s3.bucket` is set without `existingSecret`. The api, dispatcher and ingester containers get no cache credential.
- `README.md` (chart): the `cache` values. `ci/lint-values.yaml`: a cache block so `helm lint` renders it.

## Acceptance conditions

- AC1: with a bucket set the settings ConfigMap carries every non-secret ORCH_CACHE_* value [evidence: test:tests/test_chart_cache.py::test_configmap_cache_env]
- AC2: with no bucket the ConfigMap has no ORCH_CACHE_* key [evidence: test:tests/test_chart_cache.py::test_no_cache_no_env]
- AC3: only the reconciler container gets the credential env, from the existing Secret's keys [evidence: test:tests/test_chart_cache.py::test_credentials_only_on_reconciler]
- AC4: a bucket without existingSecret fails the render [evidence: test:tests/test_chart_cache.py::test_bucket_requires_secret]
- AC5: the cache image defaults to the chart's own image [evidence: test:tests/test_chart_cache.py::test_cache_image_defaults_to_chart_image]
- AC6: the existing chart tests stay green [evidence: command:uv run pytest -q tests/test_chart_config.py tests/test_chart_deployments.py tests/test_chart_ci.py]
- AC7: lint and format pass [evidence: command:uv run ruff check . && uv run ruff format --check .]

## Files

- `chart/agents-orchestrator/values.yaml`
- `chart/agents-orchestrator/templates/configmap.yaml`
- `chart/agents-orchestrator/templates/deployment.yaml`
- `chart/agents-orchestrator/README.md`
- `chart/agents-orchestrator/ci/lint-values.yaml`
- `tests/test_chart_cache.py`

## Interfaces

- Chart values `cache.*` (extends contract `agents-orchestrator-chart`); env names from contract `orch-cache-settings-env`.

## Expected outcome

`helm template` with `cache.s3.bucket=b, cache.s3.existingSecret=s` renders the ORCH_CACHE_* ConfigMap keys and the two credential `secretKeyRef`s on the reconciler container only.

## Steps

- Red: write `tests/test_chart_cache.py` with `tests/helm_render.py` (the five named tests); run it: fails.
- Green: values, templates, chart README and `ci/lint-values.yaml`; run the verify command.

## Notes

- The reconciler-only block already exists in `templates/deployment.yaml` (`if eq $component "reconciler"`).
- The image default follows the chart's existing image tag helper (appVersion when `image.tag` is empty).
