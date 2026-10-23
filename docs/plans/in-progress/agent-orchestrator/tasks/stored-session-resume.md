---
title: stored session resume
status: done
repo: agent-orchestrator
value: an agent whose session died while its pod lives recovers by itself
files: [src/agent_orchestrator/reconciler/sessions.py, tests/test_session_bootstrap.py]
verify: "uv run pytest tests/test_session_bootstrap.py -q && mise run lint"
depends_on: [session-bootstrap]
owns: []
uses: []
model: ""
estimate: 5
estimate_by: formula
actual: ""
actual_roles: ""
review: ""
worktree: /Users/szymonri/Documents/claude-code-tatara/.claude/worktrees/agent-orchestrator-stored-session-resume/agent-orchestrator
branch: agent-orchestrator-stored-session-resume
verified_head: 45da3af02ca2b94212f67d79ecfc11de0689f8cb
run: agent-orchestrator
provides: []
acs_for_audit: []
process_gaps: []
---

# stored session resume

## Requirement

Panel finding (high, fable+opus): reconciler/sessions.py:89-91 keeps a stored session whenever the wrapper still lists it, regardless of state; the wrapper lists every persisted session, so a session that went stopped/failed while the pod lives is never resumed, the ingester marks it dead, _PICK never dispatches to it, and the cluster queue stalls. Fix: look up the stored session's snapshot; keep it only when state in ADOPTABLE; when stopped/failed with a transcript call client.resume_session and set_session; otherwise clear_session and fall through to _pick/create.

## Acceptance conditions

- AC1: a stored session that is stopped with a transcript is resumed on reconcile [evidence: test:tests/test_session_bootstrap.py::test_stored_stopped_session_is_resumed]
- AC2: a stored failed session without a transcript is replaced by a new session [evidence: test:tests/test_session_bootstrap.py::test_stored_failed_session_without_transcript_replaced]
- AC3: a stored live session is kept [evidence: test:tests/test_session_bootstrap.py::test_stored_live_session_kept]

## Files

- `src/agent_orchestrator/reconciler/sessions.py`
- `tests/test_session_bootstrap.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

The requirement holds, pinned by the acceptance tests.

What is true and observable when the task is done.

## Steps

- Write the failing acceptance tests; run red.
- Implement; run green with the verify command.

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
