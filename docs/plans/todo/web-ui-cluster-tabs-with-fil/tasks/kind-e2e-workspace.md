---
title: kind e2e workspace
status: todo
repo: agent-orchestrator
value: CI proves on a real cluster that files and shells work through the public API alone
files: [tests/e2e/test_e2e_kind.py]
verify: "uv run pytest -q -p no:cacheprovider -m e2e --collect-only tests/e2e/test_e2e_kind.py && mise run lint"
depends_on: [wrapper-sha-pin]
owns: []
uses: [orch-files-api, orch-terminals-api, orch-terminal-ws, wrapper-main-pin]
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

# kind e2e workspace

## Requirement

API-only kind e2e tests for the workspace features (headless parity), in `tests/e2e/test_e2e_kind.py` (marker `e2e`, run by `mise run test:e2e` and the PR CI `e2e` job).

On the kind cluster the existing fixtures bring up (`api`, `cluster`), using only `/api/v1` over the port-forward:

- `GET /api/v1/clusters/{id}/files` lists the cluster workdir (the agent-test scenario's files or a file the test makes an agent write) and `GET .../files/content` returns a file's text; a `..` path is 400 `invalid_path`.
- `POST /api/v1/agents/{agent_id}/terminals` creates a shell; the WebSocket `.../attach` (Python `websockets` client, no Origin) runs `pwd\n` and sees the workdir path and `echo ok\n` and sees `ok`; `GET /api/v1/clusters/{id}/terminals` lists it; reattach replays; `DELETE` removes it.
- the same WebSocket with `Origin: http://evil.example` is refused (HTTP 403 on the upgrade).
- the in-cluster pod refusal test pattern (`test_in_cluster_pod_refused_by_allowlist`) is unchanged.

`e2e/values-kind.yaml` already lists the port-forward origins (task origin-allowlist).

## Acceptance conditions

- AC1: the new e2e tests are collected under the e2e marker [evidence: command:uv run pytest -q -p no:cacheprovider -m e2e --collect-only tests/e2e/test_e2e_kind.py]
- AC2: the tests cover files, terminal lifecycle over WebSocket and the Origin refusal using only the public API [evidence: judgement:tests/e2e/test_e2e_kind.py reviewed against the requirement; executed by the PR CI e2e job]
- AC3: lint passes [evidence: command:mise run lint]

## Files

- `tests/e2e/test_e2e_kind.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
