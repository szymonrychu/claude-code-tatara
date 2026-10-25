---
title: schedule settings model
status: todo
repo: agents-schedule
value: every process reads one validated configuration and a bad variable is named at startup
files: [src/agents_schedule/settings.py, tests/test_settings.py, README.md]
verify: "uv run --frozen pytest tests/test_settings.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [scaffold-project-and-cli]
owns: [agents-schedule-settings-env]
uses: [agents-common-lib]
model: ""
estimate: 5
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

# schedule settings model

## Requirement

Add `agents_schedule.settings` (design D8, D11, D13; approval A1) on the agents-common settings base (contract `agents-common-lib`), env prefix `SCHED_`:

- `SCHED_DATABASE_URL` (required), `SCHED_ORCHESTRATOR_URL` (required; the orchestrator's internal service-token port, contract `orch-service-tokens`), `SCHED_ORCHESTRATOR_TOKEN` or `SCHED_ORCHESTRATOR_TOKEN_FILE` (exactly one required; the file wins when both are set and is read at load), `SCHED_ALLOWED_CIDRS` (CSV, default `127.0.0.1/32`), `SCHED_PORT` (default 8000), `SCHED_MAX_IN_PROGRESS` (default 3, 1..50), `SCHED_MAX_PER_SCHEDULE` (default 1, 1..10), `SCHED_DEFAULT_TIMEZONE` (default `Europe/Warsaw`, must be a valid IANA zone), `SCHED_TICK_SECONDS` (default 15, 1..300), `SCHED_POLL_SECONDS` (default 10, 1..300), `SCHED_DISPATCH_MAX_ATTEMPTS` (default 5, 1..20).
- `load_settings()` raises `SettingsError` naming every bad or missing variable at once (the agents-common pattern, as `code/agent-orchestrator/src/agent_orchestrator/settings.py`).
- README `## Configuration` lists every variable with default and meaning; this is the contract `agents-schedule-settings-env` agents-helmfile consumes.

## Acceptance conditions

- AC1: defaults load with only the required variables set [evidence: test:tests/test_settings.py::test_defaults]
- AC2: every bad or missing variable is named in one SettingsError [evidence: test:tests/test_settings.py::test_errors_name_each_variable]
- AC3: the token file wins over the inline token and is read at load [evidence: test:tests/test_settings.py::test_token_file_wins]
- AC4: an unknown timezone is refused [evidence: test:tests/test_settings.py::test_default_timezone_must_be_iana]
- AC5: README documents every SCHED_ variable [evidence: doc-section:README.md#Configuration]

## Files

- `src/agents_schedule/settings.py`
- `tests/test_settings.py`
- `README.md`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
