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

## Acceptance conditions

- AC1: the claim is an ObjectBucketClaim in agents with the fixed bucket name and the rook-ceph-bucket StorageClass [evidence: test:tests/test_workspace_cache.py::test_bucket_claim_shape]
- AC2: the raw file is picked up at presync (name ends in .pre.yaml, under raw/) [evidence: test:tests/test_workspace_cache.py::test_bucket_claim_applied_at_presync]
- AC3: the orchestrator values point the cache at the rgw endpoint, path style, the claim's bucket and Secret [evidence: test:tests/test_workspace_cache.py::test_orchestrator_cache_values]
- AC4: no access key or secret literal appears in any plain values file [evidence: test:tests/test_workspace_cache.py::test_no_cache_credentials_in_values]
- AC5: lint and format pass [evidence: command:uv run ruff check . && uv run ruff format --check .]

## Files

- `raw/workspace-cache-bucket.pre.yaml`
- `values/agents-orchestrator/common.yaml`
- `tests/test_workspace_cache.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
