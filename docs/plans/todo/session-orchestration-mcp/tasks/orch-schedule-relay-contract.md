---
title: orch schedule relay contract
status: todo
repo: agents-orchestrator
value: the relay and its fake are pinned to the contract agents-schedule serves
files: [tests/fakes/schedule_relay_openapi.json, tests/fakes/schedule_relay_openapi.source, tests/fakes/schedule_relay.py, tests/test_schedule_relay_contract.py, tests/test_orchestration_relay.py]
verify: "uv run --frozen pytest tests/test_schedule_relay_contract.py tests/test_orchestration_relay.py && mise run lint"
depends_on: [orch-schedule-relay, sched-relay-routes]
model: opus
review: ""
verified_head: ""
points: 3
expected_minutes: 6
expected_tokens: 936557
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# orch schedule relay contract

## Requirement

README Goal G5, verbatim: "Schedule calls go through the orchestrator, which relays them to a token-protected listener on agents-schedule that records each schedule's owner; the agent token never leaves the orchestrator."

Design D7, verbatim: "The listener contract is committed as `openapi-relay.json` and vendored by the orchestrator, like Matrix D16."

Retro proposal (generic-any-mcp-with-git-and), verbatim: "any task that shells out to an external tool must have its AC cite a captured real output sample, and the reviewer checks fakes against it."

Needs a merged upstream: agents-schedule main carrying sched-relay-routes (`openapi-relay.json`).

Scope (agents-orchestrator): vendor `openapi-relay.json` from agents-schedule main as `tests/fakes/schedule_relay_openapi.json` with `tests/fakes/schedule_relay_openapi.source` (`agents-schedule <40-hex sha>`); new fake upstream `tests/fakes/schedule_relay.py` whose answers follow the vendored schemas; `tests/test_schedule_relay_contract.py`; `tests/test_orchestration_relay.py` moves its upstream to the fake where it used ad-hoc bodies.

## Acceptance conditions

- ac1: tests/fakes/schedule_relay_openapi.json is byte-identical to openapi-relay.json at the agents-schedule commit named in tests/fakes/schedule_relay_openapi.source, which is on that repo's main [evidence: judgement:reviewer runs git show <sha>:openapi-relay.json in agents-schedule and compares it with the vendored file]
- ac2: every orchestrator schedule route maps to a path and method of the vendored document [evidence: test:tests/test_schedule_relay_contract.py::test_relay_routes_exist_upstream]
- ac3: every success and error answer of the fake validates against the vendored response schemas [evidence: test:tests/test_schedule_relay_contract.py::test_fake_relay_matches_vendored_schema]
- ac4: the bodies the relay forwards for create, update and run validate against the vendored request schemas [evidence: test:tests/test_schedule_relay_contract.py::test_relay_requests_match_vendored_schema]
- ac5: the targeted tests and lint pass [evidence: command:uv run --frozen pytest tests/test_schedule_relay_contract.py tests/test_orchestration_relay.py && mise run lint]

## Files

- `tests/fakes/schedule_relay_openapi.json`
- `tests/fakes/schedule_relay_openapi.source`
- `tests/fakes/schedule_relay.py`
- `tests/test_schedule_relay_contract.py`
- `tests/test_orchestration_relay.py`

## Interfaces

- `tests/fakes/schedule_relay.py`: an ASGI fake of `/relay/v1/schedules*` (in-memory, owner from `X-Orch-Session`), mountable as an `httpx.ASGITransport`.
- `tests/fakes/schedule_relay_openapi.source`: one line `agents-schedule <sha>`.

## Expected outcome

The orchestrator's relay and its fake are pinned to the contract agents-schedule actually serves.

## Steps

- Confirm agents-schedule main carries `openapi-relay.json` (sched-relay-routes merged); stop and report if not.
- Red: write `tests/test_schedule_relay_contract.py` against the vendored file; run it: fails.
- Green: vendor the file and source, write the fake, point the relay tests at it; run the task's verify. Quote the summary line.

## Notes

- Follow the chat contract pattern on main: `tests/fakes/chat_openapi.json`, `tests/fakes/chat_openapi.source`, `tests/fakes/fake_chat.py`, `tests/test_chat_contract.py`; reuse its validation helpers rather than copying them.
