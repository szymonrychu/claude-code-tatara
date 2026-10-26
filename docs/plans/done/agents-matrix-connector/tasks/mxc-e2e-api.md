---
title: mxc e2e api
status: done
repo: agents-matrix-connector
value: the whole Messenger-to-agent loop is proven end to end against real processes before it goes live
files: [tests/e2e/__init__.py, tests/e2e/conftest.py, tests/e2e/test_e2e_api.py, pyproject.toml]
verify: "uv run --frozen pytest tests/e2e -m e2e -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [mxc-service-entrypoints, mxc-openapi-and-readme]
model: opus
review: ""
verified_head: 79230b4a4bcfb6238c8f75233f3b1aa835c5cbda
points: 8
expected_minutes: 18
expected_tokens: 2172985
points_actual: 5
actual_minutes: 11
actual_tokens: 1989244
actual_roles: "impl 8, review 2"
actual_role_tokens: "impl 1818256, review 170988"
---

# mxc e2e api

## Requirement

API-only end-to-end tests of the whole connector (design D14, G1-G4): real Postgres, the real `api` and `bot` processes started from the console script, `FakeHomeserver` and agents-common's `FakeOrchestrator` each served by uvicorn on a free port. Paths are in code/agents-matrix-connector.

- `tests/e2e/__init__.py`, `tests/e2e/conftest.py` (free ports, wait helpers, process fixtures with env pointing at the fakes and the migrated database, as `code/agents-webhook/tests/e2e/conftest.py`).
- `tests/e2e/test_e2e_api.py`, marked `e2e`, one test per scenario, driving Matrix only through the fake's helpers and the connector only through `/matrix/api/v1`:
  1. a bridge invite to a DM portal: the room appears in `GET /rooms` as `dm`, joined, access `default` (deny); a message is listed `ignored`, `not_allowed`; no session is created.
  2. `POST /rules` allow the room and `PUT /settings` a default preset: the next message creates one session; `complete_turn` puts the reply in the fake room; `GET /rooms/{id}/messages` shows both directions.
  3. two messages while the session runs are delivered into the same session as one follow run.
  4. the session is discarded: the next message starts a new session `mx-<id>`.
  5. a deny rule on a member of an allowed group: that member is ignored `denied: user`, another member's mention is answered, a non-mention is `not_mentioned`.
  6. an encrypted room and a space: messages ignored `room_encrypted` and `room_infrastructure`, nothing sent into them.
  7. the bot is restarted (SIGTERM and start) between a completed turn and the next tick: the room still gets exactly one reply, and history is not replayed.
- `pyproject.toml`: register the `e2e` marker.

User request 2026-10-25, verbatim: 'agents-matrix-connector New microservice- is meant to connect with existing matrix deployment and allow for talking to agents through facebook. Must support user/chat/room auto discovery and white/blacklosting. Hermes already uses working bridge.'

## Acceptance conditions

- AC1: discovery and default deny hold end to end [evidence: test:tests/e2e/test_e2e_api.py::test_invite_discovered_and_default_deny]
- AC2: an allowed room gets the agent's reply in the room [evidence: test:tests/e2e/test_e2e_api.py::test_allowed_room_round_trip]
- AC3: messages during a running session go into that session [evidence: test:tests/e2e/test_e2e_api.py::test_reuse_running_session]
- AC4: a discarded session falls back to a new one [evidence: test:tests/e2e/test_e2e_api.py::test_discarded_session_fallback]
- AC5: deny wins in an allowed group and the mention trigger applies [evidence: test:tests/e2e/test_e2e_api.py::test_group_deny_and_mention]
- AC6: encrypted and infrastructure rooms are never answered [evidence: test:tests/e2e/test_e2e_api.py::test_encrypted_and_infrastructure_ignored]
- AC7: a bot restart neither duplicates a reply nor replays history [evidence: test:tests/e2e/test_e2e_api.py::test_restart_exactly_once]

## Files

- `tests/e2e/__init__.py`
- `tests/e2e/conftest.py`
- `tests/e2e/test_e2e_api.py`
- `pyproject.toml`

## Interfaces

- Consumes every public surface of the connector: console script, settings env, `/matrix/api/v1`, `FakeHomeserver` helpers, `FakeOrchestrator` (`add_preset`, `complete_turn`, the session discard helper).

## Expected outcome

`uv run --frozen pytest tests/e2e -m e2e -q` passes the seven scenarios against real processes.

## Steps

- Red: write the conftest and the seven tests; run them: they fail until the processes behave (this task lands after mxc-service-entrypoints, so a failure here is a real defect: fix it in the module it belongs to and say which).
- Green: make them pass. Run the verify (Docker).

## Notes

- Keep `MATRIX_POLL_SECONDS` and `MATRIX_SYNC_TIMEOUT_SECONDS` small in the e2e env (for example 0.2 and 1) so the suite stays fast.
- A defect found here that sits outside this task's files is returned as a `discovered` entry, never left undone.

- 2026-10-25 done
