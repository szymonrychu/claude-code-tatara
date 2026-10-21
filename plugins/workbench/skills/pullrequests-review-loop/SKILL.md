---
name: pullrequests-review-loop
description: "Poll an automated PR reviewer's reviews (login from --reviewer or WORKBENCH_REVIEWER), judge each finding (the reviewer is flaky - never obey blindly), dispatch fixer subagents, and loop until clean or a round cap. Use between pipeline-watch and merge."
---

# pullrequests-review-loop

Drives the review-fix loop between CI going green (`pullrequests-watch`)
and merge. An automated PR reviewer (login from `--reviewer` or `WORKBENCH_REVIEWER`) posts GitHub PR reviews (`APPROVED` / `CHANGES_REQUESTED` /
`COMMENTED`) plus inline comments on our PRs. **It is flaky**:
observed flipping `CHANGES_REQUESTED` -> `APPROVED` on the exact same
unchanged commit, and sometimes going unreachable and never reviewing at all.
This skill never obeys its verdict blindly in either direction - a
`CHANGES_REQUESTED` might be wrong, an `APPROVED` might be papering over a
real finding from two minutes earlier. The calling agent always judges.

**GitHub only.** The review loop covers GitHub PRs; any GitHub host works
(the `WORKBENCH_SCM_HOSTS` map is honoured). On a GitLab repo the script prints
`pullrequests-review-loop: <repo>: unsupported on GitLab (review-loop is
GitHub-only)` on stderr, still processes the run's GitHub repos, and exits 1.
A local-only repo (no PR host) is reported skipped on stderr and does not fail
the run. For GitLab, judge unresolved discussions via `pullrequests-watch` `reviews=` and the MR UI/API.

This skill does **not** merge. Merging stays the caller's job (`merge own
PRs` step in `start-development`).

## Procedure

1. **Poll.** Run the script for the PRs in scope:

   ```
   mise exec -- python3 ${CLAUDE_PLUGIN_ROOT}/skills/pullrequests-review-loop/scripts/review_state.py \
     --branch <branch> --repos repoA,repoB
   ```

   or, with explicit PRs:

   ```
   mise exec -- python3 ${CLAUDE_PLUGIN_ROOT}/skills/pullrequests-review-loop/scripts/review_state.py \
     --prs repoA#123,repoB#45
   ```

   `--reviewer <login>` names the reviewer and wins over env `WORKBENCH_REVIEWER`; with neither the script exits 2 with `review_state: no reviewer; pass --reviewer <login> or set WORKBENCH_REVIEWER`. Output is
   newline-delimited JSON, one object per PR:

   ```
   repo, pr, url, headSha, prState, mergeable,
   reviewerDecisionOnHead: APPROVED|CHANGES_REQUESTED|COMMENTED|NONE,
   reviewsAll: [{state, submittedAt, commitId, onHead, body}, ...]   (newest first, reviewer's only),
   inlineComments: [{path, line, commitId, onHead, createdAt, body}, ...]  (newest first, reviewer's only),
   hasStaleReviews: bool,
   actionable: bool,
   error: <string, only present on a per-PR API failure>
   ```

   A per-PR `error` does not stop the others; the script exits non-zero when
   every requested PR errored or any repo was GitLab. `reviewerDecisionOnHead` is always the
   *latest* review on the current head commit - never a stale one.

2. **Judge, per PR - never obey blindly.** Read
   `${CLAUDE_PLUGIN_ROOT}/skills/start-review/references/review-checklist.md`
   first and apply it. Classify each bot finding by kind - `missing`, `extra`,
   `wrong` or `quality` - and attach `evidence` from the code (file:line or a
   command output). A finding no evidence confirms is dropped. If you are not certain an issue is real,
   do not flag it. Severity follows the checklist's
   rubric (`critical`, `high`, `medium`; nothing lower is reported). Keep a
   `declined` list naming what you did not judge, each with why. For each PR
   object:
   - If `actionable` is true, OR `reviewsAll` contains a `CHANGES_REQUESTED`
     entry anywhere (even when `reviewerDecisionOnHead` is now `APPROVED` -
     the flip-flop case), read every review body and inline comment yourself
     judge it against the actual code before acting: is the claim real? A real bug gets fixed. A wrong or stale nitpick gets a
     reasoned rebuttal (in your own head, not posted back to the bot) and is
     dropped. A flip-flopped `APPROVED` sitting on top of a real earlier
     `CHANGES_REQUESTED` finding still gets fixed - the later approve does
     not excuse it.
   - If `reviewerDecisionOnHead == "NONE"` and `reviewsAll` is empty, the
     reviewer hasn't weighed in (never reviewed, or currently unreachable).
     Do not block on it. Apply a grace window (a couple of poll rounds,
     spaced a few minutes apart, is enough - the reviewer is asynchronous,
     not a synchronous check): if it still hasn't reviewed, proceed on the
     strength of your own review (the `start-review` pass already run
     earlier in the flow) and note in your report that the automated
     reviewer never weighed in.

3. **Fix real findings.** For each PR with a verified real finding, dispatch
   a fixer subagent sized to the fix (sonnet/low for a one-line correction,
   sonnet/medium for a multi-file fix) into that repo's existing worktree.
   The fixer writes a failing test first where the finding is testable,
   then fixes, commits, and pushes. A new head commit makes every prior review stale by construction
   (`onHead` flips to false on the next poll) - the reviewer
   re-reviews the new head on its own schedule.

4. **Re-poll and repeat, bounded.** Re-run step 1 after giving the
   reviewer time to react to the new head (poll every few minutes, do not
   hot-loop). Cap fix rounds at **3 per PR**. A PR still carrying an
   unresolved real finding after 3 rounds is surfaced to the human instead of
   looped forever.

5. **Exit condition, per PR.** Stop looping and consider a PR clear when ALL
   of:
   - CI is green (checked separately via `pullrequests-watch`, not by
     this skill).
   - `reviewerDecisionOnHead != "CHANGES_REQUESTED"`, OR the reviewer never
     reviewed within the grace window (step 2's escape hatch).
   - No un-addressed real finding remains in `reviewsAll` /
     `inlineComments` per your own judgment from step 2.

6. **Hand back to the caller.** Report, per PR: final `reviewerDecisionOnHead`,
   whether any findings were fixed (and what), whether the reviewer ever
   showed up, and whether the round cap was hit. The caller merges from here
   - this skill never merges.

## Notes

- Never treat `APPROVED` as proof of correctness, and never treat
  `CHANGES_REQUESTED` as proof of a bug. Both are one flaky agent's opinion.
  The gate is your own judgment plus this loop together, not the bot's label.
- The bot flip-flopping `CHANGES_REQUESTED` -> `APPROVED` on an unchanged
  commit is expected behavior for some reviewers, not a script bug - that is
  exactly why `reviewsAll` carries full history instead of just the latest
  state.
- `hasStaleReviews: true` with `reviewerDecisionOnHead: "NONE"` means the
  reviewer's only opinion is about a commit that's no longer the head (you
  already pushed a fix past it) - treat that PR as awaiting a fresh review,
  not as clean.
