---
title: run dispatcher
status: todo
repo: agents-schedule
value: "a new run starts one cluster from its preset and sends its prompt, never twice, within the concurrency caps"
files: [src/agents_schedule/dispatcher.py, src/agents_schedule/prompt.py, tests/test_dispatcher.py]
verify: "uv run --frozen pytest tests/test_dispatcher.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [runs-repository, schedules-repository, schedule-settings-model]
owns: [sched-dispatch]
uses: [sched-runs-repo, sched-schedules-repo, agents-common-lib, preset-mapping-model, orch-service-tokens, orch-cluster-create-api]
model: opus
estimate: 5
estimate_by: formula
actual: ""
actual_roles: ""
review: full
worktree: ""
branch: ""
verified_head: ""
run: ""
provides: []
---

# run dispatcher

## Requirement

Add `agents_schedule.dispatcher` and `agents_schedule.prompt` (design D7, D8, D9; approvals A3, A8), using the agents-common orchestrator client (contract `agents-common-lib`, bearer service token per `orch-service-tokens`); no second HTTP client is written.

- `render_prompt(template, schedule_name, fired_at) -> str`: replaces exactly `{schedule_name}` and `{fired_at}` (ISO 8601 in the schedule's zone); every other brace is left as written (no `str.format`).
- `dispatch_once(pool, client, settings) -> bool`: `runs.claim_next` under the caps; a run whose schedule is now disabled goes `new -> ignored` reason `schedule_disabled`. Otherwise, each step persisted before the next so a restart resumes rather than repeats:
  1. `cluster_slug` set once: DNS-1123 label `<schedule name slug, at most 24>-<first 8 hex of run id>` (at most 40 chars, `code/agent-orchestrator/src/agent_orchestrator/spec.py:validate_slug`).
  2. No `cluster_id`: create from the preset (`POST /api/v1/clusters {preset_id, slug}`); a 409 conflict resolves the existing cluster by slug; record `cluster_id`.
  3. No `message_id`: list the cluster's messages (`GET /api/v1/clusters/{id}/messages`); adopt an existing one, else post the rendered prompt (`POST /api/v1/clusters/{id}/messages {text}`); record `message_id`.
  4. `new -> in-progress`, `started_at = now`.
- Errors: the preset is gone or the orchestrator refuses the request (404 or 422) -> `failed` with reason `preset_missing: <message>` or `orchestrator_refused: <code>`; transient (connection error, 5xx, 503) -> stays `new`, `attempts + 1`, retried on a later pass with backoff; at `SCHED_DISPATCH_MAX_ATTEMPTS` -> `failed` reason `orchestrator_unavailable`.
- `run_dispatcher(pool, client, settings, stop)` loops `dispatch_once` until it returns False, then sleeps `SCHED_POLL_SECONDS` or wakes on a new run.

## Acceptance conditions

- AC1: a new run creates a cluster from its preset, posts the rendered prompt and goes in-progress [evidence: test:tests/test_dispatcher.py::test_dispatch_happy_path]
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

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
