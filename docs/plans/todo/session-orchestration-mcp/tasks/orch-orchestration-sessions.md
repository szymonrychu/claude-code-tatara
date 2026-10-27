---
title: orch orchestration sessions
status: todo
repo: agents-orchestrator
value: "a flagged leader can create, scale and delete the sessions it created, never itself or a protected one"
files: [src/agents_orchestrator/api/orchestration_sessions.py, src/agents_orchestrator/api/sessions.py, src/agents_orchestrator/db/sessions.py, src/agents_orchestrator/api/schemas.py, src/agents_orchestrator/api/app.py, README.md, openapi.json, tests/test_orchestration_sessions.py]
verify: "uv run --frozen pytest tests/test_orchestration_sessions.py tests/test_api_sessions.py tests/test_api_create_from_preset.py tests/test_readme_api.py && mise run lint"
depends_on: [orch-orchestration-presets]
model: opus
review: ""
verified_head: ""
points: 8
expected_minutes: 14
expected_tokens: 3155191
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# orch orchestration sessions

## Requirement

README Goal G1, verbatim: "A session the user flagged `session_orchestration` (a per-preset or per-spec switch, off by default, set only by the user through agents-web or the public API) has orchestrator MCP tools to list, create, edit and delete presets, list, create, scale and delete sessions, and list, create, edit, delete and run cron schedules, on the user's request; only its leader may call them, and no unflagged session gets the tools."

README Goal G3, verbatim: "A flagged session changes only the sessions, presets and schedules it created; it reads all of them, with preset secrets masked except on its own; it cannot grant more privilege than it holds (`session_orchestration` is never grantable), cannot delete itself, and cannot delete a superleader or orchestrating session."

Design D4, verbatim: "Reads cover everything through trimmed views. Sessions: slug, id, preset, state, replicas, superleader, orchestration, created_by, no spec. [...] Ownership is by session id; when the owner is deleted, its objects stay and are managed from the UI. [...] The public `SessionView` and `PresetView` gain `created_by_slug` (additive; null for objects the user made) so agents-web can show it (Q7; my call pending the gate)."

Design D5, verbatim: "Applies to an agent-written preset spec, an agent-created session spec (from a spec or a preset) and the preset named by an agent-written schedule (the relay reads it first). `session_orchestration: true` is always refused; `kube_access` or `session_messaging` true only if the caller's own session has that same flag. Refusal: 403 `privilege_escalation`."

Design D6, verbatim: "1. 404 `not_found`; 2. 422 `self_delete`; 3. 403 `not_owner`; 4. 409 `protected_target` (the target has `session_orchestration` or `session_messaging`); 5. 409 `session_deleting`. Then `request_delete`. [...] Owned-session scale goes through `set_replicas`."

Design D9, verbatim: "`ORCH_ORCHESTRATION_MAX_OWNED_SESSIONS` (5): live owned sessions, else 409 `owned_limit`; the global `max_sessions` still applies."

Design D10, verbatim: "`session_create` takes an optional `prompt`, queued as a session message: sender the caller, hop the caller's hop plus 1, origin `session`."

Design D12, verbatim: "a session cannot delete itself, so mx-5 never releases its own room binding; deleting an owned session bound to a room releases that binding through the existing Matrix Q10 sweep (intended)."

Architect fix-as-ac, verbatim: "`self_delete`, `not_owner`, `protected_target` refusals."

Scope (agents-orchestrator): new `api/orchestration_sessions.py` (`GET /sessions`, `POST /sessions`, `POST /sessions/{slug}/scale`, `DELETE /sessions/{slug}` under `/agent/v1/orchestration`), `api/sessions.py` (the create path takes provenance; no copy of `check_spec` or `_create_from_preset`), `db/sessions.py` (store and read `created_by_*`), `api/schemas.py` (`SessionView.created_by_slug`), `api/app.py`, README, `openapi.json`.

Open question Q9 (pending; the plan follows the recommended answer), verbatim: "A flagged session may create sessions or schedules only from presets it created itself (or from an explicit spec); presets made in the UI, which may hold secrets in env, are refused not_owner, so their secrets never reach a pod the agent controls?" recommended "yes". Session create with `preset_id` calls `api/orchestration.py:require_own_preset` (orch-orchestration-gate) before any create work, so a preset the user made in the UI, or another session made, is refused 403 `not_owner`; a `spec` in the body is not restricted by it (the caller can only write what it can read, and reads mask other presets' secrets) and still passes `check_no_escalation`.

User settlement B4 (2026-10-27), verbatim: "Store origin `session` or `user` the same way on every enqueue path." The prompt of session_create is enqueued with the explicit origin `session` through the `origin` argument orch-message-origin made required.

## Acceptance conditions

- ac1: the sessions overview lists every session with slug, id, preset, state, replicas, superleader, orchestration and created_by, and no spec [evidence: test:tests/test_orchestration_sessions.py::test_overview_trimmed]
- ac2: session create from a preset id or a spec runs the same checks as POST /api/v1/sessions (check_spec, the create lock, max_sessions), stores the caller as created_by and refuses privilege_escalation for a preset or spec carrying session_orchestration or a flag the caller lacks [evidence: test:tests/test_orchestration_sessions.py::test_create_owned_no_escalation]
- ac3: session create with a preset_id the caller did not create (made in the UI, or by another session) is refused 403 not_owner with an audit row and no session, create from the caller's own preset and from an explicit spec pass, and the answer names no preset env value [evidence: test:tests/test_orchestration_sessions.py::test_create_from_foreign_preset_refused]
- ac4: with ORCH_ORCHESTRATION_MAX_OWNED_SESSIONS live owned sessions a create is refused 409 owned_limit, and deleting or purged sessions do not count [evidence: test:tests/test_orchestration_sessions.py::test_owned_limit]
- ac5: a create with prompt queues the prompt to the new session as a session message from the caller with hop the caller's hop plus 1 and origin session, passed explicitly [evidence: test:tests/test_orchestration_sessions.py::test_create_with_prompt]
- ac6: session delete checks in order 404 not_found, 422 self_delete, 403 not_owner, 409 protected_target for a target with session_orchestration or session_messaging, 409 session_deleting, then requests the delete [evidence: test:tests/test_orchestration_sessions.py::test_delete_checks_in_order]
- ac7: session scale changes only owned sessions through set_replicas with its existing refusal codes, and 403 not_owner otherwise [evidence: test:tests/test_orchestration_sessions.py::test_scale_owned_only]
- ac8: the public SessionView carries created_by_slug, null for sessions the user made [evidence: test:tests/test_orchestration_sessions.py::test_public_view_created_by]
- ac9: every session write, refusals included, writes an audit row with target_kind session and the target id and slug [evidence: test:tests/test_orchestration_sessions.py::test_session_writes_audited]
- ac10: the README documents every session orchestration route with its checks in order, and openapi.json matches the app [evidence: command:uv run --frozen pytest tests/test_readme_api.py]
- ac11: the targeted tests and lint pass [evidence: command:uv run --frozen pytest tests/test_orchestration_sessions.py tests/test_api_sessions.py tests/test_api_create_from_preset.py tests/test_readme_api.py && mise run lint]

## Files

- `src/agents_orchestrator/api/orchestration_sessions.py`
- `src/agents_orchestrator/api/sessions.py`
- `src/agents_orchestrator/db/sessions.py`
- `src/agents_orchestrator/api/schemas.py`
- `src/agents_orchestrator/api/app.py`
- `README.md`
- `openapi.json`
- `tests/test_orchestration_sessions.py`

## Interfaces

- `api/orchestration_sessions.py`: `router = APIRouter(prefix="/agent/v1/orchestration/sessions", tags=["agent"])`; body of create `{preset_id?: uuid, spec?: object, slug?: str, prompt?: str (<= 16000 chars)}`, exactly one of `preset_id` and `spec`.
- `api/sessions.py:_insert(conn, slug, spec, **provenance)` gains `created_by_session_id`, `created_by_slug`; the public create path passes none.
- `db/sessions.py:Session.created_by_session_id`, `created_by_slug`; owned check by session id.
- `schemas.SessionView.created_by_slug: str | None`.

## Expected outcome

A flagged leader can see every session and create, scale and delete only the ones it created, never itself or a protected one.

## Steps

- Red: write `tests/test_orchestration_sessions.py`; run `uv run --frozen pytest tests/test_orchestration_sessions.py`: fails.
- Green: module, create-path provenance, repo, view, app wiring, README, `openapi.json`; run the task's verify. Quote the summary line.

## Notes

- Reuse `check_spec`, `_create_from_preset`, `_CREATE_LOCK`, `request_delete`, `set_replicas`; import, never copy.
- The live-owned count is `db/orchestration.py:count_live_owned_sessions` (one predicate; retro: duplicate predicates were found late). The owned check is one predicate too.
- Prompt hop: `db/queue.py:turn_hop` of the caller plus 1 (1 in a user turn); origin `session`.
- `tests/test_api_sessions.py` and `tests/test_api_create_from_preset.py` must stay green; name any assertion on exact view keys that `created_by_slug` makes no longer accurate.
- DB cases run in CI (no Docker in agent pods).

- 2026-10-27 amended: Q9: create from own presets only; B4: explicit session origin
