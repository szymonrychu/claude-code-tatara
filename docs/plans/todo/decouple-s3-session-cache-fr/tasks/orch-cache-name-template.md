---
title: orch cache name template
status: todo
repo: agents-orchestrator
value: "A preset can name its S3 cache with a safe Jinja2 template, default <preset>-<session>"
files: [src/agents_orchestrator/cache/naming.py, tests/test_cache_naming.py, pyproject.toml, uv.lock]
verify: "uv run --frozen pytest -q -p no:cacheprovider tests/test_cache_naming.py && mise run lint"
depends_on: []
model: opus
review: ""
verified_head: ""
points: 5
expected_minutes: 10
expected_tokens: 1875101
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# orch cache name template

## Requirement

User request (2026-10-29 04:52Z, mx-34 #343), verbatim: "I also want to decouple s3 cache from preset. There must be a way to define S3 backup name with jonja2 template with default as preset-sessionname. This must also copy caches of existing sessions, so after rotation everything will work properly." (jonja2 = Jinja2)

Leader constraint: the migration copies only, never moves or deletes S3 objects.

This task delivers design D2 and D3 in agents-orchestrator: a new module `src/agents_orchestrator/cache/naming.py`, importable by the api and the reconciler (it imports neither `reconciler` nor `k8s`), that renders a cache name template in the Jinja2 3.1.6 sandbox, and the runtime dependency `jinja2>=3.1.6` (`uv add "jinja2>=3.1.6"`).

- `DEFAULT_CACHE_NAME_TEMPLATE`: the default template, rendering `<preset>-<session>`. The preset part is shortened so the rendered name always matches `spec.CACHE_KEY_RE` (`^[a-z0-9][a-z0-9._-]{0,62}$`) for every valid preset name (including one that slugifies to an empty string) and every valid session slug (at most 40 characters).
- `CACHE_NAME_VARIABLES = ("preset", "preset_id", "session", "created_by")`: `preset` is `spec.slugify(<preset name>)`, `preset_id` the preset uuid as a string, `session` the session slug, `created_by` the creating service's token name or the empty string for a user.
- `check_template(template: str) -> None` raises `ValueError` with a message naming the problem when the template is longer than 256 characters; does not parse; uses anything beyond output expressions (no `for`, `if` block, `macro`, `call`, `set`, `include`, `import`, `extends`, `with` or `filter` block, no function or method call, no attribute access); uses a filter outside `lower`, `upper`, `replace`, `trim`, `truncate`; or refers to a variable outside `CACHE_NAME_VARIABLES` (`jinja2.meta.find_undeclared_variables`).
- `render_cache_name(template: str, **variables: str) -> str` checks the template, renders it in one module-level `ImmutableSandboxedEnvironment` (`undefined=StrictUndefined`, `autoescape=False`, no loader, no extensions, `globals` emptied before any template is loaded, `*` and `**` intercepted and refused), strips the output and raises `ValueError` unless the output matches `spec.CACHE_KEY_RE`. A variable the template uses but the caller did not pass raises `ValueError` naming it. Every exception from Jinja2 or the render is caught and re-raised as `ValueError`.

## Acceptance conditions

- AC1: jinja2>=3.1.6 is a runtime dependency in pyproject.toml and uv.lock is current [evidence: command:grep -q '"jinja2>=3.1.6"' pyproject.toml && uv lock --locked]
- AC2: the default renders `<preset>-<session>` for a short preset name and slug, e.g. preset `my-repo` and session `alpha` give `my-repo-alpha` [evidence: test:tests/test_cache_naming.py::test_default_renders_preset_dash_session]
- AC3: the default renders a name matching CACHE_KEY_RE for a 40-character preset slug with a 40-character session slug, and for a preset that slugifies to an empty string [evidence: test:tests/test_cache_naming.py::test_default_always_fits_the_key_rule]
- AC4: a literal key without template syntax renders to itself [evidence: test:tests/test_cache_naming.py::test_literal_key_renders_to_itself]
- AC5: check_template raises ValueError for a template over 256 characters, a syntax error, a for loop, an if block, a set, a function or method call, attribute access, a filter outside the allowlist and an unknown variable [evidence: test:tests/test_cache_naming.py::test_check_template_refusals]
- AC6: `*` and `**` are refused, so a template cannot inflate its output by multiplication or power [evidence: test:tests/test_cache_naming.py::test_multiplication_and_power_refused]
- AC7: a rendered value that breaks CACHE_KEY_RE (uppercase, a slash, longer than 63 characters, empty) raises ValueError [evidence: test:tests/test_cache_naming.py::test_rendered_name_must_match_key_rule]
- AC8: a variable the template uses but the caller did not pass raises ValueError naming it, never renders an empty string [evidence: test:tests/test_cache_naming.py::test_missing_variable_is_an_error]
- AC9: the naming module imports neither agents_orchestrator.reconciler nor agents_orchestrator.k8s [evidence: test:tests/test_cache_naming.py::test_naming_imports_no_reconciler_or_k8s]
- AC10: lint passes [evidence: command:mise run lint]

## Files

- `src/agents_orchestrator/cache/naming.py`
- `tests/test_cache_naming.py`
- `pyproject.toml`
- `uv.lock`

## Interfaces

- `src/agents_orchestrator/cache/naming.py` (new): `DEFAULT_CACHE_NAME_TEMPLATE: str`, `CACHE_NAME_VARIABLES: tuple[str, ...] = ("preset", "preset_id", "session", "created_by")`, `TEMPLATE_MAX = 256`, `check_template(template: str) -> None` (raises `ValueError`), `render_cache_name(template: str, **variables: str) -> str` (raises `ValueError`).
- Reuses `spec.CACHE_KEY_RE` and `spec.slugify`; callers (task orch-cache-name-on-create, orch-cache-name-migration) pass `preset=slugify(name)` themselves.
- No import cycle: `spec.py` will call `naming.check_template` from the `WorkspaceCache.key` validator in the next task, so `naming` must import from `spec` only inside functions, or `spec` imports `naming` lazily; pick one and keep `python -c "import agents_orchestrator.spec, agents_orchestrator.cache.naming"` working.
- `pyproject.toml` `[project].dependencies` gains `"jinja2>=3.1.6"`; `uv.lock` updated by `uv add`.

## Expected outcome

`render_cache_name(DEFAULT_CACHE_NAME_TEMPLATE, preset="my-repo", preset_id="...", session="alpha", created_by="")` returns `my-repo-alpha`; any template beyond plain output expressions with the five allowed filters is refused with a `ValueError`; every rendered name matches `CACHE_KEY_RE`.

## Steps

- Read `src/agents_orchestrator/spec.py` (CACHE_KEY_RE, slugify, SLUG_MAX), `pyproject.toml`, and agents-webhook's `src/agents_webhook/prompt.py` (`_BoundedEnvironment`) for the sandbox shape, in one pass.
- `uv add "jinja2>=3.1.6"`; expect pyproject.toml and uv.lock to change, `uv lock --locked` exits 0.
- Red: write tests/test_cache_naming.py with every test named in the acceptance conditions; run `uv run --frozen pytest -q -p no:cacheprovider tests/test_cache_naming.py`; expect collection to fail on the missing module.
- Green: write `cache/naming.py` (environment, AST allowlist walk over `env.parse(...)`, `meta.find_undeclared_variables`, render, strip, key rule); rerun; expect all passed.
- `mise run lint`; expect `files already formatted` and exit 0.

## Notes

- Sandbox recipe and citations: brief-docs section 1 (`/workdir/workdir/.scratchpad/s3-cache/brief-docs.md`). The sandbox alone does not bound output size; the AST allowlist (no loops, no calls, five filters), the 256-character cap and the post-render key rule do.
- Default shape is the builder's within the boundary: it must render `<preset>-<session>` when both are short and always match CACHE_KEY_RE (a 40-character preset slug plus `-` plus a 40-character slug is 81 > 63, and a preset name such as `...` slugifies to an empty string). Slicing (`preset[:22]`) and a conditional expression are allowed node types if the default needs them; document the chosen text in the module docstring.
- `meta.find_undeclared_variables` can raise `TemplateAssertionError`; map it to `ValueError`.
- Rejected: rendering in a forkserver child with time and memory limits (agents-webhook `prompt.py`), because the allowlist already bounds the work and the api and reconciler would each need a child process (design D3).
- Tree state (pictures baseline, 2026-10-28): `mise run lint` green; the full suite is red-env only. Tests that use the `pool`/`dsn` fixtures need Postgres through testcontainers, and agent pods have no Docker, so they error locally (`DockerException`) and run in CI on the PR: the reviewer reads the CI job for them and quotes its summary line. `tests/test_reconciler.py::test_lightkube_default_client_uses_env_config` fails in-cluster for an unrelated reason (KUBERNETES_SERVICE_HOST).
- If a verify run fails, save the failing test name and the output tail before any rerun (retro, markdown-rendering-in-chat).
- Per-task security check (retro, recurring): user input reaching S3 keys or a template engine is the high-risk surface here; check size bounds, refusal paths and that no credential or presigned query reaches a log, a status reason or an error message.
- Before working read the repo's AGENTS.md, MEMORY.md and ROADMAP.md. No em dashes. No backward-compatibility shims.

- 2026-10-29 amended: planner filled Interfaces, Expected outcome, Steps and Notes before the gate (retro: no empty Steps)
