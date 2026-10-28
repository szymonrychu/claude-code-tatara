---
title: orch-sessions-save-unconverged
status: done
repo: agents-orchestrator
value: discarding a never-started session is instant and the README states the non-fatal onStart
files: [src/agents_orchestrator/cache/save_rule.py, tests/test_cache_save.py, README.md]
verify: uv run pytest tests/test_cache_save.py -q
depends_on: [orch-sessions-backup-save]
model: sonnet
review: ""
verified_head: bd1024124be889099be4208a4b883572973a493a
points: 3
expected_minutes: 6
expected_tokens: 950968
points_actual: 3
actual_minutes: 10
actual_tokens: 1555464
actual_roles: "impl 4, review 7"
actual_role_tokens: "impl 1161216, review 394248"
---

# orch-sessions-save-unconverged

## Requirement

Discarding a session that was discarded before its first converge (no sessions restore record, no PVC or no pod ever wrote /sessions) must not start a sessions save Job. Today `cache/save_rule.py` (`_pods_wrote_sessions`, about line 31) treats a missing restore record as "the session predates the restore", so the reconciler renders a sessions save Job against a PVC that does not exist and the discard waits up to the Job timeout (about 30 minutes) (epic review finding, .scratchpad/session-loss/review/orchestrator.md "Consider" save_rule.py:31). Distinguish "predates the sessions restore feature" from "never converged": skip the sessions save with a recorded skip reason when the session never converged (no PVC / never had a pod), keep saving for sessions that predate the feature and did run pods. Read how the reconciler records converge and PVC creation before choosing the signal; ask instead of guessing if no reliable signal exists. Also fix README.md (about line 119): it still says "A failed install fails the onStart hook, which blocks the session"; since orch-onstart-nonfatal the install failure is logged, onStart exits 0 and the hook is on_error allow, so the sentence must describe that. Test first.

## Acceptance conditions

- AC1: a session discarded before its first converge gets no sessions save Job and its cache status records the skip reason [evidence: test:tests/test_cache_save.py::test_sessions_save_skipped_when_never_converged]
- AC2: a session that predates the sessions restore and ran pods still gets a sessions save [evidence: test:tests/test_cache_save.py::test_sessions_save_runs_for_session_predating_restore]
- AC3: README no longer says a failed install blocks the session [evidence: command:! grep -q "which blocks the session" README.md]

## Files

- `src/agents_orchestrator/cache/save_rule.py`
- `tests/test_cache_save.py`
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

- 2026-10-28 done
