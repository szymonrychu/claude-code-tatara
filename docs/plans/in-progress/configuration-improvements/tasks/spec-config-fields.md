---
title: spec config fields
status: in-progress
repo: agent-orchestrator
value: "presets and clusters carry validated wrapper settings, a leader lease and an autoclose time"
files: [src/agent_orchestrator/spec.py, src/agent_orchestrator/settings.py, tests/test_spec_config.py]
verify: "uv run --frozen pytest -q tests/test_spec_config.py && uv run ruff check . && uv run ruff format --check ."
depends_on: []
model: ""
review: ""
verified_head: ""
points: 1
expected_minutes: 5
expected_tokens: 750000
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# spec config fields

## Requirement

Add the create-time configuration fields every other task builds on (design D1, D4, D5, D6; approvals A1, A3, A4). In `src/agent_orchestrator/spec.py`:

- `ClusterSpec.wrapper: WrapperSettings | None = None`, with `extra="forbid"` models that mirror the claude-code-wrapper 0.2.0 shapes (`code/claude-code-wrapper/src/claude_code_wrapper/config.py`; the wrapper is only a dev dependency, so the orchestrator defines its own models): `hooks` (a map whose keys are the 21 wrapper `HOOK_EVENTS`, copied as a module constant, each a list of at most 20 actions; action `command` {run (1..16384 chars), env (keys `[A-Z_][A-Z0-9_]*`)} or `webhook` {url (http or https with a host), secret, headers, retries >= 0}, discriminated by `type`; common keys timeout_seconds > 0, blocking, on_error allow|deny, matcher (compiling regex, only on onAgentToolCall and onToolResult), interval_seconds > 0 and when busy|always (only on onTick, interval required there)); `auto_compact` {idle_seconds >= 0, instructions (one line, no control characters, at most 2000 chars), min_context_tokens >= 0}; `system_append` (at most 16384 chars); `permissions` {allow: list[str], deny: list[str]}; `mcp_servers` (name `[A-Za-z0-9_-]{1,64}`, `any-mcp` refused as reserved; stdio {command, args, env} or http|sse {url, headers}); `plugins` {marketplaces [{name, source}], install [{plugin `name@marketplace`, scope user|project|local, required}], every install marketplace listed or `claude-plugins-official`}; `turn_stall_seconds` >= 0; `max_restarts` 0..10; `restart_continue_prompt`; `turn_max_seconds` >= 0; `agent_commands` (each one of compact, context, mcp, reload-plugins, reload-skills).
- `ClusterSpec.leader_lease_seconds: int | None` (60..604800); a model validator refuses it unless the spec is a hive (`max_replicas > 1`) with the message `leader_lease_seconds requires a hive cluster (max_replicas > 1)`.
- `ClusterSpec.autoclose_after_seconds: int | None` (1..2592000); `validate_spec` refuses a value below `settings.autoclose_min_seconds` with `autoclose_after_seconds <n> is below the minimum <m>`.

In `src/agent_orchestrator/settings.py` add `autoclose_min_seconds: int = 300` (env `ORCH_AUTOCLOSE_MIN_SECONDS`, >= 1). Validation errors name the field path (for example `wrapper.hooks.onTick.0.interval_seconds`). Unset fields dump to nothing (`model_dump(exclude_none=True)`), so presets stay sparse. The fields are create-time only: no new in-place spec writer; MEMORY's list of runtime-mutable fields stays `replicas` and `init_scripts`.

## Acceptance conditions

- AC1: a wrapper block with every key of design D1 validates and round-trips through model_dump(exclude_none=True) unchanged [evidence: test:tests/test_spec_config.py::test_wrapper_block_round_trips]
- AC2: unknown hook event, matcher outside the tool events, onTick without interval_seconds, interval_seconds or when outside onTick, a non-http webhook url and more than 20 actions are refused, each naming its field path [evidence: test:tests/test_spec_config.py::test_hook_rules_refused]
- AC3: multi-line or over-long auto_compact instructions, an any-mcp MCP server name, a plugin from an unlisted marketplace and an unknown agent command are refused [evidence: test:tests/test_spec_config.py::test_wrapper_value_rules_refused]
- AC4: leader_lease_seconds is accepted from 60 to 604800 on hive specs only, and validate_spec refuses autoclose_after_seconds below settings.autoclose_min_seconds (default 300, overridden by ORCH_AUTOCLOSE_MIN_SECONDS) [evidence: test:tests/test_spec_config.py::test_lease_and_autoclose_bounds]
- AC5: a spec without the new fields dumps none of their keys, so presets stay sparse [evidence: test:tests/test_spec_config.py::test_unset_fields_stay_sparse]
- AC6: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

## Files

- `src/agent_orchestrator/spec.py`
- `src/agent_orchestrator/settings.py`
- `tests/test_spec_config.py`

## Interfaces

Builds part `orch-spec-config-fields` (`spec.py::WrapperSettings`, `ClusterSpec.wrapper`, `ClusterSpec.leader_lease_seconds`, `ClusterSpec.autoclose_after_seconds`, `Settings.autoclose_min_seconds`), used by render-wrapper-settings, leader-lease-expiry, autoclose-sweeper and config-cluster-views. Adds env name `ORCH_AUTOCLOSE_MIN_SECONDS` to contract `agent-orchestrator-settings-env`.

## Expected outcome

`ClusterSpec` accepts `wrapper`, `leader_lease_seconds` and `autoclose_after_seconds` with named validation errors, and `ORCH_AUTOCLOSE_MIN_SECONDS` sets the autoclose floor (default 300).

## Steps

- Red, write `tests/test_spec_config.py` with the five tests named in the acceptance conditions and run `uv run --frozen pytest -q tests/test_spec_config.py` (fails on unknown fields)
- Green, add the models, fields and setting
- Run the verify command.

## Notes

Follow the existing `_env` and `_hook_url` validator style in `spec.py`. The `_cap` validator resolves `max_replicas` first, so the lease validator runs after it. Postgres-backed tests need Docker; these tests are pure model tests.
