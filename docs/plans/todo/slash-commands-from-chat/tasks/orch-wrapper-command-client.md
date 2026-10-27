---
title: orch wrapper command client
status: todo
repo: agents-orchestrator
value: "the orchestrator sends any slash command with args to a wrapper and knows the exact outcome, and its fake behaves like the real wrapper"
files: [src/agents_orchestrator/wrapper/client.py, src/agents_orchestrator/wrapper/models.py, src/agents_orchestrator/wrapper/__init__.py, src/agents_orchestrator/dispatcher/loop.py, tests/test_wrapper_client.py, tests/fakes/fake_wrapper.py, tests/test_fake_wrapper_contract.py, tests/test_dispatcher.py]
verify: "uv run --frozen pytest tests/test_wrapper_client.py tests/test_fake_wrapper_contract.py && mise run lint"
depends_on: []
model: opus
review: ""
verified_head: ""
points: 5
expected_minutes: 11
expected_tokens: 1858483
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# orch wrapper command client

## Requirement

Goal G1 (README), verbatim: "Any slash command typed in the chat runs as a Claude Code slash command on the session, at any moment, and the session stays responsive afterwards."

Design D10, verbatim (the client part): "`WrapperClient.command(session_id, name, args)` returns `CommandOutcome = CommandAccepted(command_id, record) | Busy | ConfigError | Rejected(code, reason) | Gone | Unavailable | Ambiguous`; the existing `/agents/{id}/compact` path keeps its `done {response: record}` result."

Design "Left to the builder", verbatim: "Fake wrapper (orchestrator) command timing model, as long as it emits `command_queued`, `command_started`, `command_completed` with the record shape of the real wrapper and runs a command queued during a turn after that turn completes."

Discovery fix-as-ac (agents-orchestrator.md), verbatim: "fake wrapper `/commands` ignores the per-origin allowlist (tests/fakes/fake_wrapper.py:641-649), hiding that refusal from unit tests" and "`WrapperClient.command` sends only `{"name"}`, no args (wrapper/client.py:198-200)".

Scope (agents-orchestrator):
- `wrapper/client.py`: `command(session_id, name, args="") -> CommandOutcome`, POST `{name, args}` with the send timeout; 202 -> `CommandAccepted(record["id"], record)`; 409 -> `Busy` (booting, dead, carrying the code); 429 -> `Busy` (code `command_queue_full`); 401 -> `ConfigError`; 403 and 422 -> `Rejected(code, reason)`; 404/410 -> `Gone`; connect errors -> `Unavailable`; read timeout, 500, 502 -> `Ambiguous`; other 5xx -> `Unavailable`.
- `wrapper/models.py` and `wrapper/__init__.py`: `CommandAccepted`, `CommandOutcome`, and a `code` on `Rejected` and `Busy` where the wrapper sent one.
- `dispatcher/loop.py:_run_command` (the agents commands table path for compact): `CommandAccepted` -> `("done", {"response": record})`, any other outcome -> `("failed", {"error": <reason>})`.
- `tests/fakes/fake_wrapper.py`: `POST /v1/sessions/{id}/commands` takes any D2-pattern name and string args, enforces a settable client allowlist (default `["*"]`) and the wrapper's default deny list (403 `command_denied`, 403 `command_not_allowed`, 422 `invalid_command`), answers 202 with the real record shape (`id`, `name`, `args`, `origin` "client", `state` "queued", `turn_id`), and emits `command_queued`, `command_started`, `command_completed` (`data.record`); on an idle session it runs at once (state busy, then ready), during a turn after that turn completes.
- `tests/test_fake_wrapper_contract.py`: one contract case for both legs (the real leg is `-m integration`).

Tests no longer accurate (named): `tests/test_wrapper_client.py::test_sessions_and_control_methods` pins `command()` returning the response JSON dict and the body `{"name"}`; it now asserts `{name, args}` and a `CommandAccepted`. `tests/test_dispatcher.py::test_interrupt_and_compact_commands` keeps its assertions if the result shape `{"response": record}` holds; it changes only where it reads the fake's old `command_id` key.

## Acceptance conditions

- ac1: command() posts {name, args} and maps 202, 409, 429, 401, 403, 422, 404, connect error, read timeout, 500 and 503 to the D10 outcomes (new) [evidence: test:tests/test_wrapper_client.py::test_command_outcomes]
- ac2: the control-methods test asserts the new body and outcome (updated) [evidence: test:tests/test_wrapper_client.py::test_sessions_and_control_methods]
- ac3: contract, both legs: POST /commands with any allowed name and args answers 202 with id, name, args and state queued; {name: exit} answers 403 command_denied (new; the real leg runs with -m integration in CI or on a Docker host after orch-wrapper-pin-0-4-0) [evidence: test:tests/test_fake_wrapper_contract.py::test_commands_any_name_and_denied]
- ac4: the fake emits command_queued, command_started and command_completed with the record, at once when idle and after the running turn completes otherwise (new) [evidence: test:tests/test_fake_wrapper_contract.py::test_fake_command_events_and_turn_ordering]
- ac5: (Docker) the agents compact command still ends done with the wrapper record as response [evidence: test:tests/test_dispatcher.py::test_interrupt_and_compact_commands]
- ac6: Docker-free checks and lint pass [evidence: command:uv run --frozen pytest tests/test_wrapper_client.py tests/test_fake_wrapper_contract.py && mise run lint]

## Files

- `src/agents_orchestrator/wrapper/client.py`
- `src/agents_orchestrator/wrapper/models.py`
- `src/agents_orchestrator/wrapper/__init__.py`
- `src/agents_orchestrator/dispatcher/loop.py`
- `tests/test_wrapper_client.py`
- `tests/fakes/fake_wrapper.py`
- `tests/test_fake_wrapper_contract.py`
- `tests/test_dispatcher.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
