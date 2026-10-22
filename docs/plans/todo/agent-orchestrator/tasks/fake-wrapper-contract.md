---
title: fake wrapper contract
status: todo
repo: agent-orchestrator
value: "An in-process wrapper fake that every loop test uses, kept honest by running the same contract tests against the real wrapper image."
files: [tests/fakes/fake_wrapper.py, tests/fakes/real_wrapper.py, tests/test_fake_wrapper_contract.py, e2e/agent-test.Dockerfile, e2e/agent-test.config.yaml]
verify: "uv run pytest tests/test_fake_wrapper_contract.py -q && mise run lint"
depends_on: [wrapper-client-and-sse]
owns: [fake-wrapper]
uses: [wrapper-client, wrapper-idle-since, wrapper-context-surface, wrapper-user-message-event, wrapper-peers-view]
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
  - turns: 202 when idle; 409 while busy; 503 while booting
  - interrupt and commands
  - SSE with seq ids, `Last-Event-ID` replay and `: ping`
  - history and `/v1/peers`
  - bearer auth
- Test controls on FakeWrapper:
  - `complete_turn(turn_id, text)`
  - `emit(type, data)`
  - `set_context(...)`
  - `drop_streams()` to simulate a disconnect
  - `skip_seq(n)` to simulate log rotation
  - `set_booting(bool)`
  - counters of received turns
- `tests/fakes/real_wrapper.py`: starts the image named by `ORCH_TEST_WRAPPER_IMAGE` with `docker run` and `e2e/agent-test.config.yaml`, then waits for /readyz.
- `e2e/agent-test.Dockerfile` (ARG BASE_IMAGE, default the agent image) copies the wrapper's `tests/fake_claude` from the same wrapper sha and sets it as `claude.binary`. kind-e2e reuses this image.
- `tests/test_fake_wrapper_contract.py`: a fixture parametrised over `fake` and `real` (the real leg marked `integration`). One suite covers:
  - create a session
  - submit a turn (202), then a second (409) while busy
  - the SSE sequence `session_state` busy, `user_message`, `turn_completed`, `session_state` idle with `since`
  - reconnect with Last-Event-ID replays only newer events
  - the snapshot exposes `idle_since` and `context` (possibly null)
  - `/v1/peers`
  - a bad token gives 401 with the error envelope

## Acceptance conditions

- AC1: a turn sequence emits busy, user_message, turn_completed and idle with since [evidence: test:tests/test_fake_wrapper_contract.py::test_turn_lifecycle_events]
- AC2: a second turn while busy returns 409 [evidence: test:tests/test_fake_wrapper_contract.py::test_busy_session_returns_409]
- AC3: reconnecting with Last-Event-ID replays only newer events [evidence: test:tests/test_fake_wrapper_contract.py::test_last_event_id_replay]
- AC4: the snapshot exposes idle_since and context [evidence: test:tests/test_fake_wrapper_contract.py::test_snapshot_fields]
- AC5: the peers view and bearer auth behave like the wrapper [evidence: test:tests/test_fake_wrapper_contract.py::test_peers_view_and_auth]
- AC6: the same suite passes against the real wrapper test image [evidence: command:ORCH_TEST_WRAPPER_IMAGE=agent-orchestrator-agent-test:local uv run pytest tests/test_fake_wrapper_contract.py -m integration -q]

## Files

- `tests/fakes/fake_wrapper.py`
- `tests/fakes/real_wrapper.py`
- `tests/test_fake_wrapper_contract.py`
- `e2e/agent-test.Dockerfile`
- `e2e/agent-test.config.yaml`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
