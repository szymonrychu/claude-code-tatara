# Epic and task migration skill retro

## Review

Migrated from the epic format.

## What went well

- All 10 tasks closed in review round 0, no escalation, each with a quoted tail (e.g. migrate-command: start-development 408 passed, lint clean).
- The design interrogate (fable, opus, sonnet) caught 7 act-on items before any code: real transcript inventory (1042 agent files, 887 under workflow dirs), `branch: HEAD` poisoning the names map, unsafe legacy role fold, partial matches, write order, awk range, main-only AC check.
- Whole-diff review found the one real gap (a done epic with no RETRO.md skipped by migrate, migrate.py:205 and :251); it became task migrate-retro-missing, landed round 0 (b1072ef), and the scope audit then found no gaps.
- Real run on main passed AC1-AC7: six migrate commits, five retro commits, buckets 1,2,3,5,8 now on history; dry run showed 98 tasks, 1 partial before writing.
- migrate-retro-missing, estimated from history after the migration, landed near its estimate: minutes 14 vs 13 (ratio 1.08), tokens 777962 vs 542616 (1.43), within 10 to 45 percent.
- Rulings were explicit: Q1 drop legacy roles and count the verifier as review, Q2 orchestrator runs the real migration; two tests changed with reasons (dry-run-only refusal check, test_all_includes_legacy_minutes) and one fixture moved.

## What went wrong or could improve

- Two implementers reported without a seen red run or an unfiltered summary line: minutes-to-points skipped the pytest red run (no pytest on default python3) and was only saved by the reviewer seeing the AttributeError; retro-records-once and migrate-this-repo tails rest on orchestrator checks.
- The discovery brief undercounted transcripts until the panel found the workflow dirs; the first design carried a wrong inventory and an unsafe role fold.
- The gap survived all 9 per-task reviews and the interrogate; it surfaced only at the whole-diff pass.
- Actual minutes were about a quarter of the seed expectation (95 vs 400) and tokens about 40 percent (10.0M vs 26.0M): MdAPE minutes 293.6%, tokens 340.7% against a pessimistic seed table, while MdAPE points was 0.0%.
- migrate-this-repo (5 pts, 0.06 tokens ratio) and retro-records-once (5 -> 3) were overestimated; two tasks re-pointed by -2. Orchestrator work and the five unmarked retro agents are not in migrate-this-repo's actuals, so its 7 min and 235990 tokens understate the real cost.
- Old legacy-formula minutes (5-8 min) make history buckets non-monotonic (1pt 13 min, 5pt 16 min) and the 13pt refit extrapolates tokens below the 8pt bucket, so calibration from history is skewed.

## Recommendations

- Code:
  - plugins/workbench/skills/start-development/scripts/migrate.py: the whole-number regex is repeated (declined at whole-diff review as style); share one compiled pattern.
  - Retro fill for the five old epics used a general-purpose agent following retro-writer.md, not the typed agent; no code defect, see Workflow.
- Delivered differently:
  - Legacy actual_roles were dropped and roles taken only from records (verifier counts as review), instead of mapping the old four-role taxonomy, because the old roles do not sum to `actual` in 2 tasks and any mapping is a guess (interrogate item 3, gate Q1).
  - Partial matches write actual_minutes only; tokens and roles stay empty unless records cover both impl and review (1 partial: epic-integration-worktrees/land-in-run review).
  - An added task, migrate-retro-missing, was not in the design: a done epic without RETRO.md now counts as changed.
- Tech debt:
  - History buckets hold legacy-formula minutes (scripts/ticket calibration data, docs/plans done epics): remove by recording real minutes where transcripts exist, or by excluding formula-derived actuals from calibration; the 13pt refit stays unreliable until then.
  - Transcript retention (about 30 days) is an unverified assumption; the real run is done, so only a future migration is bound by it.
  - migrate-this-repo actuals omit the orchestrator and five retro agents; no fix, accepted.
- Workflow:
  - recurring (housekeeping-rules-estimates, init-leaves-a-green-tree, template-update-skill-and-in): implementer verification is reported or accepted from weak evidence (tail reads, no seen red run, no unfiltered summary line). This epic: minutes-to-points skipped the red run, two tails taken from orchestrator checks. Change: epic-run's implementer prompt requires the red-run output and the unfiltered summary line in the report, and the reviewer reruns the check itself, rejecting a report without them.
  - Seed estimates: the seed table runs about 4x on minutes and 2.5x on tokens against this epic; once history buckets are cleaned, re-seed calibration.SEED from the closed-epic actuals and reduce the pessimism. No history yet for a re-seed; first signal only, not recurring.
  - Discovery briefs: count the real inventory (including workflow subagent dirs) before a design states it; add a discovery checklist line for data-source inventories. Single occurrence, not recurring.
  - Run the unmarked retro agents through the typed retro-writer (or mark them) so their cost reaches actuals.

## Delivery record (migrated)

### Asked

"Skill to add: migrate epics/tasks from old scheme to new one." Build `ticket.py migrate [<epic> | --all] [--dry-run]` and a thin `epic-migrate` skill (<= 45 lines) that rewrite old-scheme task files to the points scheme, fill actuals from legacy numbers and on-disk transcripts (never invented), and give every done epic a RETRO.md. Then migrate this repository's six done epics for real.

### Shipped

All 10 tasks built, 0 fix rounds. Epic review: pass (2026-10-25); one medium gap found and fixed by a tenth task (migrate-retro-missing); scope audit found no gaps or duplicates. Closed by `ticket.py close`: main fast-forwarded 6d6541a -> 0ee8cd3, integration and main verifies both green (`mise run test && mise run lint`; close.json). No MR. Real run on main: six `chore(ticket): <epic> migrate` commits (bd7f4fb, 74ed744, f33236d, 155e8dc, d8476ec, 2ace9ee) and five `chore(ticket): <epic> retro` commits (97e1b99, c3fd6dc, c153d13, 7d6d193, bc2c747); AC1-AC7 ok. Calibration buckets 1, 2, 3, 5, 8 now read from history, 13 from refit.

### Tasks

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

### Rulings

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

### Discovered and blocked

- Old actuals are low-quality: legacy formula minutes (5-8 min) make history buckets small and non-monotonic (1pt 13 min, 5pt 16 min), and the 13pt refit extrapolates tokens below the 8pt bucket (n=0). Data quality, not a defect of this epic. Nothing blocks; the user may re-bucket later.
- 1 partial match in the dry run (epic-integration-worktrees/land-in-run review): tokens/roles left empty for that task.
- Follow-up asked by the user, not done by this epic: install the plugin into /Users/szymonri/Documents/claude-code-tatara via the template-update engine after close (a peer session is active there). Who clears: the orchestrator, on the user's go; never pushed.
- Verified head of epic-migrate-skill and migrate-this-repo is the same SHA (3c5c5a5).

### Not pushed

Local main at 0ee8cd3 (plus the close and retro chore commits) is not pushed. The user pushes.

### Lessons routed to

- Implementers twice skipped or filtered away the red or summary line (minutes-to-points skipped the pytest red run): mechanical. Add a check that the implementer's `tests.red` and summary line come from `run-tests.sh` output; implementers were told to run tests through run-tests.sh. Edit the epic-run implementer brief only if a check cannot be written.
- The discovery brief undercounted transcripts (149 vs 1042) until the fable panel reviewer found the workflow dirs (887 under subagents/workflows/wf_*/): judgement call. Edit start-development discovery guidance to say inventories must use `find` over the whole projects dir, not top-level listing.
- Legacy-key and missing-RETRO.md cases were only caught by the whole-diff review: add a test fixture for "done epic without RETRO.md" (added in migrate-retro-missing) to the migrate fixtures.
