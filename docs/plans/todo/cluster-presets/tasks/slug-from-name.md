---
title: slug from name
status: todo
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
actual: ""
actual_roles: ""
review: ""
worktree: ""
branch: ""
verified_head: ""
run: ""
provides: []
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

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
