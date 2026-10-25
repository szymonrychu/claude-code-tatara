---
title: common run tracker
status: todo
repo: agents-common
value: "a triggered run starts exactly one cluster and one prompt even across restarts, and ends handled or failed"
files: [src/agents_common/runs.py, tests/test_runs.py]
verify: "uv run pytest tests/test_runs.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [common-orchestrator-client, common-settings-runtime]
model: opus
review: ""
verified_head: ""
points: 1
expected_minutes: 5
expected_tokens: 750000
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# common run tracker

## Requirement

The preset binding model and the idempotent dispatch and tracking of one run (design D8), shared by agents-webhook and agents-schedule. Paths are in code/agents-common.

- `PresetBinding{preset_id: str, prompt_template: str | None}`: what a trigger maps to.
- `RunRef{id, slug, preset_id, cluster_id: str | None, message_id: str | None, started_at}`: the run columns a service stores.
- `RunStore` Protocol: `async set_cluster(run_id, cluster_id) -> None`, `async set_message(run_id, message_id) -> None`, `async finish(run_id, status: "handled" | "failed", reason: str | None) -> bool` (the store implements these as status-guarded updates).
- `marker(run_kind, run_id) -> str` returns `<!-- agents-<run_kind>:<run_id> -->`.
- `async dispatch(client, store, run: RunRef, text: str, marker: str) -> RunRef`: if `cluster_id` is unset, `create_cluster(preset_id, slug)` (409 resolves the existing cluster) and `set_cluster`; if `message_id` is unset, `list_messages(cluster_id)` and adopt the first message whose text contains `marker`, else `post_message(cluster_id, text + "\n\n" + marker)`; then `set_message`. Each step is skipped when its id is already stored, so calling `dispatch` again after a crash at any point posts no second message and creates no second cluster.
- `async post_update(client, store, run: RunRef, cluster_id, text, marker)`: posts to an existing cluster with the same adopt-before-post rule.
- `async track(client, store, run: RunRef, now, timeout_seconds) -> str | None`: `get_message(message_id)`; turn `completed` -> `finish(handled)`; message status `failed` or `cancelled` -> `finish(failed, "message_<status>")`; turn `failed` -> `finish(failed, "turn_failed")`; `now - started_at > timeout_seconds` -> `finish(failed, "timeout")`; otherwise None (still running). `OrchestratorUnavailable` propagates (the caller retries next tick); `NotFound` on the preset or cluster -> `finish(failed, "preset_not_found" | "cluster_not_found")`.
- `tests/test_runs.py` with the fake orchestrator and an in-memory store: the happy path; a crash after create (cluster_id stored, no message) resumes without a second cluster; a crash after post but before `set_message` adopts the marker message and posts nothing; 409 resolves; each track outcome including timeout; post_update adopts too.

## Acceptance conditions

- AC1: dispatch after a crash at any step creates no second cluster and posts no second message [evidence: command:uv run pytest tests/test_runs.py -q -k crash]
- AC2: track maps completed, failed, cancelled, turn failed and timeout to handled or failed with the reason [evidence: command:uv run pytest tests/test_runs.py -q -k track]
- AC3: post_update posts to an existing cluster with the same adopt-before-post rule [evidence: command:uv run pytest tests/test_runs.py -q -k update_message]
- AC4: the preset binding and run store types exist for the schedule service [evidence: symbol:src/agents_common/runs.py::RunStore]
- AC5: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

## Files

- `src/agents_common/runs.py`
- `tests/test_runs.py`

## Interfaces

- Owns `agents-common-run-tracker` and `preset-mapping-model` (`PresetBinding`, the cross-epic name agents-schedule uses): `agents_common.runs.{PresetBinding, RunRef, RunStore, marker, dispatch, post_update, track}`.

## Expected outcome

A service implements three guarded store methods and gets crash-safe dispatch and tracking.

## Steps

- Red: write `tests/test_runs.py` with crash injection (raise after a given client call); run: fails.
- Green: implement; tests pass. Run the verify command.

## Notes

- The orchestrator message has no idempotency key; the marker plus "the cluster belongs to this run" (deterministic slug) is the idempotency (discovery fix-as-ac). No turn-completion callback exists; polling is the design (do-not-build).
