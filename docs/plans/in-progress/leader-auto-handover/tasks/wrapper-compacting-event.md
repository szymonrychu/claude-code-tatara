---
title: wrapper compacting event
status: done
repo: claude-code-wrapper
value: the orchestrator learns a leader is about to compact before the compaction runs
files: [src/claude_code_wrapper/router.py, src/claude_code_wrapper/events.py, README.md, tests/test_command_signals.py, tests/test_event_log.py]
verify: "uv run pytest -q tests/test_command_signals.py tests/test_event_log.py tests/test_readme_api.py && uv run ruff check . && uv run ruff format --check ."
depends_on: []
model: sonnet
review: ""
verified_head: ef64fb0fbe913ca9f0a6a5ea2680ae242f04b485
points: 2
expected_minutes: 6
expected_tokens: 546295
points_actual: 2
actual_minutes: 26
actual_tokens: 881354
actual_roles: "impl 25, review 1"
actual_role_tokens: "impl 816850, review 64504"
---

# wrapper compacting event

## Requirement

Goal G1 (user, 2026-10-26): "when the leader of a hive is about to compact (auto or manual), the wrapper reports it before the compaction runs". User decision: "hand over just before compaction. This needs a new pre-compaction event from the wrapper, from Claude Code's PreCompact hook, and so a claude-code-wrapper release."

Design D1, verbatim: the PreCompact relay handler (`router.py` `_on_compact_hook`) emits the event `compacting` with `{trigger}` (`manual`, `auto`, else `unknown`, the same vocabulary as `compacted`) to the event log before it returns allow, and keeps publishing the `pre_compact` signal. Claude Code waits for the hook, so the event is in the log before the compaction runs. `EVENT_TYPES` gains `compacting` just before `compacted`; README documents it. The handler still answers at once (no hold). `custom_instructions` is left out of the event.

Scope:
- `src/claude_code_wrapper/events.py`: add `"compacting"` to `EVENT_TYPES` immediately before `"compacted"`.
- `src/claude_code_wrapper/router.py` `_on_compact_hook`: for `PreCompact`, emit `compacting` through `self._emit` with `{"trigger": <normalised trigger>}` before returning `_allow()`; the `pre_compact` signal is still published with its current data. `PostCompact` is unchanged (no event).
- README: a `### compacting` section next to `### compacted` (when it is emitted: once per PreCompact hook call, before the compaction runs, for manual and auto compactions; `data`: `trigger`), and the `### compacted` text stays.
- Tests in `tests/test_command_signals.py`: the PreCompact relay emits exactly one `compacting` event whose data is `{"trigger": ...}`, it is in the log by the time `handle_claude_hook` returns, an unknown or missing trigger reads `unknown`, the relay response is still the immediate allow, and `PostCompact` emits no `compacting`.
- Test no longer accurate, to update: `tests/test_event_log.py::test_event_types_exact` pins the exact `EVENT_TYPES` list, which now gains `compacting` before `compacted`. Existing assertions in `tests/test_command_signals.py` (for example `h.events("compacted") == []` after the relays) stay as they are.

Notes: the fake claude's `auto_compact` step already runs the PreCompact hook (`tests/fake_claude/fake_claude.py:709-712`), so a scripted native compaction produces `compacting` end to end. `tests/test_readme_api.py::test_every_event_type_documented` fails until README has the section. Do not change the hook relay timeouts or make the handler wait on anything.

## Acceptance conditions

- AC1: a PreCompact relay emits exactly one `compacting` event with data `{"trigger": "auto"}` (or `manual`) before `handle_claude_hook` returns, and still answers allow at once [evidence: test:tests/test_command_signals.py::test_pre_compact_emits_compacting]
- AC2: a PreCompact payload with a missing or unknown trigger emits `compacting` with trigger `unknown`, and PostCompact emits no `compacting` [evidence: test:tests/test_command_signals.py::test_compacting_trigger_normalised]
- AC3: `EVENT_TYPES` lists `compacting` immediately before `compacted` [evidence: test:tests/test_event_log.py::test_event_types_exact]
- AC4: README documents the `compacting` event [evidence: test:tests/test_readme_api.py::test_every_event_type_documented]
- AC5: the compaction signal tests still pass [evidence: command:uv run pytest -q tests/test_command_signals.py tests/test_fake_claude_commands.py]
- AC6: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

## Files

- `src/claude_code_wrapper/router.py`
- `src/claude_code_wrapper/events.py`
- `README.md`
- `tests/test_command_signals.py`
- `tests/test_event_log.py`

## Interfaces

See the Requirement and the acceptance conditions above.

## Expected outcome

See the Requirement and the acceptance conditions above.

## Steps

- Red: add `test_pre_compact_emits_compacting` and `test_compacting_trigger_normalised` to `tests/test_command_signals.py`, update `tests/test_event_log.py::test_event_types_exact` (gains `compacting` before `compacted`); run `uv run pytest -q tests/test_command_signals.py tests/test_event_log.py`: the new tests and the exact-list test fail (no such event).
- Green: add `compacting` to `EVENT_TYPES`, emit it in `_on_compact_hook` for PreCompact, add README `### compacting`; run the task's verify command: passes.

## Notes

See the Requirement and the acceptance conditions above.

- 2026-10-26 done
