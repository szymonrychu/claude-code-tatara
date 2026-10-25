# Epic and task migration skill retro

<!-- retro:generated:begin -->
## Tasks

Delivery order; written by `ticket.py retro`.

| Task | Points (estimate) | Points (post-delivery) | Minutes (expected) | Minutes (actual) | Tokens (expected) | Tokens (actual) |
|---|---|---|---|---|---|---|
| Legacy transcript matcher | 3 | 3 | 34 | 3 | 2250000 | 463178 |
| Minutes to points | 1 | 1 | 11 | 2 | 750000 | 183209 |
| Retro writer record input | 2 | 2 | 23 | 8 | 1500000 | 227807 |
| Retro records once | 5 | 3 | 57 | 14 | 3750000 | 794503 |
| Migrate dry run | 8 | 8 | 91 | 11 | 6000000 | 3197775 |
| Migrate command | 5 | 5 | 57 | 15 | 3750000 | 3344971 |
| Deltas legacy retired | 2 | 2 | 23 | 12 | 1500000 | 546295 |
| Epic migrate skill | 3 | 3 | 34 | 9 | 2250000 | 273135 |
| Migrate this repo | 5 | 3 | 57 | 7 | 3750000 | 235990 |
| Migrate retro missing | 2 | 2 | 13 | 14 | 542616 | 777962 |
| Total | 36 | 32 | 400 | 95 | 26042616 | 10044825 |

## Deltas

| Task | Points (post-delivery - estimate) | Minutes (actual / expected) | Tokens (actual / expected) |
|---|---|---|---|
| Legacy transcript matcher | 0 | 0.09 | 0.21 |
| Minutes to points | 0 | 0.18 | 0.24 |
| Retro writer record input | 0 | 0.35 | 0.15 |
| Retro records once | -2 | 0.25 | 0.21 |
| Migrate dry run | 0 | 0.12 | 0.53 |
| Migrate command | 0 | 0.26 | 0.89 |
| Deltas legacy retired | 0 | 0.52 | 0.36 |
| Epic migrate skill | 0 | 0.26 | 0.12 |
| Migrate this repo | -2 | 0.12 | 0.06 |
| Migrate retro missing | 0 | 1.08 | 1.43 |

- MdAPE points: 0.0%
- MdAPE minutes: 293.6%
- MdAPE tokens: 340.7%
<!-- retro:generated:end -->

## Retro

| Went well | Went bad / could be improved |
|---|---|
| All 10 tasks closed in review round 0, no escalation, each with a quoted tail (e.g. migrate-command: start-development 408 passed, lint clean). | Two implementers reported without a seen red run or an unfiltered summary line: minutes-to-points skipped the pytest red run (no pytest on default python3) and was only saved by the reviewer seeing the AttributeError; retro-records-once and migrate-this-repo tails rest on orchestrator checks. |
| The design interrogate (fable, opus, sonnet) caught 7 act-on items before any code: real transcript inventory (1042 agent files, 887 under workflow dirs), `branch: HEAD` poisoning the names map, unsafe legacy role fold, partial matches, write order, awk range, main-only AC check. | The discovery brief undercounted transcripts until the panel found the workflow dirs; the first design carried a wrong inventory and an unsafe role fold. |
| Whole-diff review found the one real gap (a done epic with no RETRO.md skipped by migrate, migrate.py:205 and :251); it became task migrate-retro-missing, landed round 0 (b1072ef), and the scope audit then found no gaps. | The gap survived all 9 per-task reviews and the interrogate; it surfaced only at the whole-diff pass. |
| Real run on main passed AC1-AC7: six migrate commits, five retro commits, buckets 1,2,3,5,8 now on history; dry run showed 98 tasks, 1 partial before writing. | Actual minutes were about a quarter of the seed expectation (95 vs 400) and tokens about 40 percent (10.0M vs 26.0M): MdAPE minutes 293.6%, tokens 340.7% against a pessimistic seed table, while MdAPE points was 0.0%. |
| migrate-retro-missing, estimated from history after the migration, landed near its estimate: minutes 14 vs 13 (ratio 1.08), tokens 777962 vs 542616 (1.43), within 10 to 45 percent. | migrate-this-repo (5 pts, 0.06 tokens ratio) and retro-records-once (5 -> 3) were overestimated; two tasks re-pointed by -2. Orchestrator work and the five unmarked retro agents are not in migrate-this-repo's actuals, so its 7 min and 235990 tokens understate the real cost. |
| Rulings were explicit: Q1 drop legacy roles and count the verifier as review, Q2 orchestrator runs the real migration; two tests changed with reasons (dry-run-only refusal check, test_all_includes_legacy_minutes) and one fixture moved. | Old legacy-formula minutes (5-8 min) make history buckets non-monotonic (1pt 13 min, 5pt 16 min) and the 13pt refit extrapolates tokens below the 8pt bucket, so calibration from history is skewed. |

## Improvements

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
