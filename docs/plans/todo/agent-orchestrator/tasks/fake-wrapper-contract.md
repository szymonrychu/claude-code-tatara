---
title: fake wrapper contract
status: todo
repo: agent-orchestrator
value: "An in-process wrapper fake that every loop test uses, kept honest by running the same contract tests against the real wrapper image."
files: [tests/fakes/fake_wrapper.py, tests/fakes/real_wrapper.py, tests/test_fake_wrapper_contract.py, e2e/agent-test.Dockerfile, e2e/agent-test.config.yaml]
verify: "uv run pytest tests/test_fake_wrapper_contract.py -q && mise run lint"
depends_on: [wrapper-client-and-sse]
owns: [fake-wrapper]
uses: [wrapper-client, wrapper-idle-since, wrapper-context-surface, wrapper-user-message-event, wrapper-peers-view, wrapper-history-backward]
model: ""
estimate: 6
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

# fake wrapper contract

## Requirement

A fake claude-code-wrapper and a contract suite that runs against both the fake and the real wrapper (D19). It depends on epic claude-code-wrapper-orchestr.

- `tests/fakes/fake_wrapper.py`: `FakeWrapper`, a FastAPI app served by uvicorn on 127.0.0.1 with a random port inside the test loop (real streaming, so SSE behaves as over the network). It supports:
  - sessions: list, create (synchronous), get snapshot with `idle_since` and `context`
  - turns: 202 when idle; 409 while busy; 503 while booting; the submitted `metadata` is kept on the turn record; `GET /v1/sessions/{id}/turns` (summaries in start order) and `GET /v1/sessions/{id}/turns/{turn_id}` (the full record with `metadata`), as in the wrapper README
  - interrupt and commands
  - SSE with seq ids, `Last-Event-ID` replay and `: ping`
  - history including `before_seq`, `types`, `prev_seq` and `has_more_before` (contract wrapper-history-backward), and `/v1/peers`
  - bearer auth
  - session states creating, ready, busy, stopped and failed, each with a controllable transcript flag, and `POST /v1/sessions/{id}/resume` (409 without a transcript)
- Test controls on FakeWrapper:
  - `complete_turn(turn_id, text)`
  - `emit(type, data)`
  - `set_context(...)`
  - `drop_streams()` to simulate a disconnect
  - `skip_seq(n)` to simulate log rotation
  - `set_booting(bool)`
  - counters of received turns
  - `set_turn_status(code)` makes the next turn submissions answer any status (404, 410, 401, 403, 413, 422, 500, 503)
  - `delay_turn_response(seconds)` and `reset_connection_after_receive()` simulate a slow or ambiguous send that started (the turn is recorded as received, the client sees a timeout or a reset)
  - `reset_connection_before_receive()` simulates an ambiguous send that did not start (the client sees a reset after writing, and no turn is recorded)
  - `set_unreachable(bool)` makes every request fail to connect
  - `set_session_state(state, has_transcript)`
- `tests/fakes/real_wrapper.py`: starts the image named by `ORCH_TEST_WRAPPER_IMAGE` with `docker run` and `e2e/agent-test.config.yaml`, then waits for /readyz.
- `e2e/agent-test.Dockerfile` (ARG BASE_IMAGE, default the claude-code-wrapper image `harbor.szymonrichert.pl/containers/claude-code-wrapper:<sha7>` that settings use as the agent image; there is no derived agent image, D16) copies the wrapper's `tests/fake_claude` from the same wrapper sha and sets it as `claude.binary`. kind-e2e reuses this image.
- `tests/test_fake_wrapper_contract.py`: a fixture parametrised over `fake` and `real` (the real leg marked `integration`). One suite covers:
  - create a session
  - submit a turn (202), then a second (409) while busy
  - the SSE sequence `session_state` busy, `user_message`, `turn_completed`, `session_state` idle with `since`
  - reconnect with Last-Event-ID replays only newer events
  - the snapshot exposes `idle_since` and `context` (possibly null)
  - `/v1/peers`
  - backward history: `before_seq` with `types=user_message,turn_completed` returns ascending events, `prev_seq` is null when `has_more_before` is false, and an unknown type is 400
  - a bad token gives 401 with the error envelope
  - a stopped session with a transcript resumes through `POST .../resume`, and without a transcript the resume is refused
  - a turn submitted with `metadata {orch_message_id}` shows that metadata on `GET .../turns/{turn_id}`, and the turn appears in `GET .../turns`

## Acceptance conditions

- AC1: a turn sequence emits busy, user_message, turn_completed and idle with since [evidence: test:tests/test_fake_wrapper_contract.py::test_turn_lifecycle_events]
- AC2: a second turn while busy returns 409 [evidence: test:tests/test_fake_wrapper_contract.py::test_busy_session_returns_409]
- AC3: reconnecting with Last-Event-ID replays only newer events [evidence: test:tests/test_fake_wrapper_contract.py::test_last_event_id_replay]
- AC4: the snapshot exposes idle_since and context [evidence: test:tests/test_fake_wrapper_contract.py::test_snapshot_fields]
- AC5: the peers view and bearer auth behave like the wrapper [evidence: test:tests/test_fake_wrapper_contract.py::test_peers_view_and_auth]
- AC6: backward history with types, prev_seq and has_more_before behaves like the wrapper [evidence: test:tests/test_fake_wrapper_contract.py::test_history_backward]
- AC7: the same suite passes against the real wrapper test image [evidence: command:ORCH_TEST_WRAPPER_IMAGE=agent-orchestrator-agent-test:local uv run pytest tests/test_fake_wrapper_contract.py -m integration -q]
- AC8: the status, delay and reset controls make submit_turn answer the chosen status, time out, or reset after the turn was recorded [evidence: test:tests/test_fake_wrapper_contract.py::test_fake_status_delay_and_reset_controls]
- AC9: a stopped session with a transcript resumes and one without is refused, on both legs [evidence: test:tests/test_fake_wrapper_contract.py::test_resume_stopped_session]
- AC10: turn metadata round-trips through the turn record and the turns list, on both legs [evidence: test:tests/test_fake_wrapper_contract.py::test_turn_metadata_on_record]
- AC11: reset_connection_before_receive records no turn while reset_connection_after_receive records one, and set_unreachable refuses connections [evidence: test:tests/test_fake_wrapper_contract.py::test_fake_ambiguity_controls]

## Files

- `tests/fakes/fake_wrapper.py`
- `tests/fakes/real_wrapper.py`
- `tests/test_fake_wrapper_contract.py`
- `e2e/agent-test.Dockerfile`
- `e2e/agent-test.config.yaml`

## Interfaces

- `tests/fakes/fake_wrapper.py:FakeWrapper` (contract `fake-wrapper`): async context manager yielding `.url`, `.token` and the controls above
- `tests/fakes/real_wrapper.py:RealWrapper` with the same `.url`, `.token`

## Expected outcome

Loop tests run against a fake whose behaviour matches the real wrapper image on the same suite.

## Steps

- Write tests/test_fake_wrapper_contract.py; run `uv run pytest tests/test_fake_wrapper_contract.py -q`; expect failures.
- Implement fake_wrapper.py and real_wrapper.py, the Dockerfile and config.
- Rerun; expect the fake leg to pass.
- Build the test image: `docker build -f e2e/agent-test.Dockerfile -t agent-orchestrator-agent-test:local e2e`. Run the integration leg (AC6); expect it to pass.

## Notes

The real leg needs a wrapper image that contains epic claude-code-wrapper-orchestr. BASE_IMAGE is `harbor.szymonrichert.pl/containers/claude-code-wrapper:<sha7>` of that epic's merge; kind-e2e reuses this test image. The wrapper's fake claude is `tests/fake_claude/fake_claude.py`. No `__init__.py` under tests/fakes: pytest `pythonpath` includes `tests`, so `from fakes.fake_wrapper import FakeWrapper` works.
