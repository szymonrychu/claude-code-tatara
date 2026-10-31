# matrix read receipts retro

## Review

Migrated from the epic format.

## What went well

- 3 tasks delivered; connector repin receipts closed in 0 fix rounds (4 min vs 4, tokens 255136 vs 665870, 0.38x, suite 184 passed).
- Epic review clean: scope audit clean, helm rev 2 (chart 0.1.0-main.98b0803), post-apply diff showed no drift; PRs agents-matrix-connector #2 and agents-helmfile #27 landed.
- Points estimates held (MdAPE 0.0%, 4 vs 4); the receipt POST answered 200 and the user confirmed the message shows as seen (AC3).
- Apply was gated on a clean pre-diff and a one-time user approval, so the live change touched only the connector.
- Smoke passed on the re-run and the leftovers were removed with the user's OK.

## What went wrong or could improve

- mxc read receipts needed 1 fix round: the id tiebreak was not pinned by tests (suite 192 passed after the fix); tokens 913402 vs 545296 (1.68x).
- apply receipts live took 90 min vs 4 (22.50x), tokens 1044057 vs 665870 (1.57x); minutes MdAPE only 20.0% because the other two tasks were on estimate.
- The main orchestrator session was gone; the apply ran in this session only after the user's standing approval (AskUserQuestion), with a clean pre-diff changing only the connector.
- The apply and diff hit a transient gpg "Cannot allocate memory" error; restarting gpg-agent and retrying fixed it.
- The first smoke failed because its local port-forward died; it left smoke resources behind and the permission classifier blocked the subagent's cleanup DELETEs until the user approved.
- The live proof (AC3) depended on the user sending a message; it could not be completed unattended.

## Recommendations

- Code:
  - agents-matrix-connector read receipt path: keep tests pinning the id tiebreak (which event gets the receipt) so it cannot regress; the pin was added only after review.
- Delivered differently:
  - The apply ran in the planning/retro session, not the main orchestrator (gone), by explicit user approval for this epic only.
  - The live proof (AC3) was confirmed by the user's message ('Seems to be working'), not by an automated check.
- Tech debt:
  - Smoke script leaves resources behind when its port-forward dies (agents-helmfile smoke task): make it clean up in a trap or use a labelled sweep.
  - gpg-agent memory flake on apply/diff (local tooling): no fix in place; a retry wrapper in the apply task would remove the manual restart.
- Workflow:
  - recurring (agents-matrix-connector-depl, agents-schedule-deploy): live apply and smoke tasks run far over the minutes seed (90 vs 4 here, 26 vs 5 and 19 vs 5 before). Change: seed live apply/smoke tasks at 15-25 min and add user-dependent proof steps on top, calibrated from earlier actuals.
  - recurring (agents-matrix-connector-depl): the permission classifier blocks subagent live actions (kubectl exec there, cleanup DELETEs here). Change: plan live proof and cleanup as orchestrator-run steps, or record the approval in the plan before dispatch.
  - recurring (agents-matrix-connector-depl): acceptance that needs a user action (first real message there, a sent message here) stalls the apply task. Change: the deploy template lists user-action steps and asks for them up front, so the user is ready when the apply lands.
  - Smoke port-forward dying and the gpg flake are single occurrences; Retro table only.

## Delivery record (migrated)

### Asked

User request 2026-10-26: "Add read receipts". The agents-matrix-connector should send a Matrix `m.read` receipt for the newest event of each allowed batch when it hands the batch to an agent session, so mautrix-meta marks the Messenger message seen. Never for messages not handed off. The release is to be re-pinned and applied, and a real message must show as seen (G1-G3).

### Shipped

Connector sends a best-effort `m.read` receipt after handoff, next to typing (agents-matrix-connector PR https://github.com/szymonrychu/agents-matrix-connector/pull/2, merged as 98b0803). agents-helmfile re-pinned to 98b0803 and recorded in MEMORY (PR https://github.com/szymonrychu/agents-helmfile/pull/27, merged as d0a1956). Deploy: helm rev 2, chart 0.1.0-main.98b0803, post-apply diff showed no drift, smoke OK on re-run. Live: receipt POST 200 for in-3; user confirmed the message shows as seen. Epic review verdict: pass (2026-10-26), scope audit clean.

### Tasks

| Task | Status | Verified head | Review rounds | Verification tail |
|---|---|---|---|---|
| mxc-read-receipts | done | 98bdf1f | 1 fix round (id tiebreak unpinned) | suite 192 passed |
| connector-repin-receipts | done | 5ae6486 | 0 fix rounds | suite 184 passed |
| apply-receipts-live | done | 296318b | review not recorded in the notes (actual_roles shows review 1 min) | pre-diff: only the connector changed; smoke: OK, rerun exit 0; live receipt 200 |

All three verified heads appear in the epic git logs. Notes and files agree. Planned 3, done 3.

### Rulings

- Orchestrator runs `mise run apply` itself once (7b gone): what - standing user approval 2026-10-26 via AskUserQuestion; why - the user's call, conditioned on a clean pre-diff changing only the connector (met; the Secret change was suppressed and not inspected); cost if wrong - an unintended change in the agents namespace, mitigated by the pre-diff and the post-apply no-drift diff.
- Leftovers from the first failed smoke run deleted: what - deleted with the user's OK; why - port-forward died mid-smoke; cost if wrong - loss of a smoke schedule or session, low.
- Retry of the gpg flake during apply: what - re-run without change; why - transient failure; cost if wrong - none observed.
- AC3 accepted on the user's statement "Seems to be working": what - the user confirmed in Messenger; why - only the user can see the seen state; cost if wrong - receipts unproven for Messenger, though the POST returned 200.

### Discovered and blocked

- The port-forward used by smoke died on the first run. Not blocked (re-run passed); cleared by whoever owns the smoke task in agents-helmfile.
- The Secret agents-matrix-connector diff is unreadable by design, so a content change there was not inspected. The user or the helmfile owner can verify out of band.
- Blocked: none.

### Not pushed

Submodules: `origin/main..main` empty in agents-matrix-connector and agents-helmfile (merged via PRs). Workbench superrepo: main is 71 commits ahead of origin/main, including the retro and submodule pointer commits (3fcc0cc, aae87b6); the user or the orchestrator pushes it.

### Lessons routed to

- The apply task took 90 min against 4 expected (22.5x), because of the gpg flake and the smoke failure: add a smoke-script check that the port-forward is alive and retries once (mechanical, helmfile smoke task); add a gpg-agent preflight to `mise run apply`.
- The id tiebreak was unpinned on first implementation: add a test per tiebreak rule (done in 98bdf1f); no skill edit.
- Estimates for apply tasks should include live-verification time: judgement call, edit the epic planning skill's estimating guidance.
