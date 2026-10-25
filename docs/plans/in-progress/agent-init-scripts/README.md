---
title: agent init scripts
blockers: [hive-mode-leadership-handove]
stage: review
owner: Szymon Richert
repos: [agent-orchestrator, any-mcp, claude-code-wrapper, agents-helmfile]
created: 2026-10-24
---

# agent init scripts

## Project brief

What: Per-cluster init scripts stored on ClusterSpec and presets, run once per cluster, visible to the agent and editable by it
How: init_scripts field, a once-per-cluster init Job recorded in clusters.status.init by the reconciler, scripts and log surfaced in the workdir (.agent-init/) and through the init tools of the shared orchestrator any-mcp plugin, an edit writing to the cluster and its source preset
Why: An agent knows how its environment was built and can improve it for the next cluster

## Description

User request (2026-10-24), verbatim:

"agent configuration epic:
* init scripts in the lab platform must be exposed to an agent that's been initialised with them (so it knows how it's initialised + it's able to edit it next time)
* init scripts are running once per cluster"

Scope confirmation (user, 2026-10-24): init scripts do not exist in agent-orchestrator yet (only the wrapper's per-pod init.setup_commands); this epic adds them to ClusterSpec and presets. An agent edit goes to the cluster's stored spec AND its source preset when there is one, so the next cluster from that preset gets it. The edit tool lives in the single shared "orchestrator" any-mcp plugin owned by the hive-mode-leadership-handove epic.

## Goals

- Clusters and presets carry `init_scripts`; a cluster runs them exactly once, before its agent sessions start, and records the run in `status.init`.
- The agent reads its scripts, run state and log (workdir `.agent-init/` and the init tools) and edits them; an edit writes the cluster spec and its source preset, never rolls a pod and never re-runs.
- Documented public routes, an API-only kind e2e, preset form rows and a cluster Init scripts dialog.
- The live agents namespace runs the build; the smoke proves init scripts.

## Non-goals

- Re-running init on a running cluster.
- Per-pod setup (wrapper `init.setup_commands` unchanged).
- any-mcp or claude-code-wrapper changes (the init tools and the main-agent-only gate come from hive-mode-leadership-handove).
- Secrets for the init Job beyond `spec.env`.

## Time

Estimate: 54 agent-min | Critical path: 32 min | Expected wall at P=1.5: 1.2 h (k=2.0) | Actual: 2 min | Remaining estimate: 0 min

## Review

Filled when the epic reaches stage `review`: the verdict, the findings acted on, the findings dropped.

Verdict: pass (2026-10-25)

Evidence: Whole-diff review (sonnet), security review (sonnet), CI test/lint/frontend/e2e green on agent-orchestrator PR #10 (e2e 4 init-scripts failures fixed: init Job workingDir created as root; three test-shape bugs), live apply helm rev 11 chart 0.1.0-main.22cf283, post-apply diff clean, smoke OK.
Acted on: smoke replicas 1 -> 2 (leader step), init Job workingDir, e2e test fixes, MEMORY smoke quote (PR #16), diff evidence in task notes.
Dropped: security - no server-side main-agent gate (design: any agent may edit, wrapper gates subagents), Default preset rewritten (C3), init Job SA token (matches agent pod), log_tail exposure (C2); review - create_job error permanent (task spec), phase message wording (AC6).
Follow-up noted, not built (Non-goal: any-mcp changes): any-mcp init_scripts_get description should name .agent-init/init.sh and next-cluster semantics.
