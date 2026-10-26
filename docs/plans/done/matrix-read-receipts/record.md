# matrix read receipts record

## Asked

User request 2026-10-26: "Add read receipts". The agents-matrix-connector should send a Matrix `m.read` receipt for the newest event of each allowed batch when it hands the batch to an agent session, so mautrix-meta marks the Messenger message seen. Never for messages not handed off. The release is to be re-pinned and applied, and a real message must show as seen (G1-G3).

## Shipped

Connector sends a best-effort `m.read` receipt after handoff, next to typing (agents-matrix-connector PR https://github.com/szymonrychu/agents-matrix-connector/pull/2, merged as 98b0803). agents-helmfile re-pinned to 98b0803 and recorded in MEMORY (PR https://github.com/szymonrychu/agents-helmfile/pull/27, merged as d0a1956). Deploy: helm rev 2, chart 0.1.0-main.98b0803, post-apply diff showed no drift, smoke OK on re-run. Live: receipt POST 200 for in-3; user confirmed the message shows as seen. Epic review verdict: pass (2026-10-26), scope audit clean.

## Tasks

| Task | Status | Verified head | Review rounds | Verification tail |
|---|---|---|---|---|
| mxc-read-receipts | done | 98bdf1f | 1 fix round (id tiebreak unpinned) | suite 192 passed |
| connector-repin-receipts | done | 5ae6486 | 0 fix rounds | suite 184 passed |
| apply-receipts-live | done | 296318b | review not recorded in the notes (actual_roles shows review 1 min) | pre-diff: only the connector changed; smoke: OK, rerun exit 0; live receipt 200 |

All three verified heads appear in the epic git logs. Notes and files agree. Planned 3, done 3.

## Rulings

- Orchestrator runs `mise run apply` itself once (7b gone): what - standing user approval 2026-10-26 via AskUserQuestion; why - the user's call, conditioned on a clean pre-diff changing only the connector (met; the Secret change was suppressed and not inspected); cost if wrong - an unintended change in the agents namespace, mitigated by the pre-diff and the post-apply no-drift diff.
- Leftovers from the first failed smoke run deleted: what - deleted with the user's OK; why - port-forward died mid-smoke; cost if wrong - loss of a smoke schedule or session, low.
- Retry of the gpg flake during apply: what - re-run without change; why - transient failure; cost if wrong - none observed.
- AC3 accepted on the user's statement "Seems to be working": what - the user confirmed in Messenger; why - only the user can see the seen state; cost if wrong - receipts unproven for Messenger, though the POST returned 200.

## Discovered and blocked

- The port-forward used by smoke died on the first run. Not blocked (re-run passed); cleared by whoever owns the smoke task in agents-helmfile.
- The Secret agents-matrix-connector diff is unreadable by design, so a content change there was not inspected. The user or the helmfile owner can verify out of band.
- Blocked: none.

## Not pushed

Submodules: `origin/main..main` empty in agents-matrix-connector and agents-helmfile (merged via PRs). Workbench superrepo: main is 71 commits ahead of origin/main, including the retro and submodule pointer commits (3fcc0cc, aae87b6); the user or the orchestrator pushes it.

## Lessons routed to

- The apply task took 90 min against 4 expected (22.5x), because of the gpg flake and the smoke failure: add a smoke-script check that the port-forward is alive and retries once (mechanical, helmfile smoke task); add a gpg-agent preflight to `mise run apply`.
- The id tiebreak was unpinned on first implementation: add a test per tiebreak rule (done in 98bdf1f); no skill edit.
- Estimates for apply tasks should include live-verification time: judgement call, edit the epic planning skill's estimating guidance.
