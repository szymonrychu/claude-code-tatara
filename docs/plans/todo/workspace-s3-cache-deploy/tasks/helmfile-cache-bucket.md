---
title: helmfile cache bucket
status: todo
repo: agents-helmfile
value: the deployment gets its own rook-ceph bucket wired into the orchestrator
files: [raw/workspace-cache-bucket.pre.yaml, values/agents-orchestrator/common.yaml, tests/test_workspace_cache.py]
verify: "uv run pytest -q -p no:cacheprovider tests/test_workspace_cache.py && uv run ruff check . && uv run ruff format --check ."
depends_on: []
model: sonnet
review: ""
verified_head: ""
points: 2
expected_minutes: 5
expected_tokens: 531208
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# helmfile cache bucket

## Requirement

Provision the cache bucket on rook-ceph and wire it into the orchestrator release (design D9). Runs after the epic orchestrator-rename-sessions lands: the release is `agents-orchestrator` and its values live in `values/agents-orchestrator/` (if that epic chose other names, the orchestrator amends this file list first). Paths are in code/agents-helmfile. Rook-ceph specifics live only here.

- `raw/workspace-cache-bucket.pre.yaml`: `apiVersion: objectbucket.io/v1alpha1`, `kind: ObjectBucketClaim`, name `agents-workspace-cache`, namespace `agents`, `spec {bucketName: agents-workspace-cache, storageClassName: rook-ceph-bucket}`; a comment that the StorageClass `reclaimPolicy` is `Delete`, so deleting this claim deletes the bucket and every cache. `.hook.sh` applies it at presync.
- `values/agents-orchestrator/common.yaml`: `cache.s3 {endpoint: http://rook-ceph-rgw-ceph-objectstore.rook-ceph.svc:80, region: us-east-1, bucket: agents-workspace-cache, pathStyle: true, existingSecret: agents-workspace-cache}` (rook creates Secret `agents-workspace-cache` with `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`, the chart's default key names), with a comment naming the claim.
- `tests/test_workspace_cache.py`.

Core tasks in epic workspace-s3-cache that this task depends on (covered by the epic blocker): cache-chart-values.


Orchestrator ruling 2026-10-26 (epic security review, medium): nothing bounds the bucket total (5 GiB per key, unbounded keys), so set a bucket quota on the ObjectBucketClaim (rook additionalConfig maxSize, for example 100Gi, and maxObjects if supported by the deployed rook version; verify against the live CRD), configurable in values, and test the render.

## Acceptance conditions

- AC1: the claim is an ObjectBucketClaim in agents with the fixed bucket name and the rook-ceph-bucket StorageClass [evidence: test:tests/test_workspace_cache.py::test_bucket_claim_shape]
- AC2: the raw file is picked up at presync (name ends in .pre.yaml, under raw/) [evidence: test:tests/test_workspace_cache.py::test_bucket_claim_applied_at_presync]
- AC3: the orchestrator values point the cache at the rgw endpoint, path style, the claim's bucket and Secret [evidence: test:tests/test_workspace_cache.py::test_orchestrator_cache_values]
- AC4: no access key or secret literal appears in any plain values file [evidence: test:tests/test_workspace_cache.py::test_no_cache_credentials_in_values]
- AC5: lint and format pass [evidence: command:uv run ruff check . && uv run ruff format --check .]
- AC-quota: the bucket claim sets a size quota from values [evidence: test:tests/test_cache_bucket.py::test_bucket_quota_set]

## Files

- `raw/workspace-cache-bucket.pre.yaml`
- `values/agents-orchestrator/common.yaml`
- `tests/test_workspace_cache.py`

## Interfaces

See the Requirement; no new cross-repo contract.

## Expected outcome

Every acceptance condition holds on the committed HEAD.

## Steps

- Red: write the AC tests; run the task verify: they fail.
- Green: implement the Requirement; rerun the verify: they pass.
- Run the repo's full suite and lint: green.

## Notes

- See the Requirement and the epic design.md.

- 2026-10-26 amended: epic security review: bucket quota
