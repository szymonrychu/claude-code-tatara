---
title: wrapper notes inbox
status: done
repo: claude-code-wrapper
value: the orchestrator can push hive state and activity notes to a hived agent
files: [src/claude_code_wrapper/config.py, src/claude_code_wrapper/notes.py, src/claude_code_wrapper/api/notes.py, src/claude_code_wrapper/api/app.py, src/claude_code_wrapper/events.py, src/claude_code_wrapper/manager.py, README.md, tests/test_notes_api.py]
verify: "uv run pytest tests/test_notes_api.py tests/test_readme_api.py tests/test_readme_config.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [main-agent-only-tools]
owns: [wrapper-notes-inbox]
uses: []
model: ""
estimate: 6
estimate_by: formula
actual: ""
actual_roles: ""
review: ""
worktree: /Users/szymonri/Documents/claude-code-tatara/.claude/worktrees/hive-mode-leadership-handove-wrapper-notes-inbox/claude-code-wrapper
branch: hive-mode-leadership-handove-wrapper-notes-inbox
verified_head: 2f62f2d130cda07a29fd8af3dc50f5d597ff07e7
run: hand-orchestrated-2026-10-25
provides: []
acs_for_audit: []
process_gaps: []
---

# wrapper notes inbox

## Requirement

Foundation part F2 (Q6, Q7: the notes inbox exists only for hived agents). A client-pushed notes inbox in claude-code-wrapper.

- Config section `notes`: `enabled: bool = false`, `max_notes: int = 50` (appended notes kept per session, oldest dropped first), `max_note_chars: int = 2000`, `delivery_max_chars: int = 8000` (below Claude Code's 10,000-character hook limit), `throttle_seconds: int = 30`, `throttle_tool_results: int = 10` (the last three are used by delivery, task wrapper-notes-delivery).
- `notes.py` `NoteStore`, in memory per session: a keyed note (`key` set) replaces the previous note with the same key and is pending until delivered; an appended note (no `key`) joins a FIFO capped at `max_notes`. Nothing survives a restart (the orchestrator re-pushes `hive_state`).
- Route `POST /v1/sessions/{id}/notes` with the same bearer auth as the other `/v1` routes; body `{text: str (1..max_note_chars), key?: str matching ^[a-z0-9_]{1,40}$, source?: str (<= 80 chars)}`; 202 `{key, pending}` (pending = notes awaiting delivery); 404 `not_found` for an unknown session; 409 `notes_disabled` when `notes.enabled` is false; validation errors in the README's existing error shape.
- Events: add `note_received` and `note_delivered` to `EVENT_TYPES`; this task emits `note_received {key, source, text, chars}` on every accepted note (text is bounded by max_note_chars).
- README: `## Notes` (purpose, keyed versus appended, caps, only for hived agents, notes are data from peers), the route under the API reference, H3s for both events under `## Events (SSE)` (enforced by `tests/test_readme_api.py`), and the config keys (enforced by `tests/test_readme_config.py`).

The store hangs off the session manager (`manager.py`) if that is the natural owner; the builder may touch it.
- Interrogate item 1: the inbox stores note text as pushed and exposes it for delivery unmodified; escaping happens at framing time in delivery (wrapper-notes-delivery), and the README `## Notes` states that note text is peer data that is escaped when delivered.

## Acceptance conditions

- AC1: a keyed note replaces the previous note with the same key [evidence: test:tests/test_notes_api.py::test_keyed_note_replaces]
- AC2: appended notes are capped at max_notes with the oldest dropped [evidence: test:tests/test_notes_api.py::test_appended_notes_capped]
- AC3: the route answers 409 notes_disabled when notes are off, 404 for an unknown session and 401 without the bearer token [evidence: test:tests/test_notes_api.py::test_route_errors]
- AC4: an accepted note emits note_received with key, source, text and chars [evidence: test:tests/test_notes_api.py::test_note_received_event]
- AC5: README documents the route, both events and the config keys [evidence: command:uv run pytest tests/test_readme_api.py tests/test_readme_config.py -q]
- AC6: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]
- AC7: README `## Notes` states that note text is escaped at delivery and the stored text is unmodified [evidence: test:tests/test_notes_api.py::test_stored_text_unmodified]

## Files

- `src/claude_code_wrapper/config.py`
- `src/claude_code_wrapper/notes.py`
- `src/claude_code_wrapper/api/notes.py`
- `src/claude_code_wrapper/api/app.py`
- `src/claude_code_wrapper/events.py`
- `src/claude_code_wrapper/manager.py`
- `README.md`
- `tests/test_notes_api.py`

## Interfaces

- Owns `POST /v1/sessions/{id}/notes`, config section `notes`, events `note_received` and `note_delivered` (part `wrapper-notes-inbox`, cross-epic contract of the same name).

## Expected outcome

The orchestrator can POST keyed and appended notes to a hived agent's session and sees `note_received` on its event stream.

## Steps

- Red: write `tests/test_notes_api.py` for AC1-AC4; run `uv run pytest tests/test_notes_api.py -q`: fails (route missing).
- Green: config section, `notes.py`, `api/notes.py`, router registration in `api/app.py`, `EVENT_TYPES`, README; run the verify command: passes.

## Notes

- `EVENT_TYPES` is a closed vocabulary (`events.py:20-57`); `append` rejects unknown types.
- `tests/test_readme_api.py:77-106` enforces route and event docs; `tests/test_readme_config.py` enforces config keys.
- Never write service files into a session workdir (wrapper CLAUDE.md): the store is in memory.

- 2026-10-24 amended: interrogate verdict 2026-10-24 item 1
