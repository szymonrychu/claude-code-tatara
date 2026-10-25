---
title: dispatch worker
status: done
repo: agents-matrix-connector
value: each chat talks to one agent session that keeps its context while it runs
files: [src/agents_matrix_connector/worker.py, tests/test_worker.py]
verify: "uv run --frozen pytest tests/test_worker.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [mxc-settings-model, matrix-client-and-fake-hs, rules-and-settings-repo, runs-and-outbound-repo, chat-prompt-render]
model: opus
review: full
verified_head: 89126811d0b52d83801efca18a494c86beade295
points: 5
expected_minutes: 14
expected_tokens: 1883475
points_actual: 5
actual_minutes: 8
actual_tokens: 2561179
actual_roles: "impl 7, review 2"
actual_role_tokens: "impl 2289153, review 272026"
---

# dispatch worker

## Requirement

The dispatch worker: one session per room, reused while it runs, batches of queued messages, the new-session cap and the fallback (design D8). Paths are in code/agents-matrix-connector.

`src/agents_matrix_connector/worker.py`:

- `Worker(orchestrator: OrchestratorClient, matrix: MatrixClient, pool, settings: BotSettings, *, now=utcnow)`, `async tick() -> None`.
- For each room of `inbound.rooms_ready` (oldest first):
  1. Preset: `room_settings.preset_id`, else `settings.default_preset_id`; none -> `ignore_new(room, "no_preset")` and next room.
  2. Reuse: when `runs.latest_session(room)` exists and `agents_common.runs.running_session(orchestrator, session_id)` answers a session, create a `follow` run, `claim_room`, render with `prompt.render(first=False)` and `agents_common.runs.deliver` with marker `agents_common.runs.marker("matrix", run_id)` (`<!-- agents-matrix:<run id> -->`); this bypasses the cap. `deliver` returning None (session gone) finishes the run `failed`, `session_gone`, and `requeue_run_rows`, so the next tick starts a new session.
  3. Otherwise, when `count_first_in_progress < MATRIX_MAX_NEW_SESSIONS`: create a `first` run, `claim_room`, render with `first=True` and `agents_common.runs.dispatch` (session slug `mx-<run id>`). A `NotFound` for the preset finishes the run `failed`, `preset_not_found`, and the rows `failed`. When the cap is full the room's rows stay `new` (FIFO kept).
  4. After a successful dispatch or delivery: `matrix.typing(user_id, room, True, 30000)`; a Matrix error here is logged and ignored.
- Every DB step is a guarded transition; the create-run, claim and store writes of one room happen in one transaction before the orchestrator call, and the orchestrator call is idempotent through agents-common's adopt-before-post (a restart mid-dispatch adopts the marker message instead of posting twice).
- `OrchestratorUnavailable` leaves the run in progress for the next tick (dispatch and deliver are retried with the stored ids).
- The worker never deletes sessions.

User request 2026-10-25, verbatim: 'agents-matrix-connector New microservice- is meant to connect with existing matrix deployment and allow for talking to agents through facebook. Must support user/chat/room auto discovery and white/blacklosting. Hermes already uses working bridge.'

## Acceptance conditions

- AC1: a room with new rows and a preset gets one first run whose session is created with slug mx-<run id> and whose prompt carries all queued messages [evidence: test:tests/test_worker.py::test_first_dispatch_batches_room]
- AC2: while the room's session runs, the next batch is delivered into it as a follow run, even when the new-session cap is full [evidence: test:tests/test_worker.py::test_reuse_running_session_bypasses_cap]
- AC3: a gone session fails the follow run session_gone and puts its rows back to new in order, and the next tick creates a new session [evidence: test:tests/test_worker.py::test_session_gone_falls_back]
- AC4: with the cap full, a room without a running session keeps its rows new [evidence: test:tests/test_worker.py::test_new_session_cap]
- AC5: no preset ignores the rows no_preset and an unknown preset fails them preset_not_found [evidence: test:tests/test_worker.py::test_no_and_unknown_preset]
- AC6: a room with a run in progress is not claimed again, and a restart mid-dispatch posts no second message [evidence: test:tests/test_worker.py::test_one_run_per_room_and_restart_idempotent]
- AC7: typing is switched on in the room after a dispatch [evidence: test:tests/test_worker.py::test_typing_on_after_dispatch]

## Files

- `src/agents_matrix_connector/worker.py`
- `tests/test_worker.py`

## Interfaces

- `src/agents_matrix_connector/worker.py`: `Worker.tick`. Started by mxc-service-entrypoints in the `bot` process.
- Uses `agents_common.runs.dispatch`, `deliver`, `running_session`, `marker` and `OrchestratorClient` of the pinned agents-common (session names, design D15); `db.inbound`, `db.runs`, `db.rules`, `prompt`, `MatrixClient.typing`.

## Expected outcome

Against `FakeOrchestrator` and `FakeHomeserver`, two messages in an allowed DM produce one session and one prompt; a third message while it runs is delivered to the same session.

## Steps

- Red: `tests/test_worker.py` with the seven tests; agents-common's `FakeOrchestrator` served through `httpx.ASGITransport`, a migrated database with seeded `rooms`, `room_settings`, `settings` and `inbound` rows. Fails on the missing module.
- Green: write `worker.py`. Run the verify (Docker).

## Notes

- Mirror `code/agents-webhook/src/agents_webhook/worker.py` (claim, dispatch, reuse, fallback), adapted to per-room batches; do not copy run tracking that agents-common already provides.
- Reuse is always on for chats regardless of the preset's `reuse_running_agent` (design D8).

- 2026-10-25 done
