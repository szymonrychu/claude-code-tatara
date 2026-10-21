---
title: Builtin worktree guard
status: todo
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
worktree: ""
branch: ""
verified_head: ""
run: ""
provides: []
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

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
