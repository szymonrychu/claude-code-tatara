---
title: mxc command outcome
status: todo
repo: agents-matrix-connector
value: "a Messenger slash message finishes by the command's outcome, with the usual notice on failure, instead of timing out"
files: [pyproject.toml, uv.lock, src/agents_matrix_connector/tracker.py, README.md, MEMORY.md, tests/test_tracker.py]
verify: "uv run --frozen pytest tests/test_tracker.py tests/test_readme_api.py && mise run lint"
depends_on: [common-release-0-4-0]
model: opus
review: ""
verified_head: ""
points: 3
expected_minutes: 8
expected_tokens: 996161
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# mxc command outcome

## Requirement

User decision F2 (2026-10-29), verbatim: "Check agents-matrix-connector (code/agents-matrix-connector): if it tracks message completion by turn (its own tracker or agents-common's), add the task that makes it handle command outcomes too (user said full scope)."

Check result (2026-10-29): it does. `src/agents_matrix_connector/tracker.py` `_outcome` polls the run's orchestrator message through agents-common's client and decides only by `message.turn` and `message.status`, so a Messenger message "/compact" (stored by the orchestrator as a command message, which stays `sent` with no turn) ends `timeout` with the "Sorry, the agent could not answer that message." notice. Architect brief, verbatim: "Noted, not doing now: agents-matrix-connector has the same gap in its own tracker, and a Messenger contact can now send `/compact`." The user's decision above puts the tracker gap in scope.

Architect's mapping (design D20), verbatim:

| Command outcome | Run result |
|---|---|
| completed: ok, dismissed, skipped_cache | handled |
| failed (e.g. unknown_command, dialog_stuck, timeout) | failed, reason `command_<error>` |
| cancelled | failed, reason `command_cancelled` |
| completed with result `turn` | decided by the existing turn checks |

Design D20, verbatim: "agents-matrix-connector has its own tracker that decides by the turn (`tracker.py:_outcome`), so a Messenger "/compact" times out today: it applies the same mapping, a failed or cancelled command posts the usual notice, and a completed command finishes `handled` with reason `command` and posts nothing (my call, Open questions Q4)."

Needs the agents-common v0.4.0 tag on origin (common-release-0-4-0 ac3, pushed by the orchestrator session after mx-34's confirmation).

Scope (agents-matrix-connector, branch from origin `main`): `pyproject.toml` (agents-common v0.3.0 to v0.4.0, both the dependency and the testing extra), `uv.lock`, `src/agents_matrix_connector/tracker.py` (`_outcome` applies the mapping before the timeout check; a failed outcome with no error reads `command_failed`), `tests/test_tracker.py`, README.md (the reasons list gains `command`, `command_<error>` and `command_cancelled`), MEMORY.md (the ruling and why).

## Acceptance conditions

- ac1: the connector pins agents-common v0.4.0 in both pinning lines and uv.lock, and Message carries command [evidence: command:test "$(grep -c 'agents-common@v0.4.0' pyproject.toml)" = 2 && ! grep -q 'agents-common@v0.3.0' pyproject.toml && grep -q 'agents-common?rev=v0.4.0#' uv.lock && ! grep -q 'rev=v0.3.0' uv.lock && uv run --frozen python -c "from agents_common.orchestrator import Message; assert 'command' in Message.model_fields"]
- ac2: (Docker) a run whose message completed as a command with result ok, dismissed or skipped_cache finishes handled with reason command, settles its inbound rows and stores no outbound row (new) [evidence: test:tests/test_tracker.py::test_command_completed_handled_without_reply]
- ac3: (Docker) a failed command (unknown_command) finishes failed with reason command_unknown_command and posts the notice; a cancelled one finishes failed with reason command_cancelled and posts the notice (new) [evidence: test:tests/test_tracker.py::test_command_failed_or_cancelled_posts_notice]
- ac4: (Docker) a command completed with result turn is decided by the turn: still running keeps the run open, a completed turn posts its final text (new) [evidence: test:tests/test_tracker.py::test_promoted_command_relays_turn]
- ac5: (Docker) the turn and timeout outcomes are unchanged [evidence: test:tests/test_tracker.py::test_failure_and_timeout_notice]
- ac6: README's reasons list and MEMORY.md name the command outcomes [evidence: command:grep -q "command_cancelled" README.md && grep -q "command_cancelled" MEMORY.md]
- ac7: the named tests and lint pass [evidence: command:uv run --frozen pytest tests/test_tracker.py tests/test_readme_api.py && mise run lint]

## Files

- `pyproject.toml`
- `uv.lock`
- `src/agents_matrix_connector/tracker.py`
- `README.md`
- `MEMORY.md`
- `tests/test_tracker.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
