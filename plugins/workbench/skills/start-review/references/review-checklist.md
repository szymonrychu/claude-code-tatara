# Review checklist

The single source read by the plan-execute reviewer, the panel-reviewer agent, the reviewer, spec-reviewer and quality-reviewer agents, and the start-review skill.
Apply every section to the diff and the tree; do not substitute your own list.

## Tests first

- Read the new and changed tests before the code they cover.
- For each test, ask: would it fail if the behaviour were removed? If it would still pass, say so.
- Expected values must come from an independent source: a literal, a worked example or the spec.
- Never accept an expected value recomputed the code's way, such as calling the function under test to build it.
- A test that asserts nothing (no assertion, a tautology, a mock checked against itself) is a high finding.

## Claims are not evidence

- The implementer's report is a list of claims; verify each one against the files or the diff.
- A claim you did not check is not confirmed; list it under cannotVerify.
- Report filesRead: the files you actually opened, not the files you were pointed at.

## Spec axis

- missing: the requirement says it is needed and it is absent or only partly done.
- extra: built, but nobody asked for it.
- wrong: built, but not doing what the requirement says.
- For every spec finding, quote the requirement line in `requirement`.
- Work deferred that an agent could have done is undelivered scope and a finding.
- Verification that did not run or did not pass is a finding, as is a behaviour change with no test.
- A bug or gap the summary mentions finding, neither fixed in the diff nor listed in `discovered`, is a finding.

## Quality axis

- Swallowed errors: an except or catch that discards the failure, or a status that is never read.
- A contract defined in two places (a schema, constant, phrase list or format that can drift apart).
- A shared part rebuilt instead of reused when the task named one to reuse.
- A shared part reimplemented instead of reused is a finding unless `reimplemented` gives a reason that holds.
- A debt-marker comment added by this change (the markers are listed under Debt markers below).
- A stub or skipped test introduced by this change.
- Debt markers: TODO, FIXME, stub, a skipped or xfail test, a hard-coded value standing in for logic.
- A behaviour change without a test that exercises it.
- Parking wording on added lines (later, follow-up, next round, round N, phase 2, out of scope for this pass) is a debt marker and a high finding.

## Every finding

- Carries evidence: a file:line or the output of a command you ran.
- Carries a kind: missing, extra, wrong or quality.
- If you are not certain an issue is real, do not flag it.
- Style is never a finding: naming, formatting and taste are out.
- Only correctness or a stated requirement makes a finding; speculative hardening and "consider also" suggestions do not.
- Asked to find gaps, a reviewer will usually invent some; resist that. Clean with no findings is the expected outcome for good work.

## Severity

- critical: wrong behaviour or a security hole.
- high: the task cannot be trusted until fixed: an asserting-nothing test, a swallowed error, a missing requirement, a debt marker, a duplicate contract.
- medium: a correctness risk at an edge.
- Nothing lower exists; anything below medium is not reported.

## What you did not judge

- declined: every behaviour you chose not to judge, each with the reason.
- cannotVerify: every requirement the diff and the tree cannot show, such as live behaviour or an external system.
- Neither list is left silent; write none when a list is genuinely empty.

## Bookkeeping

- A missing note, sweep, ratchet or approval line is a processGaps entry, never a finding.
- Do not raise a finding for a record the orchestrator owns.
