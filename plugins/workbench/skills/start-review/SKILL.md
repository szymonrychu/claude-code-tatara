---
name: start-review
description: Review a branch, diff, MR or PR against its intent before merge. Phase 5 of start-development and any "review this" request. Pins the scope, fixes the intent, runs the repo's tests and lint independently, dispatches one reviewer covering spec and quality (--single, the default and only path) that reads one shared checklist, validates every finding against the code, and returns a verdict (Act on, Consider, Noted, Dismissed) without applying anything. Read-only.
---

# start-review

One review pass with one checklist. One reviewer (`--single`, the default)
reads the change on the spec and quality axes, you verify what it reports,
and the verdict is the deliverable. The
reviewer never fixes anything.

## When to use it

- Phase 5 of `workbench:start-development`, before merge.
- Any request to review a branch, diff, MR or PR: "review this", "is this ready".
- A high-risk diff (authz, secrets, concurrency, a rules engine, a data
  migration) or a contested design: run `workbench:interrogate` instead of
  step 4; steps 1-3, 5 and 6 still apply.

Not for debugging a failure: that is a different skill.

## 1. Pin the scope

Resolve the base and head to commits and size the change:

```
git rev-parse <base> <head>
git diff --stat <base>...<head>
```

Pass paths and the range to reviewers, never pasted contents. If the diff is
empty, stop: there is nothing to review, and say so.

Done when: base and head are two SHAs and the diffstat is non-empty.

## 2. Intent

Take the intent from, in order: the plan task requirements or the design doc
when they exist; else the MR/PR description; else one paragraph you write and
the user confirms. Quote requirements verbatim. A review without intent is not
run: ask first, since nothing can be judged missing, extra or wrong without it.

Done when: the intent is written down and each requirement is a quotable line.

## 3. Independent verification

Run the repo's own test and lint commands (`mise run test`, `mise run lint`, or
what the repo defines) in the head worktree, under the suite lock so sibling
runs do not contend:

```
${CLAUDE_PLUGIN_ROOT}/skills/worktree-merge/scripts/suite-lock.sh <command>
```

Quote the real tail of each run, including the summary line. Red is the first
finding, before any reviewer reports. Do not trust a green claim from the
implementer's report.

Done when: both commands ran by you, and their output tails are quoted.

## 4. The reviewer

`--single` is the default and the only path: dispatch one `reviewer` covering
spec and quality, both axes in one read with the shared checklist, with `model`
set explicitly to `sonnet`, whatever model implemented the work. `full` or
`panel` tier work gets the same single reviewer; a second opinion on other
models is a `workbench:interrogate` panel (see When to use it), not a second
reviewer here.

The reviewer gets the intent, the range, the worktree path, and this
instruction: read
`${CLAUDE_PLUGIN_ROOT}/skills/start-review/references/review-checklist.md`
first, then apply it.

- spec axis: reports missing / extra / wrong, quoting the requirement line for
  each.
- quality axis: tests first (read the tests before the code).

It returns findings with evidence and kind, then `declined` and
`cannotVerify` lists, capped at 400 words.

Done when: the report is back with findings (or none), declined and
cannotVerify.

## 5. Validate findings

Validate every finding you would act on against the code yourself: open the
file, run the command. Drop what you cannot confirm, and say it was dropped.
Merge duplicates. Process gaps (missing note, sweep or ratchet line) are
`processGaps`, not findings.

Done when: every Act on item is confirmed by your own read of the code.

## 6. Verdict

Sort into four buckets, then two lists:

- Act on: real problems for correctness, security or the stated requirement.
  These block. Finding, evidence, why it matters.
- Consider: legitimate, but the cost may not pay. State the tradeoff.
- Noted: valid, not actionable now. One line each.
- Dismissed: wrong or missing context. One line of why each.
- Declined: behaviours no one judged, with why.
- Cannot verify: requirements the diff and tree cannot show.

Done when: every finding is in exactly one bucket.

## After the verdict

Findings are never applied by the reviewer. Act on items go to an implementer
as a sharpened requirement: the implementer in the epic's integration tree. Consider items that change scope or product
behaviour go to the user. Everything else is recorded and closed. Do not
re-review the same change unless it is materially rewritten.

## Rules

- Reviewers are read-only: no edits, no commits, no state-changing commands.
- Every finding carries evidence (file:line or command output) and a kind.
- Models are set explicitly on every dispatch; never inherit the default.
- Plain hyphens and straight quotes; no decorative Unicode.
