---
title: anymcp source plugin loading
status: in-progress
repo: any-mcp
value: a config entry or a CLI call installs and loads a plugin from a git repo or a local dir
files: [src/any_mcp/config.py, src/any_mcp/discovery.py, src/any_mcp/cli.py, docs/configuration.md, tests/test_source_plugins.py, tests/fixtures/source_plugin/pyproject.toml, tests/fixtures/source_plugin/src/source_plugin/__init__.py]
verify: "uv run --frozen pytest -q tests/test_source_plugins.py tests/test_cli.py tests/test_discovery.py tests/test_config.py tests/test_docs_reference.py && mise run lint"
depends_on: [anymcp-source-installer]
model: opus
review: ""
verified_head: ""
points: 5
expected_minutes: 11
expected_tokens: 1694306
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# anymcp source plugin loading

## Requirement

Goal G2 (epic README), verbatim: "any-mcp installs and loads plugins from Terraform-module-like sources: git repo with optional //subdir and ?ref=, and local directory paths." User request, verbatim: "It must still be possible (when using pip installed any-mcp) to provide path to local dir, where plugin is defined (again- similar to terraform module handling)."

Design D2, verbatim: "`PluginEntry` gains `source: str | None`; `plugin` becomes optional. Exactly one rule: an entry has a `plugin` or a `source` or both; with a `source`, `plugin` is an entry-point name (never `module:Class`) that picks among the source package's `any_mcp.plugins` entry points, required only when the package declares more than one. The `source` string is validated by `parse_source` at config load. `name` stays required."

Design D4, verbatim: "New subcommand `any-mcp plugins install [--config PATH] [SOURCE ...]` installs each given source, or every `plugins[].source` of the config, as an explicit install (refreshes branch and tag refs). It reads only the `source` strings (expanding `${VAR}` in those strings alone), so a config whose plugin `config` names variables unset in the install environment still installs (my call: the onStart hook does not carry the agent's runtime env). Errors exit 78 with one line. At server startup (`load_plugins`, all three paths), a source entry missing from the manifest is installed first, then loaded."

Scope (any-mcp):
- `src/any_mcp/config.py`: `PluginEntry.source`, optional `plugin`, the D2 validation.
- `src/any_mcp/discovery.py`: `load_plugins` resolves source entries through `any_mcp.install` (install on a manifest miss, base dir = the config's `base_dir`), then loads the chosen entry point.
- `src/any_mcp/cli.py`: the `plugins install` subcommand; every existing invocation keeps working.
- `docs/configuration.md`: `plugins[].source`, the changed `plugins[].plugin` row, the `plugins install` command, `ANY_MCP_CACHE_DIR` (the "only variable" sentence is no longer true), and the trust model: a source is operator-trusted code installed into the server's environment.
- Tests in `tests/test_source_plugins.py` with a fixture plugin package under `tests/fixtures/source_plugin/` (pyproject with one `any_mcp.plugins` entry point).

## Acceptance conditions

- ac1: an entry with a source and no plugin validates, an entry with neither is refused, with a source a module:Class plugin value is refused, and an invalid source string fails config load with the parser's message [evidence: test:tests/test_source_plugins.py::test_entry_source_validation]
- ac2: load_plugins installs a source entry missing from the manifest and loads its single any_mcp.plugins entry point; with several entry points plugin picks one, and without plugin the load fails naming them [evidence: test:tests/test_source_plugins.py::test_load_plugins_source_entries]
- ac3: any-mcp plugins install SOURCE... installs each given source with refresh, and --config PATH installs every plugins[].source of the file, expanding ${VAR} only inside source strings, so a config whose plugin config names an unset variable still installs [evidence: test:tests/test_source_plugins.py::test_plugins_install_command]
- ac4: an install or load failure exits 78 with one stderr line naming the source [evidence: test:tests/test_source_plugins.py::test_install_failure_exit_code]
- ac5: end to end in a fresh venv with pip, any-mcp installed from the working tree installs the fixture plugin from a local path and from a git::file:// repository with //subdir and ?ref=, and --list-tools lists its tool for each [evidence: test:tests/test_source_plugins.py::test_end_to_end_local_and_git_sources]
- ac6: existing invocations keep working: the CLI, discovery, config and docs tests pass [evidence: command:uv run --frozen pytest -q tests/test_cli.py tests/test_discovery.py tests/test_config.py tests/test_docs_reference.py tests/test_docs_links.py]
- ac7: docs/configuration.md documents plugins[].source, the plugins install command and ANY_MCP_CACHE_DIR [evidence: command:grep -qF 'plugins[].source' docs/configuration.md && grep -qF 'any-mcp plugins install' docs/configuration.md && grep -qF 'ANY_MCP_CACHE_DIR' docs/configuration.md]
- ac8: lint passes [evidence: command:mise run lint]

## Files

- `src/any_mcp/config.py`
- `src/any_mcp/discovery.py`
- `src/any_mcp/cli.py`
- `docs/configuration.md`
- `tests/test_source_plugins.py`
- `tests/fixtures/source_plugin/pyproject.toml`
- `tests/fixtures/source_plugin/src/source_plugin/__init__.py`

## Interfaces

- `src/any_mcp/config.py:PluginEntry`: `plugin: str | None = None`, `source: str | None = None`; a model validator enforcing design D2 and calling `any_mcp.sources.parse_source` on `source`.
- `src/any_mcp/discovery.py:load_plugins(config, *, http_transport=None)`: unchanged signature; source entries go through `any_mcp.install.installed(...)`, else `install(..., refresh=False)`, base dir `config.base_dir`.
- CLI: `any-mcp plugins install [--config PATH] [SOURCE ...]`, exit 0 on success, 78 with one stderr line on a ConfigError, printing one line per installed source (`<source> <distribution> <sha or local>`).
- `tests/fixtures/source_plugin/`: a hatchling package `any-mcp-source-plugin` exposing entry point `source_plugin` with one tool.

## Expected outcome

An any-mcp config entry `{name: x, source: <git or local source>}` installs and loads like any other plugin, and `any-mcp plugins install` pre-installs sources for a hook.

## Steps

- Red: write `tests/test_source_plugins.py` and the fixture package; run `uv run --frozen pytest -q tests/test_source_plugins.py`: fails.
- Green: config, discovery and CLI changes; run the task's verify: passes.
- Docs: update `docs/configuration.md`; run ac6 and ac7 commands: pass.

## Notes

- Rulings and their pin tests: with a source, `plugin` names an entry point, never `module:Class` (test_entry_source_validation); `plugins install --config` expands `${VAR}` only inside source strings (test_plugins_install_command, with a config whose plugin config names an unset variable); install-on-miss at startup does not refresh (test_load_plugins_source_entries).
- The end-to-end test follows `tests/test_release.py`: `uv venv --seed` in `tmp_path`, install any-mcp from `ROOT` (the working tree, not a git URL, so uncommitted work counts), then run the venv's `any-mcp`; set `ANY_MCP_CACHE_DIR` into `tmp_path`. The git variant commits the fixture into a temp repo under a subdir and tags it.
- The subcommand must not break `any-mcp --config ...` or `any-mcp --plugin ...` with no subcommand (ac6 covers the CLI tests).
- `tests/test_docs_reference.py` requires every top-level config key and CLI flag documented; `ANY_MCP_CONFIG is the only variable` is no longer true and changes in configuration.md.
- `tests/test_import_boundary.py` scans `src/any_mcp` and `examples`: keep fastmcp imports out of the new code.
