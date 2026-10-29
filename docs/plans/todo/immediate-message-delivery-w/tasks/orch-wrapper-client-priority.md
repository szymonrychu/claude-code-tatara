---
title: orch wrapper client priority
status: todo
repo: agents-orchestrator
value: the orchestrator can ask a wrapper for immediate delivery and read a merged answer
files: [src/agents_orchestrator/wrapper/client.py, src/agents_orchestrator/wrapper/models.py, tests/fakes/fake_wrapper.py, tests/test_wrapper_client.py, tests/test_fake_wrapper_contract.py]
verify: "uv run --frozen pytest tests/test_wrapper_client.py tests/test_fake_wrapper_contract.py -m \"not integration\" && mise run lint"
depends_on: []
model: sonnet
review: ""
verified_head: ""
points: 3
expected_minutes: 7
expected_tokens: 996161
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# orch wrapper client priority

## Requirement

Design D3 (response), verbatim: "The wrapper answers 202 `{turn_id: <running turn id>, state: "running", merged: true, merge_id}`."

Design D4 (codes), verbatim: "an `immediate` message is refused, and nothing is pasted, when: the turn is in its command phase or a slash command is running or queued for the Stop (409 `command_active`); the slash epic's `DialogScanner` patterns match the current screen (409 `dialog_open`); an interrupt of the turn is in flight (409 `interrupting`); the turn already holds `sessions.merge.max_unconfirmed` unconfirmed pastes (default 4) or `sessions.merge.max_per_turn` merged pastes (default 32) (429 `merge_queue_full`) [...] `idle` while busy stays 409 `busy`; booting and dead stay 503."

Design D13 (client part), verbatim: "`loop._send` sends `priority`; 202 `merged` or not is `mark_sent` with the returned turn id; a 409 other than booting|dead (`busy`, `command_active`, `dialog_open`, `interrupting`) and 429 `merge_queue_full` requeue with `not_before = now() + retry_backoff_base_seconds`, no attempt counted, no reservation to release (my call: an immediate requeue would spin against a busy wrapper)."

Design D14 (model part), verbatim: "The orchestrator's `TurnRecord` model gains `merged`."

Scope (agents-orchestrator): `wrapper/client.py` (`submit_turn(..., priority=None)`, 429 on a turn send maps to `Busy`), `wrapper/models.py` (`TurnAccepted.merged`, `TurnRecord.merged`), `tests/fakes/fake_wrapper.py` (mirrors the wrapper's merge leg, refusals and cap), `tests/test_wrapper_client.py`, `tests/test_fake_wrapper_contract.py` (the merge case, fake leg; the real leg is enabled by orch-wrapper-pin-0-5-0).

## Acceptance conditions

- ac1: submit_turn sends priority in the body when given and none when not; a 202 parses TurnAccepted with turn_id and merged (false when the field is absent) (new) [evidence: test:tests/test_wrapper_client.py::test_submit_turn_sends_priority_and_parses_merged]
- ac2: a turn send answered 409 busy, command_active, dialog_open or interrupting, or 429 merge_queue_full, maps to Busy with the wrapper's code; 409 booting and dead keep their mapping (new) [evidence: test:tests/test_wrapper_client.py::test_submit_turn_refusal_codes]
- ac3: TurnRecord parses merged entries (merge_id, metadata, absorbed_at) and defaults to an empty list (new) [evidence: test:tests/test_wrapper_client.py::test_turn_record_parses_merged]
- ac4: the fake wrapper merges an immediate turn into a running one (same turn id, merged true, the record lists the merge), answers 409 busy to idle while busy and 429 merge_queue_full past the cap (fake leg) (new) [evidence: command:uv run --frozen pytest "tests/test_fake_wrapper_contract.py::test_immediate_while_busy_merges[fake]"]
- ac5: targeted suites and lint pass [evidence: command:uv run --frozen pytest tests/test_wrapper_client.py tests/test_fake_wrapper_contract.py -m "not integration" && mise run lint]

## Files

- `src/agents_orchestrator/wrapper/client.py`
- `src/agents_orchestrator/wrapper/models.py`
- `tests/fakes/fake_wrapper.py`
- `tests/test_wrapper_client.py`
- `tests/test_fake_wrapper_contract.py`

## Interfaces

- `WrapperClient.submit_turn(session_id: str, text: str, metadata: dict | None = None, priority: str | None = None) -> SubmitOutcome`; body `{"text", "metadata"?, "priority"?}`.
- `wrapper/models.py`: `TurnAccepted(turn_id: str, merged: bool = False)`; `MergedPrompt(_Model)` with `merge_id`, `origin`, `metadata`, `pasted_at`, `absorbed_at`; `TurnRecord.merged: list[MergedPrompt] = []`.
- `tests/fakes/fake_wrapper.py`: the same request field, response and refusal codes as the wrapper's D4 (`merge_queue_full` cap 4 unconfirmed; the fake can mark merges absorbed on demand).

## Expected outcome

The orchestrator can ask the wrapper for immediate or idle delivery and understands a merged answer and every refusal, and its fake wrapper behaves like the real one.

## Steps

- Read `wrapper/client.py` (`_send`, `submit_turn`, `_map_refusal`), `wrapper/models.py`, `tests/fakes/fake_wrapper.py`, `tests/test_wrapper_client.py`, `tests/test_fake_wrapper_contract.py` and the wrapper task wrapper-immediate-turn-merge's Interfaces in one pass.
- Red: add the tests named ac1 to ac4 (the contract case parametrised like the others; mark its real leg skipped with a reason naming orch-wrapper-pin-0-5-0); run `uv run --frozen pytest tests/test_wrapper_client.py tests/test_fake_wrapper_contract.py -m "not integration"`; expect them to fail.
- Green: implement the client, models and fake; run the task's verify; expect all passed. Quote the summary line.

## Notes

- The real contract leg runs against the pinned wrapper image (0.4.0 until orch-wrapper-pin-0-5-0), which refuses an unknown `priority` field; the merge case's real leg is skipped until that task removes the skip.
- `command()` keeps its own 429 mapping; only the turn send changes.
- Tree state: tests that use the `pool`/`dsn` fixtures need Postgres through testcontainers and agent pods have no Docker, so they error locally (`DockerException`) and run in CI on the PR; the reviewer reads the CI job for them and quotes its summary line. `tests/test_reconciler.py::test_lightkube_default_client_uses_env_config` fails in-cluster for an unrelated reason.
- Before working read the repo's AGENTS.md, MEMORY.md and ROADMAP.md. No em dashes. No backward-compatibility shims. If a verify run fails, save the failing test name and the output tail before any rerun.

- 2026-10-29 amended: planner filled Interfaces, Expected outcome, Steps and Notes before the gate (retro: no empty Steps)
