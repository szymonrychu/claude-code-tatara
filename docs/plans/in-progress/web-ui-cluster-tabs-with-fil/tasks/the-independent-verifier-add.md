---
title: "The independent verifier added a '--timeout' flag its script does not accept and sent stderr to /dev/null, so it exited 2 with no output and produced both findings."
status: todo
repo: agent-orchestrator
value: "A broken verifier call becomes a high finding against a task that is green, which wastes a fix round. The verifier should run its script exactly as specified and keep stderr."
files: []
verify: ""
depends_on: []
owns: []
uses: []
model: ""
estimate: ""
estimate_by: ""
actual: ""
actual_roles: ""
review: ""
worktree: ""
branch: ""
verified_head: ""
run: ""
provides: []
---

# The independent verifier added a '--timeout' flag its script does not accept and sent stderr to /dev/null, so it exited 2 with no output and produced both findings.

## Requirement

The independent verifier added a '--timeout' flag its script does not accept and sent stderr to /dev/null, so it exited 2 with no output and produced both findings.

Where: verifier role in the plan-execute workflow (the script that writes the ACS/ACE temp files)

Why: A broken verifier call becomes a high finding against a task that is green, which wastes a fix round. The verifier should run its script exactly as specified and keep stderr.

## Acceptance conditions

- AC1: The independent verifier added a '--timeout' flag its script does not accept and sent stderr to /dev/null, so it exited 2 with no output and produced both findings. at verifier role in the plan-execute workflow (the script that writes the ACS/ACE temp files) is resolved [evidence: judgement]

## Files



## Interfaces

Keep the interfaces around verifier role in the plan-execute workflow (the script that writes the ACS/ACE temp files) unchanged unless resolving it requires otherwise: The independent verifier added a '--timeout' flag its script does not accept and sent stderr to /dev/null, so it exited 2 with no output and produced both findings..

## Expected outcome

The independent verifier added a '--timeout' flag its script does not accept and sent stderr to /dev/null, so it exited 2 with no output and produced both findings. at verifier role in the plan-execute workflow (the script that writes the ACS/ACE temp files) is resolved, and A broken verifier call becomes a high finding against a task that is green, which wastes a fix round. The verifier should run its script exactly as specified and keep stderr. no longer applies.

## Steps

1. Write a failing test that shows: The independent verifier added a '--timeout' flag its script does not accept and sent stderr to /dev/null, so it exited 2 with no output and produced both findings..
2. Fix it at verifier role in the plan-execute workflow (the script that writes the ACS/ACE temp files).
3. Run the task verify command and confirm it passes.

## Notes

Discovered in task `terminal-ws-relay` during run `web-ui-cluster-tabs-with-fil`.

