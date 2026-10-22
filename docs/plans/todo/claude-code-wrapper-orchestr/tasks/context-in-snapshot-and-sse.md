---
title: Context in snapshot and SSE
status: todo
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
worktree: ""
branch: ""
verified_head: ""
run: ""
provides: []
---

# Context in snapshot and SSE

## Requirement

Expose context usage. The snapshot gains `context: {used_tokens, window_tokens, used_percentage, model, source: "statusline", updated_at} | null`, filled from the values the statusline relay delivers to the router (`on_statusline`). A new SSE/history event `context` carries the same fields and is emitted only when the values change (dedupe on used_tokens, window_tokens and used_percentage). The context is null until the first assistant message, and is reset to null (and a null-context event emitted if it was non-null) after `compacted`, as the statusline docs describe. The denominator is the full model window reported by the statusline; the wrapper holds no model-window table. `context` is added to EVENT_TYPES and documented in README.md (snapshot table and event table).

## Acceptance conditions

- AC1: snapshot context is null before any statusline update [evidence: test:tests/test_context_surface.py::test_snapshot_context_null_initially]
- AC2: a statusline update fills the snapshot and emits one context event [evidence: test:tests/test_context_surface.py::test_update_fills_snapshot_and_emits_event]
- AC3: an identical update emits no second event [evidence: test:tests/test_context_surface.py::test_identical_update_is_deduped]
- AC4: compacted resets context to null [evidence: test:tests/test_context_surface.py::test_compact_resets_context]
- AC5: README documents the context snapshot field and event [evidence: test:tests/test_readme_api.py::test_every_event_type_documented]

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
