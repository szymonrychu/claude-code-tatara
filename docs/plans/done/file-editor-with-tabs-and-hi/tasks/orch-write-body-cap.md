---
title: orch write body cap
status: done
repo: agents-orchestrator
value: oversized saves are refused at the orchestrator before buffering and forwarding
files: [src/agents_orchestrator/api/schemas.py, src/agents_orchestrator/api/workspace.py, tests/test_api_file_write.py, openapi.json, README.md]
verify: "unset VIRTUAL_ENV && uv run --frozen pytest tests/test_api_file_write.py tests/test_readme_api.py && mise run lint"
depends_on: [orch-wrapper-pin-write]
model: sonnet
review: ""
verified_head: 1cd6f3b877c50d6fa3901e8566d1fe31323b5156
points: 2
expected_minutes: 5
expected_tokens: 543940
points_actual: 2
actual_minutes: 13
actual_tokens: 822045
actual_roles: "impl 4, review 9"
actual_role_tokens: "impl 574863, review 247182"
---

# orch write body cap

## Requirement

Epic security review finding (2026-10-27), verbatim: "agents-orchestrator/src/agents_orchestrator/api/schemas.py:289-296 (WriteFile); api/workspace.py:349-374. evidence: `content: str` has no max_length; the route is `body: schemas.WriteFile`, and the 1 MiB cap is enforced only by the wrapper (files.py write_file: `if len(data) > max_bytes`). impact: the orchestrator and the wrapper each buffer and parse the whole body before the cap check. A client that reaches the route can force large allocations on both. fix: add max_length or a Content-Length guard on the orchestrator."

Scope (agents-orchestrator): the file-write route refuses a request whose body is larger than the wrapper's write cap can ever accept (1 MiB of UTF-8 content plus JSON overhead, worst-case escaping included) before parsing it fully and before forwarding anything to the wrapper, with 413 and the same error envelope the API uses elsewhere; a content at exactly the wrapper's cap is still forwarded; openapi.json and README stay in sync if the schema changes. The wrapper side is unchanged (noted, not doing now).

## Acceptance conditions

- ac1: an oversized write body is refused with 413 before any wrapper request is made [evidence: test:tests/test_api_file_write.py::test_write_body_too_large]
- ac2: content at the wrapper's cap (1 MiB of UTF-8) is still forwarded [evidence: test:tests/test_api_file_write.py::test_write_at_cap_forwarded]
- ac3: openapi.json matches the generated document and the README API check passes [evidence: test:tests/test_readme_api.py]
- ac4: the targeted suites and lint pass [evidence: command:unset VIRTUAL_ENV && uv run --frozen pytest tests/test_api_file_write.py tests/test_readme_api.py && mise run lint]

## Files

- `src/agents_orchestrator/api/schemas.py`
- `src/agents_orchestrator/api/workspace.py`
- `tests/test_api_file_write.py`
- `openapi.json`
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

- 2026-10-27 done
