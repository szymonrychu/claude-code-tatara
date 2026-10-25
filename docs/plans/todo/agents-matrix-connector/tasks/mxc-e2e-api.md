---
title: mxc e2e api
status: todo
repo: agents-matrix-connector
value: the whole Messenger-to-agent loop is proven end to end against real processes before it goes live
files: [tests/e2e/__init__.py, tests/e2e/conftest.py, tests/e2e/test_e2e_api.py, pyproject.toml]
verify: "uv run --frozen pytest tests/e2e -m e2e -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [mxc-service-entrypoints, mxc-openapi-and-readme]
model: opus
review: ""
verified_head: ""
points: 8
expected_minutes: 18
expected_tokens: 2172985
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
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

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
