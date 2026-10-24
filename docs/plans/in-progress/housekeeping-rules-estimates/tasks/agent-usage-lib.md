---
title: Agent usage lib
status: done
repo: workbench
value: "Per-agent time and tokens are read from transcripts once, correctly, by one module"
files: [plugins/workbench/scripts/lib/agent_usage.py, plugins/workbench/scripts/tests/test_agent_usage.py, plugins/workbench/hooks/lib/core.py, plugins/workbench/hooks/tests/test_core_stop.py]
verify: "bash plugins/workbench/scripts/run-tests.sh --only scripts && bash plugins/workbench/scripts/run-tests.sh --only hooks && mise run lint"
depends_on: [workbench-dirs, output-spill-to-logs]
model: opus
review: ""
verified_head: f34227b
---

# Agent usage lib

## Requirement

User requirement (U3, verbatim, the measured part): "delivery time (start to finish in minutes), tokens used for each task (including implementation + review)"

User requirement (U4, verbatim, the seamless part): "It must be seamless for the agent (taking over most of the estimation from agent's reasoning)."

Design D9: `plugins/workbench/scripts/lib/agent_usage.py` (stdlib, Python 3.9 safe) owns the per-agent usage record. `transcript_lines(path)` yields each JSON object of a transcript, skipping unreadable or garbled lines; `core.collect_worktrees` uses it instead of its inline loop. `summarize(path)` returns the first and last `timestamp`, the model of the last assistant line, and tokens summed once per `message.id` (falling back to `requestId`, then the line itself), keeping `input`, `cache_creation`, `cache_read` and `output` and their `total`. `parse_marker(path)` reads the first line of the first user message and matches `[wb <epic>/<task>/<role>]` (role `impl` or `review`). `role_for(marker_role, agent_type)` takes the marker role, else maps `workbench:implementer` to `impl` and `workbench:reviewer` to `review`. `write_record(logs_dir, record)` writes `<logs>/agents/<agentId>.json` as an atomic overwrite (temp file plus os.replace), never an append. `read_records(logs_dir, epic=None, task=None)` returns the matching records, re-summarising each from its `transcript` when that file still exists. Tokens are input + cache_creation + cache_read + output (hooks brief finding 4).

## Acceptance conditions

- AC1: a transcript fixture with the same message.id on several assistant lines counts its usage once; requestId is the fallback key [evidence: test:plugins/workbench/scripts/tests/test_agent_usage.py::test_tokens_summed_once_per_message_id]
- AC2: garbled and non-assistant lines are skipped; start, end and model come from the transcript [evidence: test:plugins/workbench/scripts/tests/test_agent_usage.py::test_summarize_tolerates_garbage]
- AC3: the marker is parsed from the first user message's first line, and the role falls back to agentType when the marker is missing [evidence: test:plugins/workbench/scripts/tests/test_agent_usage.py::test_marker_and_role]
- AC4: writing the same agent's record twice leaves one file holding the second record [evidence: test:plugins/workbench/scripts/tests/test_agent_usage.py::test_write_record_overwrites]
- AC5: read_records filters by epic and task and re-summarises from the transcript when it exists, else keeps the stored totals [evidence: test:plugins/workbench/scripts/tests/test_agent_usage.py::test_read_records_resummarises]
- AC6: the commit guard still finds worktrees from the transcript through the shared iterator [evidence: test:plugins/workbench/hooks/tests/test_core_stop.py::test_commit_guard_decisions]
- AC7: scripts and hooks suites and lint pass [evidence: command:bash plugins/workbench/scripts/run-tests.sh --only scripts && bash plugins/workbench/scripts/run-tests.sh --only hooks && mise run lint]

## Files

- `plugins/workbench/scripts/lib/agent_usage.py`
- `plugins/workbench/scripts/tests/test_agent_usage.py`
- `plugins/workbench/hooks/lib/core.py`
- `plugins/workbench/hooks/tests/test_core_stop.py`

## Interfaces

- `agent_usage.MARKER` (compiled regex), `agent_usage.transcript_lines(path) -> Iterator[dict]`
- `agent_usage.summarize(path) -> dict` keys `start`, `end`, `model`, `tokens` (`input`, `cache_creation`, `cache_read`, `output`, `total`)
- `agent_usage.parse_marker(path) -> tuple[str, str, str] | None`, `agent_usage.role_for(marker_role, agent_type) -> str`
- Record JSON: `agentId`, `agentType`, `model`, `epic`, `task`, `role`, `transcript`, `start`, `end`, `tokens`, `updatedAt`.
- `agent_usage.write_record(logs_dir, record) -> Path`, `agent_usage.read_records(logs_dir, epic=None, task=None) -> list[dict]`

## Expected outcome

One shared module reads Claude transcripts correctly (no double counting) and owns the record format the hook writes and ticket.py reads.

## Steps

1. List the files under Files, read them in one pass with hooks/worktree_lib.py (how hooks import scripts/lib); write test_agent_usage.py with transcript fixtures and run `pytest scripts/tests/test_agent_usage.py -q` from plugins/workbench: it fails.
2. Implement; switch core.collect_worktrees to the shared iterator; run the verify once.
3. Commit; leave the tree clean.

## Notes

- Estimate: 5 points.
- Reuse (brief): the transcript loop in hooks/lib/core.py:collect_worktrees (450-491); factor the line iterator out, do not write a third walker. Do-not-build: a new transcript JSONL walker.
- Fix-as-ac (brief): duplicate usage per message (on-disk check: 5 assistant lines, 4 unique ids) - AC1.
- Hooks brief finding 4: assistant lines carry `timestamp`, `message.model`, `message.usage` with input_tokens, cache_creation_input_tokens, cache_read_input_tokens, output_tokens; keep the four components.
- Do-not-build (hooks brief): per-agent duration from the Agent tool result (no usage for background agents); use transcript timestamps.
- `aggregate` across records for a task is added by stamp-actuals.

- 2026-10-25 done
