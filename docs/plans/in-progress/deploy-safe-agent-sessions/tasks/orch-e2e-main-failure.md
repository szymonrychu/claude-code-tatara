---
title: orch e2e main failure
status: in-progress
repo: agents-orchestrator
value: "the orchestrator main CI e2e is green, so gating publishes on it keeps main deployable"
files: [tests/e2e/test_e2e_kind.py, tests/e2e/conftest.py, scripts/e2e.sh, MEMORY.md]
verify: "uv run pytest -q -p no:cacheprovider -m e2e --collect-only tests/e2e/test_e2e_kind.py && uv run ruff check . && uv run ruff format --check ."
depends_on: []
model: sonnet
review: ""
verified_head: ""
points: 3
expected_minutes: 6
expected_tokens: 936557
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# orch e2e main failure

## Requirement

Design D10, user decision verbatim: "The orchestrator main CI e2e failed on run 40565058706 (commit 96e46f3) while the PR run 40562435463 passed: one task diagnoses it from the run log (gh run view --log-failed) and fixes the cause, so gating on e2e keeps main green."

Planner probe (read-only, 2026-10-27), verbatim from design D10: "the failed test is `tests/e2e/test_e2e_kind.py::test_in_session_pod_refused_by_allowlist`, `httpx.RemoteProtocolError: Server disconnected without sending a response.` on the port-forwarded `api` client, `1 failed, 39 passed`. The cause is the task's to confirm."

Scope (agents-orchestrator):
- Read `gh run view 40565058706 --repo szymonrychu/agents-orchestrator --log-failed` and compare with PR run 40562435463; name the cause (the line and the evidence) in MEMORY.md.
- Fix the cause in `tests/e2e/test_e2e_kind.py`, `tests/e2e/conftest.py` or `scripts/e2e.sh`. A retry that hides a product defect is not a fix: a cause in `src/` is returned as a discovered item (what, where, why) instead.
- The fixed test keeps its assertions (403 forbidden from an in-session pod, health exempt, loopback allowed).

Steps: read the log; reproduce or explain; fix; `uv run pytest -q -p no:cacheprovider -m e2e --collect-only tests/e2e/test_e2e_kind.py`; the PR CI e2e job (kind) passes.

Notes: no Docker or kind in agent pods: the PR CI e2e job is the evidence (about 16 min). This task runs before orch-ci-publish-gate so gating on e2e does not block a green main.

## Acceptance conditions

- AC1: MEMORY.md names the cause of the run 40565058706 e2e failure with its evidence [evidence: command:grep -q "40565058706" MEMORY.md]
- AC2: the e2e tests are collected [evidence: command:uv run pytest -q -p no:cacheprovider -m e2e --collect-only tests/e2e/test_e2e_kind.py]
- AC3: the kind e2e passes, test_in_session_pod_refused_by_allowlist included, with its assertions unchanged [evidence: command:mise run test:e2e]
- AC4: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

## Files

- `tests/e2e/test_e2e_kind.py`
- `tests/e2e/conftest.py`
- `scripts/e2e.sh`
- `MEMORY.md`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

- Red: write the tests the requirement and acceptance conditions name (or, for a release/deploy/CI step, the check the evidence names); run `"uv run pytest -q -p no:cacheprovider -m e2e --collect-only tests/e2e/test_e2e_kind.py && uv run ruff check . && uv run ruff format --check ."` and see them fail for the expected reason.
- Green: implement the requirement exactly as written; run `"uv run pytest -q -p no:cacheprovider -m e2e --collect-only tests/e2e/test_e2e_kind.py && uv run ruff check . && uv run ruff format --check ."` and expect every check to pass, quoting the summary line.
- Refactor with the verify still green; update MEMORY.md with a dated entry for any non-obvious decision.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
