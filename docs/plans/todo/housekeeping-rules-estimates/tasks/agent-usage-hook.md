---
title: Agent usage hook
status: todo
repo: workbench
value: Every subagent run leaves an accurate usage record in .logs without the orchestrator doing anything
files: [plugins/workbench/hooks/agent-usage-recorder.py, plugins/workbench/hooks/tests/test_agent_usage_recorder.py, plugins/workbench/hooks/tests/test_py39_safe.py, plugins/workbench/.claude-plugin/plugin.json, plugins/workbench/skills/start-development/references/hooks.md, scripts/tests/harness/test_claude_only_hooks.py]
verify: "bash plugins/workbench/scripts/run-tests.sh --only hooks && bash plugins/workbench/scripts/run-tests.sh --only start-development && mise run test:scripts && mise run lint"
depends_on: [agent-usage-lib]
model: opus
review: ""
verified_head: ""
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

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
