---
title: Cache probe
status: done
repo: workbench
value: "A measurement, not a guess, decides whether prompt reordering saves cache writes"
files: [plugins/workbench/workflows/hook-probe.js, plugins/workbench/workflows/tests/hook-probe.test.mjs, plugins/workbench/scripts/hook-evidence.py, plugins/workbench/scripts/tests/test_hook_evidence.py]
verify: "cd plugins/workbench && node --test workflows/tests/hook-probe.test.mjs && pytest scripts/tests/test_hook_evidence.py -q && ruff check scripts"
depends_on: []
model: sonnet
review: ""
verified_head: 0a7b69478789916ba7f84cb8d086d3181d16b18d
points: 1
expected_minutes: 6
expected_tokens: 750000
points_actual: ""
actual_minutes: 2
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# Cache probe

## Requirement

Build the measurement that decides the prompt-cache change (design D6). The probe runs before any prompt is reordered.

- `plugins/workbench/workflows/hook-probe.js`: with `args.probe === 'cache'` it skips the four hook probes and the `args.worktree` check and runs two phases. `Cache static-first`: three agents dispatched one after another (`agentType: 'workbench:implementer'`, model sonnet, effort low), whose prompts share an identical static block of at least 4000 characters and differ only in a last line `Probe <n>: reply with ok true`. `Cache task-first`: the same three with the varying line first. Labels `probe:cache:static#1` to `#3` and `probe:cache:task#1` to `#3`. It returns `{probe: 'cache', labels: [...]}`. Without `args.probe` the existing behaviour is unchanged.
- `plugins/workbench/scripts/hook-evidence.py --cache <run dir> [--json]`: reads `journal.jsonl` labels and each `agent-<id>.jsonl`, takes the first assistant message's `usage.cache_creation_input_tokens` and `usage.cache_read_input_tokens` and the transcript `cwd`, prints one line per label, then a verdict line: `CACHE saving static=<n2>,<n3> task=<m2>,<m3>` when the second and third static-first agents each created fewer than 5000 tokens, else `CACHE none static=... task=...`. `--json` prints `{agents: [{label, cacheCreation, cacheRead, cwd}], verdict}`. The existing hook counting is unchanged.

## Acceptance conditions

- AC1: cache mode dispatches three static-first agents then three task-first agents, one at a time [evidence: test:plugins/workbench/workflows/tests/hook-probe.test.mjs::cache-probe-runs-six-serial-agents-without-worktree]
- AC2: the static-first prompts share an identical block of at least 4000 characters [evidence: test:plugins/workbench/workflows/tests/hook-probe.test.mjs::cache-probe-prompts-share-a-static-block]
- AC3: hook-evidence prints CACHE saving when the second and third static-first agents create under 5000 tokens [evidence: test:plugins/workbench/scripts/tests/test_hook_evidence.py::test_cache_saving_verdict]
- AC4: hook-evidence prints CACHE none otherwise [evidence: test:plugins/workbench/scripts/tests/test_hook_evidence.py::test_cache_none_verdict_and_json]
- AC5: the JSON output lists creation, read and cwd per agent [evidence: test:plugins/workbench/scripts/tests/test_hook_evidence.py::test_cache_none_verdict_and_json]
- AC6: the existing hook-probe and hook-evidence tests still pass [evidence: command:cd plugins/workbench && node --test workflows/tests/hook-probe.test.mjs && pytest scripts/tests/test_hook_evidence.py -q]

## Files

- `plugins/workbench/workflows/hook-probe.js`
- `plugins/workbench/workflows/tests/hook-probe.test.mjs`
- `plugins/workbench/scripts/hook-evidence.py`
- `plugins/workbench/scripts/tests/test_hook_evidence.py`

## Interfaces

- Owns `cache-probe-verdict`: the `CACHE saving|none` line and the `--json` shape of `hook-evidence.py --cache`, in `plugins/workbench/scripts/hook-evidence.py`. cache-prefix-change acts on the verdict the orchestrator records.

## Expected outcome

One Workflow run plus one command says whether static-first prompts make the second and later agents read the cache instead of writing it.

## Steps

- Red: add AC1-AC2 to `workflows/tests/hook-probe.test.mjs` and AC3-AC5 to `scripts/tests/test_hook_evidence.py` (fixture run dirs with fake journal and transcript rows); run `cd plugins/workbench && node --test workflows/tests/hook-probe.test.mjs && pytest scripts/tests/test_hook_evidence.py -q`; expect failures.
- Green: the cache mode and `--cache`.
- Run the task verify; expect all green.

## Notes

- After this task lands on the epic branch, the orchestrator runs `Workflow({scriptPath: '<integration tree>/plugins/workbench/workflows/hook-probe.js', args: {probe: 'cache'}})`, then `hook-evidence.py --cache <run dir> --json`, and records the JSON and the verdict in design.md under `## Cache probe result` (D6).
- Measured: per-agent cache writes are 17k to 28k and cross-agent sharing is near zero, even for the static-first reviewPrompt (brief (a) Cache); the probe separates prompt order from launch concurrency by dispatching serially.
- Node test titles are single kebab tokens.
