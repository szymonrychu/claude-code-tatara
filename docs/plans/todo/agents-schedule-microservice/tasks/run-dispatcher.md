---
title: run dispatcher
status: todo
repo: agents-schedule
value: "a new run starts one cluster from its preset and sends its prompt, never twice, within the concurrency caps"
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

Add `agents_schedule.dispatcher` and `agents_schedule.prompt` (design D7, D8, D9; approvals A3, A8) on agents-common `runs.dispatch` and `OrchestratorClient` (contracts `preset-mapping-model`, `agents-common-lib`; bearer service token on the orchestrator service port, `orch-service-tokens`). No second HTTP client and no second dispatch algorithm is written here.

- `render_prompt(template, schedule_name, fired_at) -> str`: replaces exactly `{schedule_name}` and `{fired_at}` (ISO 8601 in the schedule's zone); every other brace is left as written (no `str.format`).
- `cluster_slug(schedule_name, run_id) -> str`: DNS-1123 label `<schedule name slug, at most 24>-<first 8 hex of run id>`, at most 40 chars (`code/agent-orchestrator/src/agent_orchestrator/spec.py:validate_slug`).
- A `RunStore` over the runs table (the agents-common protocol), so `runs.dispatch` records `cluster_id` and `message_id` on the run with guarded updates.
- `dispatch_once(pool, client, settings) -> bool`: `runs.claim_next` under the caps (`new -> in-progress`); a claimed run whose schedule is now disabled goes `in-progress -> ignored` reason `schedule_disabled`. Otherwise `runs.dispatch` with the preset binding (`PresetBinding` of the schedule's `preset_id`), the slug and the rendered prompt carrying `marker("schedule", run_id)` (`<!-- agents-schedule:<id> -->`): create from the preset (409 resolves the existing cluster by slug), record `cluster_id`, look for a message with the marker before posting, post, record `message_id`. A restart at any point resumes the same run and never creates a second cluster or posts a second prompt.
- Errors: preset gone or the orchestrator refuses (404 or 422) -> `failed` with reason `preset_missing: <message>` or `orchestrator_refused: <code>`; transient (connection error, 5xx, 503) -> stays `in-progress` with `attempts + 1` and is resumed on a later pass with backoff; at `SCHED_DISPATCH_MAX_ATTEMPTS` -> `failed` reason `orchestrator_unavailable`.
- `run_dispatcher(pool, client, settings, stop)` resumes in-progress runs without `message_id`, then loops `dispatch_once` until it returns False, then sleeps `SCHED_POLL_SECONDS` or wakes on a new run.

## Acceptance conditions

- AC1: a new run creates a cluster from its preset, posts the rendered prompt and records both ids [evidence: test:tests/test_dispatcher.py::test_dispatch_happy_path]
- AC2: a restart after create, or after post, never creates a second cluster or posts a second prompt [evidence: test:tests/test_dispatcher.py::test_resume_never_repeats]
- AC3: a 409 on create resolves the existing cluster [evidence: test:tests/test_dispatcher.py::test_conflict_resolves_existing_cluster]
- AC4: at most SCHED_MAX_IN_PROGRESS runs are in-progress and later runs wait FIFO [evidence: test:tests/test_dispatcher.py::test_global_cap_fifo]
- AC5: a missing preset fails the run with a reason; transient errors retry then fail orchestrator_unavailable [evidence: test:tests/test_dispatcher.py::test_error_mapping]
- AC6: placeholders render and other braces are left alone [evidence: test:tests/test_dispatcher.py::test_render_prompt]
- AC7: the slug is a DNS-1123 label of at most 40 characters for any schedule name [evidence: test:tests/test_dispatcher.py::test_slug_is_dns_label]

## Files

- `src/agents_schedule/dispatcher.py`
- `src/agents_schedule/prompt.py`
- `tests/test_dispatcher.py`

## Interfaces

- `agents_schedule.prompt:render_prompt(template: str, schedule_name: str, fired_at: datetime) -> str`, `cluster_slug(schedule_name: str, run_id: UUID) -> str`, the marker from agents-common `marker("schedule", run_id)`.
- `agents_schedule.dispatcher:RunsStore` (agents-common `RunStore`), `dispatch_once(pool, client, settings) -> bool`, `run_dispatcher(pool, client, settings, stop) -> None` (part `sched-dispatch`).
- Consumes `agents_common.runs.dispatch`, `PresetBinding`, `agents_common.orchestrator.OrchestratorClient`.

## Expected outcome

Each new run yields exactly one cluster and one prompt, under the caps, and every failure has a reason.

## Steps

- Write tests/test_dispatcher.py against `agents_common.fake_orchestrator` (contract `agents-common-lib`) and a migrated DB; run: fails.
- Write prompt.py and dispatcher.py; `uv run --frozen pytest tests/test_dispatcher.py -q`: `7 passed`.
- Lint clean.

## Notes

- The prompt goes as a message after create; presets carry no prompt (`code/agent-orchestrator/src/agent_orchestrator/spec.py:ClusterSpec`). do-not-build: a prompt field on presets.
- Same dispatch as agents-webhook (its design D8), with this service's marker and slug.
- If an agents-common signature differs from the names above, use the library's as released; never re-implement dispatch here.
