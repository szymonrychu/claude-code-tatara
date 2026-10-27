---
title: leader auto handover
blockers: []
stage: review
owner: Szymon Richert
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

- G1: when the leader of a hive is about to compact (auto or manual), the wrapper reports it before the compaction runs (the `compacting` event; only this report precedes the compaction) and the orchestrator then moves leadership to another ready agent of the cluster at the leader's turn boundary, which for a busy leader is after the native compaction has run.
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

Verdict: pass (2026-10-27)

Reviewed 2026-10-27. Full notes: .scratchpad/leader-auto-handover-review.md (whole-diff start-review --single per repo, sonnet; scope-auditor, sonnet).

- Goals G1-G6 landed. G6 closed by helmfile-apply-smoke: live first-message proof after a scale-down handover (session cc2f85d7-cd74-4ea1-be90-43cb597e3eec, message 69 answered by the new pod-0 leader), `mise run smoke` green on agents-helmfile main 0ed86cf, MEMORY entry merged (agents-helmfile PR #34). Non-goals respected.
- Acted on (new tasks, done): smoke-step7-per-wait-deadlin (step 7 agent lookup and make-leader waits reused the scale-up deadline; agents-helmfile PR #34); orch-eligibility-single-sour (duplicated eligibility and handover-pending SQL predicates moved into db/eligibility.py, behaviour unchanged, CI test 1083 passed and kind e2e green; agents-orchestrator PR #25).
- Noted: the busy-leader race is pinned at queue level only; correctness near an election assumes wrapper and DB clocks agree; no live compaction has been observed since the apply, so real Claude Code PreCompact before an auto compaction is unproven live.
- Dropped: none.
- Full suite: lint green in all four repos. In this pod, tests failed only for environment reasons: no Docker, a Harbor 401, in-cluster kube config, and four wrapper PTY tests in files the epic does not touch. The DB tests were proven by agents-orchestrator CI.
