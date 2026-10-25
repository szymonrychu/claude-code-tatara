---
title: kind e2e config
status: todo
repo: agent-orchestrator
value: "CI proves hooks, idle compact, lease and autoclose on a real cluster through the API"
files: [tests/e2e/test_e2e_kind.py, e2e/values-kind.yaml]
verify: "uv run pytest -q -p no:cacheprovider -m e2e --collect-only tests/e2e/test_e2e_kind.py && uv run ruff check . && uv run ruff format --check ."
depends_on: [render-wrapper-settings, leader-lease-expiry, autoclose-sweeper, config-cluster-views]
owns: []
uses: [orch-cluster-config-api, orch-leader-lease, orch-cluster-autoclose]
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

# kind e2e config

## Requirement

Prove each capability on a real cluster through the API only (design D6, D9; approval A6). In `tests/e2e/test_e2e_kind.py` add three tests under the `e2e` marker, each creating its own cluster through `POST /api/v1/clusters` and deleting it in teardown:

- `test_wrapper_hook_and_idle_compact`: spec `wrapper` with an `onTurnComplete` command hook `echo "$POD_NAME" > hook-ran.txt` and `auto_compact {idle_seconds: 5}`; send one message, wait for its turn to finish, read `hook-ran.txt` through `GET /api/v1/clusters/{id}/files/content` and assert it holds the agent's pod name (proving the hook ran and the escaped `$` reached the shell); then assert a `compacted` event appears through `GET /api/v1/clusters/{id}/events?types=compacted` within a bounded wait.
- `test_leader_lease_hands_over`: a two-agent hive with `leader_lease_seconds: 60`; record `leader_agent_id` and `leader_epoch`, wait (bounded at 180 s) until the view shows another leader, a higher epoch and `leader_reason` `lease_expired`.
- `test_autoclose_discards_cluster`: `autoclose_after_seconds: 30`; the view shows `closes_at` equal to `created_at + 30 s`; within a bounded wait the cluster is `deleting` and then `GET` answers 404.

`e2e/values-kind.yaml` sets `ORCH_AUTOCLOSE_MIN_SECONDS: "30"`. Every wait is bounded and fails with a named message.

Interfaces: uses parts `orch-cluster-config-api`, `orch-leader-lease`, `orch-cluster-autoclose`.

Notes: the agent test image runs the wrapper's fake claude, which handles `/compact` (`code/claude-code-wrapper/tests/fake_claude/fake_claude.py`). The e2e run is the PR CI `e2e` job; locally only collection is checked.

## Acceptance conditions

- AC1: the three new e2e tests are collected under the e2e marker [evidence: command:uv run pytest -q -p no:cacheprovider -m e2e --collect-only tests/e2e/test_e2e_kind.py]
- AC2: the hook test proves a command hook ran with the shell seeing $POD_NAME and an idle compact happened, through the files and events APIs only [evidence: judgement:tests/e2e/test_e2e_kind.py::test_wrapper_hook_and_idle_compact reviewed; executed by the PR CI e2e job]
- AC3: the lease test sees a new leader with reason lease_expired and a higher epoch through the cluster view [evidence: judgement:tests/e2e/test_e2e_kind.py::test_leader_lease_hands_over reviewed; executed by the PR CI e2e job]
- AC4: the autoclose test sees closes_at, then deleting, then 404, with ORCH_AUTOCLOSE_MIN_SECONDS 30 in the kind values [evidence: judgement:tests/e2e/test_e2e_kind.py::test_autoclose_discards_cluster reviewed; executed by the PR CI e2e job]
- AC5: every cluster an e2e test creates is deleted in its teardown and every wait is bounded [evidence: judgement:tests/e2e/test_e2e_kind.py teardown and waits reviewed]
- AC6: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

## Files

- `tests/e2e/test_e2e_kind.py`
- `e2e/values-kind.yaml`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
