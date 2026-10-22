# Phases 1-3: discovery, design, plan

Detail for phases 1-3 of `SKILL.md`. Headings below are demoted one level from the original.

## Phase 1 - Discovery

Full path only; the lean path uses 1L recon. **Component mode only:** invoke
`git-submodules-refresh` first. If a submodule looks stale, detached, or carries unpushed work,
dispatch `submodule-auditor` and resolve what it reports. **Finish that before dispatching anything
else**: every later agent reads the tree they leave behind.

Then invoke `start-discovery` with the task. Its lanes run in parallel (LSP symbol
sweep, per-repo `codebase-cartographer` agents, external prior art via `start-research`, and lane 4,
the reuse hunt via `research-code-internal`, which writes the shared-parts map) and return a written
brief ending in `Plan inputs`.

Scale the fan-out to the question: all lanes for an unfamiliar cross-repo change, one targeted agent
for a narrow one. Never skip the tree state and the verification commands. Check every repo in scope
for uncommitted work and run its lint and tests before planning against it; a dirty or red tree
found now is cheap, at merge time it blocks (boy scout rule below). Carry forward the brief, the
verbatim verification commands per repo, and each tree's state. The brief's path goes to phase 4 as
`contextPack`, so every implementer and reviewer reads the verified facts.

## Research steps (optional)

Four lenses, each its own skill; decide per lens from this table (discovery lanes 4 and 5 run some).

| Skill | Run when | Skip when | Feeds |
|---|---|---|---|
| `research-code-internal` | the plan will add any helper, reader, parser, schema field or subsystem; a repo in scope has > ~200 source files; always on the full path before phase 4 | lean path with every file named and no new helper | shared-parts map, `owns`/`uses`/`existing` |
| `research-code-external` | the change has known analogues (a protocol, parser, scheduler, cache, auth flow, rules engine) or the design has an open fork | pure in-house glue, config edits, version bumps | design doc Decisions and Research |
| `research-papers` | the problem has a scientific or algorithmic core (scheduling, matching, probabilistic reasoning, parsing theory, concurrency protocols, ML) or the user names a paper | CRUD, infra plumbing, UI, documentation | design doc Decisions and Research |
| `research-docs` | a library, framework, provider or platform API is used in a new way, upgraded, or touched in >= 3 call sites; any Helm, Terraform provider or Kubernetes API change | a change that touches no external API surface | acceptance conditions on tasks, removed plan items |

The three internet lenses run through `start-research` with its `lenses` argument. Every brief ends
in `## Plan inputs`, defined in `references/plan-inputs.md`; the planner consumes every entry.
**Every lens is recorded as ran, or skipped with its reason, in the design doc's Research section.**
A lens nobody decided on is a gap.

## Phase 2 - Design doc

Explore the problem with the discovery and research briefs in hand. Produce genuinely different
approaches, not variations of one, against the axes that actually decide between them.

When more than one approach is viable, or the choice is expensive to reverse (a schema, a public
interface, a deployment topology), dispatch `architect-researcher` on that question and bring its
recommendation in as one input; it does not replace the gate. Pass `model` explicitly (it overrides
the agent's frontmatter), sized by question shape: **open-ended** ("how should we structure X")
uses the agent's default, which reads code first; **consulting-shaped** (a very complex
architectural decision: one well-framed question with the options laid out, or an ambiguity a
previous pass could not settle) uses `fable`, and fable is for nothing else. Narrow and hard is
exactly the consulting case, and it gets missed because it looks small.

### Ask only what no probe can answer

Classify every question before it reaches the user. **A fact you could observe** (how the code
behaves, what a flag resolves to, what an API returns) is not theirs: settle it with a read-only
probe or throwaway prototype. **A product or preference call** is theirs. Grill on preference,
never on fact.

If the change turns on a runtime mode (multiplexing, tenancy, sandboxing, a different backend),
verify its blast radius before the gate, per `references/mode-flags.md`. Write the design doc from
`templates/design.md` at `doc_path.sh design "<topic>"` (in `${CLAUDE_PLUGIN_ROOT}/skills/start-research/scripts/`); fill
every heading, and mark each default the user did not state `(my call)`. Research briefs may be
gitignored, so the design doc carries the findings it relies on, not just links.

**The work is an epic** at `docs/plans/{todo,in-progress,done}/<epic>/`, owned by `ticket.py`
(`${CLAUDE_PLUGIN_ROOT}/skills/start-development/scripts/ticket.py`, run with `python3`). First `ticket.py check --title
"<title>"` (`--files`, `--owns`, `--blockers` where known) lists near duplicates; extend one rather
than start a twin. Then `epic-create` (`ticket.py new-epic --title "<title>"`) creates it with its `README.md`
(title, blockers by epic title, description, goals, non-goals; written for humans from the user's
input, the research briefs and the scope discussion). The design doc goes to
`ticket.py path <epic> design`. Several epics: one `epic-create` each, `--blockers` naming what each
waits on. Nothing lives directly under `docs/plans/` outside the three phase folders.

## Phase 3 - Plan doc and tasks

Dispatch ONE `workbench:planner` agent (`opus` per call when more than one repo changes or the plan
adds a new subsystem) with `{epic, briefs[], userDecisions[], relatedEpics[]}`. Overlapping files are
ordered by `dependsOn` except files matching `overlapIgnore` (`references/workbench-config.md`). It writes:
- one task file per task via `epic-task-create`: `ticket.py new-task --epic <epic> --title "<title>" --repo ... --value ...
  --files ... --verify ...` (plus `--depends-on`, `--owns`, `--uses`, `--model`, `--review`,
  `--requirement-file`, `--ac-file`, and `--estimate <minutes>`: size each task to one test file's worth of behaviour, at most 8 files; give it a targeted verify (named test files or a component suite plus lint, never the full suite); merge sibling tasks under 3 files that share a test file into one; estimates come from `ticket.py estimate <epic>` and `--estimate` is only an override; report only, never a budget); the task slug is its id everywhere. design.md's `## Research
  inputs` maps every `Plan inputs` entry to a task slug or to "rejected: <why>". The task files are
  the plan: no plan doc, no tasks.json to keep in sync;
- the approval ledger at `<epic dir>/approvals.json` (`references/approvals.md`).

The **lean path** has no design.md: the README carries goals and non-goals, the tasks their
acceptance conditions, and the lint skips design coverage.

The lane 4 shared-parts map becomes the task graph: a part two or more tasks need gets exactly one
owner in `owns`; every task needing it lists it in `uses` and the owner in `dependsOn`; a part that
already exists goes into `existing` (`{name, where}`). A part many tasks need and nobody has built
is a **foundation task** that runs first. An item spanning families goes to ONE task. A contract is
a shared part: its owner task lists it in owns, every consumer in uses, and it is defined in exactly
one file; the plan's Contracts table names all three.

The task list is consumed programmatically by phase 4; its fields (`id`, `requirement`, `value`,
`files`, `verify`, `owns`, `uses`, `dependsOn` and the rest) are in `references/task-fields.md`.

Rules for the task list:
- **One task = one test file's worth of behaviour, at most 8 files**; split larger ones by test file.
- **Every plan item is a task with an explicit requirement**, written as acceptance conditions -
  what the implementer, reviewer and scope auditor are held to; a vague one silently shrinks scope.
- Two tasks whose `files` intersect are ordered by `dependsOn`; prefer a short foundation chain over
  duplicates. Name the affected repos; that set is every later phase's repo subset.
- Tests, docs, and generated-artifact regeneration are their own tasks or explicit acceptance
  conditions; they are the first things dropped otherwise.

Lint with `node ${CLAUDE_PLUGIN_ROOT}/workflows/validate-tasks.mjs --epic <epic dir>`; it must print
`ok`. It runs plan-execute's own validation (one owner per part, `uses` implies dependency, no
cycles, overlapping files ordered, the size cap) plus the task files, decision coverage, contracts
and the approval ledger (`references/approvals.md`) against the README and design.md, before any
worktree exists. Then run the **builder check** per `references/builder-check.md`: one fresh
`sonnet` agent reads the epic's README, design.md and tasks and reports only the questions it would
still need answered. Settle the answered and minor ones in the docs; the "theirs" pile goes into the
gate message as one batch.

When `architect-researcher` and you disagree, the design is contested, or the change is high-risk
(authz, secrets, concurrency, a rules engine, a data migration), run `workbench:interrogate` on the
epic (design.md plus tasks) before the gate, and put its verdict in the gate message.
