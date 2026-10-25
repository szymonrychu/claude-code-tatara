---
title: mxc settings model
status: todo
repo: agents-matrix-connector
value: every connector knob is one validated MATRIX_ variable with default deny and the token only from a file
files: [src/agents_matrix_connector/settings.py, tests/test_settings.py, README.md]
verify: "uv run --frozen pytest tests/test_settings.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [mxc-scaffold-and-cli]
model: sonnet
review: ""
verified_head: ""
points: 2
expected_minutes: 8
expected_tokens: 542616
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# mxc settings model

## Requirement

The `MATRIX_*` settings of the connector (design D2, D5, D6, D7, D8, D9, D10, D11; contract `matrix-connector-settings-env`). Paths are in code/agents-matrix-connector.

`src/agents_matrix_connector/settings.py`:

- `ConnectorSettings(agents_common.settings.BaseServiceSettings)` with `env_prefix="MATRIX_"` (so `MATRIX_DATABASE_URL`, `MATRIX_ORCHESTRATOR_URL`, `MATRIX_ORCHESTRATOR_TOKEN(_FILE)`, `MATRIX_HTTP_PORT` come from the base) and these fields: `homeserver_url` (required, http or https URL, trailing slash stripped), `user_id` (required, matches `^@[^:\s]+:\S+$`), `device_id` (default `agents-matrix-connector`), `self_identities: CsvList` (each a Matrix user id), `bridge_bots: CsvList` (default `["@facebookbot:szymonrichert.pl"]`), `puppet_pattern` (default `^@facebook_(?P<id>[0-9]+):`, must compile with a named group `id`), `default_policy: Literal["deny", "allow"]` (default `deny`), `group_trigger: Literal["mention", "all"]` (default `mention`), `max_new_sessions` (3, >= 1), `max_queued_per_room` (20, >= 1), `max_inbound_chars` (8000, >= 100), `reply_chunk_chars` (4000, 100..20000), `run_timeout_seconds` (1800, >= 60), `poll_seconds` (3, > 0), `sync_timeout_seconds` (30, 1..120), `retention_days` (30, >= 1), `api_allowed_cidrs: CsvList` (default `["127.0.0.1/32"]`, each a CIDR).
- `self_ids() -> frozenset[str]`: `user_id` plus `self_identities`.
- `BotSettings(ConnectorSettings)`: adds `access_token: SecretStr` and `access_token_file`; the file wins and is stripped; a missing token fails with `MATRIX_ACCESS_TOKEN::required`. `ApiSettings` is `ConnectorSettings` (the api never talks to Matrix and needs no Matrix token).
- Every invalid value raises `agents_common.settings.SettingsError` naming the `MATRIX_*` variable; the access token never appears in `repr()` or `str()` of the settings or of the error.
- `README.md` `## Configuration`: one table row per variable (name, default, which subcommands read it: migrate, api, bot), including the base fields.

User request 2026-10-25, verbatim: 'agents-matrix-connector New microservice- is meant to connect with existing matrix deployment and allow for talking to agents through facebook. Must support user/chat/room auto discovery and white/blacklosting. Hermes already uses working bridge.'

## Acceptance conditions

- AC1: defaults match the requirement and `self_ids()` holds the user id and the self identities [evidence: test:tests/test_settings.py::test_defaults_and_self_ids]
- AC2: a missing homeserver URL, user id or (for the bot) access token raises SettingsError naming the variable [evidence: test:tests/test_settings.py::test_required_variables_named]
- AC3: `MATRIX_ACCESS_TOKEN_FILE` wins over `MATRIX_ACCESS_TOKEN` and is stripped [evidence: test:tests/test_settings.py::test_access_token_file_wins]
- AC4: invalid user id, CIDR, policy, trigger, puppet pattern (no `id` group) and out-of-range limits are rejected naming the variable [evidence: test:tests/test_settings.py::test_invalid_values_named]
- AC5: the access token never appears in repr, str or the SettingsError text [evidence: test:tests/test_settings.py::test_token_never_rendered]
- AC6: README `## Configuration` lists every settings field as a `MATRIX_*` row [evidence: test:tests/test_settings.py::test_readme_lists_every_variable]

## Files

- `src/agents_matrix_connector/settings.py`
- `tests/test_settings.py`
- `README.md`

## Interfaces

- `src/agents_matrix_connector/settings.py`: `ConnectorSettings`, `BotSettings`, `ApiSettings` (contract `matrix-connector-settings-env`, consumed by mxc-chart-workloads and helmfile-matrix-releases).

## Expected outcome

`BotSettings()` built from env with `MATRIX_DATABASE_URL`, `MATRIX_ORCHESTRATOR_URL`, `MATRIX_ORCHESTRATOR_TOKEN`, `MATRIX_HOMESERVER_URL`, `MATRIX_USER_ID` and `MATRIX_ACCESS_TOKEN_FILE` loads with default-deny policy; every bad variable is named in one error.

## Steps

- Red: `tests/test_settings.py` with the six tests (use `monkeypatch.setenv` and `tmp_path` token files). `uv run --frozen pytest tests/test_settings.py -q` fails on the missing module.
- Green: write `settings.py` and the README table. Run the verify.

## Notes

- Follow `code/agents-webhook/src/agents_webhook/settings.py` (`WebhookSettings`, `LocalSettings`) and `agents_common.settings` (`CsvList`, `_token_from_file` pattern, `SettingsError`).
- The puppet pattern is operator config, compiled with stdlib `re`; it never comes from a chat user.
