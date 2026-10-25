---
name: research-docs
description: "Read the official docs of every library, platform and API in scope at the installed version, and report anti-patterns in our usage and functionality the library already provides. Use by default on the full path when a library, framework, provider or platform API is used in a new way, upgraded, or touched in 3 or more call sites, and for any Helm, Terraform provider or Kubernetes API change. Runs start-research, which dispatches the workbench:research-docs-purist agent."
---

# research-docs

Reads the official docs at the version we run, so the plan neither misuses an API nor rebuilds what it provides.

## When to run it

Run when:
- default-on for the full path whenever a library, framework, provider or
  platform API is used in a new way, upgraded, or touched in 3 or more call sites;
- any Helm, Terraform provider or Kubernetes API change.

Skip when:
- a change that touches no external API surface.

## Procedure

1. Get the brief path: `bash ${CLAUDE_PLUGIN_ROOT}/skills/start-research/scripts/doc_path.sh research "<topic>-docs"`.
2. Pin the version: read it from the lockfile or manifest (`go.mod`,
   `uv.lock`, `package-lock.json`, `Chart.lock`, provider lock file), never
   from memory.
3. Invoke `start-research` with lenses [docs-purist] (it dispatches the
   `workbench:research-docs-purist` agent), the topic, and the pinned
   versions. Model: `sonnet`. Sources, in order: Context7 first
   (`ToolSearch("+context7 docs")`, then resolve-library-id, then query-docs)
   and `<docs-site>/llms.txt`; web second.
4. Verify every package name against its registry (PyPI, npm, Go proxy,
   Terraform registry, Artifact Hub) before it reaches the plan.
5. Report anti-patterns in our usage (`fix-as-ac`) and functionality the
   library already provides (`do-not-build`).

## Output: Plan inputs

Return the four `## Plan inputs` lists (`reuse`, `do-not-build`, `fix-as-ac`, `ideas`) exactly as
defined in phase 1 of `${CLAUDE_PLUGIN_ROOT}/skills/start-development/SKILL.md`; do not restate
them.

## Rules

- Read-only: research only, no edits to the repos in scope.
- Every claim cited with a source URL, file:line, or DOI / arXiv id.
- Model sonnet unless stated; set the model explicitly on every agent call.
