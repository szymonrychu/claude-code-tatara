---
title: orch feed dead code and compact helper
status: done
repo: agents-orchestrator
value: "no dead feed code and one effective-compaction helper, as the design says"
files: [src/agents_orchestrator/dispatcher/feed.py, src/agents_orchestrator/api/agent.py, src/agents_orchestrator/dispatcher/hive.py, src/agents_orchestrator/k8s/on_start.py, src/agents_orchestrator/k8s/render.py, src/agents_orchestrator/db/views.py, tests/test_hive_feed.py]
verify: "uv run --frozen pytest -q tests/test_hive_feed.py && mise run lint"
depends_on: [orch-flaky-push-after-decisi]
model: sonnet
review: ""
verified_head: 35e8f2a4e1dd9ec19b7b1614a949d302be729d6f
points: 2
expected_minutes: 6
expected_tokens: 546295
points_actual: 2
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# orch feed dead code and compact helper

## Requirement

Scope audit gaps at close (scope-auditor, 2026-10-29), against design.md anti-goal verbatim: "Dead feed code or a dead column left behind \"for compatibility\"." and design D5 (line 106): "`max(coalesce(spec.auto_compact_pct, settings.default_auto_compact_pct) - HANDOVER_MARGIN_PCT, 1)`, one helper in" hive.py.
(1) Remove the unreachable `leadership` branch from `dispatcher/feed.py:digest_lines` (nothing in src produces a `leadership` row any more) and its docstring lines, and drop the unused `pending` return: `digest_lines` returns only the lines; update every caller (`api/agent.py` activity route, any other) and tests/test_hive_feed.py (retire the leadership-row tests; a retirement test pins the removal).
(2) Collapse the effective compaction point to the one helper `dispatcher/hive.py:compact_pct`, reused by `k8s/on_start.py`, `k8s/render.py` and `db/views.py`, keeping today's behaviour for each caller (note: hive.py uses `is None`, the others `or`; spec Field ge=1 makes 0 impossible, so both agree; keep it so). No behaviour change, no migration.

## Acceptance conditions

- ac1: no `leadership` row handling remains in feed.py and digest_lines returns only lines [evidence: test:tests/test_hive_feed.py::test_digest_lines_has_no_leadership_row_kind]
- ac2: one helper computes the effective compaction point: `grep -rn default_auto_compact_pct src` hits only settings, hive.py:compact_pct and call sites passing settings to it [evidence: judgement:reviewer runs the grep and reads each hit]
- ac3: orchestrator tests and lint pass in CI on the PR head (DB tests are CI-only) [evidence: command:gh pr checks]

## Files

- `src/agents_orchestrator/dispatcher/feed.py`
- `src/agents_orchestrator/api/agent.py`
- `src/agents_orchestrator/dispatcher/hive.py`
- `src/agents_orchestrator/k8s/on_start.py`
- `src/agents_orchestrator/k8s/render.py`
- `src/agents_orchestrator/db/views.py`
- `tests/test_hive_feed.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

- Branch `orch-feed-cleanup` from fresh origin/main (be554bb).
- Red: add test_digest_lines_has_no_leadership_row_kind (a `leadership` row yields no line, and digest_lines returns a list, not a tuple); retire the leadership-row tests; run the verify: red.
- Green: remove the branch, docstring lines and `pending` return; update callers. Reuse hive.compact_pct in on_start.py, render.py and views.py. Rerun the verify plus the unit tests of the touched callers (DB-free ones): green. Commit, push, open a PR to main; DB tests and e2e are CI-only, so wait for `gh pr checks` green with `gh pr checks --watch`.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.

- 2026-10-29 in-progress

- 2026-10-29 done: PR #38 review pass (CI test/lint/e2e/chart green), merged 2d6d722

- 2026-10-29 actuals: no agent records
