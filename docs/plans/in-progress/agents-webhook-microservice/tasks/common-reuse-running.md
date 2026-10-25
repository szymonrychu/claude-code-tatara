---
title: common reuse running
status: todo
repo: agents-common
value: trigger services can tell whether the agent for an event still runs and deliver to it without loss
files: [src/agents_common/orchestrator.py, src/agents_common/runs.py, src/agents_common/fake_orchestrator.py, README.md, tests/test_reuse.py]
verify: "uv run pytest tests/test_reuse.py tests/test_runs.py tests/test_orchestrator_client.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [common-release-v0-1-0]
model: sonnet
review: full
verified_head: ""
points: 3
expected_minutes: 16
expected_tokens: 723362
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# common reuse running

## Requirement

Shared support for routing a trigger event to the agent still running for it (design D16, D17, D19; user requirement 2026-10-25: "as long as an agent handling specific event is running, it will receive any new webhooks/events instead of creating new one", "(agent reuse is an optional feature, it can be set during preset creation)"). Paths are in code/agents-common. Additive only: every v0.1.0 name keeps its behaviour.

- `orchestrator.py`: `Preset.spec: dict[str, Any] = {}` (the sparse preset spec) and property `Preset.reuse_running_agent -> bool` (True only when `spec.get("reuse_running_agent") is True`); `Cluster.status: dict[str, Any] | None = None`.
- `runs.py`:
  - `async running_cluster(client, cluster_id) -> Cluster | None`: the cluster when `GET /api/v1/clusters/{id}` answers and `desired == "active"`; None on NotFound or `desired == "deleting"`; `OrchestratorUnavailable` propagates.
  - `async deliver(client, store, run, cluster_id, text, marker) -> RunRef | None`: `post_update`'s adopt-before-post rule, but returns None without finishing the run when the cluster is gone (404 `not_found`, 409 or 410 on the post), so the caller can fall back to a new cluster.
  - `async track_delivery(client, store, run, *, timeout_seconds, now=None) -> Literal["handled", "gone"] | None`: message `sent` -> `finish(handled)` and "handled"; message `cancelled` or `failed` before `sent`, or the message 404 -> "gone" without finishing; past `timeout_seconds` since `run.started_at` -> `finish(failed, "timeout")`; still queued or dispatching -> None.
- `fake_orchestrator.py`: `add_preset(name, is_default=False, spec=None)` serves `spec`; `mark_sent(message_id)`; `discard_cluster(cluster_id)` sets `desired: deleting` and cancels its queued messages; `remove_cluster(cluster_id)` makes it 404; posting to a deleting cluster answers 409 `conflict`.
- `README.md`: the new names in the `orchestrator`, `runs` and `fake_orchestrator` sections.
- `tests/test_reuse.py`: the preset flag true, false and absent; running_cluster for active, deleting, removed and unavailable; deliver posts once with the marker and adopts after a crash; deliver to a deleting or removed cluster returns None and leaves the run open; track_delivery for sent, cancelled after discard, failed, message gone, timeout and still queued; the v0.1.0 tests stay green.

## Acceptance conditions

- AC1: the preset reuse flag is read from the sparse spec and defaults to false [evidence: test:tests/test_reuse.py::test_preset_reuse_flag]
- AC2: running_cluster is the cluster only while it exists with desired active [evidence: test:tests/test_reuse.py::test_running_cluster_states]
- AC3: deliver posts once with the marker and returns None without finishing the run when the cluster is gone [evidence: test:tests/test_reuse.py::test_deliver_gone_returns_none]
- AC4: track_delivery ends handled on sent, reports gone on cancel, failure or a missing message, and fails on timeout [evidence: test:tests/test_reuse.py::test_track_delivery_outcomes]
- AC5: the fake orchestrator serves preset specs, sent messages and discarded or removed clusters [evidence: test:tests/test_reuse.py::test_fake_discard_and_sent]
- AC6: the v0.1.0 behaviour is unchanged and lint passes [evidence: command:uv run pytest tests/test_runs.py tests/test_orchestrator_client.py -q && uv run ruff check . && uv run ruff format --check .]

## Files

- `src/agents_common/orchestrator.py`
- `src/agents_common/runs.py`
- `src/agents_common/fake_orchestrator.py`
- `README.md`
- `tests/test_reuse.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
