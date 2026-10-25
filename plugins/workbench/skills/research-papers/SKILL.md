---
name: research-papers
description: "Find scientific literature relevant to the algorithmic core of a problem before design. Use when the problem has a scientific or algorithmic core (scheduling, matching, probabilistic reasoning, parsing theory, concurrency protocols, ML) or the user names a paper. Runs start-research, which dispatches the workbench:research-paper-scout agent; cites DOI or arXiv id and separates peer-reviewed from preprint."
---

# research-papers

Finds the literature behind the algorithmic core of the problem, with peer-reviewed work told apart from preprints.

## When to run it

Run when:
- the problem has a scientific or algorithmic core (scheduling, matching,
  probabilistic reasoning, parsing theory, concurrency protocols, ML);
- the user names a paper.

Skip when:
- CRUD, infra plumbing, UI, documentation.

## Procedure

1. Get the brief path: `bash ${CLAUDE_PLUGIN_ROOT}/skills/start-research/scripts/doc_path.sh research "<topic>-papers"`.
2. Invoke `start-research` with lenses [paper-scout] (it dispatches the
   `workbench:research-paper-scout` agent) and the topic, writing the
   brief to that path. Model: `sonnet`.
3. Check each finding carries a DOI or arXiv id, year, venue, peer-reviewed or
   preprint, and an `applicability` line. Drop findings without them.
4. Distil into the Plan inputs below; every adopted idea names its paper.

## Output: Plan inputs

Return the four `## Plan inputs` lists (`reuse`, `do-not-build`, `fix-as-ac`, `ideas`) exactly as
defined in phase 1 of `${CLAUDE_PLUGIN_ROOT}/skills/start-development/SKILL.md`; do not restate
them.

## Rules

- Read-only: research only, no edits to the repos in scope.
- Every claim cited with a source URL, file:line, or DOI / arXiv id.
- Model sonnet unless stated; set the model explicitly on every agent call.
