---
title: Builtin worktree guard
status: in-progress
repo: workbench
value: Any future use of the harness built-in worktree feature turns the suite red
files: [scripts/tests/test_builtin_worktree_guard.py, plugins/workbench/skills/start-development/tests/test_repo_hygiene.py, plugins/workbench/.claude-plugin/plugin.json, .claude-plugin/marketplace.json]
verify: "mise run test && mise run lint"
depends_on: [docs-flow-phases, docs-worktree-refs, docs-readmes-fallback]
owns: []
uses: []
model: sonnet
estimate: 60
actual: ""
review: ""
worktree: /Users/szymonri/Documents/workbench/.claude/worktrees/epic-integration-worktrees--builtin-worktree-guard
branch: epic-integration-worktrees--builtin-worktree-guard
verified_head: ""
run: epic-integration-worktrees
provides: []
acs_for_audit: []
process_gaps: []
---

# Builtin worktree guard

## Requirement

Pin with tests that no workbench file uses or instructs the harness built-in worktree feature (user decision U1, design D1).

- New `scripts/tests/test_builtin_worktree_guard.py` scans every tracked file (`git ls-files`) under `plugins/workbench/skills`, `agents`, `workflows`, `hooks` and `rules`, plus `scripts/harness`. It also scans every file the harness emitters render from this repo's sources into `tmp_path`, using the emitter registry the harness tests use.
- The patterns it looks for: `isolation: "worktree"`, `isolation: 'worktree'`, `isolation: worktree`, `EnterWorktree`, `ExitWorktree`, `claude --worktree`, `claude -w `, `WorktreeCreate`, `WorktreeRemove`.
- A matching line passes only when it forbids the feature (it carries a negation such as "never", "not", "no" or "do not"), or when it sits in a test file that asserts the pattern's absence. Every other match fails, naming the file, the line and the pattern.
- The test also asserts:
  - `plugins/workbench/.claude-plugin/plugin.json` declares no `WorktreeCreate` or `WorktreeRemove` hook;
  - no agent frontmatter under `plugins/workbench/agents` carries `isolation`.
- Self-test of the matcher: fixture lines `isolation: "worktree"` and `Use EnterWorktree to enter the tree` fail; `Do not call the built-in EnterWorktree` passes.
- `plugins/workbench/skills/start-development/tests/test_repo_hygiene.py` drops `isolation` from `AGENT_KEYS`, so an agent declaring it fails hygiene.
- `plugins/workbench/.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json` change "per-subagent worktree isolation" to "per-task git worktrees with an epic integration worktree", and the two descriptions stay equal.

## Acceptance conditions

- AC1: no tracked plugin, harness or emitted file instructs the built-in worktree feature [evidence: test:scripts/tests/test_builtin_worktree_guard.py::test_no_builtin_worktree_instructions]
- AC2: the matcher flags instructing lines and passes forbidding ones [evidence: test:scripts/tests/test_builtin_worktree_guard.py::test_matcher_flags_use_and_passes_guards]
- AC3: plugin.json declares no WorktreeCreate or WorktreeRemove hook and no agent declares isolation [evidence: test:scripts/tests/test_builtin_worktree_guard.py::test_manifest_and_agents_declare_no_builtin_worktree]
- AC4: repo hygiene no longer allows isolation in agent frontmatter [evidence: command:! grep -n '"isolation"' plugins/workbench/skills/start-development/tests/test_repo_hygiene.py]
- AC5: the manifests describe per-task git worktrees and stay equal [evidence: test:plugins/workbench/skills/start-development/tests/test_release.py::test_marketplace_description_matches_plugin_json]
- AC6: neither manifest says worktree isolation [evidence: command:! grep -n 'worktree isolation' plugins/workbench/.claude-plugin/plugin.json .claude-plugin/marketplace.json]

## Files

- `scripts/tests/test_builtin_worktree_guard.py`
- `plugins/workbench/skills/start-development/tests/test_repo_hygiene.py`
- `plugins/workbench/.claude-plugin/plugin.json`
- `.claude-plugin/marketplace.json`

## Interfaces

- Test only plus manifest wording; no runtime change.

## Expected outcome

Adding any instruction to use EnterWorktree, Agent isolation, `claude --worktree` or a WorktreeCreate/WorktreeRemove hook anywhere in the plugin or its generated harness files turns `mise run test` red.

## Steps

- Red: write the test with the matcher self-test first, and remove `isolation` from `AGENT_KEYS`; run `pytest scripts/tests/test_builtin_worktree_guard.py -q`. The self-test fails until the matcher exists; the manifest-wording AC fails until the descriptions change.
- Green: implement the matcher and change the two descriptions.
- Run `mise run test && mise run lint` from the root.

## Notes

- Existing guard pins stay: start-research/tests/test_start_skills_structure.py:257-269, workflows/tests/plan-execute.test.mjs:349-356, plan-execute-implementer.test.mjs:64.
- plan-execute.js:348 lists `isolation` among agent() options and :1846 says "No isolation option here on purpose"; neither matches the patterns.
- Runs last so it scans the final wording of every doc task.

- 2026-10-21 run epic-integration-worktrees: dependency-failed on docs-flow-phases, docs-worktree-refs, docs-readmes-fallback

- 2026-10-21 run epic-integration-worktrees: dependency-failed on docs-flow-phases, docs-readmes-fallback
