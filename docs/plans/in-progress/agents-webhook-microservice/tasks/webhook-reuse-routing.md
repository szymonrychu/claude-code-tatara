---
title: webhook reuse routing
status: in-progress
repo: agents-webhook
value: follow-up events for an item go to the agent still working on it when its preset opts in
files: [pyproject.toml, uv.lock, src/agents_webhook/worker.py, tests/test_worker_reuse.py]
verify: "uv run pytest tests/test_worker_reuse.py tests/test_worker.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [webhook-dispatch-worker, common-release-v0-2-0]
model: opus
review: full
verified_head: ""
points: 5
expected_minutes: 15
expected_tokens: 1836811
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# webhook reuse routing

## Requirement

Route a new event to the agent still running for it (design D16, D17; user requirement 2026-10-25: "as long as an agent handling specific event is running, it will receive any new webhooks/events instead of creating new one"; clarification: "(agent reuse is an optional feature, it can be set during preset creation)"). Paths are in code/agents-webhook.

- `pyproject.toml`, `uv.lock`: agents-common pinned to tag `v0.2.0` (task common-release-v0-2-0).
- `worker.py`, the `route(row)` hook of webhook-dispatch-worker:
  1. Each tick, for the endpoints with `new` rows, read the preset (`client.get_preset(endpoint.preset_id)`, once per endpoint per tick) and pass the endpoints whose `Preset.reuse_running_agent` is true as `reuse_endpoints` to `claim_next`; a missing preset counts as off (dispatch then fails `preset_not_found` as before); an unavailable orchestrator skips claims for that endpoint this tick.
  2. A claimed row with a `prior` run on a reuse endpoint: `runs.running_cluster(client, prior.cluster_id)`. Running (the cluster exists and is not deleting, whether or not its first turn completed) -> `mark_update(row, prior root id)`, `runs.deliver(...)` with `prompt.render(event, template, update=True)` and the row's own marker, record `cluster_id`, `cluster_slug` and `message_id`; the update bypasses the caps.
  3. Tracking an update row: `runs.track_delivery(..., timeout_seconds=run_timeout_seconds)`; `sent` -> `handled` (linked by `update_of`); `gone` -> fallback.
  4. Fallback (not running, deliver returned None, or the message was cancelled or failed before `sent` because the cluster was discarded mid-delivery): `clear_update`, then first dispatch as a new cluster `wh-<id>` when the caps allow, else `release` to `new` keeping its FIFO place. A fallback happens at most once per row; the row's reason records `reuse_fallback` only when it then fails.
  5. Order: rows of one key are delivered one at a time in arrival order (claim_next's per-key rule); a delivery while the agent is busy waits in the orchestrator's message queue and is never merged with another delivery.
- `tests/test_worker_reuse.py` (DB fixture, FakeOrchestrator from v0.2.0): reuse on: a second event for the same PR while the first turn runs, and again after it completed, goes to the same cluster and ends `handled` with `update_of`; reuse off (absent or false): it starts its own cluster after the first ends; the endpoint's preset flag is read once per tick; three updates arrive in order; the cluster discarded before delivery -> new cluster; discarded mid-delivery (message cancelled) -> new cluster, no lost event; caps full -> the reuse delivery still goes and a fallback row is released; autoclose (`desired: deleting`) ends reuse; a restart between deliver and set_message adopts the marker message.

## Acceptance conditions

- AC1: with reuse on, an event for a key whose cluster still runs is delivered to that cluster, before or after its first turn completed, and ends handled with a link to the parent [evidence: command:uv run pytest tests/test_worker_reuse.py -q -k reuse_on]
- AC2: with reuse off or unset, the same event starts its own cluster [evidence: command:uv run pytest tests/test_worker_reuse.py -q -k reuse_off]
- AC3: deliveries for one key keep arrival order and are not merged while the agent is busy [evidence: command:uv run pytest tests/test_worker_reuse.py -q -k order]
- AC4: a cluster discarded before or during delivery, or closed by autoclose, makes the event start a new cluster without loss [evidence: command:uv run pytest tests/test_worker_reuse.py -q -k discard]
- AC5: reuse deliveries bypass the caps and a restart never posts twice [evidence: command:uv run pytest tests/test_worker_reuse.py -q -k "caps or restart"]
- AC6: agents-common is pinned to v0.2.0 and lint passes [evidence: command:grep -q "agents-common@v0.2.0" pyproject.toml && uv run ruff check . && uv run ruff format --check .]

## Files

- `pyproject.toml`
- `uv.lock`
- `src/agents_webhook/worker.py`
- `tests/test_worker_reuse.py`

## Interfaces

- Consumes `agents-common-reuse` (v0.2.0) and `preset-reuse-running-agent`.
- Fills `worker.route(row)` of webhook-dispatch-worker.

## Expected outcome

With a preset that opts in, every later event for the same PR, MR, issue or alert reaches the agent still running for it; otherwise a new agent starts.

## Steps

- Red: `tests/test_worker_reuse.py`; run `uv run pytest tests/test_worker_reuse.py -q`: fail.
- Green: bump the pin and `uv lock`, then the routing; run the verify command (the dispatch tests stay green).

## Notes

- Blocked until tag v0.2.0 exists (task common-release-v0-2-0).
- The orchestrator queues messages per cluster, so a delivery during a busy turn waits there in order.

- 2026-10-25 in-progress: re-plan 2026-10-25: added; not started
