---
title: Plugin discovery
status: in-progress
repo: any-mcp
value: Plugins load from installed packages or plain files named in the config
files: [src/any_mcp/discovery.py, tests/test_discovery.py]
verify: "uv run --frozen pytest tests/test_discovery.py -q && mise run lint"
depends_on: [plugin-abc, config-model]
owns: [plugin-loader]
uses: [plugin-abc, any-mcp-config]
model: sonnet
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

# Plugin discovery

## Requirement

Resolve plugin references and instantiate configured plugins with their contexts (design D4, D5).

- `resolve_plugin_class(ref, *, python_path=()) -> type[Plugin]`: `module:Class` imports the module (after prepending each `python_path` directory to `sys.path` once) and takes the attribute; a bare name looks up the entry point of that name in group `any_mcp.plugins`. A missing module, missing attribute, unknown entry point, or a target that is not a `Plugin` subclass raises `ConfigError` naming the reference.
- `load_plugins(config, *, http_transport=None) -> list[LoadedPlugin]`, in config order: validate the entry's `config` with the class's `Config` (errors become `ConfigError` naming `plugins[<i>].config.<field>`), create the instance, build its `PluginContext` with `name` the entry name, `namespace` the entry namespace when not `None` else the entry name, `http` from `make_client(base_url, transport=http_transport, timeout=...)` where `base_url` is the validated config's `base_url` attribute when the `Config` model has one, a logger named `any_mcp.plugin.<name>`, and `response_budget_chars` from `config.tools`.
- `LoadedPlugin.timeout` and `.reload_every` come from the entry when set, else from the class.
- Two entries with the same class give two independent instances with separate contexts and clients.
- No directory scanning.

## Acceptance conditions

- AC1: a module:Class reference resolves, with python_path directories added to sys.path once [evidence: test:tests/test_discovery.py::test_module_class_reference]
- AC2: a bare name resolves through the any_mcp.plugins entry-point group [evidence: test:tests/test_discovery.py::test_entry_point_reference]
- AC3: missing modules, attributes, entry points and non-Plugin targets raise ConfigError naming the reference [evidence: test:tests/test_discovery.py::test_bad_references]
- AC4: plugin config is validated by the Config model and errors name the plugins index and field [evidence: test:tests/test_discovery.py::test_plugin_config_validation]
- AC5: namespace, timeout and reload_every come from the entry over the class defaults [evidence: test:tests/test_discovery.py::test_entry_overrides]
- AC6: ctx.http uses the Config base_url and the given transport [evidence: test:tests/test_discovery.py::test_context_http_client]
- AC7: two entries of one class are independent instances [evidence: test:tests/test_discovery.py::test_two_instances_of_one_class]
- AC8: lint passes [evidence: command:mise run lint]

## Files

- `src/any_mcp/discovery.py`
- `tests/test_discovery.py`

## Interfaces

`any_mcp.discovery` (the `plugin-loader` part): `ENTRY_POINT_GROUP = "any_mcp.plugins"`, `resolve_plugin_class(ref: str, *, python_path: Sequence[Path] = ()) -> type[Plugin]`, `@dataclass LoadedPlugin(entry: PluginEntry, plugin: Plugin, namespace: str, timeout: float, reload_every: float | None, ctx: PluginContext)`, `load_plugins(config: AnyMcpConfig, *, http_transport: httpx.AsyncBaseTransport | None = None) -> list[LoadedPlugin]`.

## Expected outcome

A config file or `--plugin` list turns into ready plugin instances, each with its own validated config and HTTP client, before any hook runs.

## Steps

- Write `tests/test_discovery.py` with plugin modules written under `tmp_path` and entry points monkeypatched on `importlib.metadata.entry_points`; run `uv run --frozen pytest tests/test_discovery.py -q`; expect import errors.
- Implement `src/any_mcp/discovery.py`; rerun (all pass), then `mise run lint`.

## Notes

`setup()` is not called here; the registry owns the lifecycle. Prior art for entry points plus `module:Class`: simonw/llm and IBM context-forge (prior-art D1, D4).
