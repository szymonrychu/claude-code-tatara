---
title: OpenAPI plugin
status: done
repo: any-mcp
value: Any OpenAPI 3 API becomes a curated set of tools with config only
files: [src/any_mcp/openapi.py, tests/test_openapi.py, tests/fixtures/openapi/petstore.yaml, tests/fixtures/openapi/recursive.json]
verify: "uv run --frozen pytest tests/test_openapi.py -q && mise run lint"
depends_on: [testing-harness]
owns: [openapi-plugin]
uses: [plugin-abc, schema-tools, tool-types, plugin-harness]
model: sonnet
estimate: 6
estimate_by: formula
actual: ""
actual_roles: ""
review: ""
worktree: /Users/szymonri/Documents/claude-code-tatara/.claude/worktrees/any-mcp-openapi-plugin/any-mcp
branch: any-mcp-openapi-plugin
verified_head: 5d7213c7b2e773d8785c7628c7841c164ae6a187
run: any-mcp
provides: []
acs_for_audit: []
process_gaps: []
---

# OpenAPI plugin

## Requirement

Ship the built-in `OpenAPIPlugin` that turns an OpenAPI document into tools through the plugin hooks (design D12).

- `OpenAPIPlugin(Plugin)` with `name = "openapi"` and `Config(spec: str, base_url: str | None = None, allow: list[str] = [], tags: list[str] = [], headers: dict[str, str] = {}, bearer_token: str | None = None)`; it is `_abstract`-exempt from the `load_tools` class check because it overrides `load_tools`.
- `spec` is a file path (relative to the config file directory) or an `http(s)` URL fetched with `ctx.http`; JSON or YAML; OpenAPI 3.0.x and 3.1.x. A Swagger 2.0 document raises `ConfigError` saying only OpenAPI 3 is supported.
- Selection: operations whose `operationId` matches an `allow` glob or that carry one of `tags`; with both empty, `load_tools` raises `ConfigError` with `set allow or tags in the openapi plugin config (allow: ["*"] exposes every operation)`.
- Each selected operation becomes a `ToolSpec`: name = `operationId`, else `<method>_<path with non-alphanumerics as _>`; description = summary and description joined (method and path when both are missing); path, query and header parameters become properties (`required` from the parameter); an `application/json` request body becomes one `body` property (required when the body is); tags from the operation; `HttpBinding(method, path, query=..., headers=..., body="body" or None)`.
- Only local `$ref`s resolve, through `normalize_schema` with the spec as root (cycles cut); an external `$ref` raises `ConfigError` naming it.
- `base_url` from config, else the first `servers[].url` (a relative one resolved against the spec URL); a spec with neither and no config `base_url` raises `ConfigError`.
- `credentials()` returns `headers` plus `Authorization: Bearer <bearer_token>` when set.
- Subclasses may override any hook, and `spec`/`allow` defaults may come from subclass `Config` defaults.

## Acceptance conditions

- AC1: OpenAPI 3.0 YAML and 3.1 JSON specs load from a relative file and from a URL through ctx.http [evidence: test:tests/test_openapi.py::test_loads_specs_from_file_and_url]
- AC2: operations are selected by allow globs or tags, and with neither load_tools raises ConfigError with the guidance message [evidence: test:tests/test_openapi.py::test_selection_requires_filter]
- AC3: tool names come from operationId with the method and path fallback, and descriptions from summary and description [evidence: test:tests/test_openapi.py::test_tool_names_and_descriptions]
- AC4: parameters and the JSON body map to properties, required flags and an HttpBinding [evidence: test:tests/test_openapi.py::test_parameter_and_body_mapping]
- AC5: local refs resolve, recursive schemas are cut and an external ref raises ConfigError naming it [evidence: test:tests/test_openapi.py::test_ref_handling]
- AC6: a Swagger 2.0 document is rejected with ConfigError [evidence: test:tests/test_openapi.py::test_swagger2_rejected]
- AC7: base_url comes from config or servers, and static headers and bearer_token are sent as credentials [evidence: test:tests/test_openapi.py::test_base_url_and_credentials]
- AC8: through PluginHarness with a MockTransport, listPets sends GET /pets?limit=2 and returns structured JSON [evidence: test:tests/test_openapi.py::test_end_to_end_with_harness]
- AC9: lint passes [evidence: command:mise run lint]

## Files

- `src/any_mcp/openapi.py`
- `tests/test_openapi.py`
- `tests/fixtures/openapi/petstore.yaml`
- `tests/fixtures/openapi/recursive.json`

## Interfaces

`any_mcp.openapi.OpenAPIPlugin` (the `openapi-plugin` part) and `OpenAPIPlugin.Config`; helper `operations_to_specs(spec: Mapping[str, Any], *, allow: Sequence[str], tags: Sequence[str]) -> list[ToolSpec]` for subclasses and tests.

## Expected outcome

A config entry `plugin: any_mcp.openapi:OpenAPIPlugin` with `config: {spec: ./petstore.yaml, allow: [listPets]}` exposes `listPets` as a validated, HTTP-bound tool with no code.

## Steps

- Write `tests/fixtures/openapi/petstore.yaml` (OpenAPI 3.0: listPets, getPet, createPet, a tagged admin operation) and `tests/fixtures/openapi/recursive.json` (OpenAPI 3.1 with a self-referencing schema and a chained `$ref`), then `tests/test_openapi.py`; run `uv run --frozen pytest tests/test_openapi.py -q`; expect import errors.
- Implement `src/any_mcp/openapi.py`; rerun (all pass), then `mise run lint`.

## Notes

Converted in-house rather than with FastMCP's OpenAPIProvider so every call goes through the plugin hooks and plugins never touch FastMCP (prior-art F8, F10). External refs stay unresolved to avoid SSRF (prior-art O5). FastMCP's docs recommend curated subsets over whole-API mirrors, hence the required filter (prior-art trap 4).
