# markdown rendering in chat retro

<!-- retro:generated:begin -->
## Tasks

Delivery order; written by `ticket.py retro`.

| Task | Points (estimate) | Points (post-delivery) | Minutes (expected) | Minutes (actual) | Tokens (expected) | Tokens (actual) |
|---|---|---|---|---|---|---|
| chat markdown renderer | 5 | 5 | 11 | 8 | 1858483 | 1454781 |
| chat rows render markdown | 3 | 3 | 6 | 4 | 963314 | 452225 |
| Total | 8 | 8 | 17 | 12 | 2821797 | 1907006 |

## Deltas

| Task | Points (post-delivery - estimate) | Minutes (actual / expected) | Tokens (actual / expected) |
|---|---|---|---|
| chat markdown renderer | 0 | 0.73 | 0.78 |
| chat rows render markdown | 0 | 0.67 | 0.47 |

- MdAPE points: 0.0%
- MdAPE minutes: 43.8%
- MdAPE tokens: 70.4%
<!-- retro:generated:end -->

## Retro

| Went well | Went bad / could be improved |
|---|---|
| Both tasks (chat markdown renderer, chat rows render markdown) closed in one review round: zero fix rounds, zero escalations. | One unnamed vitest failure on the whole-epic reviewer's first full run (1 failed, 523 passed); two reruns and the orchestrator's run were green and it was treated as a load flake, but the failing test name and cause were not captured, so it can neither be fixed nor ruled out. |
| Points held: 8 estimated, 8 post-delivery, MdAPE 0.0%. | Minutes and tokens came in under the seed on both tasks (12 actual vs 17 expected minutes; 1907006 vs 2821797 tokens); MdAPE minutes 43.8%, tokens 70.4%. chat rows render markdown ran 0.47x tokens, so the seed was loose, not tight. |
| Whole-epic review (sonnet) clean: XSS paths (raw HTML, links, images, code), row kinds, overflow and frame parsing checked. | A reviewer misread its own malformed `tail` output as a failure and reran the verify, wasting a run. |
| Scope audit: complete, no gaps, no duplicates. Security researcher skipped with a stated reason (no secrets, RBAC, ingress, privilege, CI vars or image pins in the diff; XSS covered by the reviewer). | The bundle-size delta was measured through an uncommitted temporary import, so the figure cannot be reproduced from the tree; its value is unknown here. |
| Full suite on the orchestrator run: `Test Files  45 passed (45)`, `Tests  524 passed (524)`, lint clean (.logs/md-web-full.log). Epic closed in about an hour of wall clock. | |

## Improvements

- Code:
  - agents-web chat markdown renderer: the epic left no committed test or script that measures its bundle cost; add a bundle-size check (or record the measurement command in MEMORY.md) so the delta is reproducible.
  - agents-web vitest suite: one test is flaky under load (name unknown); once a failure is captured, fix its timing dependence.
- Delivered differently:
  - none
- Tech debt:
  - Bundle-size delta for the markdown renderer rests on an uncommitted temporary import, not on anything in the tree; a committed size budget check would remove it.
  - Unidentified vitest load flake in agents-web, closed as a flake without a name; a captured failing test name would remove it.
- Workflow:
  - recurring (file-download-in-file-browse, paste-env-contents-into-the): minutes and tokens seeds are off for small tasks; there small pure-module and UI tasks came in at 0.17-0.46x and six of seven tasks at 0.55-0.82x minutes, here both tasks came in at 0.67-0.73x minutes and 0.47-0.78x tokens. Change: calibrate minutes and tokens seeds by task kind from earlier epics' actuals (small UI and pure-module tasks lower).
  - Reviewers should capture the failing test name and the output tail when a first full run fails, and rerun only after saving it; add a line to the reviewer brief (one-off, Retro table only).
  - A reviewer misread malformed `tail` output as a failure (one-off, Retro table only).
