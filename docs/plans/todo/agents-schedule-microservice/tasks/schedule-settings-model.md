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

Add `agents_schedule.settings` (design D8, D11, D13; approval A1) on agents-common `BaseServiceSettings` (contract `agents-common-lib`: per-service env prefix, `SettingsError` naming each bad variable, `*_FILE` secrets), env prefix `SCHED_`:

- `SCHED_DATABASE_URL` (required), `SCHED_ORCHESTRATOR_URL` (required; the orchestrator's service port, contracts `orch-service-tokens` and `orch-services-service`, live `http://agent-orchestrator-services:8002`), `SCHED_ORCHESTRATOR_TOKEN` or `SCHED_ORCHESTRATOR_TOKEN_FILE` (exactly one required; the base's `*_FILE` rule), `SCHED_ALLOWED_CIDRS` (CSV, default `127.0.0.1/32`), `SCHED_PORT` (default 8000), `SCHED_MAX_IN_PROGRESS` (default 3, 1..50), `SCHED_MAX_PER_SCHEDULE` (default 1, 1..10), `SCHED_DEFAULT_TIMEZONE` (default `Europe/Warsaw`, must be a valid IANA zone), `SCHED_TICK_SECONDS` (default 15, 1..300), `SCHED_POLL_SECONDS` (default 10, 1..300), `SCHED_DISPATCH_MAX_ATTEMPTS` (default 5, 1..20), `SCHED_RUN_TIMEOUT_SECONDS` (default 3600, 60..86400; the webhook's D6 rule, so a stuck turn cannot hold a slot forever).
- `load_settings()` raises `SettingsError` naming every bad or missing variable at once.
- README `## Configuration` lists every variable with default and meaning; this is the contract `agents-schedule-settings-env` agents-helmfile consumes.

## Acceptance conditions

- AC1: defaults load with only the required variables set [evidence: test:tests/test_settings.py::test_defaults]
- AC2: every bad or missing variable is named in one SettingsError [evidence: test:tests/test_settings.py::test_errors_name_each_variable]
- AC3: the token can come from a file and exactly one token source is required [evidence: test:tests/test_settings.py::test_token_sources]
- AC4: an unknown timezone is refused [evidence: test:tests/test_settings.py::test_default_timezone_must_be_iana]
- AC5: README documents every SCHED_ variable [evidence: doc-section:README.md#Configuration]

## Files

- `src/agents_schedule/settings.py`
- `tests/test_settings.py`
- `README.md`

## Interfaces

- `agents_schedule.settings:Settings` (pydantic-settings, `env_prefix="SCHED_"`), `load_settings() -> Settings`, `SettingsError` (contract `agents-schedule-settings-env`, file README.md `## Configuration`).

## Expected outcome

Every process loads one Settings object; a misconfigured pod exits at startup naming each bad variable.

## Steps

- Write tests/test_settings.py with the four named tests; run it: fails (no module).
- Write settings.py on the agents-common base; `uv run --frozen pytest tests/test_settings.py -q`: `4 passed`.
- Add README `## Configuration`; lint clean.

## Notes

- Never log the token; `repr` of Settings masks it (SecretStr).
- `SCHED_ALLOWED_CIDRS` mirrors `ORCH_ALLOWED_CIDRS`: only the oauth2-proxy sidecar (127.0.0.1) or a port-forward reaches the api.
