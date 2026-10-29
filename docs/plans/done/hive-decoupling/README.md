---
title: hive decoupling
blockers: [matrix-connector-agent-initi]
stage: review
owner: Szymon Richert
repos: [agents-orchestrator, any-mcp-tatara-plugins, agents-helmfile]
created: 2026-10-27
---

# hive decoupling

## Project brief

What: Members stop receiving a truncated stream of the leader's activity; context moves on demand, and a leader near its limit hands over directly to a chosen successor
How: fable-architected design on top of leader-auto-handover: on-demand handoff instead of streamed peer-notes, a limit signal to the leader, a direct leader-successor conversation
Why: Streamed peer-notes consume every member's context on every turn

## Description

User request (2026-10-27, relayed by the mx-5 leader, msg 124), verbatim:

"Decouple agents in session more. Right now non-leaders get truncated stream of what's leader is doing. Ask fable architect to decouple or use handoff or something to consume non-leaders less.
Maybe leader could get a signal to pass on its session details to another agent when it hits a limit and both could talk to each other about details for handoff?"

Relayer's reading: non-leader members get a truncated stream of the leader's activity (seen as peer-notes on every turn), which uses up their context. A fable architect designs a better approach (on-demand handoff instead of streaming, or similar), including a leader-initiated handoff: near its limit the leader gets a signal, picks a successor, and the two talk directly to transfer details. Build on the done epic leader-auto-handover; do not duplicate it.

Queued after matrix-connector-agent-initi.

## Goals

- G1: Members receive no streamed activity: the dispatcher sends no appended feed note, `hive_state` is re-pushed only when the leader, epoch, membership or readiness changes, and `session_leaders.feed_cursor` is dropped.
- G2: Any hive agent pulls recent activity on demand: `GET /agent/v1/activity` (optional `agent`, `limit` 1..200) and the plugin tool `orchestrator_activity`.
- G3: A leader at or above the effective handover threshold (its compaction percentage minus 15) gets one keyed `handover_due` note with ranked successor candidates, their ccw addresses and the handoff protocol; the `hive_state` hint and the plugin advice always use the effective threshold.
- G4: The leader briefs a chosen successor directly over ccw peer messaging, then hands over with `orchestrator_leadership_handover(to=..., epoch=...)`; the requester learns every handover request outcome (applied, or rejected with its reason) as a keyed `leadership_request` note.
- G5: Released and deployed: any-mcp-tatara-plugins next minor tag, orchestrator pins, agents-helmfile bump, apply, a smoke covering the activity route and tool, and a live handoff proof.

## Non-goals

- Any claude-code-wrapper change or release; any agents-web change.
- A digest or summarised stream to members, or a shared journal file.
- An automatic threshold handover by the orchestrator, or any new automatic pick rule.
- An orchestrator-mediated handoff protocol, or a new table or writer for the brief.
- A new `session_leaders.reason` value or stream frame; a per-session switch for the signal or the pull tool.
- Pushing the compact summary to the successor.
- Changing any leader-auto-handover backstop (compaction and scale-down handover, claim hold, reconciler pod hold).
- Rate limiting `activity`; dropping `events.created_at` (the session export reads it).

## Review

Filled when the epic reaches stage `review`: the verdict, the findings acted on, the findings dropped.

Verdict: pass (2026-10-29)

# hive-decoupling phase 5 judgement (tatara-2, 2026-10-29)

Ranges: orchestrator a9f936f..be554bb; plugins 4506e70..6d5cc19 (v0.4.0); helmfile 52b6893..c786dc4 excluding PR #51. Reviewer sonnet (whole diff) and security-researcher sonnet.

## Act on
- F1 (validated: plugins __init__.py:119-123 renders `auto_compact_pct - 15` with no floor; spec.py:475 allows ge=1): G3 says the plugin advice always uses the effective threshold `max(compact - 15, 1)`. Fix task plugin-advice-threshold-floo, plugin 0.5.1 on cct2's v0.5.0; the ref pin rides with cct2's slash deploy.

## Consider
- F2: the effective compaction point is spelled in 4 places (hive.py compact_pct, k8s/on_start.py:73, k8s/render.py:149, db/views.py:76). Design line 205 itself spells the rendered plugin config inline, so this is not a spec breach; reuse of hive.compact_pct is a cheap cleanup for cct2.
- F3: dispatcher/feed.py keeps the synthetic `leadership` branch (nothing produces it) and digest_lines returns a `pending` list the only caller drops. Design D1/D3 say digest_lines stays unchanged; the anti-goal says no dead feed code. Low cost cleanup; handed to cct2 as optional.

## Noted
- Security LOW: GET /agent/v1/activity loads up to 1000 event rows with full data per call, no rate limit (own session only; rate limiting is a non-goal).
- Security LOW: activity lines carry Bash commands unredacted to every pod of the session (pre-existing with the feed; now pulled, not pushed).
- Security INFO: authz (require_agent, session-scoped query), SQL parameterized, migration 0011 DROP COLUMN IF EXISTS, helmfile exposes no secrets.
- Live orchestrator df2b80e lacks the PR #37 fix fe2c623 until be554bb is deployed (task helmfile-orch-flaky-fix-pin).

## Dismissed
- none.

## Cannot verify
- Live apply and handoff proof rest on MEMORY.md and .logs/hive-decoupling-deploy-2026-10-29/live-proof.md (the reviewer of PR #53 checked them against the logs).
- Migration 0010 from slash-commands merging after 0011 (migrator applies by set, per run notes).

## Independent verification (supervisor, review worktrees at origin/main heads)
- agents-helmfile c786dc4: test "301 passed in 479.74s"; lint "All checks passed!", "no leaks found".
- agents-orchestrator be554bb: lint "All checks passed!"; test "1 failed, 699 passed, 69 deselected, 1 warning, 629 errors": the 629 errors are DB tests without Docker (docker unixconn FileNotFoundError, CI-only per design); the 1 failure test_reconciler.py::test_lightkube_default_client_uses_env_config is pod-environment (in-cluster SA env wins over KUBECONFIG). CI evidence: main run 40901222840 test/lint/chart green, e2e as watched by the pin task.
- any-mcp-tatara-plugins dfa0355: lint "All checks passed!"; test "1 failed, 27 passed": known pod-only tests/test_source_install.py (git 2.39 --end-of-options), CI green.

## After the scope audit
- F2 and F3 (also scope audit gaps 1 and 2) were acted on, not left as Consider: task orch-feed-dead-code-and-comp (orchestrator PR #38, 2d6d722), pinned by helmfile-orch-cleanup-pin (PR #55), deployed and smoke OK.
- F1 fixed in plugins v0.5.1 (PR #5). Its live pin rides with cct2's slash deploy (mx-34 #460/#461).
- Verdict: pass.
