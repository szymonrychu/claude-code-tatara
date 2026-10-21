---
name: start-debugging
description: "Debug a defect with a gated flow: reproduce, isolate, find the root cause, prove a regression test, then fix through the lean path. Use for an error message or stack trace, a failing test nobody owns, 'works in staging but not in prod', a regression after a deploy, or a failed post-deploy health check. Replaces report-template debugging for work in these trees. Read-only until the fix phase."
---

# Start debugging

## Iron law

No fix without a root cause, and no fix without a red regression test. Three gates, in order:

1. Gate 1 - a red-capable feedback loop exists (end of phase 1).
2. Gate 2 - the root cause is one sentence backed by evidence (end of phase 5).
3. Gate 3 - the regression test was seen failing for the right reason (end of phase 6).

Nothing is edited in the product code before gate 3.

## Phase 0 - Intake

Write down: expected vs actual, when it started (commit, deploy, date), who or what is affected. Verify the claim: reproduce it yourself, or it is a report, not a bug. Quote the command and its output.

Done when: expected, actual, onset and blast radius are written, and the symptom was seen with your own command.

## Phase 1 - Feedback loop

Build one command that is `red-capable` (asserts the exact symptom, not "something failed"), `deterministic`, fast, and `agent-runnable` (no human, no prompt). Show the invocation and its output:

```
$ pytest tests/test_x.py::test_symptom -q
FAILED ... AssertionError: expected 3, got 0
```

Pick the loop type in preference order from `references/loops.md`. Flaky: raise the reproduction rate first (pin seeds, tighten inputs, loop N times and count). No red-capable command, no phase 2.

Done when: the command fails with the exact symptom, repeatedly, and the output is quoted.

## Phase 2 - Minimise

Confirm the minimal case is the same failure, not a nearby one: compare the error text and the failing line. Cut inputs, config, services and steps one at a time, re-running the loop after each cut, until every element left is load-bearing.

Done when: removing any remaining element makes the symptom disappear, and the failure signature is unchanged.

## Phase 3 - Hypothesise

Write 3-5 ranked falsifiable hypotheses, each in the form "if X is the cause, changing Y makes it disappear". Find similar working code and list every difference. Walk back the call chain to the trigger: never fix just where the error appears.

Done when: the ranked list exists, each hypothesis names the one change that would falsify it.

## Phase 4 - Instrument and test

One variable per experiment, top hypothesis first. Tag every debug log `[DEBUG-<4 hex>]` (one random tag per session) so cleanup is one grep. Performance problems: Measure first, with a profile or timing, before any guess. A surviving hypothesis must explain every earlier observation; one it cannot explain is wrong or incomplete.

Done when: one hypothesis survived its experiment and explains all observations, the others are marked refuted with the evidence.

## Phase 5 - Root cause

State it in one sentence with the evidence (command, output, file:line). Count the fixes tried: after three failed fixes, stop. Run `workbench:interrogate` on the hypotheses; if that does not settle it, it is a design question for the user - the one permitted stop. Do not try a fourth fix.

Done when: the sentence is written, the evidence is quoted, and a change at the cause (not the symptom site) is identified.

## Phase 6 - Regression test, proven

Write the regression test at the seam where the cause lives, before the fix, and watch it fail for the reason in the root-cause sentence. If the red was forced by a mutation (reverting a line, injecting the bug), diff the tree against a pristine copy to prove the mutation landed and nothing else changed. Recipes: `references/loops.md`.

Done when: the test is red for the right reason, with the failure output quoted.

## Phase 7 - Fix

Implement through `start-development`'s lean path with the regression test as the acceptance condition. Then the proof: test passes; revert the fix, test fails; restore, test passes. Finally the original un-minimised loop from phase 1 is green.

Done when: the revert proof ran with output quoted, and the original loop is green.

## Phase 8 - Cleanup and record

Run `grep -rn "DEBUG-<tag>"` over the tree: it must be empty. Put the confirmed hypothesis in the commit message. Write the record with `doc_path.sh record "<slug>-debug"` (see `${CLAUDE_PLUGIN_ROOT}/skills/start-research/scripts/doc_path.sh`), listing: loop command, hypotheses tried, root cause, regression test, fix commit.

Done when: the grep is empty, the commit message names the hypothesis, and the record exists.

## Red flags

Any of these sends the flow back to phase 1:

- "quick fix for now"
- "one more attempt"
- "skip the test, I will verify manually"
- "just try changing X"
- a fix proposed before phase 5, or "it works now" with no loop output

## Agans' nine rules

1. Understand the system.
2. Make it fail.
3. Quit thinking and look.
4. Divide and conquer.
5. Change one thing at a time.
6. Keep an audit trail.
7. Check the plug.
8. Get a fresh view.
9. If you did not fix it, it is not fixed.

## Rules

- Read-only until phase 7: no product edits, only the loop, tests and tagged debug logs.
- Every claim is backed by a command output pasted in the record.
- Models are explicit on every subagent call; never inherit the default.
- Plain hyphens and straight quotes, ASCII only.

Sources: superpowers systematic-debugging, mattpocock diagnosing-bugs, Agans (Debugging, nine rules), Zeller (Why Programs Fail), code.claude.com best-practices.
