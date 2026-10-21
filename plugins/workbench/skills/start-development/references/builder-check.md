# Builder check

Run once, after the design and plan docs are drafted and before the human gate. One fresh `sonnet` agent, no prior context, so it reads the docs the way the builder will.

## Prompt

```
You are a talented engineer in this domain, handed the epic at <epic-dir>: its
<epic-dir>/README.md, its <epic-dir>/design.md (absent on the lean path) and the task files
under <epic-dir>/tasks/.

Report only the questions you would still need answered before building. Nothing else:
no praise, no summary, no suggestions. One line per question, numbered, each naming the
section it comes from. If you have none, say "no questions".
```

Replace `<epic-dir>` with the directory from `ticket.py path <epic> readme`, minus the file name.

## Sorting rule

Sort every question into exactly one bucket:

- **answered**: the docs already settle it, or the answer is obvious from them. Write the answer into the doc where the builder will look.
- **minor**: a small choice with a sensible default. Settle it, write it into the doc, and mark it `(my call)`.
- **theirs**: a preference or product call only the user can make. Ask it in the gate message, numbered, each with a recommended answer, worded so that "yes" accepts it, all as one batch.

Facts are never asked. If a question is about something checkable (a file, a command, an API, a version), settle it with a probe and write the result into the doc.
