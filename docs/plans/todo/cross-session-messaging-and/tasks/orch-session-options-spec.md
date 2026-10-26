---
title: orch session options spec
status: todo
repo: agents-orchestrator
value: "presets and sessions can carry the two new options, and the server refuses Kubernetes access until it is configured"
files: [src/agents_orchestrator/spec.py, src/agents_orchestrator/settings.py, src/agents_orchestrator/api/schemas.py, src/agents_orchestrator/api/sessions.py, openapi.json, README.md, tests/test_spec_session_options.py, tests/test_nomenclature.py]
verify: "unset VIRTUAL_ENV && uv run --frozen pytest -q tests/test_spec_session_options.py tests/test_settings.py tests/test_readme_api.py tests/test_nomenclature.py && mise run lint"
depends_on: []
model: opus
review: ""
verified_head: ""
points: 3
expected_minutes: 7
expected_tokens: 977684
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# orch session options spec

## Requirement

User decisions 2026-10-26, verbatim: "Both options are per-session spec fields, settable on presets." "Kubernetes access means: all namespaces, all resources, full read-write." "Cross-session messaging means: the session's leader can send messages to other sessions' leaders and receive messages from other sessions' leaders."

Goals G1 and G2 (epic README), verbatim: "A sparse create-time spec option for cross-session messaging; ..." and "A sparse create-time spec option for Kubernetes access; ...". Design D1, D3, D4 (setting), D5 (setting), D10 (settings).

Scope (agents-orchestrator):
- `src/agents_orchestrator/spec.py` `SessionSpec`: `session_messaging: bool | None = Field(default=None, strict=True)` and `kube_access: bool | None = Field(default=None, strict=True)`, each with a comment like `reuse_running_agent`'s. Unset is not stored on a session row and not dumped in a preset.
- `validate_spec`: `kube_access` true while `settings.kube_access_service_account` is empty is an error "Kubernetes access is not configured (ORCH_KUBE_ACCESS_SERVICE_ACCOUNT is unset)", with the `stored` exemption the cache check has (accepted on a preset PUT when unchanged from the stored spec).
- `src/agents_orchestrator/settings.py`: `kube_access_service_account: str = ""` with a property `kube_access_available`; `agent_service_account: str = "default"`; `kubectl_version: str = "1.33"`; `session_message_rate_per_minute: int = Field(default=10, ge=1)`; `session_message_queued_max: int = Field(default=20, ge=1)`; `session_message_max_hops: int = Field(default=8, ge=1)`; `session_message_pair_max_per_hour: int = Field(default=30, ge=1)`.
- `src/agents_orchestrator/api/schemas.py`: `MetaKubeAccess(available: bool)`; `Meta.kube_access: MetaKubeAccess`. `src/agents_orchestrator/api/sessions.py` `meta()` fills it from the setting.
- `README.md`: the `POST /api/v1/sessions` bullet and `### Session configuration` list both sparse fields and what they do; `## Configuration` gains one row per new setting (`ORCH_KUBE_ACCESS_SERVICE_ACCOUNT`, `ORCH_AGENT_SERVICE_ACCOUNT`, `ORCH_KUBECTL_VERSION`, `ORCH_SESSION_MESSAGE_RATE_PER_MINUTE`, `ORCH_SESSION_MESSAGE_QUEUED_MAX`, `ORCH_SESSION_MESSAGE_MAX_HOPS`, `ORCH_SESSION_MESSAGE_PAIR_MAX_PER_HOUR`); `### GET /api/v1/meta` names `kube_access.available`.
- `openapi.json` regenerated (`uv run python -m agents_orchestrator.api.openapi > openapi.json`).
- `tests/test_nomenclature.py`: `ALLOWED_PHRASES` gains `"cluster-admin"`. This test is no longer accurate for this epic: its docstring allows lines naming a Kubernetes cluster, and `cluster-admin` is the Kubernetes built-in ClusterRole this epic's README and chart must name (design D2); nothing else in that test changes.

The settings are only declared and documented here; the tasks that use them are orch-agent-service-accounts, orch-kube-access-render, orch-agent-session-messaging and chart-kube-access-rbac.

## Acceptance conditions

- ac1: session_messaging and kube_access accept booleans only (a string or number is a 422), and when not given they are neither stored on the session nor dumped in a preset [evidence: test:tests/test_spec_session_options.py::test_options_sparse_and_strict]
- ac2: a preset saved with both options returns them on GET, and a session created from that preset carries both in its spec [evidence: test:tests/test_spec_session_options.py::test_preset_carries_options_to_session]
- ac3: kube_access true is refused 422 invalid_request naming ORCH_KUBE_ACCESS_SERVICE_ACCOUNT when the setting is unset and accepted when it is set, and a preset PUT that keeps an unchanged stored kube_access true is accepted while the setting is unset [evidence: test:tests/test_spec_session_options.py::test_kube_access_gated_by_setting]
- ac4: GET /api/v1/meta reports kube_access.available false without the setting and true with it [evidence: test:tests/test_spec_session_options.py::test_meta_kube_access_available]
- ac5: the six new settings have the documented defaults and reject a rate, cap or hop maximum below 1 [evidence: test:tests/test_spec_session_options.py::test_new_settings_defaults_and_bounds]
- ac6: README documents every setting and route, openapi.json matches the app and the nomenclature guard passes [evidence: command:unset VIRTUAL_ENV && uv run --frozen pytest -q tests/test_readme_api.py tests/test_settings.py tests/test_nomenclature.py tests/test_spec_hive.py tests/test_api_presets.py]
- ac7: lint passes [evidence: command:mise run lint]

## Files

- `src/agents_orchestrator/spec.py`
- `src/agents_orchestrator/settings.py`
- `src/agents_orchestrator/api/schemas.py`
- `src/agents_orchestrator/api/sessions.py`
- `openapi.json`
- `README.md`
- `tests/test_spec_session_options.py`
- `tests/test_nomenclature.py`

## Interfaces

- `spec.py:SessionSpec.session_messaging: bool | None` and `SessionSpec.kube_access: bool | None` (strict, sparse).
- `spec.py:validate_spec(spec, settings, stored=None)` gains the kube_access check.
- `settings.py:Settings.kube_access_service_account: str`, `.kube_access_available -> bool`, `.agent_service_account: str`, `.kubectl_version: str`, `.session_message_rate_per_minute: int`, `.session_message_queued_max: int`, `.session_message_max_hops: int`, `.session_message_pair_max_per_hour: int`.
- `api/schemas.py:MetaKubeAccess{available: bool}`, `Meta.kube_access`.
- Contract for agents-web (task web-preset-session-options): `SessionSpec.session_messaging`, `SessionSpec.kube_access`, `Meta.kube_access.available` in `openapi.json`.

## Expected outcome

A preset or session spec can carry `session_messaging` and `kube_access`; nothing changes for specs without them; `kube_access` is refused until the server is configured for it, and `/meta` says whether it is.

## Steps

- Red: write `tests/test_spec_session_options.py` with the five tests named in the acceptance conditions; run `unset VIRTUAL_ENV && uv run --frozen pytest -q tests/test_spec_session_options.py`: fails (unknown fields, no settings, no meta key).
- Green: edit `spec.py`, `settings.py`, `api/schemas.py`, `api/sessions.py`; regenerate `openapi.json`; update `README.md` and `tests/test_nomenclature.py` (`cluster-admin`); run the task's verify: passes.
- Run ac6 and ac7 commands: pass.

## Notes

- Rulings and their pin tests: strict booleans (ac1); sparse storage (ac1, the session row uses `exclude_none`, the preset `exclude_unset`); stored exemption only for an unchanged value (ac3); setting bounds (ac5).
- Precedents: `reuse_running_agent` (spec.py:436) for sparse strict booleans; the cache check in `validate_spec` (spec.py:588) and `MetaCache` (api/schemas.py:149) for the setting gate.
- `tests/test_settings.py::test_env_names_documented_in_readme` requires each new `ORCH_*` name in README `## Configuration`.
- Do not use the word "cluster" in new text except Kubernetes phrases on the guard's allowlist (`ClusterRole`, `in-cluster`, `cluster-admin` after this task).
- Orchestrator tests need Docker; run with `VIRTUAL_ENV` unset. If pytest fails on imports, the `.venv` may carry a stale shebang (retro paste-env-contents-into-the): `uv sync` recreates it.
