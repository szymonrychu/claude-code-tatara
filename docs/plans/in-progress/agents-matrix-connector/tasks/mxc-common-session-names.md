---
title: mxc common session names
status: done
repo: agents-matrix-connector
value: the connector uses the renamed orchestrator session API from agents-common v0.3.0
files: [pyproject.toml, uv.lock, src/agents_matrix_connector, tests]
verify: "uv lock --check && uv run ruff check ."
depends_on: [mxc-scaffold-and-cli]
model: ""
review: ""
verified_head: f136e440a270d369d80c8f0450c2a05aa90357e4
points: 2
expected_minutes: 8
expected_tokens: 535073
points_actual: 1
actual_minutes: 1
actual_tokens: 158341
actual_roles: "impl 1, review 1"
actual_role_tokens: "impl 101440, review 56901"
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

- Consumes `agents-common` v0.3.0: `agents_common.orchestrator.OrchestratorClient.create_session`, `/api/v1/sessions`, `session_id`, `agents_common.runs.running_session`, `RunRef.session_id`.

## Expected outcome

The connector pins agents-common v0.3.0 and uses only the session names; no cluster-named call or identifier remains in src or tests.

## Steps

- Confirm the tag: `git ls-remote --tags https://github.com/szymonrychu/agents-common v0.3.0` prints a ref; otherwise end blocked.
- Red: run the AC1 command on the v0.2.0 pin; it fails (no `create_session`).
- Green: pin v0.3.0 (runtime and dev entries), `uv lock`, switch every client and run-tracker call to the session names; rerun AC1 and AC2: pass.
- Run `mise run test` and `mise run lint`: pass.

## Notes

- agents-common v0.3.0 is tagged on its merge commit 6dd79c8 (2026-10-25) and installs cleanly from the tag.
- If the scaffold already pinned v0.3.0 (the tag existed when the epic started), this task only verifies AC1-AC3 and removes nothing.

- 2026-10-25 done
