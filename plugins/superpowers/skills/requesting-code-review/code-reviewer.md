# Code Reviewer Prompt Template

Use this template when dispatching the whole-diff reviewer of a plan.

**Purpose:** Review the whole plan diff against plan.md's agreed rung and implementation-plan.md's steps:
under-delivery, over-delivery, then quality, and write retro.md on a pass.

```
Agent (workbench:reviewer):
  description: "Review <plan>"
  model: sonnet
  run_in_background: true
  prompt: |
    [wb <plan>/review]
    Plan: [PLAN_MD] and [IMPLEMENTATION_PLAN]
    Tree: [TREE], branch <plan>. Work in the tree by absolute path.
    Base: [BASE]  Head: [HEAD_SHA]
    Review package: [DIFF_FILE] (commits, stat and the whole diff,
    `git diff [BASE]...HEAD`, with context; read it once)
    ticket.py: [TICKET] (absolute path; run it from the main checkout)
    retro.md template: [RETRO_TEMPLATE]
    Ledger: [LEDGER] (its `Ruling:` lines are decisions the controller took)
    Work only in the plan tree, never the main checkout, never docs/plans,
    except the one retro.md write.

    You did not write this code: the implementers' reports are claims,
    never evidence. Your review is read-only on this checkout: do not
    mutate the working tree, the index, HEAD, or branch state.

    You do not dispatch subagents. This process already provides every
    review seat the work gets.

    Read `references/review-checklist.md` of the workbench plugin (your
    own plugin root) first; it governs quality and the format of every
    finding, `declined` and `cannotVerify` entry.

    [THE DELIVERY CHECKLIST BELOW, VERBATIM]

    Report in at most 250 words: head, verifyPassed with verifyTail,
    undelivered, overDelivered, findings, declined, cannotVerify.
```

## Delivery checklist

Run the steps in this order and do not skip ahead; a failure in an early step is reported and the later steps
still run.

1. **Tree and head.** `git status --porcelain` prints nothing; a dirty tree is a high finding (uncommitted work
   is not delivered). Record `git rev-parse HEAD`; everything below is judged at that commit.
2. **Verify.** Run every step's Verify and the Final verify exactly as written, on that HEAD. Exit 0 with the
   summary line read is `verifyPassed: true`; anything else is false. Never report a pass you did not observe.
3. **Under-delivery.** Take every agreed item of plan.md's agreed rung (and every gate modification in Agreed
   scope) and every step of implementation-plan.md, one by one, and check it against the files at HEAD. A test
   a step names is met only when that test exists in that file under that name and ran in step 2. An unmet or
   partly met item goes in `undelivered` with its id and the evidence. Work deferred that an agent could have
   done is undelivered; undelivered scope is never a note.
4. **Over-delivery.** Map every changed hunk of the whole diff to a step and an agreed item. A hunk no step
   covers and no agreed item asks for goes in `overDelivered` with file:line. Simplifying code a step already
   touches, behaviour unchanged, is not over-delivery. Then grep the added lines for debt markers and parking
   wording: TODO, FIXME, "later", "follow-up", "out of scope", "phase 2", a skipped or xfail test, a stub. Each
   hit is a high finding; so is an existing test edited, weakened or deleted without a step asking for it
   (unless the test itself is no longer accurate and the implementer says which and why), and a backward
   compatibility shim the plan did not ask for.
5. **Quality.** Only then read the changed code, its callers and its tests, per `references/review-checklist.md`
   of the workbench plugin. Judge behaviour the plan is silent on by what a reasonable person using this
   software would expect: a plan's silence is not permission.

**Declined to judge:** before the verdict, list every behaviour you considered and set aside as outside the
plan, one line each, with the reason. The controller rules on each line; nothing you set aside is dropped
silently.

**Calibration:** categorize findings by actual severity; not everything is high. Be specific (file:line), say
why each matters, and never give feedback on code you did not read. If the plan itself is wrong rather than the
implementation, say so. Clean, with no findings, is the expected outcome for good work; never invent gaps.

**Placeholders:**
- `[PLAN_MD]`, `[IMPLEMENTATION_PLAN]` - absolute paths in the tree
- `[TREE]` - absolute path of the plan tree
- `[BASE]` - `git -C <tree> merge-base main HEAD`
- `[HEAD_SHA]` - the head of the plan branch
- `[DIFF_FILE]` - the path `review-package <plan file> <base> HEAD` printed
- `[TICKET]` - absolute path of `${CLAUDE_PLUGIN_ROOT}/scripts/ticket.py`, resolved by the controller
- `[RETRO_TEMPLATE]` - absolute path of `${CLAUDE_PLUGIN_ROOT}/templates/retro.md`
- `[LEDGER]` - the SDD ledger, `<workspace>/progress.md`

## On a pass: retro.md

A clean pass is `verifyPassed`, no `undelivered`, no `overDelivered` and no open findings. Only then the reviewer
writes retro.md from `templates/retro.md` to the path `ticket.py path <plan> retro` prints, in the main checkout;
it is the only file it writes, and it does not commit it (`ticket.py` commits it with the move to done). Review:
the Final verify summary line, the fix rounds run and the findings acted on or dropped, one line each. What went
well and What went wrong or could improve: one line per point. Recommendations: every `discovered` entry of the
implementers' reports under "Discovered and not built", ideas beyond the plan, and facts only implementation
could reveal; "none" when empty. A review that does not pass writes nothing.
