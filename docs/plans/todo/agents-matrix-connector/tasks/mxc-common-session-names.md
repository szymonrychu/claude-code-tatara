---
title: mxc common session names
status: todo
repo: agents-matrix-connector
value: the connector uses the renamed orchestrator session API from agents-common v0.3.0
files: [pyproject.toml, uv.lock, src/agents_matrix_connector, tests]
verify: "uv lock --check && uv run ruff check ."
depends_on: [mxc-scaffold-and-cli]
model: ""
review: ""
verified_head: ""
points: 2
expected_minutes: 8
expected_tokens: 535073
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# mxc common session names

## Requirement

Gate item 16 (user 'Go', 2026-10-25): the connector starts before orchestrator-rename-sessions and pins agents-common v0.2.0 (task mxc-scaffold-and-cli). Once orchestrator-rename-sessions has released agents-common v0.3.0 with session names (its tasks common-client-sessions and common-release-v0-3-0; confirm with `git ls-remote --tags https://github.com/szymonrychu/agents-common v0.3.0`), bump the pin in pyproject.toml (runtime and the dev `agents-common[testing]` entry) to v0.3.0, re-lock, and switch every connector use of the orchestrator client and run tracker to the session names (create_session and friends). Leave no cluster-named call or identifier in src or tests. If v0.3.0 does not exist yet, end `blocked`, whoCanClear "orchestrator: orchestrator-rename-sessions must release agents-common v0.3.0". The orchestrator dispatches runs-and-outbound-repo, dispatch-worker, reply-tracker and every later task that uses the orchestrator client only after this task is done.

## Acceptance conditions

- AC1: agents-common is pinned to v0.3.0 and its client has session names [evidence: command:grep -q 'agents-common @ git+https://github.com/szymonrychu/agents-common@v0.3.0' pyproject.toml && uv run --frozen python -c "from agents_common.orchestrator import OrchestratorClient; assert hasattr(OrchestratorClient, 'create_session')"]
- AC2: no cluster-named orchestrator call remains in the connector [evidence: command:! grep -rniE 'create_cluster|cluster_id|clusters' src tests]
- AC3: the suite and lint pass [evidence: command:mise run test && mise run lint]

## Files

- `pyproject.toml`
- `uv.lock`
- `src/agents_matrix_connector`
- `tests`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
