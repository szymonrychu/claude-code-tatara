---
title: bench cli
status: todo
repo: agent-orchestrator
value: "Runs the experiment the user wants: does round-robin with several peered agents finish faster, fail less and verify more often?"
files: [src/agent_orchestrator/bench/__init__.py, src/agent_orchestrator/bench/spec.py, src/agent_orchestrator/bench/runner.py, src/agent_orchestrator/bench/report.py, src/agent_orchestrator/cli.py, tests/test_bench.py, examples/bench.yaml, README.md]
verify: "uv run pytest tests/test_bench.py -q && mise run lint"
depends_on: [entrypoints-and-singleton, readme-api-and-openapi]
owns: []
uses: [orch-cli, openapi-v1]
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

# bench cli

## Requirement

`orch bench SPEC --api URL --out FILE [--keep]` (D18). It talks only to the public API, through httpx.

The spec YAML has:
- `arms: [{name, replicas, peers}]`
- `cluster: {model, effort, ...}`, a ClusterSpec base
- `tasks: [{name, prompt, verify}]`
- `repeats`, `timeout_seconds`
- optional `chaos: {after_seconds}`

Spec validation errors exit 2, naming the field.

For each arm, in order:
- Create cluster `bench-<arm>-<run>`, a DNS-1123 slug of at most 40 characters.
- Wait until ready equals replicas and every agent has a session.
- For each task and repeat, POST the message and follow `GET /api/v1/stream` until its turn completes or fails, falling back to polling `GET /messages/{id}`.
- With chaos, POST `/agents/{id}/restart` on a random busy agent after `after_seconds`.
- Then POST the verify command as a check and wait for it.

Each (arm, task, repeat) writes one JSONL record: wall seconds from queued to completed, turn status, failed turns, input and output tokens from turn usage, verify passed, exit code.

At the end it prints a summary table per arm (runs, mean and p50 wall, failures, mean tokens, verify pass rate) and discards the bench clusters with purge, unless `--keep`.

`examples/bench.yaml` has the three arms 1/off, 3/off and 3/on. README.md gains `## Bench`.

## Acceptance conditions

- AC1: spec parsing validates arms, tasks and repeats and exits 2 on errors [evidence: test:tests/test_bench.py::test_spec_parsing_and_validation]
- AC2: every arm, task and repeat is run against the API [evidence: test:tests/test_bench.py::test_runs_each_arm_and_repeat]
- AC3: JSONL records carry wall time, failures, tokens and verify result [evidence: test:tests/test_bench.py::test_metrics_jsonl_fields]
- AC4: the summary table aggregates per arm [evidence: test:tests/test_bench.py::test_summary_table]
- AC5: the chaos step restarts an agent mid-run [evidence: test:tests/test_bench.py::test_chaos_restart_called]
- AC6: bench clusters are discarded and purged unless --keep [evidence: test:tests/test_bench.py::test_clusters_discarded_unless_keep]
- AC7: the example spec parses [evidence: command:uv run python -c "from agent_orchestrator.bench.spec import load_spec; load_spec('examples/bench.yaml')"]

## Files

- `src/agent_orchestrator/bench/__init__.py`
- `src/agent_orchestrator/bench/spec.py`
- `src/agent_orchestrator/bench/runner.py`
- `src/agent_orchestrator/bench/report.py`
- `src/agent_orchestrator/cli.py`
- `tests/test_bench.py`
- `examples/bench.yaml`
- `README.md`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
