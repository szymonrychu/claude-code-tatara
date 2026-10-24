---
title: slug from name
status: done
repo: agent-orchestrator
value: clusters scheduled from a preset get a valid slug without the user typing one
files: [src/agent_orchestrator/spec.py, src/agent_orchestrator/bench/runner.py, tests/test_slugs.py]
verify: "uv run pytest -q -p no:cacheprovider tests/test_slugs.py tests/test_bench.py && uv run ruff check . && uv run ruff format --check ."
depends_on: []
owns: [slugify-helper]
uses: []
model: ""
estimate: 5
estimate_by: formula
actual: 2
actual_roles: "impl 1, verify 1, review 1, land 1"
review: ""
worktree: /home/user/claude-code-tatara/.claude/worktrees/cluster-presets-slug-from-name/agent-orchestrator
branch: cluster-presets-slug-from-name
verified_head: eac3b59b3cd94534dff90ae9d44a175617504ddd
run: cluster-presets
provides: [slugify-helper]
acs_for_audit: []
process_gaps: []
fork_point: f1baa5b
---

# slug from name

## Requirement

Add the shared slug helper (part `slugify-helper`, design D4, user Q1 and Q8) to `src/agent_orchestrator/spec.py`, test-first in a new `tests/test_slugs.py`.

- `slugify(text: str, max_len: int = SLUG_MAX) -> str`: lowercase; every run of characters outside `[a-z0-9]` becomes one `-`; leading and trailing `-` stripped; cut to `max_len` and trailing `-` stripped again; returns `""` when nothing usable remains.
- `generated_slug(name: str, rand: Callable[[], str] | None = None) -> str`: `<base>-<suffix>`, where `suffix` is 4 random lowercase ASCII letters (`secrets.choice(string.ascii_lowercase)`; `rand` returns the 4 letters, injected by tests) and `base` is `slugify(name, SLUG_MAX - 5)`, or `cluster` when that is empty. A base equal to `orchestrator` or starting with `orchestrator-` gets the prefix `p-` and is re-cut to `SLUG_MAX - 5`. The result always passes `validate_slug` and is at most `SLUG_MAX` (40) characters.
- `bench/runner.py:arm_slug` uses `slugify` for its body instead of its own regex; its output for every input stays the same (the existing `tests/test_bench.py` stays green).

## Acceptance conditions

- AC1: slugify maps names to their DNS-1123 form, collapses separators, strips edge dashes and respects max_len [evidence: test:tests/test_slugs.py::test_slugify_dns_1123_form]
- AC2: generated_slug returns base, a dash and 4 lowercase letters, at most 40 characters, valid for validate_slug, also for an 80-character name [evidence: test:tests/test_slugs.py::test_generated_slug_shape_and_length]
- AC3: a name whose base is orchestrator or orchestrator-* gets the p- prefix and passes validate_slug [evidence: test:tests/test_slugs.py::test_generated_slug_avoids_reserved_prefix]
- AC4: a name with no usable characters falls back to the cluster base [evidence: test:tests/test_slugs.py::test_generated_slug_fallback_base]
- AC5: arm_slug output is unchanged and its body comes from slugify [evidence: command:uv run pytest -q -p no:cacheprovider tests/test_bench.py]
- AC6: the targeted tests and lint pass [evidence: command:uv run pytest -q -p no:cacheprovider tests/test_slugs.py tests/test_bench.py && uv run ruff check . && uv run ruff format --check .]

## Files

- `src/agent_orchestrator/spec.py`
- `src/agent_orchestrator/bench/runner.py`
- `tests/test_slugs.py`

## Interfaces

- `spec.slugify(text: str, max_len: int = SLUG_MAX) -> str` and `spec.generated_slug(name: str, rand: Callable[[], str] | None = None) -> str` (part `slugify-helper`, consumed by create-cluster-from-preset).
- `bench/runner.py:arm_slug(arm, run)` keeps its signature and output.

## Expected outcome

Any preset name maps to a valid, short, non-reserved cluster slug with a random suffix, from one helper the bench also uses.

## Steps

- Write `tests/test_slugs.py` with the four tests named in the AC refs; run `uv run pytest -q -p no:cacheprovider tests/test_slugs.py`: fails on the missing functions.
- Implement `slugify` and `generated_slug` in `spec.py`, switch `arm_slug` to `slugify`; run the verify command: passes.

## Notes

- `validate_slug` (spec.py) is the oracle: DNS-1123 label, at most `SLUG_MAX` 40, `orchestrator` and `orchestrator-*` reserved.
- Reuse map: `arm_slug` sanitising is the adopted prior art (discovery/reuse.md ideas).
