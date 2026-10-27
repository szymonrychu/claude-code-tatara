---
title: orch e2e hive activity
status: todo
repo: agents-orchestrator
value: the kind e2e proves members pull activity and get no feed note
files: [tests/e2e/test_e2e_kind.py]
verify: "uv run --frozen python -m py_compile tests/e2e/test_e2e_kind.py && mise run lint"
depends_on: [orch-hive-tools-activity]
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

# orch e2e hive activity

## Requirement

README Goals G1 and G2, verbatim: "Members receive no streamed activity: the dispatcher sends no appended feed note, `hive_state` is re-pushed only when the leader, epoch, membership or readiness changes, and `session_leaders.feed_cursor` is dropped." "Any hive agent pulls recent activity on demand: `GET /agent/v1/activity` (optional `agent`, `limit` 1..200) and the plugin tool `orchestrator_activity`."

Design D10, verbatim: "The kind e2e replaces the feed assertion of `test_hive_notes_delivered` with the activity route and "no appended orchestrator note" and adds `activity` to `HIVE_ONLY_TOOLS`. D4 is not in the kind e2e (my call): the fake claude emits no statusline, so no `context_pct` exists there; D4 is proven by DB tests and the live proof (D11)."

Fix-as-ac (brief), verbatim: "`tests/e2e/test_e2e_kind.py` feed assertions (not read in this discovery; the builder lists them in the task) are replaced by an `activity` route assertion." Listed (F3): `test_hive_notes_delivered` (`feed_on_reader`) and the `HIVE_PUSH_TIMEOUT` comment (line 78, "feed rows settle for 5 s").

Scope (agents-orchestrator, `tests/e2e/test_e2e_kind.py` only):
- `test_hive_notes_delivered` is no longer accurate (named: it waits for a feed note on the reader): after the writer's turn writing `NOTE_FILE`, the reader's `GET /agent/v1/activity` (through the existing `agent_call` helper) lists a line naming `NOTE_FILE` by the writer; both agents still have a keyed `hive_state` note; no `note_received` event with a null key reaches either agent.
- `HIVE_ONLY_TOOLS` gains `activity` (the alone session must not render it).
- `HIVE_PUSH_TIMEOUT` comment no longer mentions the feed settle.
- The leader-auto-handover e2e tests (`test_leader_compaction_hands_over`, `test_scale_down_below_leader_hands_over`) stay unchanged and green.

## Acceptance conditions

- ac1: in kind, the reader pulls the writer's file write through GET /agent/v1/activity, both agents hold a keyed hive_state note and no unkeyed note arrives (rewritten, named) [evidence: test:tests/e2e/test_e2e_kind.py::test_hive_notes_delivered]
- ac2: an alone session renders none of the hive-only tools, activity included [evidence: test:tests/e2e/test_e2e_kind.py::test_alone_session_has_no_hive_tools]
- ac3: the e2e file has no feed wording left [evidence: command:! grep -nE 'feed_on_reader|feed note|feed rows' tests/e2e/test_e2e_kind.py && grep -q '"activity"' tests/e2e/test_e2e_kind.py]
- ac4: the kind e2e CI job is green on the PR head, leader-auto-handover e2e cases included [evidence: judgement:reviewer quotes the e2e job conclusion of the PR head commit]
- ac5: the file compiles and lint passes [evidence: command:uv run --frozen python -m py_compile tests/e2e/test_e2e_kind.py && mise run lint]

## Files

- `tests/e2e/test_e2e_kind.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
