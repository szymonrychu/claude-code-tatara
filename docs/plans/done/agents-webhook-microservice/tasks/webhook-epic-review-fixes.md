---
title: webhook epic review fixes
status: done
repo: agents-webhook
value: worker prompts match the preview and API errors are honest and uniform
files: [src/agents_webhook/db/events.py, src/agents_webhook/migrations, src/agents_webhook/worker.py, src/agents_webhook/api/routes.py, src/agents_webhook/cli.py, tests/test_worker.py, tests/test_api.py, tests/test_ingest_http.py, README.md]
verify: "uv run pytest tests/test_api.py tests/test_ingest_http.py -o addopts= -q && uv run ruff check ."
depends_on: [webhook-template-memory-cap]
model: ""
review: ""
verified_head: a6557a5
points: 3
expected_minutes: 14
expected_tokens: 723362
points_actual: 3
actual_minutes: 5
actual_tokens: 1067583
actual_roles: "impl 3, review 2"
actual_role_tokens: "impl 667697, review 399886"
---

# webhook epic review fixes

## Requirement

Epic whole-diff review 2026-10-25 (full findings: /Users/szymonri/Documents/claude-code-tatara/.scratchpad/wh-epic-review-webhook.md). Three fixes in agents-webhook:

1. The template context is lossy. `to_normalized` (db/events.py, used by worker.py) rebuilds the event from the row, which stores neither `draft` nor `changed`, so the worker always renders `draft=False` and `changed=()`. The README documents both variables, and the UI preview shows the real values. Persist them: add a migration with columns for draft and changed, and write them in record(). `to_normalized` restores them, so the worker renders exactly what the preview shows. Add a test that a stored draft PR with changed fields renders the same context in the worker as in the preview.
2. A non-UUID preset_id gives the wrong error. The orchestrator service port answers 403 for a non-UUID preset path, and api/routes.py maps that to 503 `orchestrator_unavailable` instead of the documented 422 `unknown_preset`. Validate preset_id as a UUID in the request model, which gives 422 unknown_preset with the standard error shape. Map an orchestrator 401/403 to a distinct, honest error code (for example 502 `orchestrator_auth`) instead of 503. Test both against a fake that behaves like the real service_auth.py: 403 on a non-UUID path, 401 on a bad token.
3. The 408 body in cli.py is `{"error":"request_timeout"}`. Change it to the standard `{"error":{"code":"request_timeout","message":...}}` shape and test it.

Update the README and docs where they describe these.

## Acceptance conditions

- AC1: draft and changed survive storage and reach the worker's template context [evidence: test:tests/test_worker.py::test_worker_context_matches_preview_for_draft_and_changed]
- AC2: a non-UUID preset_id gives 422 unknown_preset and an orchestrator auth failure is not reported as 503 [evidence: test:tests/test_api.py::test_preset_id_validation_and_orchestrator_auth_errors]
- AC3: the 408 body uses the standard error shape [evidence: test:tests/test_ingest_http.py::test_request_timeout_body_shape]
- AC4: the suite and lint pass [evidence: command:mise run test && mise run lint]

## Files

- `src/agents_webhook/db/events.py`
- `src/agents_webhook/migrations`
- `src/agents_webhook/worker.py`
- `src/agents_webhook/api/routes.py`
- `src/agents_webhook/cli.py`
- `tests/test_worker.py`
- `tests/test_api.py`
- `tests/test_ingest_http.py`
- `README.md`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.

- 2026-10-25 done
