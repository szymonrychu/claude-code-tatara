---
title: Agent usage lib
status: todo
repo: workbench
value: "Per-agent time and tokens are read from transcripts once, correctly, by one module"
files: [plugins/workbench/scripts/lib/agent_usage.py, plugins/workbench/scripts/tests/test_agent_usage.py, plugins/workbench/hooks/lib/core.py, plugins/workbench/hooks/tests/test_core_stop.py]
verify: "bash plugins/workbench/scripts/run-tests.sh --only scripts && bash plugins/workbench/scripts/run-tests.sh --only hooks && mise run lint"
depends_on: [workbench-dirs, output-spill-to-logs]
model: opus
review: ""
verified_head: ""
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

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
