---
title: Config model
status: todo
repo: any-mcp
value: "One validated YAML file configures the server and every plugin, with clear errors"
files: [src/any_mcp/config.py, tests/test_config.py]
verify: "uv run --frozen pytest tests/test_config.py -q && mise run lint"
depends_on: [core-types]
owns: [any-mcp-config]
uses: [tool-errors]
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

# Config model

## Requirement

Define the any-mcp YAML config file and its loader (design D5). This is the `any-mcp-config` contract the agent-orchestrator epic renders into a ConfigMap.

- Pydantic models, all `extra="forbid"`: `AnyMcpConfig(server, tools, python_path, plugins)`, `ServerSettings(name="any-mcp", instructions=None, transport="stdio" | "http", log_level="info", http)`, `HttpSettings(host="127.0.0.1", port=8000, path="/mcp", bearer_token=None, allowed_origins=[])`, `ToolSettings(max_name_length=60 (16 to 128), list_ttl_ms=30000, cache_scope="public" | "private", response_budget_chars=40000)`, `PluginEntry(name, plugin, namespace=None, allow=[], tags=[], timeout=None, reload_every=None, config={})`.
- `PluginEntry.name` matches `^[a-z][a-z0-9_-]{0,19}$`; two entries with the same name are rejected.
- `load_config(path, *, env=None) -> AnyMcpConfig`: reads YAML; expands `${VAR}` and `${VAR:-default}` in every string value, nested ones included, from `env` (default `os.environ`); a missing variable with no default raises `ConfigError` naming the variable and the key path; records the config file's directory as `base_dir` and resolves `python_path` entries against it.
- `config_from_plugins(refs) -> AnyMcpConfig`: one entry per `--plugin` reference with defaults; the entry name is the lowercased class name for `module:Class` and the reference itself for an entry-point name.
- Every failure (unreadable file, YAML error, a non-mapping top level, an unknown key, a validation error) raises `ConfigError` whose message names the file and the dotted key path.

## Acceptance conditions

- AC1: a config with one plugin entry loads with every default from design D5 [evidence: test:tests/test_config.py::test_defaults]
- AC2: VAR and VAR-with-default expansion works in nested strings and a missing variable raises ConfigError naming variable and key [evidence: test:tests/test_config.py::test_env_expansion]
- AC3: unknown keys at any level raise ConfigError with the dotted key path [evidence: test:tests/test_config.py::test_unknown_keys_rejected]
- AC4: plugin entry names follow the pattern and duplicates are rejected [evidence: test:tests/test_config.py::test_plugin_entry_rules]
- AC5: python_path entries resolve against the config file directory, recorded as base_dir [evidence: test:tests/test_config.py::test_python_path_relative_to_config]
- AC6: config_from_plugins builds one default entry per reference with the specified names [evidence: test:tests/test_config.py::test_config_from_plugins]
- AC7: unreadable files, YAML errors and non-mapping documents raise ConfigError naming the file [evidence: test:tests/test_config.py::test_invalid_files]
- AC8: lint passes [evidence: command:mise run lint]

## Files

- `src/any_mcp/config.py`
- `tests/test_config.py`

## Interfaces

`any_mcp.config`: `AnyMcpConfig`, `ServerSettings`, `HttpSettings`, `ToolSettings`, `PluginEntry`, `load_config(path: Path | str, *, env: Mapping[str, str] | None = None) -> AnyMcpConfig`, `config_from_plugins(refs: Sequence[str]) -> AnyMcpConfig`, `AnyMcpConfig.base_dir: Path | None`. Raises `any_mcp.errors.ConfigError`. Cross-epic contract `any-mcp-config` (consumer: agent-orchestrator).

## Expected outcome

One validated config object drives discovery, the registry and the transports; a bad config fails with a message that names exactly what is wrong.

## Steps

- Write `tests/test_config.py` using `tmp_path` YAML files; run `uv run --frozen pytest tests/test_config.py -q`; expect import errors.
- Implement `src/any_mcp/config.py`; rerun (all pass), then `mise run lint`.

## Notes

Mirror claude-code-wrapper's config rules (`${VAR}` / `${VAR:-d}` interpolation, unknown keys rejected). `bearer_token` may be a `SecretStr`; never include its value in an error message.
