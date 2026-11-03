# hive-inactivity-limits: retro

There were two final reviews on 2026-11-03.

**Group O.** Review of agents-orchestrator PR #66 (head 624fc3b), with full findings in
`.superpowers/sdd/implementation-hive-inactivity-limits/final-review.md`.

**Groups W and H and the deploy.** A whole-scope review of the rest:

- agents-web PR #47 (merged f1003f8, released v0.18.0);
- agents-helmfile PR #90 (merged 508a2e1, applied);
- the live check, checked end to end against orchestrator origin/main d21da00 (v4.0.1).

Full findings: `.superpowers/sdd/implementation-hive-inactivity-limits/final-review-wh.md`.

Inputs to both reviews:

- the spec `docs/future/hive-inactivity-limits.md` (every Recommended option accepted);
- `docs/plans/hive-inactivity-limits/implementation.md`;
- the SDD ledger `.superpowers/sdd/implementation-hive-inactivity-limits/progress.md` (rulings I-R1
  to I-R4);
- the apply report `.scratchpad/hive-inactivity-limits/apply-508a2e1.md`.

## Verdict

**The epic is complete and live.** It runs as orchestrator v4.0.1 and web v0.18.0, from helmfile
508a2e1 (helm revisions 40 and 30), applied 2026-11-03 at 09:08Z. The only open item is F1, the
per-preset reminder values of 10 min on `-auto` presets and 55 min on the rest. It sits with the
superleader (mx-195) and needs no code.

**Group O.** The review found two blockers, and both were resolved before the merge:

- Critical, the migration collision: the migration was renamed to `0030_inactivity_limits.sql`
  (fix1 108aacd).
- Important, the major version: v4.0.0 was proposed and released, because removing a spec field
  is a breaking change.

Every Minor was fixed or ruled doc-only, except M3 (the pending self-close has no deadline). M3 is
a follow-up.

**Groups W and H.** No Critical findings. One Important finding:

- The inactivity banner and the issue line say "Closing for inactivity at <deadline>".
- But an idle session is discarded about 30 s after its notice turn ends, which is usually well
  before the deadline.
- The live run went at 341 s, about 40 s after the close request.
- So the UI overstates the time the user has to press Keep session.
- The plan dictated this text.

Eight Minor findings: four are wording or cosmetic, two are about missing live and pre-apply
evidence, and two are about fragile cross-repo contracts. Nothing is over-delivered.

| Requirement (spec decision) | Delivered | Where |
|---|---|---|
| Quiet clock of user-visible updates (1) | yes | `db/sessions.quiet_clock_sql`, relays `touch_update`; web quiet line |
| Settings default plus sparse `spec.inactivity` (2) | yes | `settings.py`, `spec.py`, `/meta`; web `PresetForm.tsx` two fields |
| `discard_after_idle_seconds` replaced, no alias (3) | yes | `0030_inactivity_limits.sql`, `spec.py`; web schema sync |
| Code defaults off; helmfile on (4) | yes | `settings.py`; helmfile `values/agents-orchestrator/common.yaml` 3600/14400/300 |
| One reminder per quiet period (5) | yes, live | `remind_inactive`; live: one notice at 131 s on a 120 s limit |
| Regular-lane close notice, handoff deadline, mid-turn discard (6) | yes; only the idle path seen live | `close_inactive`, `close_overdue`, `discard_idle`; web banner |
| Only the user extends (7); inbound message cancels (10) | yes, not exercised live | `cancel_close`, `release_inactive_close`; web Keep session unchanged |
| Superleaders exempt (8) | yes | `_LIMITED`, `inactivity.effective`; the web form still shows the fields (Minor) |
| Audit columns in view, stream, export, web (9) | yes | `schemas.py`, `views.py`, `export.py`; web notice line, queue label, banner |
| Follow-up branch, new migration (11) | yes, 0030 | applied once by the ingester init on deploy |

## What came up during implementation

### Group O

- The migration number was re-checked at O8, and #65 took 0029 one minute later.
  - The ledger entry "Migration stays 0029 (#65 holds 0028)" was written at 00:55Z.
  - #65's dae03f9, which adds its own 0029, was committed at 00:54:46Z and pushed around then.
  - A one-shot check before opening the PR cannot catch a sibling that is moving at the same time.
  - The final review caught it by reproducing the primary-key failure on a fresh database, and
    fix1 renamed the file to 0030.
- Removing a spec field became a major release.
  - The commit was titled `feat(spec)!`, and `scripts/next_version.py` turns any `!` into a major
    bump.
  - So #66 released v4.0.0, and #67 then made it v4.0.1.
  - Every version the plan named was wrong: it expected v3.6.0, then v3.8.0 for the orchestrator,
    and v0.16.0 for the web.
- The epic had to merge main twice: #65 (seven conflicting files) and #61.
  - #61 made `spec.inactivity` an ordinary editable field for a superleader. On a privileged
    preset, changing it is refused as `privileged_target`.
  - Ruling I-R4 settled which of the two epics dropped `discard_after_idle_seconds`.
- O5 found that the old `discard_idle` never ran real per-session transactions.
  - The pool connection is not autocommit, so each `conn.transaction()` was a savepoint of an
    implicit transaction, and every lock and flip lasted until the pool block ended.
  - The `_sweep_each` refactor fixed this for all steps.
  - This was a latent pre-existing bug that the spec did not know about.
- Message ordering under the row lock needed an id-based cancel clause.
  - A message whose transaction began before the close carries an earlier `created_at` (its
    `now()`) but a later id.
  - The spec's "created after the close request" alone would have missed it.
  - The fix depends on `enqueue_message` being the only insert path and on the CACHE 1 sequence.
    That invariant is now load-bearing and documented only in MEMORY.md.
- Review Minors were carried task to task and closed (O5 to O6 to O7 to O8), and none was
  dropped:
  - status guards on every act UPDATE;
  - per-step try/except, so one failing step no longer starves `discard_idle`;
  - a kind-aware discard log line;
  - the touch-failure log being asserted in tests.
- Two semantics the spec did not settle were decided in documentation:
  - `last_update_at` means two different things: the stored stamp in the export, the computed
    clock in the view.
  - `reminder_at` stays set after the reminder fires.
- The user changed the reminder values late: 10 min for `-auto` presets and 55 min for the rest.
  - That changed the reminder wording ("at least every <N>" instead of "hourly").
  - It also added task F1.

### Groups W and H and the deploy

- **A hive died mid-epic.** tatara-0 died during the merge phase; tatara-1 drove #66 to its merge.
  - The ledger and the per-task brief, report and review files were enough to resume. Nothing was
    redone.
  - There is a gap of about three hours in the ledger (02:46Z to 05:35Z), while #66 waited for #61.
  - The superleader address also changed during the epic (mx-99, then mx-195).
- **The schema sync pulled in a neighbour's change.** The W1 sync from c3ae718 brought in #65's
  message attachments.
  - openapi-typescript turns a field with a server default into a required input field.
  - So `PostMessage.attachments` became required and `tsc -b` broke in code W1 never touched.
  - W1 fixed it with a local `Omit` override in `client.ts`. That fix is correct, but it is manual
    and will be needed again for the next defaulted input field.
- **Notices are matched by text prefix.** The web recognises notices in the chat log by text
  prefix, because the chat log comes from wrapper events that carry no `notice` field.
  - This works, and it also catches a notice typed into a running turn, because the wrapper's
    message marker goes at the end of the paste.
  - But the contract is two comments in two repos, with no test across them.
- **Releases and the apply hit transient failures.**
  - Harbor answered 403 from nginx on the images login of the v4.0.1 release job. Re-running the
    failed jobs passed.
  - During the apply, `helmfile diff` and the helmfile step of `mise run apply` both failed with
    "gpg: public key decryption failed: Cannot allocate memory" on `regcred.pre.secrets.yaml`.
    Nothing was applied, and re-running only the helmfile step passed.
  - None of these failures had anything to do with the code.
- **Three changes shipped as one roll.** H1, H2 and the v4.0.1 pin bump went into one helmfile PR
  (#90). Web 0.18.0 needs the api's `/meta.inactivity`, so shipping them together was correct and
  avoided two extra rolls.
- **The live check passed, with gaps.** The run used a 120 s reminder and a 300 s close:
  reminder at 130 s, close notice and `close_kind` at 301 s, deleting at 341 s. The gaps:
  - The close happened by the idle path, so `close_overdue` ("deadline passed") never ran live.
  - Keep session and the inbound-message cancel were not tried.
  - Run 1's jq for the notice was wrong: the messages endpoint returns a bare array.
- **One pre-apply check was not recorded.** The group O review asked for a check before the apply
  that no stored spec still had `discard_after_idle_seconds`. Neither the apply report nor the
  logs record it. There were no errors after the roll, but the check was skipped silently.
- **The usual friction appeared again:**
  - the full helmfile suite takes 12 to 14 min and the full vitest run 2.5 to 4 min, longer than
    tool timeouts, so runs went to the background;
  - fakepg needs `orch_template` dropped between pytest runs;
  - the known pod-only lightkube failure is still re-explained in every report.

## What was overlooked in discovery and planning

- **Migration numbering was treated as a single check, not as a reservation.**
  - The plan even said "0028 is reserved" for an epic that never used it.
  - Meanwhile #65 claimed 0028 and 0029 without coordinating.
  - The same number contest was reported in the hive-self-close retro.
- **The release-version effect of a breaking-change subject was not modelled.**
  - The plan required removing the field with no alias, which is breaking by definition.
  - It still promised "next free minor", and it hard-coded version numbers that were all stale by
    merge time.
- **The web text for the hard limit was specified from the deadline alone.** The plan's W2 line
  ("Closing for inactivity at {HH:MMZ of close_deadline_at}") ignored that spec 3.4 discards an
  idle session at turn end plus grace. As a result, the user-facing Keep session window is
  misstated (Important I1).
- **The live check did not force each path it asked to see.**
  - It asked for the "deadline passed" log line but let the session go idle.
  - Seeing that line needs a session kept busy past the handoff window, for example a start
    prompt that runs a long tool call.
  - Keep session and the inbound-message cancel had no live step.
- **Review-mandated pre-apply checks were not carried into the apply brief.** The M1 check lived
  in a retro recommendation and a ledger note, not in the task the apply agent received.
- **Schema-sync side effects were not planned.**
  - Syncing a web schema from a newer orchestrator brings in every API change since the last sync,
    not just this epic's.
  - The generator's defaults-as-required behaviour was not known.
- **Self-close was left as it was, and that leaves a gap:** a pending self-close suspends both
  limits.
  - A leader that self-closes but never becomes idle holds its pods indefinitely with no deadline.
  - This is the same "closing but blocked" blind spot the hive-self-close retro named.
- **Changing a setting can invalidate stored presets, and nobody checked this.**
  - `validate_spec` compares a preset's reminder against the current setting for close.
  - Lowering `ORCH_INACTIVITY_CLOSE_SECONDS` later would make session creation from such presets
    fail with 422.
  - With F1's per-preset reminders (600 s and 3300 s), the close setting must stay above 3300 s.
- **PRs that edit the same files were not mapped.** #65 and #61 both touched files this epic
  edited, which caused a seven-file merge and a second merge of main.
- **The lock cost of the migration was not in the Risks section.** The migration validates a
  CHECK on `messages` in place on live data. In practice the apply showed no trouble.
- **Leader loss was not part of the plan.** Recovery worked only because the ledger was kept up
  to date.

## Recommendations

1. **Fix the Important finding with a small web PR.**
   - Word the inactivity banner and issue line as an upper bound: "Closing for inactivity when
     idle, by 14:05Z at the latest" and "closing for inactivity, by 14:05Z".
   - In the same pass, correct the helmfile comment at `values/agents-orchestrator/common.yaml:108`
     from "no activity" to "no user-visible update".
   - A plan that writes UI text for a timed, destructive action should derive that text from
     every path that can trigger it.
2. **Stop contested migration numbers at the source** (open from the group O review). Do one of
   these:
   - Reserve numbers in a tracked file that merges at once.
   - Or add an agents-orchestrator CI check that fails when two files share a version prefix, and
     run it on the merged result.

   Today a collision between two open PRs passes both PRs' CI and git.
3. **Make versions and pre-apply checks evidence, not memory.**
   - Plans should say "the version `scripts/next_version.py` prints on the merge with main", never
     a number. Any spec that removes a field should state "major" up front.
   - Every check a review asks for before an apply should go into the apply brief as a checklist
     item, with its command output saved under `.logs/<name>/`.
4. **Make the live check a tested, committed smoke step that forces each path.** It should cover:
   - the reminder notice, asserted on the bare-array messages list;
   - a busy session that is still running at the deadline, which must log "deadline passed";
   - Keep session during the window;
   - an inbound message during the window.
5. **Close the self-close gap in a follow-up** (open from the group O review).
   - Give a pending self-close a deadline, for example `close_deadline_at` set to the request plus
     the handoff window, or a separate cap. Then no close request can hold pods forever.
   - Pair it with the web "why is it not closing" hint that the hive-self-close retro asked for.
6. **Replace the text-prefix contract for notices.**
   - Either the wrapper echoes the turn metadata (`orch_message_id`) on `user_message`, or the
     ingester tags events by message id.
   - Then the web reads `MessageView.notice`. Until then, add a test on the orchestrator side that
     pins both prefixes as a published contract.
7. **Fix the generated web types once.** Configure openapi-typescript so that fields with a server
   default stay optional in request bodies (check its `defaultNonNullable` option), or split
   request types from response types. Then a schema sync stops breaking `tsc` on defaulted fields.
8. **Harden the release and apply wrappers against known transient failures.**
   - The release watcher re-runs a failed images job once when the failure is a Harbor 403 or 401
     at login, and reports it.
   - The apply wrapper retries the helmfile step once on the gpg "Cannot allocate memory" error,
     without re-running the 12 min test suite.
   - Separately, find out why gpg runs out of memory in agent pods.
9. **Guard F1 against settings drift.** Run `presets_check` after every `ORCH_INACTIVITY_*`
   change, and record in the helmfile values comment that the close setting must stay above the
   largest per-preset reminder (3300 s).
10. **Carried from earlier retros:**
    - Make the fakepg recipe drop `orch_template` itself.
    - Fix `test_lightkube_default_client_uses_env_config` for agent pods.
    - Keep the per-task ledger, which is what made the tatara-0 to tatara-1 handover lossless, and
      have the leader that takes over write a ledger line that names the handover.
