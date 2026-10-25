---
title: configuration improvements
blockers: [agent-init-scripts, cluster-scaling, frontend-decoupling]
stage: review
owner: Szymon Richert
repos: [agent-orchestrator, agents-web, agents-helmfile]
created: 2026-10-25
---

# configuration improvements

## Project brief

What: Expose more claude-code-wrapper settings (hooks, idle_auto_compact), optional leader lease timeout, optional cluster autoclose after a time, Clusters entry in the hamburger menu above Presets
How: ClusterSpec and preset fields rendered into the wrapper config, a lease timeout in the leadership tables, an autoclose deadline enforced by the reconciler, a menu entry
Why: Get more of tatara-new's configurability into the Python platform

## Description

User request (2026-10-25), verbatim. Overall target: "Target getting more and more from tatara system (/Users/szymonri/Documents/tatara-new)"

"## configuration improvements
  * expose more claude-code-wrapper settings (including hooks, idle_auto_compact)
  * add optional timeout to leader lease
  * add autoclose after time (optional parameter- closing agent cluster after specified time)
  * clusters gets it's own place in \"hamburger\" menu, above \"presets\""

## Goals

- A preset or cluster spec carries a typed `wrapper` block (hooks on all 21 wrapper events, command and webhook; idle auto-compact; system prompt append; extra permissions; extra MCP servers; plugins; turn stall, restart and turn limits; agent slash commands) that reaches the claude-code-wrapper config with every reserved entry intact.
- A hive cluster can set `leader_lease_seconds`: once a leader has led that long, leadership is handed to the agent free the longest at the leader's next turn boundary; a running turn is never interrupted.
- A cluster can set `autoclose_after_seconds` (at least 300 s): counted from creation, the cluster is then discarded through the existing discard path.
- The hamburger menu's Settings list opens a Clusters page, listed above Presets.
- Every capability has a documented API and an API-only kind e2e test; the epic ends released, pinned, applied and smoked in the agents namespace.

## Non-goals

- No raw wrapper config overlay: `extra_args`, `boot`, `server`, `paths`, peers internals, `claude_json`, `config_files`, `permission_mode` and secret Claude env vars stay unexposed.
- No claude-code-wrapper code change or release (wrapper 0.2.0 already implements every setting).
- No pod TTL, handoff turn before close, or stop/pause state; no change to `LEADER_GRACE_SECONDS`.
- No editing of these fields on a running cluster (spec stays immutable after create except replicas and init_scripts).

## Time

Estimate: 57 agent-min | Critical path: 29 min | Expected wall at P=1.5: 1.3 h (k=2.0) | Actual: 0 min | Remaining estimate: 57 min

## Review

Filled when the epic reaches stage `review`: the verdict, the findings acted on, the findings dropped.

Verdict: pass (2026-10-25)

Evidence: per-task implementer + sonnet reviewer, fix rounds: openapi regen (spec-config-fields), ccw MCP name reserved (render-wrapper-settings). Whole-diff review clean (A1-A8). PR #14 CI incl. kind e2e green; agents-web PR #5 green; live apply orchestrator 0.1.0-main.60cb11c + agents-web 0.1.0-main.1343836, no drift, smoke OK incl config check (helmfile PR #20 merged).
Security: no critical/high. MEDIUM plaintext webhook secrets / MCP headers returned by cluster and preset views: noted, not done now (same model as existing spec.env; masking is a new feature, user to decide). LOW _escape docstring overstates MCP env protection (within the accepted command-hook exposure): noted. LOW onTick interval has no floor / timeouts uncapped: affects only the user's own pod (wrapper skips overlapping ticks): dropped.
