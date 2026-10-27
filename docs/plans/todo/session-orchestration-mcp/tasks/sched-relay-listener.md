---
title: sched relay listener
status: todo
repo: agents-schedule
value: the orchestrator gets a token-protected way into agents-schedule without opening the SSO-protected UI api
files: [src/agents_schedule/settings.py, src/agents_schedule/runtime.py, src/agents_schedule/api/relay.py, README.md, tests/test_settings.py, tests/test_relay_gate.py, tests/test_entrypoints.py]
verify: "uv run pytest tests/test_settings.py tests/test_relay_gate.py tests/test_entrypoints.py && mise run lint"
depends_on: [sched-schedule-owner]
model: opus
review: ""
verified_head: ""
points: 5
expected_minutes: 8
expected_tokens: 1828146
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# sched relay listener

## Requirement

README Goal G5, verbatim: "Schedule calls go through the orchestrator, which relays them to a token-protected listener on agents-schedule that records each schedule's owner; the agent token never leaves the orchestrator."

Design D7, verbatim: "agents-schedule: a second listener `SCHED_RELAY_PORT` with a bearer gate on `SCHED_RELAY_TOKEN_SHA256`, mirroring the connector's agent listener and `ServiceGate`, not bound when the hash is empty."

Design D9, verbatim: "Schedule side: `SCHED_RELAY_MAX_PER_OWNER` (10) owned schedules, else 409 `owned_limit` (my call on the code); `SCHED_RELAY_MIN_INTERVAL_MINUTES` (15): the next three fires must be at least this far apart, else 422 `too_frequent`."

Design D15, verbatim: "Port 8001 is free in the api container."

Scope (agents-schedule): `settings.py` (`relay_port` 8001, `relay_token_sha256`, `relay_max_per_owner` 10, `relay_min_interval_minutes` 15), `runtime.py` (`sched api` serves the relay app on `SCHED_RELAY_PORT` next to the UI app when the hash is set), new `api/relay.py` (the relay app: bearer gate, `X-Orch-Session` and `X-Orch-Slug` required, `/healthz`, `/readyz`, the `/relay/v1` prefix with no routes yet), README (settings and the listener), `tests/test_settings.py`, new `tests/test_relay_gate.py`, `tests/test_entrypoints.py`.

## Acceptance conditions

- ac1: SCHED_RELAY_PORT defaults to 8001, SCHED_RELAY_TOKEN_SHA256 is empty or 64 lowercase hex characters (else an error naming it) and never in repr, SCHED_RELAY_MAX_PER_OWNER defaults to 10 and SCHED_RELAY_MIN_INTERVAL_MINUTES to 15, both at least 1 [evidence: test:tests/test_settings.py::test_relay_settings]
- ac2: the relay app accepts a request only when the sha256 of its bearer token equals SCHED_RELAY_TOKEN_SHA256 (constant-time), else 401 unauthorized with WWW-Authenticate, and the token never reaches a log line or an error body [evidence: test:tests/test_relay_gate.py::test_bearer_gate]
- ac3: a relay request without a UUID X-Orch-Session or a non-empty X-Orch-Slug is refused 422 invalid_request, and /healthz and /readyz answer without a token [evidence: test:tests/test_relay_gate.py::test_caller_headers_required]
- ac4: the relay app has no source allowlist and serves only /relay/v1, /healthz and /readyz, and the UI app on SCHED_HTTP_PORT serves no relay route and keeps its allowlist [evidence: test:tests/test_relay_gate.py::test_ports_separate]
- ac5: sched api binds the relay listener on SCHED_RELAY_PORT when the hash is set and not at all when it is empty, and both listeners stop on SIGTERM [evidence: test:tests/test_entrypoints.py::test_api_binds_relay_listener_only_with_hash]
- ac6: the README documents the four settings and the relay listener [evidence: command:grep -q SCHED_RELAY_TOKEN_SHA256 README.md && grep -q SCHED_RELAY_MIN_INTERVAL_MINUTES README.md]
- ac7: the targeted tests and lint pass [evidence: command:uv run pytest tests/test_settings.py tests/test_relay_gate.py tests/test_entrypoints.py && mise run lint]

## Files

- `src/agents_schedule/settings.py`
- `src/agents_schedule/runtime.py`
- `src/agents_schedule/api/relay.py`
- `README.md`
- `tests/test_settings.py`
- `tests/test_relay_gate.py`
- `tests/test_entrypoints.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
