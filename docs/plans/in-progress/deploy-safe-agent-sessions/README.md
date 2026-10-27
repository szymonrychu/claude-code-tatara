---
title: deploy-safe agent sessions
blockers: []
stage: build
owner: Szymon Richert
repos: [agents-orchestrator, claude-code-wrapper, agents-web, agents-helmfile]
created: 2026-10-27
---

# deploy-safe agent sessions

## Project brief

What: Agent sessions survive deploys and pod restarts: the ingester re-attaches after resume, rollouts never replace busy or leader pods, interrupted turns continue, transcripts are backed up, and red builds never deploy
How: Orchestrator ingester/eligibility/reconciler fixes with OnDelete plus an idle-only replacer, wrapper turn continuation, S3 backup of /sessions via the existing cache jobs, web warnings, CI needs plus a helmfile pin check, and a kind e2e rolling the image mid-turn
Why: On 2026-10-27 a deploy rolled every agent pod; the orchestrator never re-attached, sessions hung, the user discarded them and lost both conversations

## Description

Incident 2026-10-27 (evidence: .scratchpad/session-loss/ in the workbench root, cluster-evidence.md, hang-analysis.md, code-analysis.md, carto-*.md, reuse.md, research.md; brief docs/research/2026-10-27-session-survival.md).

At 20:03Z the agents-helmfile #35 apply upgraded agents-orchestrator to 96e46f3; the reconciler re-applied every agent StatefulSet and, with the default RollingUpdate, rolled every agent pod at once (wrapper 0.3.0 -> 0.3.1), including the pod whose leader was running the apply mid-turn (the apply died before agents-web; smoke never ran). Every resume returned 200, but the ingester had ended each agent's stream on the wrapper's session_closed, never re-attached after the resume (same session id, unchanged AgentRef) and re-marked the agent dead from the stored session_closed (ingester/loop.py:106-140,191-195,296-306). The dispatcher only delivers to idle agents (db/queue.py:273): queued messages sat 20+ minutes; leader eligibility ignores dead agents. The interrupted turn was never continued (API resume sends no continue prompt). The user saw hung sessions and discarded both at 20:29; discard deleted the PVCs and the Claude transcripts (/sessions), which the S3 cache does not save, so code came back but conversations did not.

User request (2026-10-27 20:44Z, relayed by mx-34 msg 150), verbatim: "Figuring out what happened that the session hanged 2. Convert the evidence into actionable epic and fix it autonomously". Approved scope (mx-34 msg 157, user standing decision 20:53Z): root cause fix; busy/leader-aware or staged agent StatefulSet template rollouts; resume continues the interrupted turn; non-fatal onStart plugin install; no deploy of a red main CI build; regression e2e rolling the image mid-turn; back up Claude transcripts (/sessions) with the workdir to S3 and restore them on recreate or resume; web UI warns before discarding a session's history; a deploy never runs inside a pod that the same deploy rolls. Gate pre-approved: every design question is answered with the recommended option, recorded as (my call).

## Goals

- G1: After an agent pod restart and a successful wrapper resume, the ingester re-attaches from the last stored event, the agent leaves `dead`, and queued messages are delivered (the 20:07-20:29 hang cannot recur).
- G2: A dead agent is never eligible as leader; leadership moves to a live agent.
- G3: Agent StatefulSet template changes never replace a busy agent pod or the current leader mid-turn: updateStrategy OnDelete plus a reconciler replacer that deletes one outdated pod at a time, only when idle, leader last after handover; a pod running a deploy is therefore never rolled by that deploy.
- G4: A wrapper session resumed after a shutdown that interrupted a turn continues that turn with the continue prompt, and the orchestrator renders a default continue prompt.
- G5: A failed any-mcp plugin install in onStart is logged and leaves the agent pod Ready.
- G6: Claude transcripts (/sessions) are backed up to S3 with the workdir at discard and restored on recreate, and a recreated session resumes the restored conversation.
- G7: The web discard dialog states what history is lost or backed up; the chat shows an agent-unavailable banner with the age of the oldest queued message.
- G8: No red main build is published or deployed: CI publish jobs need e2e/tests, and the agents-helmfile apply refuses pins whose commit checks are not green.
- G9: A kind e2e rolls the agent image while a turn is running and proves no busy pod is replaced, the turn continues, and queued messages are delivered.
- G10: Released and deployed: wrapper release tag, orchestrator and web pins, agents-helmfile bump, apply and smoke green, with a live check that the deploy did not roll a busy agent.

## Non-goals

- Running helmfile apply as an in-cluster Job runner (G3 keeps the deployer's busy pod from being rolled instead).
- Sending Claude's documented exit keystrokes on SIGTERM (inferred need only; noted, not doing now).
- Changing hive leadership handover semantics beyond excluding dead agents.
- Periodic (non-discard) transcript backups.

## Review

Filled when the epic reaches stage `review`: the verdict, the findings acted on, the findings dropped.
