# Paste .env contents into the preset env editor retro

<!-- retro:generated:begin -->
## Tasks

Delivery order; written by `ticket.py retro`.

| Task | Points (estimate) | Points (post-delivery) | Minutes (expected) | Minutes (actual) | Tokens (expected) | Tokens (actual) |
|---|---|---|---|---|---|---|
| dotenv parser module | 2 | 2 | 6 | 1 | 559738 | 147955 |
| Paste .env control in the preset form | 3 | 3 | 7 | 3 | 996161 | 458846 |
| Total | 5 | 5 | 13 | 4 | 1555899 | 606801 |

## Deltas

| Task | Points (post-delivery - estimate) | Minutes (actual / expected) | Tokens (actual / expected) |
|---|---|---|---|
| dotenv parser module | 0 | 0.17 | 0.26 |
| Paste .env control in the preset form | 0 | 0.43 | 0.46 |

- MdAPE points: 0.0%
- MdAPE minutes: 316.7%
- MdAPE tokens: 197.7%
<!-- retro:generated:end -->

## Retro

| Went well | Went bad / could be improved |
|---|---|
| dotenv-parser-module closed in 1 review round, 9 tests passed, lint clean. | paste-env-control-in-the-pre needed 2 rounds: fix round 1 added pin tests (first-duplicate replace, paste marks env set) that the first pass missed; final 43 passed. |
| Builder check raised 6 edge cases, all settled up front as rulings in the task bodies; reviewer then caught the two unpinned rules. | Minutes and tokens far under the seed (minutes 4 vs 13, MdAPE 316.7%; tokens 606801 vs 1555899, MdAPE 197.7%); points MdAPE 0.0%. |
| Delivered and deployed in one session: agents-web PR #14 (9302d1d), agents-helmfile PR #29 (d6fa24a), suite 422 passed, scope audit all landed. | One implementer hand-back said only "placeholder" and had to be re-requested. |
| | ticket.py amend lints the whole epic, so two tasks with a bad AC format could not be amended one at a time; the orchestrator wrote the sections directly. |
| | macOS has no `timeout`: the first CI watcher exited 127. |
| | The orchestrator .venv had a stale pytest shebang from the old directory name (agent-orchestrator); `mise run test` failed with import errors until the venv was recreated. |

## Improvements

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
