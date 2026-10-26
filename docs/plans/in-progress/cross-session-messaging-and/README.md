---
title: Cross-session messaging and Kubernetes access session options
blockers: []
stage: review
owner: Szymon Richert
repos: [agents-orchestrator, any-mcp, agents-web, agents-helmfile]
created: 2026-10-26
---

# Cross-session messaging and Kubernetes access session options

## Project brief

What: Two opt-in session options: superleader messaging (a session whose leader can message the leaders of all sessions, and every leader can message superleaders), and cluster-admin in-cluster Kubernetes access for a session's agents
How: Spec fields threaded through orchestrator (queue with sender session, dispatcher framing, rendering, chart ServiceAccount + ClusterRoleBinding behind a value), new any-mcp orchestrator tools, preset form switches and chat labels, deployed via agents-helmfile
Why: Let one agent team orchestrate others (e.g. the Messenger assistant delegating to the project team) and let a project team operate the cluster it deploys to

## Description

Two new per-session options (spec fields, settable on presets) for agents-orchestrator sessions ("clusters" of agents):

1. Cross-session messaging (superleader): a session with the option on is a superleader session: its leader sees the leaders of all open sessions and can send messages to any of them. The leader of every other session (a hive leader, or the single agent of an alone session) sees only the superleader sessions (plus its own members through the hive tools) and can send messages only to them. The option is needed on one end only; the tools are rendered for every session. The user talks to agents through Facebook chat, and those agents dispatch messages to existing sessions and relay their answers. Messages go through the orchestrator's existing message queue, so delivery is durable and follows the target's leader.
2. Kubernetes access: the agents of a session get in-cluster Kubernetes credentials with full read-write on all namespaces and all resources.

Both are opt-in per session and off by default. Kubernetes access is additionally gated by the deployment (a chart value that creates the privileged ServiceAccount); without it the option is refused. Work spans agents-orchestrator (spec, API, dispatcher, rendering, chart RBAC), any-mcp (orchestrator plugin tools), agents-web (preset form, chat display) and agents-helmfile (deploy). After deploy the "facebook chat" preset enables messaging and "claude-code-tatara" enables Kubernetes access.

## Goals

- A sparse create-time spec option for cross-session messaging that makes a session a superleader: its leader lists the leaders of all open sessions and can send a message to any of them; the leader of every other session, alone sessions included, lists only the superleader sessions and can send only to them; every session receives messages sent to it as turns on its leader that name the sender session.
- A sparse create-time spec option for Kubernetes access; agent pods of a session with it on run as a ServiceAccount bound to cluster-admin with its token mounted and the in-cluster API address passed to the agent's shell, so in-cluster access works from it (kubectl comes from a user hook or the agent, not the orchestrator).
- Every other agent pod and every Job runs with an explicit ServiceAccount and no mounted token.
- Both options are editable in the agents-web preset form, and received cross-session messages are shown with their sender session in the chat.
- Deployed: new orchestrator, any-mcp and agents-web versions applied through agents-helmfile with the Kubernetes access chart value on; the "facebook chat" preset has messaging on (its running session discarded) and "claude-code-tatara" has Kubernetes access on.

## Non-goals

- No scoped or per-namespace Kubernetes roles; access is all-or-nothing cluster-admin.
- No synchronous request/reply or context transfer between sessions; messaging is an async mailbox.
- No messaging for non-leader agents, and no messaging between two sessions of which neither is a superleader.
- No change to the claude-code-tatara preset's env or onStart hook (the user removes its kubeconfig machinery).

## Review

Filled when the epic reaches stage `review`: the verdict, the findings acted on, the findings dropped.

Verdict: pass (2026-10-26)

Epic review (phase 5), 2026-10-27.
- Full suites: orchestrator 1027 passed (non-integration), lint and chart tests clean; agents-web 429 passed, lint clean; any-mcp 215 passed; agents-helmfile 208 passed, lint and gitleaks clean.
- PR CI: any-mcp #4 green; agents-web #15 green; agents-orchestrator #22 green after one e2e fix (two kind e2e assertions still expected the two-tool allow list; fixed f92cc8d); agents-helmfile #30 pending.
- Whole-diff review (sonnet): no findings across seams (frame contract, tool names, settings names, superleader authz, ServiceAccount wiring).
- Security review (sonnet): no critical/high. MEDIUM fixed as task agent-serviceaccounts-do-not (agent ServiceAccounts no longer inherit api annotations). LOW dismissed: 404 vs 403 slug probing (slugs are not secret); advisory limit overshoot (documented D10).
- Interrogate panel ran on the design before the gate (fable/opus/sonnet); its findings were applied to the plan.
- Scope audit (sonnet): all landed; G5 deploy and presets pending.
- Discovered task: allow-the-init-scripts-tools (agents were told to use a tool no allow list included).
