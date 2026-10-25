---
title: bench hive arm
status: done
repo: agent-orchestrator
value: the speed-up claim is measured with a hive arm
files: [src/agent_orchestrator/bench/spec.py, src/agent_orchestrator/bench/runner.py, src/agent_orchestrator/bench/report.py, examples/bench.yaml, tests/test_bench.py]
verify: "uv run pytest tests/test_bench.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [spec-cap-static, views-leader-stream]
owns: []
uses: [orch-spec-cap-static, orch-leader-views]
model: ""
estimate: 6
estimate_by: formula
actual: ""
actual_roles: ""
review: ""
worktree: /Users/szymonri/Documents/claude-code-tatara/.claude/worktrees/hive-mode-leadership-handove-bench-hive-arm/agent-orchestrator
branch: hive-mode-leadership-handove-bench-hive-arm
verified_head: e65b302a74619b8798325277326053e0c2d14298
run: hand-orchestrated-2026-10-25
provides: []
acs_for_audit: []
process_gaps: []
---

# bench hive arm

## Requirement

Measure the speed-up claim (Q12: no switch, the bench still records the result). `bench/spec.py` `Arm` gains optional `max_replicas` and `static`, passed by `bench/runner.py` into the created cluster spec; `bench/report.py` records each arm's final leader epoch (from the cluster view) next to wall time, failed turns, tokens and verify pass rate. `examples/bench.yaml` adds arm `hive3` (replicas 3, peers true) and a comment that every arm with more than one replica is now a hive (rr3 and rr3-peers included), with `single` as the alone baseline.

## Acceptance conditions

- AC1: Arm accepts max_replicas and static and the runner puts them into the cluster spec [evidence: test:tests/test_bench.py::test_arm_cap_and_static_in_spec]
- AC2: the report records the final leader epoch per arm [evidence: test:tests/test_bench.py::test_report_leader_epoch]
- AC3: examples/bench.yaml parses and contains the hive3 arm [evidence: test:tests/test_bench.py::test_example_has_hive_arm]
- AC4: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

## Files

- `src/agent_orchestrator/bench/spec.py`
- `src/agent_orchestrator/bench/runner.py`
- `src/agent_orchestrator/bench/report.py`
- `examples/bench.yaml`
- `tests/test_bench.py`

## Interfaces

- `bench/spec.py` `Arm{name, replicas, peers, max_replicas?, static?}`.

## Expected outcome

`orch bench` can run a hive arm and reports its leader epoch.

## Steps

- Red: add the three tests to `tests/test_bench.py`; run `uv run pytest tests/test_bench.py -q`: fails.
- Green: spec, runner, report, example; run the verify command: passes.

## Notes

- `Arm` at `bench/spec.py:24-30`; runner drives only `/api/v1`.
