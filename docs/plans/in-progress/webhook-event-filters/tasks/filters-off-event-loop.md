---
title: filters off event loop
status: done
repo: agents-webhook
value: a large rule set or event cannot stall webhook ingest
files: [src/agents_webhook/filters.py, src/agents_webhook/ingest/app.py, src/agents_webhook/api/routes.py, tests/test_filters.py, tests/test_ingest_http.py, README.md]
verify: "uv run pytest tests/test_filters.py tests/test_ingest_http.py -o addopts= && uv run ruff check ."
depends_on: []
model: ""
review: ""
verified_head: 9f048aa
points: 3
expected_minutes: 8
expected_tokens: 849076
points_actual: 3
actual_minutes: 6
actual_tokens: 592137
actual_roles: impl 6
actual_role_tokens: impl 592137
---

# filters off event loop

## Requirement

Epic security review 2026-10-25 (medium): filter validation and evaluation, and regex compilation on a `_rule_set` cache miss, run synchronously inside the async ingest handler (ingest/app.py `verdict`, filters.py). The validated bounds allow 20 rules x 50 values = 1000 RE2 patterns per list, each searching every field text up to 65536 chars and every list element. One authenticated delivery against a large rule set can stall the event loop for seconds, blocking other endpoints' ingest and the probes. RE2 itself stays linear.

Fix in agents-webhook:
1. Run the filter verdict (classify plus filters.evaluate, including any compile on a cache miss) off the event loop via `asyncio.to_thread` in ingest, and in the api preview route.
2. Add a total budget per endpoint, enforced in `filters.validate`: at most 200 values summed across all allow and deny rules (`MAX_TOTAL_VALUES = 200`). The error carries the path, as other validation errors do. Keep the per-rule and per-list bounds.
3. Cap the number of list elements evaluated per field (`MAX_LIST_ITEMS = 100`). Past the cap, fail closed exactly like the oversize text rule: a regex or equals rule on a list longer than the cap cannot satisfy allow, and counts as a deny match.
4. Document both limits and the fail-closed list rule in the filters.py docstring and the README `## Filters`.

## Acceptance conditions

- AC1: ingest and preview evaluate filters off the event loop [evidence: test:tests/test_ingest_http.py::test_filter_verdict_runs_off_event_loop]
- AC2: validation refuses more than 200 values in total, naming the path [evidence: test:tests/test_filters.py::test_total_values_budget]
- AC3: a list longer than MAX_LIST_ITEMS fails closed for allow and deny [evidence: test:tests/test_filters.py::test_oversized_list_fails_closed]
- AC4: the suite and lint pass [evidence: command:mise run test && mise run lint]

## Files

- `src/agents_webhook/filters.py`
- `src/agents_webhook/ingest/app.py`
- `src/agents_webhook/api/routes.py`
- `tests/test_filters.py`
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
