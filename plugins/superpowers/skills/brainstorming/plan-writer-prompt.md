# Plan Writer Prompt

Dispatch one general-purpose subagent with `model: opus` set explicitly and this prompt, in plan mode, once
discovery's briefs exist and `ticket.py new` created plan.md. Keep its agent id: after the gate the same agent is
continued (SendMessage) in implementation mode with the user's answer verbatim, for superpowers:writing-plans.
Fill in the placeholders; hand it paths, never file contents.

```
You write one plan. A precise plan is where scope is protected cheapest: the
implementer builds the agreed rung and the reviewer checks the whole diff
against it, nothing else. You write only under your plan dir, found with
`python3 [TICKET] path [PLAN] plan`. The orchestrator created plan.md with
`ticket.py new`.

Mode: plan.
Plan: [PLAN]
ticket.py: [TICKET] (absolute path; run it with python3 from the main checkout)
Briefs: [BRIEF_PATHS] (read each by its heading index: grep its `^#` headings
first, then read only the sections the plan needs)

Read first, in the plugin root (the directory above ticket.py's `scripts/`):
`references/tickets.md` (the layout and the subcommands) and the template of
the file you write, `templates/plan.md` or `templates/implementation-plan.md`.

[THE DISCIPLINE, MODE AND RULES SECTIONS BELOW, VERBATIM]

Return at most 200 words: the plan slug, the mode, the rungs (plan mode) or
the chunk count and order (implementation mode), the commit, and the
preference questions only.
```

## Discipline

- Before writing, list every file the plan touches and read them all in one pass; then make all edits for the step.
- Never plan a step that edits, deletes, skips or xfails a test to make it pass, unless the test itself is no
  longer accurate; then the step names which test and why.
- Never guess a requirement. One you are unsure of is an open question for the gate, or a fact settled by a
  read-only probe.
- No backward compatibility in a step unless the user asked for it.

## Mode: plan

1. Fill plan.md from its template, `templates/plan.md`: What and why in the user's terms; Non-goals; Design with
   file:symbol where code exists; Decisions with the alternatives and why, a default the user did not state
   marked `(my call)`; Research (each lens ran or skipped with the reason); Irreversible operations. Place every
   entry of the briefs' Plan inputs: `reuse` in Design, `do-not-build` in Non-goals, `fix-as-ac` in the step that
   will pin it, `ideas` in Research.
2. The scope ladder, cumulative, from the absolute MVP to the most complete delivery: `### Rung <n>: <MVP|...|
   complete> - <name>` with checkable items `- <n>.<m>: <item>`. The first rung is the smallest delivery that is
   worth merging; each later rung adds only what the next step of value needs. Mark the recommended rung.
3. Write every open question with a recommended answer, worded so that "yes" accepts it: `- Q<n>: <question>
   [recommended: <answer>]`. Ask only what no probe can answer.
4. Agreed scope reads "not agreed yet" and `rung` stays empty until the gate.
5. Commit only plan.md as `docs(plan): <plan> plan`.

A continuation with the builder check's piles revises plan.md the same way (answered: into the plan; minor: a
Decision marked `(my call)`; theirs: an open question with a recommended answer) and commits it again as
`docs(plan): <plan> plan`.

## Mode: implementation

Input: the user's gate answer verbatim. It is binding; do not re-ask it. There is no second gate: what you write
is the contract. Follow superpowers:writing-plans.

1. In plan.md record Agreed scope (the rung and every modification, verbatim where it binds), turn each open
   question's recommendation into `[answer: <text>]`; the same edit sets `rung` to the picked rung number.
2. Write implementation-plan.md for the agreed rung only, at `ticket.py path <plan> implementation`, from its
   template: Agreed rung, Approach, then chunks `## Chunk <k>: <name> (model: <sonnet|opus>)`, each chunk one
   implementer, run in order in one tree, with steps `### S<n>: <title>` carrying Files, Covers (the plan.md item
   numbers), Test first, Change and Verify. Then Files to delete, Final verify (the repo's full test and lint
   command) and After merge. Each test ref resolves to the exact command the repo runs it with (its mise tasks,
   Makefile, package.json or pyproject); never invent one.
3. Sizing: one step is one test file's worth of behaviour, at most 8 files; a step's Verify is targeted (named
   test files or a component suite plus lint), never the full suite. A chunk is opus when it adds a module or
   touches more than five files, else sonnet. Every item of the agreed rung is covered by at least one step.
4. Commit plan.md and implementation-plan.md as `docs(plan): <plan> implementation plan`.

## Rules

- Never write `.py` scratch files. Scratch input is `.md` or `.json` under the repo's `.scratchpad/`.
- Retirement tests assert on `git ls-files <path>`, never on the filesystem.
- Codebase lookup is LSP and grep.
