---
title: Registry
status: in-progress
repo: any-mcp
value: "Many plugins appear as one sorted, collision-free tool list that reloads safely"
files: [src/any_mcp/registry.py, tests/test_registry.py]
verify: "uv run --frozen pytest tests/test_registry.py -q && mise run lint"
depends_on: [plugin-discovery, schemas-and-validation]
owns: [tool-registry]
uses: [plugin-abc, schema-tools, any-mcp-config, tool-types, plugin-loader]
model: opus
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

# Registry

## Requirement

Aggregate loaded plugins into one global, deterministic tool list with lifecycle and reload (design D6, D8).

- `ToolRegistry(plugins, settings)`. `start()`: for each plugin in order, `setup()` then the first `load_tools()`; a failure raises `ConfigError` naming the plugin (plugins already set up are torn down first). `stop()`: cancels periodic reloads and runs `teardown()` for every plugin that was set up, in reverse order, continuing past failures (each logged).
- Each plugin's specs are filtered by the entry's `allow` globs (on plugin-local names; empty means all) and `tags` (empty means all; otherwise a spec needs one matching tag), named with `exposed_name(namespace, spec.name, max_length=settings.max_name_length)`, and their schemas normalised: `input_schema` is `normalize_schema(spec.json_schema())`, `listed_schema` is `listing_schema(input_schema)`. A `SchemaError` becomes `ConfigError` naming plugin and tool. Two tools with one exposed name raise `ConfigError` naming both plugins and tools.
- `tools()` returns every `ExposedTool` sorted by name; `get(name)` returns one or `None`. The list is global: no method takes a caller or connection.
- `reload(plugin=None) -> bool`: reloads one or all plugins under a single `asyncio.Lock`, compares the new list with the old (names, descriptions, schemas, tags, annotations) and, only when it differs, awaits every listener added with `add_listener`. A plugin whose `load_tools()` raises keeps its previous tools and logs one stderr line naming it.
- `run_periodic()`: for each plugin with `reload_every`, reloads that plugin every `reload_every` seconds until `stop()`.
- `request_reload(plugin_name)` schedules `reload(plugin_name)` as a task; `start()` binds it into each plugin's context, so `ctx.request_reload()` works.

## Acceptance conditions

- AC1: start runs setup and load_tools in order, a failing plugin raises ConfigError naming it after earlier plugins are torn down, and stop tears down in reverse past failures [evidence: test:tests/test_registry.py::test_start_and_stop_lifecycle]
- AC2: names are namespaced and sorted, allow globs and tags filter, and a duplicate exposed name raises ConfigError naming both [evidence: test:tests/test_registry.py::test_names_filters_and_collisions]
- AC3: schemas are normalised for validation and listing, and a SchemaError names plugin and tool [evidence: test:tests/test_registry.py::test_schema_normalization_applied]
- AC4: reload returns True and awaits listeners once only on a real change, otherwise returns False with no listener call [evidence: test:tests/test_registry.py::test_reload_diff_notifies_on_change]
- AC5: a raising reload keeps the plugin's previous tools and logs one line [evidence: test:tests/test_registry.py::test_failed_reload_keeps_tools]
- AC6: overlapping reloads are serialised and never interleave load_tools calls [evidence: test:tests/test_registry.py::test_reloads_serialised]
- AC7: periodic reload runs every reload_every seconds and stops on stop [evidence: test:tests/test_registry.py::test_periodic_reload]
- AC8: ctx.request_reload triggers a reload of that plugin [evidence: test:tests/test_registry.py::test_request_reload]
- AC9: lint passes [evidence: command:mise run lint]

## Files

- `src/any_mcp/registry.py`
- `tests/test_registry.py`

## Interfaces

`any_mcp.registry` (the `tool-registry` part): `@dataclass(frozen=True) ExposedTool(name: str, plugin: LoadedPlugin, spec: ToolSpec, input_schema: dict, listed_schema: dict, output_schema: dict | None)`, `class ToolRegistry(plugins: Sequence[LoadedPlugin], settings: ToolSettings)` with `async start()`, `async stop()`, `tools() -> list[ExposedTool]`, `get(name: str) -> ExposedTool | None`, `async reload(plugin: str | None = None) -> bool`, `add_listener(cb: Callable[[], Awaitable[None]])`, `async run_periodic()`, `request_reload(plugin: str) -> None`.

## Expected outcome

Any number of plugins appear as one sorted, collision-free, schema-normalised tool list that reloads safely and reports real changes only.

## Steps

- Write `tests/test_registry.py` with in-test plugins whose `load_tools` returns specs from a mutable list and records calls; run `uv run --frozen pytest tests/test_registry.py -q`; expect import errors.
- Implement `src/any_mcp/registry.py`; rerun (all pass), then `mise run lint`.

## Notes

Swap the list atomically (build the new list, then assign) so a concurrent `tools()` never sees a half-reloaded state. Reload correctness must not depend on any notification reaching a client (prior-art trap 5); listeners only let the adapter send one. Per-session tool sets are non-conformant on the 2026-07-28 protocol (docs brief 1.15), hence one global list.
