---
title: wrapper merge stop gate
status: todo
repo: claude-code-wrapper
value: "a turn that absorbed messages always ends once, so a mid-turn message can never wedge the agent"
files: [src/claude_code_wrapper/router.py, src/claude_code_wrapper/session.py, src/claude_code_wrapper/config.py, README.md, MEMORY.md, tests/test_turn_merge_stop.py]
verify: "uv run pytest tests/test_turn_merge_stop.py tests/test_turn_merge.py tests/test_stop_gate.py tests/test_command_turn_resume.py tests/test_session_turns.py tests/test_shutdown_turn_resume.py tests/test_readme_config.py && uv run ruff check . && uv run ruff format --check ."
depends_on: [wrapper-immediate-turn-merge]
model: opus
review: ""
verified_head: ""
points: 5
expected_minutes: 10
expected_tokens: 1875101
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# wrapper merge stop gate

## Requirement

Goal G3 (README), verbatim: "a message delivered mid-turn never wedges the session: the running turn still ends on its Stop, and the message is linked to the turn that answered it (hop guard and delivery verifier included)."

Design D6, verbatim: "At a Stop that targets the running turn, after the onStop gate allowed it, when the turn holds a merge with no `absorbed_at`: the relay answers allow, the turn stays running and busy (`turn_deferred` with reason `merge_pending` and the pending `merge_ids`), and the wrapper waits up to `sessions.merge.settle_seconds` (default 15, my call) for the merge markers. Claude Code sends input still queued at the turn's end without another key press (docs A2), so the queued prompt starts and its own Stop (same turn marker) completes the turn normally. If the bound expires first, the wrapper completes the turn from the deferred Stop's payload (`last_assistant_message`, usage) and leaves the unseen merges with `absorbed_at: null`. Order inside `_stop_gate`: onStop block wins, then the hook or background defer, then `merge_pending`, then the slash epic's command hold; queued commands stay queued until the turn really completes. A Stop with every merge confirmed completes as today."

Design D7, verbatim: "`POST /interrupt` ends the running turn `interrupted` as today, its merged messages with it; the merges never seen stay `absorbed_at: null` and the wrapper never resends them. Claude Code sends queued input right after Esc (docs B1); if it does so, the run that follows surfaces through the existing ready-state Stop path (`stop_target` while ready makes an `origin="agent"` record), so the session cannot wedge. The second ESC stays conditional on a missing interrupt line, so it does not hit the auto-sent prompt or open the rewind menu (docs B3)."

Design anti-goal, verbatim: "A Stop that never completes the running turn because a merged paste was never seen: the defer is bounded (D6)."

Design Non-goals, verbatim: "No change to `limits.turn_max_seconds`: it keeps counting from the first submit (wrapper MEMORY 2026-10-28), so merged messages do not extend a bounded turn."

Scope (claude-code-wrapper): `router.py` (`_stop_gate` merge-pending leg and order, the settle timer, completion from the stored Stop payload), `session.py` (interrupt with merges, timer cancellation when the turn ends), `config.py` (`sessions.merge.settle_seconds`), `README.md` (turn lifecycle with merges, interrupt), `MEMORY.md` (dated entry on the merge model: marker rule, bounded defer, interrupt), `tests/test_turn_merge_stop.py` (new).

## Acceptance conditions

- ac1: a Stop for the running turn while a merge has no absorbed_at answers allow, keeps the turn running and the session busy, and emits turn_deferred with reason merge_pending and the pending merge_ids (new) [evidence: test:tests/test_turn_merge_stop.py::test_stop_with_unconfirmed_merge_defers]
- ac2: when the merged prompt then shows in the transcript and its Stop arrives, the same turn completes once, with final_text from that later Stop (new) [evidence: test:tests/test_turn_merge_stop.py::test_deferred_turn_completes_on_the_merged_prompt_stop]
- ac3: when merge.settle_seconds passes with the merge unseen, the turn completes once from the deferred Stop's last_assistant_message and usage, the merge keeps absorbed_at null and the session is ready (new) [evidence: test:tests/test_turn_merge_stop.py::test_settle_bound_completes_the_turn]
- ac4: the settle wait ends without a second completion when the turn ends another way first (interrupt, turn_max_seconds timeout, claude exit) (new) [evidence: test:tests/test_turn_merge_stop.py::test_settle_wait_ends_when_turn_ends_otherwise]
- ac5: gate order: an onStop block wins over merge_pending; with client commands queued and a merge pending, the commands stay queued until the turn completes and then run (slash D9) (new) [evidence: test:tests/test_turn_merge_stop.py::test_gate_order_block_then_merge_then_commands]
- ac6: an interrupt of a turn with merges ends it interrupted, unseen merges keep absorbed_at null, nothing is resent, a later Stop of a prompt Claude sent after the Esc makes an origin agent record, and the next POST /turns answers 202 (new) [evidence: test:tests/test_turn_merge_stop.py::test_interrupt_with_merges_never_wedges]
- ac7: with queued input at the interrupt the second ESC is sent only when no interrupt line arrived within interrupt_settle_seconds (new) [evidence: test:tests/test_turn_merge_stop.py::test_second_esc_only_without_interrupt_line]
- ac8: with the fake in queue mode, a message pasted near the end of a text-only turn ends up in exactly one completed turn whose record lists the merge as absorbed (new) [evidence: test:tests/test_turn_merge_stop.py::test_turn_end_queue_end_to_end]
- ac9: turn_max_seconds still counts from the first submit with merges in the turn (new) [evidence: test:tests/test_turn_merge_stop.py::test_turn_max_seconds_counts_from_first_submit_with_merges]
- ac10: README documents the merge lifecycle and sessions.merge.settle_seconds; MEMORY.md has the dated merge entry [evidence: command:grep -q 'settle_seconds' README.md && grep -q 'merge_pending' README.md && grep -q 'ccw merge' MEMORY.md && uv run pytest tests/test_readme_config.py]
- ac11: targeted suites and lint pass [evidence: command:uv run pytest tests/test_turn_merge_stop.py tests/test_turn_merge.py tests/test_stop_gate.py tests/test_command_turn_resume.py tests/test_session_turns.py tests/test_shutdown_turn_resume.py tests/test_readme_config.py && uv run ruff check . && uv run ruff format --check .]

## Files

- `src/claude_code_wrapper/router.py`
- `src/claude_code_wrapper/session.py`
- `src/claude_code_wrapper/config.py`
- `README.md`
- `MEMORY.md`
- `tests/test_turn_merge_stop.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
