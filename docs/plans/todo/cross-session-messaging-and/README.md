---
title: Cross-session messaging and Kubernetes access session options
blockers: []
stage: build
owner: ""
repos: [agents-orchestrator, any-mcp, agents-web, agents-helmfile]
created: 2026-10-26
---

# Cross-session messaging and Kubernetes access session options

## Project brief

What: Two opt-in session options: leader-to-leader messaging between sessions, and cluster-admin in-cluster Kubernetes access for a session's agents
How: Spec fields threaded through orchestrator (queue with sender session, dispatcher framing, rendering, chart ServiceAccount + ClusterRoleBinding behind a value), new any-mcp orchestrator tools, preset form switches and chat labels, deployed via agents-helmfile
Why: Let one agent team orchestrate others (e.g. the Messenger assistant delegating to the project team) and let a project team operate the cluster it deploys to

## Description

Two new per-session options (spec fields, settable on presets) for agents-orchestrator sessions ("clusters" of agents):

1. Cross-session messaging: the leader of a session can send messages to the leaders of other sessions and receive messages from them, through orchestrator tools in the agent pods. Messages go through the orchestrator's existing message queue, so delivery is durable and follows the target's leader.
2. Kubernetes access: the agents of a session get in-cluster Kubernetes credentials with full read-write on all namespaces and all resources.

Both are opt-in per session and off by default. Kubernetes access is additionally gated by the deployment (a chart value that creates the privileged ServiceAccount); without it the option is refused. Work spans agents-orchestrator (spec, API, dispatcher, rendering, chart RBAC), any-mcp (orchestrator plugin tools), agents-web (preset form, chat display) and agents-helmfile (deploy). After deploy the "facebook chat" preset enables messaging and "claude-code-tatara" enables Kubernetes access.

## Goals

- A sparse create-time spec option for cross-session messaging; a session with it on can list messaging-enabled sessions and send a message to another one's leader, and receives messages sent to it as turns on its leader that name the sender session.
- A sparse create-time spec option for Kubernetes access; agent pods of a session with it on run as a ServiceAccount bound to cluster-admin with its token mounted, and kubectl in-cluster access works from the agent's shell.
- Every other agent pod and every Job runs with an explicit ServiceAccount and no mounted token.
- Both options are editable in the agents-web preset form, and received cross-session messages are shown with their sender session in the chat.
- Deployed: new orchestrator, any-mcp and agents-web versions applied through agents-helmfile with the Kubernetes access chart value on; the "facebook chat" preset has messaging on (its running session discarded) and "claude-code-tatara" has Kubernetes access on.

## Non-goals

- No scoped or per-namespace Kubernetes roles; access is all-or-nothing cluster-admin.
- No synchronous request/reply or context transfer between sessions; messaging is an async mailbox.
- No messaging for non-leader agents and no cross-session messaging for sessions without the option.
- No change to the claude-code-tatara preset's env or onStart hook (the user removes its kubeconfig machinery).

## Review

Filled when the epic reaches stage `review`: the verdict, the findings acted on, the findings dropped.
