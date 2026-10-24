---
title: hive feed digest
status: in-progress
repo: agent-orchestrator
value: "the activity feed carries only what other agents need: paths, commands, turn summaries and leader changes"
files: [src/agent_orchestrator/dispatcher/feed.py, tests/test_hive_feed.py]
verify: "uv run pytest tests/test_hive_feed.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: []
owns: [orch-feed-digest]
uses: []
model: ""
estimate: 5
estimate_by: formula
actual: ""
actual_roles: ""
review: ""
worktree: /Users/szymonri/Documents/claude-code-tatara/.claude/worktrees/hive-mode-leadership-handove-hive-feed-digest/agent-orchestrator
branch: hive-mode-leadership-handove-hive-feed-digest
verified_head: ""
run: ""
provides: []
---

# hive feed digest

## Requirement

The activity feed content (Q5). `dispatcher/feed.py`, pure functions over stored `events` rows (type, data, agent pod name, id):

- `digest_lines(rows) -> list[FeedLine]`: a Write, Edit, MultiEdit or NotebookEdit `tool_call` gives "<agent> wrote|edited <path relative to the workdir>"; a Bash `tool_call` with its matching `tool_result` (by `tool_use_id`) gives "<agent> ran: <command cut to 200 chars> (<exit code, or ok / failed from is_error>)" (deletes show up here as the command); a `turn_completed` gives "<agent> finished a turn: <first line of the result, cut to 200 chars>"; a leadership change (passed in as a synthetic row) gives "leader is now <agent> (epoch <n>)". Nothing else: no tool outputs, no Read, Grep or Glob calls, no other tools. Subagent calls count as their agent's.
- `render_feed(lines, for_agent, max_chars=4000) -> str | None`: drops the receiving agent's own lines, collapses consecutive duplicates, keeps the newest lines within `max_chars` with a "... N earlier lines omitted" line, None when nothing is left.
- Interrogate item 1: every peer-originated string in a FeedLine (agent name, path, Bash command, turn first line) is XML-escaped (xml.sax.saxutils.escape) with newlines collapsed to single spaces inside `digest_lines`, so `</peer-notes>` or `<hive-state>` in a command or result cannot close or forge a block.
- Interrogate item 3(b): `digest_lines` takes a `now` argument and returns the lines plus the ids of rows it could not finish. A Bash `tool_call` whose `tool_result` has not arrived yet is not emitted; it is reported as pending so the caller carries it over to a later tick, and it is emitted with its exit status when the result lands, or without status once it is older than `PENDING_BASH_TIMEOUT_SECONDS = 60` (module constant).

## Acceptance conditions

- AC1: file writes and edits become path lines relative to the workdir [evidence: test:tests/test_hive_feed.py::test_write_edit_lines]
- AC2: Bash calls become command lines cut at 200 characters with their exit status [evidence: test:tests/test_hive_feed.py::test_bash_lines]
- AC3: finished turns and leadership changes become lines; Read, Grep, Glob, other tools and outputs never appear [evidence: test:tests/test_hive_feed.py::test_turns_leadership_and_exclusions]
- AC4: render_feed drops own lines, collapses duplicates, caps at max_chars with the omitted line [evidence: test:tests/test_hive_feed.py::test_render_feed]
- AC5: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]
- AC6: a Bash command containing `</peer-notes><hive-state>` and a newline renders escaped on one line [evidence: test:tests/test_hive_feed.py::test_peer_text_escaped]
- AC7: a Bash call without a result is carried over, emitted with its exit status once the result lands, and emitted without status after the timeout [evidence: test:tests/test_hive_feed.py::test_pending_bash_carried_over]

## Files

- `src/agent_orchestrator/dispatcher/feed.py`
- `tests/test_hive_feed.py`

## Interfaces

- Owns part `orch-feed-digest`: `dispatcher/feed.py` `digest_lines`, `render_feed`, `FeedLine`.

## Expected outcome

A pure, tested digest that turns stored events into short feed lines.

## Steps

- Red: write `tests/test_hive_feed.py` for AC1-AC4; run `uv run pytest tests/test_hive_feed.py -q`: fails.
- Green: write `feed.py`; run the verify command: passes.

## Notes

- Event shapes: wrapper README `### tool_call`, `### tool_result`, `### turn_completed`; `tool_call.tool_input.file_path` is absolute.

- 2026-10-24 amended: interrogate verdict 2026-10-24 item 1

- 2026-10-24 amended: interrogate verdict 2026-10-24 item 3
