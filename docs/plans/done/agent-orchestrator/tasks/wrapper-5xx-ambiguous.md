---
title: wrapper 5xx ambiguous
status: done
repo: agent-orchestrator
value: a wrapper error after it may have accepted a turn never causes a double send
files: [src/agent_orchestrator/wrapper/client.py, tests/test_wrapper_client.py, tests/test_dispatcher.py]
verify: "uv run pytest tests/test_wrapper_client.py tests/test_dispatcher.py -q && mise run lint"
depends_on: [dispatcher-loop, wrapper-client-and-sse]
owns: []
uses: []
model: ""
estimate: 5
estimate_by: formula
actual: ""
actual_roles: ""
review: ""
worktree: /Users/szymonri/Documents/claude-code-tatara/.claude/worktrees/agent-orchestrator-wrapper-5xx-ambiguous/agent-orchestrator
branch: "HEAD (worktree agent-orchestrator-wrapper-5xx-ambiguous)"
verified_head: dbc07550d994a2d3716c535afe26a3de75ea7d83
run: agent-orchestrator
provides: []
acs_for_audit: [AC1]
process_gaps: ["tests.red / verification.evidence not recorded in the implementer's output; I reproduced it: with client.py at 6a45f7b^, test_submit_5xx_mapping, test_submit_turn_maps_every_status and test_wrapper_500_goes_through_verifier fail; with HEAD, 34 tests pass"]
fork_point: 6e26b89
---

# wrapper 5xx ambiguous

## Requirement

Panel finding (medium, sonnet): wrapper/client.py _map_submit maps every status >= 500 to Unavailable, which requeues; a 500/502 after the wrapper recorded the turn would double-send. Map 500 and 502 to Ambiguous (verifier path); keep connect failures, 503 and 504 as Unavailable. Pin it with tests on the mapping and a dispatcher test that a 500 goes through verify and is not resent when the turn started.

## Acceptance conditions

- AC1: 500 and 502 map to Ambiguous, 503/504/connect errors to Unavailable [evidence: test:tests/test_wrapper_client.py::test_submit_5xx_mapping]
- AC2: a 500 whose turn started resolves to sent without a second submit [evidence: test:tests/test_dispatcher.py::test_wrapper_500_goes_through_verifier]

## Files

- `src/agent_orchestrator/wrapper/client.py`
- `tests/test_wrapper_client.py`
- `tests/test_dispatcher.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

The requirement holds, pinned by the acceptance tests.

What is true and observable when the task is done.

## Steps

- Write the failing acceptance tests; run red.
- Implement; run green with the verify command.

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
