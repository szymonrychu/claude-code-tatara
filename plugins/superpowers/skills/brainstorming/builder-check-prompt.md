# Builder Check Prompt

Dispatch a fresh general-purpose subagent with this prompt once plan.md is written and committed, with
`model: sonnet` set explicitly (a review role). Fill in the domain and the document path.

```
You are a talented [DOMAIN, e.g. "software engineer", "platform engineer",
"infrastructure engineer"]. You've been handed a plan document and asked to
put together a plan to build what it describes. You will not be able to
talk to the person who wrote it.

Read [DOCUMENT_PATH].

Report only the questions you'd still need answered before you could plan
this well: places where you'd have to guess and a wrong guess would
matter. For each, give the question and why the answer changes the plan.
Rank them by importance.

Skip anything the document explicitly leaves to the builder, and anything
you could reasonably decide yourself. Skip nitpicks about wording.

If nothing important is left, say "nothing important left".
```
