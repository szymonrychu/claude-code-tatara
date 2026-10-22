---
title: Context in snapshot and SSE
status: in-progress
repo: claude-code-wrapper
value: Orchestrator draws the 0-100 percent context gauge from the wrapper
files: [src/claude_code_wrapper/manager.py, src/claude_code_wrapper/router.py, src/claude_code_wrapper/events.py, README.md, tests/test_context_surface.py]
verify: "uv run pytest tests/test_context_surface.py tests/test_readme_api.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [statusline-relay]
owns: [wrapper-context-surface]
uses: [wrapper-statusline-callback]
model: ""
estimate: 6
estimate_by: formula
actual: ""
actual_roles: ""
review: ""
worktree: /Users/szymonri/Documents/claude-code-tatara/.claude/worktrees/claude-code-wrapper-orchestr-context-in-snapshot-and-sse/claude-code-wrapper
branch: claude-code-wrapper-orchestr-context-in-snapshot-and-sse
verified_head: ""
run: ""
provides: []
---

# Context in snapshot and SSE

## Requirement

Expose context usage. The snapshot gains `context: {used_tokens, window_tokens, used_percentage, model, source: "statusline", updated_at} | null`, filled from the values the statusline relay delivers to the router (`on_statusline`). A new SSE/history event `context` carries the same fields and is emitted only when the values change (dedupe on used_tokens, window_tokens and used_percentage). The context is null until the first assistant message, and is reset to null (and a null-context event emitted if it was non-null) after `compacted`, as the statusline docs describe. The denominator is the full model window reported by the statusline; the wrapper holds no model-window table. `context` is added to EVENT_TYPES and documented in README.md (snapshot table and event table).
Field derivation from the statusline stdin JSON (statusline doc, "Available data", context_window fields: `current_usage{input_tokens, output_tokens, cache_creation_input_tokens, cache_read_input_tokens}`, `context_window_size`, `used_percentage`, `model.{id,display_name}`): `used_tokens` = `input_tokens + cache_creation_input_tokens + cache_read_input_tokens` of `current_usage` (output tokens excluded, matching the doc's definition of used_percentage); `window_tokens` = `context_window_size`; `model` = the statusline `model.id`; `used_percentage` = the statusline value, and when it is null but `window_tokens` and `used_tokens` are both known it is computed as `used_tokens / window_tokens * 100` (clamped to 0-100); otherwise null. When `current_usage` is null (before the first call and after /compact) the whole context is null. `context` and its events ride the normal ring and rotation (my call).

## Acceptance conditions

- AC1: snapshot context is null before any statusline update [evidence: test:tests/test_context_surface.py::test_snapshot_context_null_initially]
- AC2: a statusline update fills the snapshot and emits one context event [evidence: test:tests/test_context_surface.py::test_update_fills_snapshot_and_emits_event]
- AC3: an identical update emits no second event [evidence: test:tests/test_context_surface.py::test_identical_update_is_deduped]
- AC4: compacted resets context to null [evidence: test:tests/test_context_surface.py::test_compact_resets_context]
- AC5: README documents the context snapshot field and event [evidence: test:tests/test_readme_api.py::test_every_event_type_documented]
- AC6: used_tokens is the sum of input, cache_creation and cache_read tokens and model is model.id [evidence: test:tests/test_context_surface.py::test_used_tokens_sum_and_model_id]
- AC7: a null used_percentage with known window and tokens is computed; unknown inputs give null [evidence: test:tests/test_context_surface.py::test_used_percentage_computed_when_null]

## Files

- `src/claude_code_wrapper/manager.py`
- `src/claude_code_wrapper/router.py`
- `src/claude_code_wrapper/events.py`
- `README.md`
- `tests/test_context_surface.py`

## Interfaces

manager.py snapshot gains context {used_tokens, window_tokens, used_percentage, model, source, updated_at} | null; events.py gains context. Contracts wrapper-context-surface (owns), wrapper-statusline-callback (uses).

## Expected outcome

Snapshot context is null, then filled after a statusline update, with one context event per distinct change, and null again after compaction.

## Steps

- Write tests/test_context_surface.py driving router.on_statusline; run it and see it fail.
- Store the latest context in the router, expose it in manager.py snapshot, add the context event type with dedupe, reset on compacted; update README.md.
- Run `uv run pytest tests/test_context_surface.py tests/test_readme_api.py -q && uv run ruff check . && uv run ruff format --check .`.

## Notes

router.py already keeps _last_context for auto-compact (router.py:257, 858); do not conflate it with the statusline values. Compaction emit is router.py:887.
Statusline field semantics are from the Claude Code statusline doc (brief-docs.md section 5, item 1): used_percentage = (input + cache_creation + cache_read) / context_window_size, output excluded; current_usage and the percentages are null early in the session and current_usage after /compact.
