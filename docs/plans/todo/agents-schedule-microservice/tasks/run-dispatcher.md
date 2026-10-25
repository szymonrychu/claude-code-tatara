---
title: run dispatcher
status: todo
repo: agents-schedule
value: "a new run starts one session from its preset and sends its prompt, never twice, within the concurrency caps"
files: [src/agents_schedule/dispatcher.py, src/agents_schedule/prompt.py, tests/test_dispatcher.py]
verify: "uv run --frozen pytest tests/test_dispatcher.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [runs-repository, schedules-repository, schedule-settings-model]
model: opus
review: full
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

# run dispatcher

## Requirement

Add `agents_schedule.dispatcher` and `agents_schedule.prompt` (design D7, D8, D9, D15; approvals A3, A8) on agents-common v0.3.0 `runs.dispatch`, `runs.running_session`, `runs.deliver` and `OrchestratorClient` (contracts `preset-mapping-model`, `agents-common-lib`, `agents-common-reuse`, `preset-reuse-running-agent`; bearer service token on the orchestrator service port, `orch-service-tokens`). No second HTTP client and no second dispatch algorithm is written here.

- `render_prompt(template, schedule_name, fired_at) -> str`: replaces exactly `{schedule_name}` and `{fired_at}` (ISO 8601 in the schedule's zone); every other brace is left as written (no `str.format`).
- `session_slug(schedule_name, run_id) -> str`: DNS-1123 label `<schedule name slug, at most 24>-<first 8 hex of run id>`, at most 40 chars (`code/agents-orchestrator/src/agents_orchestrator/spec.py:validate_slug`).
- A `RunStore` over the runs table (the agents-common protocol), so `runs.dispatch` records `session_id` and `message_id` on the run with guarded updates.
- `dispatch_once(pool, client, settings) -> bool`: `runs.claim_next` under the caps (`new -> in-progress`); a claimed run whose schedule is now disabled goes `in-progress -> ignored` reason `schedule_disabled`. Otherwise the run is sent in one of two ways, each at most once, with the rendered prompt carrying `marker("schedule", run_id)` (`<!-- agents-schedule:<id> -->`):
  - Reuse (design D15): when the run's `reuse` is null, `client.get_preset(preset_id)` reports `reuse_running_agent` true, and the schedule's `latest_with_session` run has a `session_id` for which `runs.running_session(client, session_id)` returns a session, set `reuse = delivered` (guarded) and post the prompt there with `runs.deliver(client, store, run, session_id, text, marker)`. A returned RunRef (message recorded) ends the pass; `None` (session gone or being deleted) sets `reuse = fallback` and falls through to creation. The overlap rule D6 keeps at most one new or in-progress run per schedule, so reuse applies when the previous run is already finished but its session is still running.
  - Create: `runs.dispatch` with the slug (the run's `session_slug`) and the `PresetBinding` of the schedule's `preset_id`, with `session_id` cleared on the RunRef after a fallback: create the session from the preset (409 resolves the existing session by slug), record `session_id`, look for a message with the marker before posting, post, record `message_id`.
  A restart at any point resumes the same run: `reuse = delivered` without `message_id` re-runs `runs.deliver` (adopt-before-post, so no second prompt), `reuse = fallback` or null with the session already created resumes `runs.dispatch`. No second session is created and no second prompt is posted.
- Errors: preset gone (404 on `get_preset` or on create) -> `failed` reason `preset_not_found` (set by `runs.dispatch`); the orchestrator refuses (422) -> `failed` reason `orchestrator_refused: <code>`; transient (connection error, 5xx, 503) -> stays `in-progress` with `attempts + 1` and is resumed on a later pass with backoff; at `SCHED_DISPATCH_MAX_ATTEMPTS` -> `failed` reason `orchestrator_unavailable`.
- `run_dispatcher(pool, client, settings, stop)` resumes in-progress runs without `message_id`, then loops `dispatch_once` until it returns False, then sleeps `SCHED_POLL_SECONDS` or wakes on a new run.

## Acceptance conditions

- AC1: a new run creates a session from its preset, posts the rendered prompt and records both ids [evidence: test:tests/test_dispatcher.py::test_dispatch_happy_path]
- AC2: a restart after create, or after post, never creates a second session or posts a second prompt [evidence: test:tests/test_dispatcher.py::test_resume_never_repeats]
- AC3: a 409 on create resolves the existing session [evidence: test:tests/test_dispatcher.py::test_conflict_resolves_existing_session]
- AC4: at most SCHED_MAX_IN_PROGRESS runs are in-progress and later runs wait FIFO [evidence: test:tests/test_dispatcher.py::test_global_cap_fifo]
- AC5: a missing preset fails the run with reason preset_not_found; transient errors retry then fail orchestrator_unavailable [evidence: test:tests/test_dispatcher.py::test_error_mapping]
- AC6: placeholders render and other braces are left alone [evidence: test:tests/test_dispatcher.py::test_render_prompt]
- AC7: the slug is a DNS-1123 label of at most 40 characters for any schedule name [evidence: test:tests/test_dispatcher.py::test_slug_is_dns_label]
- AC8: with the preset opting in and the schedule's previous run's session running, the run posts its prompt there and creates no session [evidence: test:tests/test_dispatcher.py::test_reuse_posts_to_running_session]
- AC9: a preset that does not opt in creates a new session even when the previous session is running [evidence: test:tests/test_dispatcher.py::test_no_reuse_when_preset_not_opted_in]
- AC10: reuse falls back to a new session when the previous session is gone or deliver returns None [evidence: test:tests/test_dispatcher.py::test_reuse_falls_back_when_session_gone]
- AC11: a restart after the reuse post never posts a second prompt [evidence: test:tests/test_dispatcher.py::test_reuse_resume_never_reposts]

## Files

- `src/agents_schedule/dispatcher.py`
- `src/agents_schedule/prompt.py`
- `tests/test_dispatcher.py`

## Interfaces

- `agents_schedule.prompt:render_prompt(template: str, schedule_name: str, fired_at: datetime) -> str`, `session_slug(schedule_name: str, run_id: UUID) -> str`, the marker from agents-common `marker("schedule", run_id)`.
- `agents_schedule.dispatcher:RunsStore` (agents-common `RunStore`), `dispatch_once(pool, client, settings) -> bool`, `run_dispatcher(pool, client, settings, stop) -> None` (part `sched-dispatch`).
- Consumes `agents_common.runs.dispatch`, `running_session`, `deliver`, `PresetBinding`, `agents_common.orchestrator.OrchestratorClient` (`get_preset`, `Preset.reuse_running_agent`), and `db.runs.latest_with_session`.

## Expected outcome

Each new run yields exactly one prompt, in a new session or (preset opt-in) in the schedule's still-running earlier session, under the caps, and every failure has a reason.

## Steps

- Write tests/test_dispatcher.py against `agents_common.fake_orchestrator` (contract `agents-common-lib`) and a migrated DB; run: fails.
- Write prompt.py and dispatcher.py; `uv run --frozen pytest tests/test_dispatcher.py -q`: `11 passed`.
- Lint clean.

## Notes

- The prompt goes as a message after create; presets carry no prompt (`code/agents-orchestrator/src/agents_orchestrator/spec.py:SessionSpec`). do-not-build: a prompt field on presets.
- Same dispatch as agents-webhook (its design D8), with this service's marker and slug; the reuse branch is the agents-webhook rule keyed by the schedule (its design "Cross-epic impact"). The overlap rule D6 means the earlier run is finished by the time the later one is claimed.
- If an agents-common signature differs from the names above, use the library's as released; never re-implement dispatch here.

- 2026-10-25 amended: align to released agents-common v0.3.0 session names and the reuse rule
