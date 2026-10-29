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

- `config.py`: `sessions.merge.settle_seconds: float = 15.0` (`ge=0`).
- Event `turn_deferred` gains reason `merge_pending` and a `merge_ids: list[str]` field (other reasons unchanged).
- `_stop_gate` order: onStop block -> hook or background defer -> `merge_pending` -> slash command hold -> complete.
- Turn record: merges never seen keep `absorbed_at: null` after completion or interrupt; nothing else in the record changes shape.

## Expected outcome

A turn that absorbed messages still completes exactly once: on the Stop that follows the last merged prompt, or at the latest `merge.settle_seconds` after a Stop when a paste was never taken. An interrupt keeps its contract and never leaves the session busy.

## Steps

- Read `router.py` (`_on_stop`, `_stop_gate`, `_emit_deferred`, `_after_turn`), `session.py` (`stop_target`, `complete`, `_end_turn`, `interrupt`, `_run_interrupt`, `on_interrupted`, `_watch_turn`), `config.py`, `tests/test_stop_gate.py`, `tests/test_command_turn_resume.py`, `tests/test_turn_merge.py`, the fake's queue mode and `docs/claude-midturn-input.md` (P2, P5) in one pass.
- Red: write `tests/test_turn_merge_stop.py` with every test named in the acceptance conditions; run `uv run pytest tests/test_turn_merge_stop.py`; expect them to fail.
- Green: implement the merge-pending leg, the bounded wait, the completion from the stored payload, the interrupt rule, README and MEMORY; run the task's verify; expect all passed. Quote the summary line.

## Notes

- Depends on probe P2 (one Stop or two at a turn end with queued input) and P5 (Esc with queued input). If the consequences table contradicts D6 or D7, the orchestrator amends this task before it starts.
- The deferred Stop's payload and usage must be kept so the bound can complete the turn honestly; the usage accumulator keeps counting if the merged prompt runs.
- `turn_max_seconds` and `turn_stall_seconds` keep their meaning; the settle timer is separate and cancelled with the turn.
- Before working read the repo's AGENTS.md, MEMORY.md and ROADMAP.md. No em dashes. No backward-compatibility shims. If a verify run fails, save the failing test name and the output tail before any rerun.

- 2026-10-29 amended: planner filled Interfaces, Expected outcome, Steps and Notes before the gate (retro: no empty Steps)
