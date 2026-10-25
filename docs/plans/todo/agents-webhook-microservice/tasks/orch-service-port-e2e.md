---
title: orch service port e2e
status: todo
repo: agent-orchestrator
value: "the service port is proven in a real cluster: an in-cluster pod with a token gets in, without one it does not"
files: [tests/e2e/test_e2e_kind.py, e2e/values-kind.yaml]
verify: "uv run pytest tests/e2e/test_e2e_kind.py --collect-only -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [orch-service-port-auth, orch-chart-services-port]
owns: []
uses: [orch-service-tokens, orch-services-service]
model: ""
estimate: 5
estimate_by: formula
actual: ""
actual_roles: ""
review: ""
worktree: ""
branch: ""
verified_head: ""
run: ""
provides: []
---

# orch service port e2e

## Requirement

Kind e2e for the service port (design D10, D14). Paths are in code/agent-orchestrator.

- `e2e/values-kind.yaml`: `serviceApi.tokenHashes.e2e: <sha256 of a fixed e2e token>`.
- `tests/e2e/test_e2e_kind.py::test_in_cluster_service_token`: from an in-cluster pod (as `test_in_cluster_pod_refused_by_allowlist` L616 does), `GET http://<release>-services:8002/api/v1/presets` with the e2e token answers 200; without it 401; `DELETE /api/v1/clusters/<id>` with it 403; the same pod on the main Service port still gets 403 from the allowlist.
- `mise run test:e2e` passes (in CI the `e2e` job; locally when kind is available).

## Acceptance conditions

- AC1: the new e2e test is collected [evidence: command:uv run pytest tests/e2e/test_e2e_kind.py --collect-only -q | grep -q test_in_cluster_service_token]
- AC2: the kind e2e passes with the service token check [evidence: command:mise run test:e2e]
- AC3: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

## Files

- `tests/e2e/test_e2e_kind.py`
- `e2e/values-kind.yaml`

## Interfaces

- Uses `orch-service-tokens` and `orch-services-service`.

## Expected outcome

The kind e2e proves token access on the services Service and the unchanged allowlist on the main Service.

## Steps

- Red: add the test; with the old chart values it fails (no services Service).
- Green: values-kind token; `mise run test:e2e` passes (or the CI e2e job; quote its result).

## Notes

- cluster-scaling also edits `tests/e2e/test_e2e_kind.py` and `e2e/values-kind.yaml`; rebase on whichever lands first.
