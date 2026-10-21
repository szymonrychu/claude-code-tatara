# Task fields

The task list at `doc_path.sh tasks "<topic>"` is consumed programmatically by phase 4 of
`start-development`: each entry becomes one task in the `workbench:plan-execute` args. Every
field below is read by the workflow, the lint (`validate-tasks.mjs`) or both.

| Field | Meaning |
|---|---|
| `id` | short stable identifier, e.g. T1; on the ticket flow the id is the task slug (the task file name) |
| `title` | one line |
| `short` | optional very short kebab title for agent labels (`token-refresh`); derived from the title when absent |
| `repo` | which code/ submodule, or "superrepo" in meta mode |
| `requirement` | the complete statement of what done means for this task - every acceptance condition, not a summary |
| `value` | one line: what this task is worth to the user; required |
| `files` | files the task is expected to touch, where known (an array) |
| `ac` | acceptance conditions: `[{id, text, evidence: {kind, ref}}]`, `id` unique within the task, `text` and `ref` non-empty (`ref` may be empty only for `judgement`). `kind` is one of five: `test` (a test name or `file::name` that passes), `symbol` (a function or class the diff adds or changes), `command` (a command that exits 0), `doc-section` (`<file>#<heading>` exists as a heading), `judgement` (no mechanical proof; a reviewer decides). Required on the ticket flow (`validate-tasks.mjs --epic`), optional on the legacy `--plan` flow; plan-execute rejects a malformed `ac` before any agent runs. A `test` ref runs with its package's runner from the package root (the nearest `pyproject.toml`, `package.json` or `package.xml`), not the repo root; `refRunners` in `.claude/workbench.json` maps globs to commands (`workbench-config.md`), and the lint rejects a `test:` ref with no runner (add a `refRunners` entry or use a `command:` ref). `judgement` ACs go to the epic audit. Parking words (the `DEBT_MARKERS` line in `plan-execute.js`) in the requirement, AC texts or notes are rejected by the lint |
| `notes` | constraints, gotchas, prior art from the brief |
| `verify` | the task's TARGETED test + lint command, e.g. `pytest tests/test_decode.py && mise run lint` |
| `model` | optional 'opus' only for the most problematic implementation tasks (hard rules reasoning, concurrency); default sonnet. Every review and scope audit runs on sonnet whatever implemented the work |
| `review` | optional tier `skip`, `light`, `full` or `panel`; an explicit value wins (`true` is `full`, `false` is `skip`). Otherwise a changed path matching auth, secret, sops, rbac, migration, lock, mutex, thread, concurren, `.github/`, `.gitlab-ci`, `hooks/` or permission gives `full`; else `skip` when the verifier has no findings, every `ac` is met with test, symbol, command or doc-section evidence, and the diff adds at most 150 non-test lines in at most 4 files; else `light` (a task without `ac` is at least `light`, never `skip`). The verifier's `tierHint` can raise the tier, never lower it. `skip` runs no reviewer (the scope audit still reads it); `light` runs one review round (effort medium), one fixer and the verifier, no second review; `full` runs the review loop (effort high); `panel` runs `full` and marks the task result `panel: true` |
| `owns` | shared parts (map names) only this task builds |
| `uses` | shared parts it consumes; one owned by another task requires that task in dependsOn, directly or transitively |
| `dependsOn` | task ids that must finish clean first |
| `estimate` | task frontmatter, minutes, written by the planner under the "about an hour" rule (`new-task --estimate`). Report only: it feeds the epic README `Time` section, the heartbeat ETA and the record, never a budget, and nothing in plan-execute reads it. `validate-tasks.mjs --epic` warns (does not fail) when it is over 90, as a split hint next to the 8-file rule |
| `actual` | task frontmatter, minutes, written by `ticket.py apply-run` from the task's `durationMs` in the plan-execute return (measured around `runOne` with `Date.now()`). Added across runs, replaced when the same run is applied twice. Report only |
| `overlapIgnore` | `.claude/workbench.json` key, not a task field: files matching it (doc files by default, plus your globs) do not need ordering through `dependsOn` when two tasks touch them |
| `size` | optional 'large' when a task genuinely needs more than 8 files |
| `sizeReason` | required with size 'large': why it cannot be split |

On the ticket flow the task list is derived from the epic's task files by `ticket.py tasks`, ids are task slugs (also in `approvals.json`, `design.md` coverage and contracts rows, `dependsOn`), and the lint is `node ${CLAUDE_PLUGIN_ROOT}/workflows/validate-tasks.mjs --epic <epic dir>`, which also requires `ac` on every task.

The epic README `## Time` section (sum of estimates, sum of actuals, remaining estimate over tasks not done) is derived: `ticket.py tasks` and `apply-run` regenerate it. It is time reporting only; the context and tool-call ceilings and two continuations stay the only budgets.

A retirement test (one that pins a removal) asserts on `git ls-files <path>`, never on the filesystem, because an untracked empty directory can survive a merge. The TDD exception for a deletion is narrow: the diff's non-test changes are deletions only and a test that pins the removal is added or changed; the implementer names it in `tests.note` as "deletion pinned by a retirement test".
