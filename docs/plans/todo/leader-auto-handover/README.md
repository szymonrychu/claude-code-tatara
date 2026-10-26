---
title: leader auto handover
blockers: []
stage: build
owner: ""
repos: [claude-code-wrapper, agents-orchestrator, agents-web, agents-helmfile]
created: 2026-10-26
---

# leader auto handover

## Project brief

What: a hive leader passes leadership to another agent automatically before it compacts and before a scale-down removes its pod
How: a wrapper pre-compaction event the orchestrator turns into an epoch-fenced handover, and a scale path that hands over first, both picking among ready agents that stay
Why: a compacted or removed leader loses the user-facing context; another agent should take the next request

## Description

User request 2026-10-26, verbatim: 'when session cluster leader gets compacted (or scaled down), pass it's leadership to another agent in the cluster.'

User decisions 2026-10-26 (AskUserQuestion and a follow-up correction): hand over just before compaction (a new pre-compaction event from the wrapper); on a scale-down that would remove the leader's pod, hand over first and then shrink, still refusing when no ready agent that stays exists; always on for hived agents (max_replicas > 1), no per-cluster switch ('Sorry.. auto handover always on for hived agents').

Discovery: /Users/szymonri/Documents/claude-code-tatara/.scratchpad/leader-handover/discovery.md. Decisions: decisions.md next to it. Builds on done epics hive-mode-leadership-handove and cluster-scaling, and amends hive D26 ("advised, never forced") and cluster-scaling's "the leader is never removed".

## Goals

- G1: when the leader of a hive is about to compact (auto or manual), the wrapper reports it before the compaction runs and the orchestrator moves leadership to another ready agent of the cluster; a busy leader moves at its turn boundary.
- G2: a scale-down whose new replica count would remove the leader's pod first hands leadership to a ready agent that stays, then shrinks; with no such agent it is refused as today.
- G3: the new leader is chosen among ready agents that stay in the cluster (never one about to be removed); with no eligible agent the leader keeps leading and the move is retried.
- G4: always on for every hive (max_replicas > 1); a cluster of one never hands over.
- G5: the UI, API and stream show automatic handovers with their reason (compaction, scale-down); documented API and API-only e2e test.
- G6: released and deployed: wrapper release, orchestrator pins, agents-helmfile bump, apply and a smoke step covering a scale-down below the leader.

## Non-goals

- No per-cluster switch for automatic handover.
- No holding or blocking Claude Code's compaction until the handover is acknowledged.
- No threshold-based early handover; the existing context advice stays as it is.
- No takeovers by agents, no consensus protocol; the orchestrator stays the single authority.

## Review

Filled when the epic reaches stage `review`: the verdict, the findings acted on, the findings dropped.
