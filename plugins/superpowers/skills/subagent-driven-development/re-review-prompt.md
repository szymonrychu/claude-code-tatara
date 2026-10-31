# Fix-Round Re-Review Prompt Template

Use this template after a fix round: it continues the SAME `workbench:reviewer` that ran the whole-diff review,
with SendMessage, so the reviewer keeps its own context. It is the only re-review a round gets, and there are at
most two rounds.

**Purpose:** verdict each finding of the previous pass, and run the review again on the new HEAD.

```
SendMessage to [REVIEWER_AGENT_ID] (workbench:reviewer, model: sonnet, set
at dispatch and unchanged for the round):
  [wb <plan>/review]
  Fix round [R] of 2. The implementer worked on these findings:

  [FINDINGS, verbatim, one per bullet]

  Fix base: [FIX_BASE_SHA] (the head your previous pass saw)
  Head: [HEAD_SHA]
  Fix diff: [DIFF_FILE] (commits, stat and the diff with context; read it
  once)
  Whole diff: `git diff [BASE]...HEAD` in [TREE]

  Your review is read-only on this checkout: do not mutate the working tree,
  the index, HEAD, or branch state.

  1. Verdict every finding, in order: ADDRESSED or NOT ADDRESSED, with
     file:line evidence. "Attempted" is not addressed: the specific defect
     must no longer exist.
  2. New breakage the fix itself introduced, with severity and file:line;
     "none" if clean.
  3. Then run all your steps again on the new HEAD: clean tree, every
     step's Verify and the Final verify, under-delivery, over-delivery,
     debt markers, quality. A finding is closed only by the files.

  On a clean pass write retro.md, as in your first pass, and nothing else.
  Report in at most 250 words, in the same shape as your first report, with
  the finding verdicts first.
```

**Placeholders:**
- `[REVIEWER_AGENT_ID]` - the reviewer the whole-diff review dispatched
- `[R]` - 1 or 2
- `[FINDINGS]` - the open findings of the previous pass (reviewer and security-researcher), copied verbatim
- `[FIX_BASE_SHA]` - the head the previous pass saw
- `[HEAD_SHA]` - the current head of the plan branch
- `[DIFF_FILE]` - the path `scripts/review-package <plan file> <fix base> HEAD` printed
- `[BASE]` - the plan's base, `git -C <tree> merge-base main HEAD`
- `[TREE]` - absolute path of the plan tree

**Reviewer returns:** per-finding verdicts, new breakage in the fix diff, and its full report on the new HEAD;
retro.md exists only when that report is a clean pass.
