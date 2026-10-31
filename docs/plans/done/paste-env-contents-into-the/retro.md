# Paste .env contents into the preset env editor retro

## Review

Migrated from the epic format.

## What went well

- dotenv-parser-module closed in 1 review round, 9 tests passed, lint clean.
- Builder check raised 6 edge cases, all settled up front as rulings in the task bodies; reviewer then caught the two unpinned rules.
- Delivered and deployed in one session: agents-web PR #14 (9302d1d), agents-helmfile PR #29 (d6fa24a), suite 422 passed, scope audit all landed.

## What went wrong or could improve

- paste-env-control-in-the-pre needed 2 rounds: fix round 1 added pin tests (first-duplicate replace, paste marks env set) that the first pass missed; final 43 passed.
- Minutes and tokens far under the seed (minutes 4 vs 13, MdAPE 316.7%; tokens 606801 vs 1555899, MdAPE 197.7%); points MdAPE 0.0%.
- One implementer hand-back said only "placeholder" and had to be re-requested.
- ticket.py amend lints the whole epic, so two tasks with a bad AC format could not be amended one at a time; the orchestrator wrote the sections directly.
- macOS has no `timeout`: the first CI watcher exited 127.
- The orchestrator .venv had a stale pytest shebang from the old directory name (agent-orchestrator); `mise run test` failed with import errors until the venv was recreated.

## Recommendations

- Code:
  - agents-web src/sessions/dotenv.ts: `KEY= # c` gives empty value and unknown double-quote escapes are kept literally (rulings); keep parser tests pinning both.
  - agents-web PresetForm: stale paste error text persists until the next Apply (dropped); clear it on text change.
- Delivered differently:
  - none
- Tech debt:
  - Stale paste error text in PresetForm (agents-web): remove by clearing the error on textbox change.
- Workflow:
  - recurring (matrix-read-receipts): a rule not pinned by a test was found only in review (id tiebreak there; first-duplicate replace and paste marks env set here). Change: task template requires each merge-semantics or tiebreak ruling in Notes to name a pin test, and the implementer brief lists them.
  - recurring (agents-matrix-connector-depl, agents-schedule-deploy, agents-matrix-connector): flat seeds far off actuals; here minutes and tokens came in at 0.17-0.46x. Change: calibrate minutes and tokens seeds from earlier epics' actuals by task kind (small pure-module and UI tasks lower).
  - epic-run should reject a hand-back with no verify output and no head sha before review (one-off here, already routed in record.md).
  - ticket.py amend should lint only the amended task, not the whole epic (one-off, Retro table only).

## Delivery record (migrated)

### Asked

A "Paste .env" textbox in the agents-web preset form env editor that fills env rows from pasted .env text. A pure dotenv parser module plus a toggleable textbox with Apply/Cancel in PresetForm, merging into existing rows and reusing their validation. A paste with any unparseable line applies nothing and shows the line numbers.

### Shipped

parseDotenv (src/sessions/dotenv.ts) and the Paste .env control in PresetForm. Epic review verdict: pass (HEAD 314b6bf, base d8769b1); full suite 422 passed, lint clean; whole-diff review no findings; scope audit all landed.
- agents-web PR https://github.com/szymonrychu/agents-web/pull/14 merged as 9302d1d.
- Deploy: agents-helmfile PR https://github.com/szymonrychu/agents-helmfile/pull/29 merged as d6fa24a, applied; helmfile tests 187 passed, rollout OK, image agents-web:9302d1d.

### Tasks

| task | status | verified head | review rounds | verification tail |
|---|---|---|---|---|
| dotenv-parser-module | done | 99ef9225a93b31c27ce30887eb7535c9d73eeffc | 1 (clean) | Tests 9 passed (9); lint clean |
| paste-env-control-in-the-pre | done | 314b6bf05cbf0eb84c9ab3ad1fded0bd203cc6e4 | 2 (fix round 1 added pin tests: first-duplicate replace, paste marks env set) | Tests 43 passed (43) |

Both verified heads appear in the agents-web epic history. Files and notes agree.

### Rulings

- Dotenv subset rules (my call): `KEY= # c` gives an empty value; unknown escape in double quotes kept literally. Why: common dotenv behaviour, fixed in the task. Cost if wrong: a pasted value with such text differs from the user's intent; one-line parser change.
- Merge semantics (my call): replace existing key in place, append new keys in order, drop empty rows, keep secret-looking or reserved keys flagged by envKeyError, duplicate existing rows replace the first match only, no-pair Apply changes nothing. Why: reuse existing validation, no silent drops. Cost if wrong: surprising merge result; small PresetForm change.
- Builder check raised 6 minor edge cases, all settled as (my call) in the task bodies. Cost if wrong: minor UX differences.
- Dropped: stale paste error text until next Apply (UX nicety, not required). Cost: stale message may briefly mislead.

### Discovered and blocked

none. Process note: one implementer hand-back was an empty "placeholder" report and was re-requested.

### Not pushed

agents-web: nothing (main equals origin/main). Meta repo main is ahead of origin/main by at least 10 commits (ticket moves, submodule pointer advances, up to 0f6adc3); the user pushes.

### Lessons routed to

- Empty or placeholder implementer hand-back: add a check in epic-run that rejects a hand-back with no verify output and no head sha before review (mechanical).
- Missing pin tests found only in review (first-duplicate, env marked set): judgement call; edit the task template so merge-semantics rulings in Notes each name a pin test.
