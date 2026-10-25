---
title: Agent usage hook
status: done
repo: workbench
value: Every subagent run leaves an accurate usage record in .logs without the orchestrator doing anything
files: [plugins/workbench/hooks/agent-usage-recorder.py, plugins/workbench/hooks/tests/test_agent_usage_recorder.py, plugins/workbench/hooks/tests/test_py39_safe.py, plugins/workbench/.claude-plugin/plugin.json, plugins/workbench/skills/start-development/references/hooks.md, scripts/tests/harness/test_claude_only_hooks.py]
verify: "bash plugins/workbench/scripts/run-tests.sh --only hooks && bash plugins/workbench/scripts/run-tests.sh --only start-development && mise run test:scripts && mise run lint"
depends_on: [agent-usage-lib]
model: opus
review: ""
verified_head: cec85a7
---

# Agent usage hook

## Requirement

User requirement (U3, verbatim, the measured part): "delivery time (start to finish in minutes), tokens used for each task (including implementation + review)"

User requirement (U1, verbatim): "all logs land in gitignored `.logs` in workbench root"

Design D9: a new hook `plugins/workbench/hooks/agent-usage-recorder.py` (Python 3.9 safe, `from __future__ import annotations`) runs on SubagentStart and SubagentStop through two new `.claude-plugin/plugin.json` entries; the subagent-commit-guard entry and its Decision are unchanged. On SubagentStart it writes the record with the start time, `agent_id`, `agent_type`, the agent transcript path derived from `transcript_path` and `session_id` (`<dir>/<session_id>/subagents/agent-<agent_id>.jsonl`) and the marker when readable. On SubagentStop it recomputes the record from the whole `agent_transcript_path` with `agent_usage.summarize`, keeps the earlier start from the SubagentStart record, and overwrites `<main checkout>/.logs/agents/<agentId>.json` (resolved with `workbench.logs_dir` from the event cwd, so a subagent in an integration tree writes to the main checkout). An event with an empty `agent_type` (internal agents) writes nothing. Any error (garbled stdin, missing or garbled transcript, unwritable dir) exits 0 with no output. Design D14: the recorder is Claude-only; no harness target emits it, pinned by a root test.

## Acceptance conditions

- AC1: a SubagentStop payload with a transcript writes `.logs/agents/<agentId>.json` with agentType, model, epic, task, role, start, end and tokens [evidence: test:plugins/workbench/hooks/tests/test_agent_usage_recorder.py::test_stop_writes_record]
- AC2: stopping the same agent twice (a fix round) overwrites one record recomputed from the whole transcript, tokens not doubled [evidence: test:plugins/workbench/hooks/tests/test_agent_usage_recorder.py::test_second_stop_overwrites]
- AC3: SubagentStart writes the start record and a later stop keeps that start [evidence: test:plugins/workbench/hooks/tests/test_agent_usage_recorder.py::test_start_then_stop_keeps_start]
- AC4: an event with an empty agent_type writes nothing [evidence: test:plugins/workbench/hooks/tests/test_agent_usage_recorder.py::test_internal_agent_writes_nothing]
- AC5: garbled stdin, a missing transcript and a garbled transcript all exit 0 with empty stdout [evidence: test:plugins/workbench/hooks/tests/test_agent_usage_recorder.py::test_fails_open]
- AC6: with cwd inside a linked worktree the record lands under the main checkout's `.logs`, with and without meta.json beside the transcript [evidence: test:plugins/workbench/hooks/tests/test_agent_usage_recorder.py::test_record_lands_in_main_checkout]
- AC7: plugin.json registers the recorder on SubagentStart and SubagentStop and keeps the commit guard entry unchanged [evidence: test:plugins/workbench/hooks/tests/test_agent_usage_recorder.py::test_plugin_json_registers_recorder]
- AC8: the recorder script and agent_usage.py are covered by the Python 3.9 safety tests [evidence: test:plugins/workbench/hooks/tests/test_py39_safe.py::test_every_hook_imports_without_tomllib]
- AC9: no harness target (copilot, codex, gemini, cursor, antigravity) emits agent-usage-recorder from the real plugin [evidence: test:scripts/tests/harness/test_claude_only_hooks.py::test_recorder_is_claude_only]
- AC10: references/hooks.md documents the recorder, its record path and that it is Claude-only [evidence: command:grep -n "agent-usage-recorder" plugins/workbench/skills/start-development/references/hooks.md]
- AC11: hooks, start-development and root scripts suites and lint pass [evidence: command:bash plugins/workbench/scripts/run-tests.sh --only hooks && bash plugins/workbench/scripts/run-tests.sh --only start-development && mise run test:scripts && mise run lint]

## Files

- `plugins/workbench/hooks/agent-usage-recorder.py`
- `plugins/workbench/hooks/tests/test_agent_usage_recorder.py`
- `plugins/workbench/hooks/tests/test_py39_safe.py`
- `plugins/workbench/.claude-plugin/plugin.json`
- `plugins/workbench/skills/start-development/references/hooks.md`
- `scripts/tests/harness/test_claude_only_hooks.py`

## Interfaces

- Entry: `python3 "${CLAUDE_PLUGIN_ROOT}/hooks/agent-usage-recorder.py"`, stdin the Claude hook payload; reads `hook_event_name`, `agent_id`, `agent_type`, `agent_transcript_path`, `transcript_path`, `session_id`, `cwd`.
- Uses `agent_usage.summarize`, `parse_marker`, `role_for`, `write_record` and `workbench.logs_dir`.

## Expected outcome

Every implementer and reviewer run leaves one accurate, idempotent usage record in the main checkout's `.logs/agents`, without ever blocking or slowing a stop.

## Steps

1. List the files under Files, read them in one pass with hooks/subagent-commit-guard.py and hooks/tests/test_py39_safe.py; write the AC1-AC9 tests and run `pytest hooks/tests/test_agent_usage_recorder.py -q` from plugins/workbench and `pytest scripts/tests/harness/test_claude_only_hooks.py -q` from the repo root: they fail.
2. Implement the entry script, register it, extend the py39 lists, document it; run the verify once.
3. Commit; leave the tree clean.

## Notes

- Estimate: 5 points.
- Reuse (brief): hooks/subagent-commit-guard.py stdin parse and fail-open shape (38-43); core.verify_recorder/write_verify_record record-then-write split as the pattern.
- Fix-as-ac (brief): SubagentStop refires after a commit-guard block and every SendMessage round - keyed by agentId, idempotent overwrite (AC2). Fail open, separate plugin.json entry (AC5, AC7). Root resolution from a worktree (AC6). Role from meta.json agentType is unknown at first stop; role comes from the marker, then agentType (AC6 covers both). Python floor: test_py39_safe.py and test_fail_closed.py (the recorder is fail-open, so it is not a deny hook). Other harnesses keep explicit allowlists (D14, AC9).
- Hooks brief: SubagentStart fires on spawn and on resume; SubagentStop fires for internal agents with agent_type "" (AC4); agent transcripts live at `~/.claude/projects/{project}/{sessionId}/subagents/agent-{agentId}.jsonl` with `agent-{agentId}.meta.json` beside.
- Adopted idea (hooks brief): record at SubagentStart and overwrite at every stop, and let the stamp step re-read transcript paths so a missed stop loses nothing (read_records in agent-usage-lib).
- The recorder is not registered in core.HOOKS (brief reuse entry): it makes no allow/deny/block decision and no harness adapter runs it, so the entry script calls agent_usage directly (my call).
- Bootstrap: the plugin loads from the main checkout, so this hook records nothing until the epic merges and `/reload-plugins` runs; runs before that are recovered by actuals-backfill (D16).

- 2026-10-25 done
