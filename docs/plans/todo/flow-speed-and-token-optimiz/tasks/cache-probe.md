---
title: Cache probe
status: todo
repo: workbench
value: "A measurement, not a guess, decides whether prompt reordering saves cache writes"
files: [plugins/workbench/workflows/hook-probe.js, plugins/workbench/workflows/tests/hook-probe.test.mjs, plugins/workbench/scripts/hook-evidence.py, plugins/workbench/scripts/tests/test_hook_evidence.py]
verify: "cd plugins/workbench && node --test workflows/tests/hook-probe.test.mjs && pytest scripts/tests/test_hook_evidence.py -q && ruff check scripts"
depends_on: []
owns: [cache-probe-verdict]
uses: []
model: sonnet
estimate: 6
actual: ""
review: ""
worktree: ""
branch: ""
verified_head: ""
run: ""
provides: []
---

# Cache probe

## Requirement

Build the measurement that decides the prompt-cache change (design D6). The probe runs before any prompt is reordered.

- `plugins/workbench/workflows/hook-probe.js`: with `args.probe === 'cache'` it skips the four hook probes and the `args.worktree` check and runs two phases. `Cache static-first`: three agents dispatched one after another (`agentType: 'workbench:implementer'`, model sonnet, effort low), whose prompts share an identical static block of at least 4000 characters and differ only in a last line `Probe <n>: reply with ok true`. `Cache task-first`: the same three with the varying line first. Labels `probe:cache:static#1` to `#3` and `probe:cache:task#1` to `#3`. It returns `{probe: 'cache', labels: [...]}`. Without `args.probe` the existing behaviour is unchanged.
- `plugins/workbench/scripts/hook-evidence.py --cache <run dir> [--json]`: reads `journal.jsonl` labels and each `agent-<id>.jsonl`, takes the first assistant message's `usage.cache_creation_input_tokens` and `usage.cache_read_input_tokens` and the transcript `cwd`, prints one line per label, then a verdict line: `CACHE saving static=<n2>,<n3> task=<m2>,<m3>` when the second and third static-first agents each created fewer than 5000 tokens, else `CACHE none static=... task=...`. `--json` prints `{agents: [{label, cacheCreation, cacheRead, cwd}], verdict}`. The existing hook counting is unchanged.

## Acceptance conditions

- AC1: cache mode dispatches three static-first agents then three task-first agents, one at a time [evidence: test:plugins/workbench/workflows/tests/hook-probe.test.mjs::cache-mode-dispatches-three-static-then-three-task-first]
- AC2: the static-first prompts share an identical block of at least 4000 characters [evidence: test:plugins/workbench/workflows/tests/hook-probe.test.mjs::cache-mode-static-block-is-identical]
- AC3: hook-evidence prints CACHE saving when the second and third static-first agents create under 5000 tokens [evidence: test:plugins/workbench/scripts/tests/test_hook_evidence.py::test_cache_verdict_saving]
- AC4: hook-evidence prints CACHE none otherwise [evidence: test:plugins/workbench/scripts/tests/test_hook_evidence.py::test_cache_verdict_none]
- AC5: the JSON output lists creation, read and cwd per agent [evidence: test:plugins/workbench/scripts/tests/test_hook_evidence.py::test_cache_json_lists_cwd_per_agent]
- AC6: the existing hook-probe and hook-evidence tests still pass [evidence: command:cd plugins/workbench && node --test workflows/tests/hook-probe.test.mjs && pytest scripts/tests/test_hook_evidence.py -q]

## Files

- `plugins/workbench/workflows/hook-probe.js`
- `plugins/workbench/workflows/tests/hook-probe.test.mjs`
- `plugins/workbench/scripts/hook-evidence.py`
- `plugins/workbench/scripts/tests/test_hook_evidence.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
