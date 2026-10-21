# Plan inputs

The one definition of the `## Plan inputs` section. Every research lens, `start-research`,
`start-discovery` and `reuse-hunter` point here instead of restating it; read from phases 1 to 3 of
`start-development`.

Every research brief ends in a mandatory final `## Plan inputs` section with these four lists, in
this order. An empty list is written "none", never omitted. Entries are plain lines in these
formats:

```
reuse         name - file:symbol - which plan items need it       (feeds owns/uses/existing)
do-not-build  item - what provides it instead - source            (removes plan items)
fix-as-ac     anti-pattern - where - the acceptance condition     (adds ACs to tasks)
ideas         adopted / rejected, one line each, with the source  (design doc "Research")
```

`file:symbol` is one that was found, never guessed. `start-discovery` merges and de-duplicates the
lists of every lane into one section; `research-code-internal` additionally returns the shared-parts
map (part, exists-at, needed-by, proposed owner).

## How each list is consumed

| List | Consumer | Becomes |
|---|---|---|
| `reuse` | the planner (phase 3) | `owns`/`uses` in the task graph; `args.existing` of `workbench:plan-execute` as `{ name, where }` (name, file:symbol) |
| `do-not-build` | the planner, then plan-execute | plan items removed; `args.doNotBuild` as `{ name, reason }` (item, what provides it instead). The scope auditor flags building one as `missing` |
| `fix-as-ac` | the planner | acceptance conditions on the tasks that touch `where` |
| `ideas` | the design doc | the "Research" section, adopted and rejected with their sources |

The planner consumes every entry: the plan doc's `## Research inputs` maps each one to a task id or
to "rejected: <why>".
