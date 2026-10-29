# Handover: claude-code-tatara to cct2 (2026-10-29, final at ~17:3xZ)

The user is decommissioning claude-code-tatara (mx-34 #437: "Ask tatara to move all epics to cct and go idle"). The follow-up (mx-34 #440: "Let it finish its work ofc") let tatara finish hive-decoupling first. That epic is now done, and every remaining tatara epic belongs to cct2. Superrepo main carries this note and the submodule pins.

## Held resources

- Lease `agents-helmfile-apply`: released. Tatara held it only during its two applies, then deleted it.
- Orchestrator file locks: none.
- Cluster: nothing half-applied. The last apply was orchestrator 2d6d722 (helmfile main c2855fc), followed by smoke OK.
- Live versions: orchestrator 2d6d722, plugins ref v0.4.0, agent image 0.3.3, connector c98c501, web per helmfile main.
- In-pod deploy helpers (kube context from the SA, Harbor helm login): see "Deploy gotchas" in the tatara workdir `.scratchpad/session-loss/handoff-after-deploy.md`.

## For cct2's slash deploy

- Pin plugins **v0.5.1**, not v0.5.0. v0.5.1 (ef17204) descends from v0.5.0 (dfa0355) and adds one change: the hive-decoupling handover-advice floor, `max(auto_compact_pct - 15, 1)`. It needs nothing newer than the live orchestrator.
- The orchestrator on main is 2d6d722 plus whatever slash adds. Its migrations end at 0011 (drop feed_cursor). Slash brings 0010 and 0012, and the migrator applies by set.

## hive-decoupling: DONE (docs/plans/done/hive-decoupling)

- All 20 tasks are done, the review passed, and the epic is moved to done and reaped. The record and retro are in the epic dir.
- After the gate, the phase 5 review and scope audit added three tasks:
  - plugin-advice-threshold-floo (plugins PR #5, tag v0.5.1);
  - orch-feed-dead-code-and-comp (orchestrator PR #38, 2d6d722);
  - helmfile-orch-cleanup-pin (helmfile PR #55).
- The be554bb flaky-test fix shipped on its own (helmfile PR #54), as cct2 asked, then was superseded by 2d6d722.
- Judgement: tatara `.scratchpad/hive-decoupling/judgement.md`. Two LOW security notes are not acted on:
  - activity route cost: up to 1000 rows per call, no rate limit;
  - activity lines carry Bash commands unredacted.

## Queued epics (docs/plans/todo), now cct2's

- session-orchestration-mcp: planned with 24 tasks. Blocked on slash-commands-from-chat; hive-decoupling and Matrix are done. Numbers: orchestrator migration 0013, because slash already ships 0012 (tatara's counter in mx-34 msg 468). Plugins v0.6.0 and agents-schedule v0.2.0 are pending the user's answer. The design reads the next free migration and the plugin minor at build time.
- decision-board: README-only shell, blocked on session-orchestration-mcp. Not planned. Open at planning: the component name, and how an answer reaches the asking session.
- semver-image-tags-at-the-end: planned with 6 tasks, no blockers, agreed for the end of the chain.

## Rules learned

- Propose every tag through mx-34 and wait for its confirmation (user rule since 14:27Z). Tatara broke it once, with v0.5.1, and mx-34 reported it to the user.

## Done earlier

- matrix-connector-agent-initi: done (35/35), with record and retro.
- cct2-1 wedge: cleared 02:23Z. The stale-busy detector follow-up is not started; see docs/plans/2026-10-28-wrapper-queued-command-wedge-debug-record.md.

## Stale local refs (ignore)

The tatara clone holds local-only `slash-commands-from-chat` commits from 2026-10-27 in orchestrator, web, plugins and wrapper. A commit with the same subject on cct2's origin branches supersedes each one. They were not pushed.
