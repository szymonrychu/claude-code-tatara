# Epic and task migration skill record

## Asked

"Skill to add: migrate epics/tasks from old scheme to new one." Build `ticket.py migrate [<epic> | --all] [--dry-run]` and a thin `epic-migrate` skill (<= 45 lines) that rewrite old-scheme task files to the points scheme, fill actuals from legacy numbers and on-disk transcripts (never invented), and give every done epic a RETRO.md. Then migrate this repository's six done epics for real.

## Shipped

All 10 tasks built, 0 fix rounds. Epic review: pass (2026-10-25); one medium gap found and fixed by a tenth task (migrate-retro-missing); scope audit found no gaps or duplicates. Closed by `ticket.py close`: main fast-forwarded 6d6541a -> 0ee8cd3, integration and main verifies both green (`mise run test && mise run lint`; close.json). No MR. Real run on main: six `chore(ticket): <epic> migrate` commits (bd7f4fb, 74ed744, f33236d, 155e8dc, d8476ec, 2ace9ee) and five `chore(ticket): <epic> retro` commits (97e1b99, c3fd6dc, c153d13, 7d6d193, bc2c747); AC1-AC7 ok. Calibration buckets 1, 2, 3, 5, 8 now read from history, 13 from refit.

## Tasks

Gate approved 2026-10-25 ("go"): Q1 (drop legacy roles, verifier counts as review) yes, Q2 (orchestrator runs the real migration on main) yes. Interrogate panel ran before the gate; 7 act-on items folded into the plan.

| Task | Status | Verified head | Rounds | Verification tail |
|---|---|---|---|---|
| legacy-transcript-matcher | done | a408f1e | 0 | PASS scripts 155 passed; lint clean; real check 18 lean matches (9 impl + 9 review) |
| minutes-to-points | done | 77abb7a | 0 | PASS scripts 173 passed; lint clean. Implementer skipped the pytest red run (no pytest on default python3); reviewer confirmed AttributeError without the function |
| retro-writer-record-input | done | e91ee9a | 0 | PASS start-development 384 passed; lint clean |
| retro-records-once | done | 816af0c | 0 | PASS start-development 388, scripts 173; lint clean; real deltas run on lean matches done-commit order |
| migrate-dry-run | done | 494d702 | 0 | PASS start-development 399; lint clean; real dry run: 98 tasks in 6 epics, 33 old tasks with both roles matched, 1 partial, 6 RETRO.md, main untouched |
| migrate-command | done | b92409c | 0 | PASS start-development 408; lint clean. Test removed: dry-run-only refusal check in test_ticket_migrate_map.py (no longer accurate once the write path exists) |
| deltas-legacy-retired | done | ec62d68 | 0 | PASS start-development 409; lint clean. Test replaced: test_all_includes_legacy_minutes by the retirement pin |
| epic-migrate-skill | done | 3c5c5a5 | 0 | PASS start-development 412; lint clean |
| migrate-this-repo | done | 3c5c5a5 | 0 | assertions passed 1958, all green, lint clean; AC1-AC7 ok (run in main checkout) |
| migrate-retro-missing | done | b1072ef | 0 | PASS start-development 415; lint clean; dry run on main still nothing to change. Test fixture moved (ep-new to in-progress in test_dry_run_nothing_to_change) |

Epic-level: full suite in the integration tree on b1072ef, assertions passed 1961, lint exit 0. Points estimate 36, post-delivery 32 (retro-records-once 5 -> 3, migrate-this-repo 5 -> 3). Actual minutes 95 vs expected 400; tokens 10044825 vs 26042616 (RETRO.md).

## Rulings

- Q1 drop legacy actual_roles; verifier transcripts count as review. Why: the old four-role taxonomy does not sum to `actual` in 2 tasks and has no non-guess mapping. Cost if wrong: role split of old tasks is absent rather than approximate.
- Q2 orchestrator runs the real migration on main with the tree's ticket.py. Why: the integration tree cannot see main's docs/plans. Cost if wrong: six migrate and five retro commits on local main to revert.
- Q3 D10 stays all-or-nothing (dry run lists every problem first). Cost: one bad file blocks a whole run.
- Q4 `migrate --all` covers every epic in every phase, this epic included. Cost: none, new-scheme files print nothing to change.
- Q5 `points` set with empty expected values: fill from calibration.SEED[points].
- Interrogate items 2 and 4: names map takes only task file paths and names containing both epic and task slug (never `HEAD`); tokens and roles written only when records cover both impl and review. Cost if wrong: some old tasks lack tokens.
- Test removed (migrate-command): dry-run-only refusal check, no longer accurate. Test replaced (deltas-legacy-retired): test_all_includes_legacy_minutes, no longer accurate.
- Epic review gap migrate-retro-missing placed as a tenth task (2pt, sonnet). Reviewer declined: a repeated whole-number regex, SHA constant placement (style).
- Security lens skipped: diff touches no hooks, secrets, RBAC, ingress, CI vars or image pins.
- Declined (user decisions Q2/Q3): formula estimates of 5-8 minutes map to 1 point and dominate bucket 1.

## Discovered and blocked

- Old actuals are low-quality: legacy formula minutes (5-8 min) make history buckets small and non-monotonic (1pt 13 min, 5pt 16 min), and the 13pt refit extrapolates tokens below the 8pt bucket (n=0). Data quality, not a defect of this epic. Nothing blocks; the user may re-bucket later.
- 1 partial match in the dry run (epic-integration-worktrees/land-in-run review): tokens/roles left empty for that task.
- Follow-up asked by the user, not done by this epic: install the plugin into /Users/szymonri/Documents/claude-code-tatara via the template-update engine after close (a peer session is active there). Who clears: the orchestrator, on the user's go; never pushed.
- Verified head of epic-migrate-skill and migrate-this-repo is the same SHA (3c5c5a5).

## Not pushed

Local main at 0ee8cd3 (plus the close and retro chore commits) is not pushed. The user pushes.

## Lessons routed to

- Implementers twice skipped or filtered away the red or summary line (minutes-to-points skipped the pytest red run): mechanical. Add a check that the implementer's `tests.red` and summary line come from `run-tests.sh` output; implementers were told to run tests through run-tests.sh. Edit the epic-run implementer brief only if a check cannot be written.
- The discovery brief undercounted transcripts (149 vs 1042) until the fable panel reviewer found the workflow dirs (887 under subagents/workflows/wf_*/): judgement call. Edit start-development discovery guidance to say inventories must use `find` over the whole projects dir, not top-level listing.
- Legacy-key and missing-RETRO.md cases were only caught by the whole-diff review: add a test fixture for "done epic without RETRO.md" (added in migrate-retro-missing) to the migrate fixtures.
