---
name: interrogate
description: One-pass adversarial review by a panel of three models (fable, opus, sonnet) plus a lead verdict that sorts every finding into act on, consider, noted, or dismissed. Use for a contested design, a high-risk diff (authz, secrets, concurrency, rules engines, data migrations), or a task plan-execute escalated - instead of another review->fix round. Never auto-applies anything.
---

# interrogate

Ported from pstack's `interrogate`. The signal comes from model diversity, not
from assigned personas: every reviewer gets the same prompt, and a finding two
models raise independently is worth more than anything one model raises alone.

One pass. The panel reviews once, you judge once, and the verdict is the
deliverable. It is not a loop, which is the point: a review->fix loop spends
tokens re-arguing, and a panel verdict ends the argument.

## When to use it

- The design doc and plan doc are contested or high-risk: run the panel
  before the gate and put the verdict in the gate message.
- A design is contested, or two viable shapes remain at the gate.
- The diff touches authz, secrets, concurrency, a rules engine, or a data
  migration - where the costly bugs are reasoning bugs a green suite misses.
- `workbench:plan-execute` returned a task in `escalated`. One panel verdict
  replaces another fix round.
- An epic review (phase 5 of `workbench:start-development`) that covers
  `panel` tier tasks: the panel replaces `start-review --single` there.

Not for routine diffs: the per-task review in `plan-execute` covers those.

## 1. Scope

Name exactly what is reviewed: a diff range (`git diff main...HEAD` in the
worktree), a file list, or a design doc. Pass paths, never pasted contents.

## 2. Intent

Write one paragraph: what the change is for, and the acceptance conditions it
must meet (the plan requirement, verbatim, when there is one). If you cannot
state the intent, the review cannot judge against it - ask first.

## 3. Panel

Dispatch three `panel-reviewer` agents in ONE message, in the background, one
per model, each with `model` set explicitly:

| Reviewer | model |
|---|---|
| A | `fable` |
| B | `opus` |
| C | `sonnet` |

Every reviewer gets the identical prompt: the intent paragraph, the scope
paths, the worktree path, and the discovery brief path when one exists. Cap
each report at 400 words.

## 4. Synthesize

- Merge duplicates: different models describe one issue differently. Record
  which models raised each.
- Findings raised by 2 or more reviewers independently are highest signal.
- A lone-model finding is still read, and weighted accordingly.
- Where one model flags something and another explicitly clears it, note the
  disagreement; it is information for the verdict.

## 5. Lead judgment

You are the lead, a pragmatic senior engineer, not a vote counter. Verify any
finding you would act on against the code yourself before it goes in Act on.

## Verdict

### Act on
Real problems for correctness, security, or the stated requirement. These
block. For each: the finding, which models raised it, why it matters.

### Consider
Legitimate, but the cost of addressing it may not pay. The tradeoff, stated.

### Noted
Valid and not actionable now. One line each.

### Dismissed
Wrong, nitpicking, or missing context. One line of why each.

Then an agreement line: where the models converged and where they split.

## After the verdict

Never auto-apply. Act on items go to an implementer as a sharpened requirement
(a new `workbench:plan-execute` run, or a single agent on the lean path).
Consider items that change scope or product behaviour go to the user.
Everything else is recorded and closed. The panel does not run again on the
same change unless the change itself is materially rewritten.
