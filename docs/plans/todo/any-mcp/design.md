# any-mcp design

## Summary

any-mcp is a Python MCP server that does nothing on its own: every tool comes from a plugin. A
plugin subclasses `any_mcp.Plugin` and implements one required hook, `load_tools()`, plus any of
the optional hooks (`setup`, `teardown`, `credentials`, `before_call`, `call`, `shape_response`,
`on_error`), whose defaults do the common proxy work (HTTP binding, argument validation, response
shaping, error mapping, reload). It runs over stdio by default and over streamable HTTP with
`--transport http`. The MCP protocol layer is FastMCP 4.x, reached only through one adapter
module, so plugins never import `fastmcp`. v1 serves tools only and ships as git tag `v0.1.0`,
installable with `pip install "any-mcp @ git+https://github.com/szymonrychu/any-mcp@v0.1.0"`.

## Intent and why

The user wants an "MCP to API proxy": one server that takes all the common MCP work (transports,
protocol eras, schemas, validation, errors, reload) under one umbrella and asks its users only for
the business logic of an API, as a small plugin. Writing one MCP server per API repeats that work
every time and couples each server to a fast-moving framework (FastMCP shipped three majors in
about ten months, prior-art brief F1/F2). The immediate consumer is the agent-orchestrator epic:
every agent session starts with any-mcp preinstalled from a pinned git tag, so the CLI, the
config format and the release tag are cross-epic contracts.

## Goals

- G1: a plugin is one class: `load_tools()` (or one `@tool` method) is the only thing it must
  provide; every other hook has a working default.
- G2: plugins load from the entry-point group `any_mcp.plugins` and from `module:Class` entries in
  the config file (with optional `python_path` directories), several at once (a group of APIs).
- G3: one entrypoint `any-mcp`: stdio by default, streamable HTTP with `--transport http`; both the
  2026-07-28 protocol and handshake-era (`<=2025-11-25`) clients work.
- G4: argument validation, exception-to-`isError` mapping, namespacing, deterministic tool order,
  `ttlMs`/`cacheScope`, name sanitising, schema normalising and a response size budget are done by
  the core, never by plugins.
- G5: a built-in `OpenAPIPlugin` (the big example's base) and runnable, tested examples: hello
  (one method), single-endpoint, a decorator multi-tool plugin with auth, a packaged OpenAPI
  plugin, and a multi-plugin group config.
- G6: docs with their own acceptance conditions: README, concepts, plugin authoring guide (small
  and big), testing plugins, configuration reference, transport reference.
- G7: CI on GitHub Actions (`mise run lint`, `mise run test`) and a release workflow; tag `v0.1.0`
  installs with pip from git and `any-mcp --help` exits 0.
- G8: any-mcp is a standard pyproject package with the console script `any-mcp`, installable the same
  ways as claude-code-wrapper: `pip install any-mcp` (package-index name), `pip install
  git+https://github.com/szymonrychu/any-mcp`, `pip install .`, `pipx install any-mcp`, `uv tool
  install any-mcp`; `any-mcp --version` works and the README documents every form.

## Non-goals

- No business-logic plugins beyond the examples.
- No auth gateway (no OAuth server, no per-user consent, no token exchange); client tokens are
  never forwarded downstream.
- No MCP resources or prompts from plugins in v1 (tools only), no MRTR (`InputRequiredResult`)
  surface for plugins.
- No server-initiated sampling, elicitation, roots or MCP logging (deprecated in 2026-07-28).
- No legacy HTTP+SSE transport.

## Anti-goals

- A plugin that imports `fastmcp` or `mcp` to work: that couples every plugin to a framework major.
- Correctness that depends on `tools/list_changed` reaching the client (Cursor ignores it, and it
  only reaches `subscriptions/listen` subscribers).
- A plugin exception surfacing as JSON-RPC `-32603` instead of an `isError` result the model can
  read.
- Mirroring a whole API 1:1 by default (context bloat): the OpenAPI plugin needs an explicit filter.
- Anything other than MCP messages on stdout in stdio mode.
- Inbound `Authorization` headers or cookies reaching any outbound request.

## Constraints

- New component repo at `code/any-mcp` (public GitHub origin `szymonrychu/any-mcp`, created by the
  orchestrator after the gate). The `scaffold` task creates the layout inside it.
- Python `>=3.12`, uv (`uv.lock` committed), hatchling, ruff (line length 100, rules E F I UP B
  SIM), pytest with pytest-asyncio auto mode, mise tasks `lint` and `test`, GitHub Actions CI. These
  mirror `code/claude-code-wrapper/pyproject.toml` and `mise.toml`.
- Runtime dependencies are declared once by `scaffold`: `fastmcp>=4.1,<5`, `pydantic>=2`,
  `jsonschema>=4.23`, `pyyaml`, `httpx`. Later tasks do not edit `pyproject.toml` or `uv.lock`
  except `release`.
- Only `src/any_mcp/_fastmcp_adapter.py` imports `fastmcp` or `mcp`; a test enforces it.
- Task verify commands are `uv run --frozen pytest <named test files> -q && mise run lint`.
- MIT license, matching the sibling components.

## Decisions

### D1: Build on FastMCP 4.x behind any-mcp's own plugin ABC

any-mcp depends on `fastmcp>=4.1,<5` (which brings `mcp>=2.2,<3`) and uses it only from
`_fastmcp_adapter.py`: a FastMCP `Provider` lists the registry's tools as FastMCP `Tool`
subclasses with raw JSON-schema `parameters` whose `run()` calls the any-mcp call pipeline.
Alternatives: the official SDK low-level `Server` (re-implements validation, error mapping,
transports and era negotiation; its middleware is provisional), building from scratch (same, more).
Why: FastMCP 4 already serves both protocol eras, both transports and raw-schema tools; hiding it
keeps a FastMCP major to one adapter rewrite. Fallback if FastMCP blocks something: the adapter
targets `mcp.server.MCPServer` plus `SubscriptionBus`. (my call, user-proposed; open question Q1.)
Serves G.

### D2: The plugin contract

`class Plugin(ABC)` in `src/any_mcp/plugin.py` with class attributes `name` (default namespace),
`Config` (a pydantic model, default `NoConfig`), `reload_every: float | None`, `timeout: float`
(default 30 s), an instance attribute `ctx: PluginContext` set by the core before `setup()`, and
async hooks: `setup()`, `teardown()`, `load_tools() -> Sequence[ToolSpec]`,
`credentials(call) -> Mapping[str, str]`, `before_call(call) -> ToolCall` (raise `Deny` to
refuse), `call(call) -> RawResponse`, `shape_response(call, raw) -> ToolResult`,
`on_error(call, exc) -> ToolResult`. `load_tools` is the one required hook: the `@tool` method
decorator builds `ToolSpec`s from type hints and docstrings, and the default `load_tools` returns
them, so a class must either override `load_tools` or define at least one `@tool` method, else
defining the class raises `TypeError` naming `load_tools`. All hooks are async; there is no pluggy.
Alternatives: pluggy hookspecs (sync only), FastMCP Providers as the plugin type (couples plugins to
FastMCP). (my call.) Serves A, E.

### D3: Declarative HTTP binding and the default call

`ToolSpec.http = HttpBinding(method, path, query, headers, body, base_url)` lets a plugin describe
an endpoint with no call code: the default `call()` fills `{name}` path segments, query
parameters, headers and a JSON body from the validated arguments, adds `credentials()` headers and
sends it with `ctx.http`, an `httpx.AsyncClient` owned by the core (base URL from the plugin
config's `base_url` when present). A status `>= 400` raises `UpstreamError`. `ToolSpec.handler` (set
by `@tool`) runs Python instead. any-mcp depends on `httpx` itself and never exposes FastMCP's HTTP
client to plugins. (my call.) Serves A, E.

### D4: Plugin discovery

Plugins load from the entry-point group `any_mcp.plugins` (`[project.entry-points."any_mcp.plugins"]
petstore = "petstore_plugin:PetstorePlugin"`) and from `module:Class` references, with optional
`python_path` directories (relative to the config file) prepended to `sys.path` so a single-file
plugin needs no packaging. `--plugin <ref>` (repeatable) on the CLI adds an entry without a
config file. No directory scanning and no pluggy. A reference that does not resolve to a `Plugin`
subclass is a config error naming the reference. (my call.) Serves E.

### D5: One YAML config file

`--config <path>` (or `ANY_MCP_CONFIG`): keys `server` (`name`, `instructions`, `transport`,
`log_level`, `http.{host, port, path, bearer_token, allowed_origins}`), `tools`
(`max_name_length` 60, `list_ttl_ms` 30000, `cache_scope` `public`, `response_budget_chars`
40000), `python_path`, and `plugins[]` (`name`, `plugin`, `namespace`, `allow`, `tags`, `timeout`,
`reload_every`, `config`). `${VAR}` and `${VAR:-default}` expand in every string value, unknown keys
are rejected, each plugin's `config` is validated by its `Config` model. An invalid config, or a
plugin that fails to load, `setup()` or its first `load_tools()`, exits 78 with one stderr line
naming the key or plugin. CLI flags override `server.transport` and `server.http.*`. (my call;
78 mirrors claude-code-wrapper.) Serves E, B.

### D6: The tool list

Exposed names are `<namespace>_<tool>` (namespace defaults to the plugin entry `name`; `""` means
no prefix), sanitised to `[A-Za-z0-9_.-]`, and when longer than `max_name_length` truncated with a
stable `_<6 hex of sha1(full name)>` suffix; two tools with the same exposed name are a startup
error naming both. `allow` (globs on plugin-local names) and `tags` filter each plugin's tools.
The list is global (never per connection), sorted by exposed name, and served with `ttlMs` =
`list_ttl_ms` and `cacheScope` = `cache_scope`. Input schemas are normalised: local `$ref`s are
inlined, recursion is cut at depth 8, a root `anyOf`/`oneOf` of object schemas is flattened into
one object for listing (validation still uses the original), a no-argument tool gets
`{"type": "object", "additionalProperties": false}`, and a non-object root is a load error. (my
call.) Serves A.

### D7: The call pipeline and error mapping

`pipeline.call_tool(registry, name, arguments)`: unknown name raises `UnknownTool` (the adapter
returns JSON-RPC `-32602`); otherwise validate arguments against the original schema with
`jsonschema` Draft 2020-12 (a string that parses as JSON of the expected object or array type is
accepted, a known Claude Code quirk), then `before_call`, `credentials` and `call` under the
plugin's timeout, then `shape_response`. Any exception from validation or a hook goes to
`on_error`; the default `on_error` (and the fallback when `on_error` itself raises) returns an
`isError: true` result with a text message and `structuredContent` `{"error": {"kind",
"message", "status"?}}`, `kind` one of `invalid_arguments`, `denied`, `upstream`, `timeout`,
`internal`. Internal errors show the exception type, never a traceback or credential. Each call
logs one stderr line (request id, tool, duration, outcome), never arguments or headers. (user
decision for the error and validation rules; shapes my call.) Serves A, G.

### D8: Reload

`load_tools()` runs at startup, every `reload_every` seconds when set (the plugin entry's config `reload_every` overrides the `Plugin` class attribute `reload_every`),
and after `ctx.request_reload()`. Reloads are serialised under one `asyncio.Lock`; the new list is
diffed against the old and change listeners fire only on a real change; the adapter then sends the
tool-list-changed notification FastMCP supports. A reload that raises keeps the previous tools of
that plugin and logs one stderr line. Correctness never depends on the notification: the next
`tools/list` is always current, and `ttlMs` is short. (user decision for not relying on
`list_changed`; mechanism my call.) Serves A, G.

### D9: Default response shaping

`response.shape_default(raw, budget_chars)`: a JSON body (or a handler's JSON-serialisable value)
becomes `structuredContent` plus a compact JSON `TextContent` copy; `text/*` becomes text; other
bytes become a one-line description (`<n> bytes of <content type>`); an empty body becomes
`OK (<status>)`. Over `response_budget_chars` (default 40000, under Claude Code's 10k-token
warning) the text is truncated with `[truncated: <shown> of <total> chars]` and
`structuredContent` is dropped; for a tool with an `output_schema` an over-budget response is an
`isError` result naming the size, because its structured content must conform. (my call.) Serves A.

### D10: Transports

`any-mcp` defaults to stdio: stdout carries only MCP messages, logs go to stderr, the process exits
0 on stdin EOF and tears plugins down on SIGTERM. `--transport http` serves streamable HTTP at
`server.http.path` (default `/mcp`) on `127.0.0.1:8000` by default, through FastMCP, with both
protocol eras. Requests whose `Origin` is not loopback or in `allowed_origins` get 403. When
`bearer_token` is set, requests without `Authorization: Bearer <token>` get 401; binding a
non-loopback host without a token logs a stderr warning. `--transport sse` does not exist.
(my call within the user's "stdio default, s-http possible".) Serves B.

### D11: No inbound credential ever reaches an outbound request

Outbound credentials come only from a plugin's `credentials()` hook and its config (env-expanded).
`ToolCall` carries no inbound headers, `ctx.http` is created by the core with no inbound headers,
and no forwarding option exists. (user decision.) Serves G.

### D12: Built-in OpenAPIPlugin, converted in-house

`any_mcp.openapi.OpenAPIPlugin` reads an OpenAPI 3.0 or 3.1 spec (JSON or YAML, file path relative
to the config file, or URL fetched with `ctx.http`) and turns each selected operation into a
`ToolSpec` with an `HttpBinding`: name from `operationId` (else `<method>_<path slug>`),
description from summary and description, path/query/header parameters as properties, a JSON
request body under one `body` property. Only local `$ref`s resolve (an external ref is a load
error, no SSRF); cycles are cut by the D6 normaliser. Selection needs `allow` (operationId globs)
or `tags` in its config; with neither, loading fails with a message telling the user to set one
(or `allow: ["*"]`). Config also takes `base_url`, static `headers` and `bearer_token` (env
expanded), sent through `credentials()`. Swagger 2.0 is a load error. Alternative: wrap FastMCP's
`OpenAPIProvider` (bypasses the plugin hooks and couples the plugin to FastMCP; fastmcp#1372
chained-`$ref` bug). (my call; open question Q5.) Serves D.

### D13: A testing harness for plugin authors

`any_mcp.testing.PluginHarness(plugin, config=..., transport=httpx.MockTransport(...))` and
`PluginHarness.from_config(path, transport=...)` start the real server in memory (through the
adapter) and expose `list_tools()`, `call(tool, arguments)` (accepting the plugin-local or exposed
name) and `reload()`, returning plain dicts and a `HarnessResult(text, structured, is_error)`.
Every example is tested with it, offline. (my call.) Serves D, E.

### D14: The documentation set, tested

`README.md` (what, install, 60-second quickstart, links), `docs/concepts.md` (plugin lifecycle,
hooks, call pipeline, reload, namespacing, errors, security), `docs/plugin-authoring.md` (small:
hello and single-endpoint; medium: decorator multi-tool with auth; big: packaged OpenAPI plugin;
groups of APIs), `docs/testing-plugins.md`, `docs/configuration.md` (every config key),
`docs/transports.md` (stdio, HTTP, protocol eras, Claude Code registration). Tests keep them true:
links resolve, every config key and CLI flag is documented, code blocks marked as an example file
equal that file. (user decision that docs are deliverables; set my call.) Serves C.

### D15: v1 is tools only

Plugins provide tools; no resources, prompts or MRTR in the v1 API, and the server declares only the
tools capability. (user decision; open questions Q2, Q3.) Serves H.

### D16: Release as a pinned git tag

Version `0.1.0` lives in `pyproject.toml` only (`any_mcp.__version__` reads package metadata).
`CHANGELOG.md`, a tag-triggered `.github/workflows/release.yml` (tag equals version, lint, test,
`pip install` from the git tag into a clean venv, `any-mcp --help`), and a test that installs from
`git+file://` at `HEAD` into a fresh venv. The orchestrator pushes tag `v0.1.0` after the epic
closes on `main`. (user decision for the tag; version number my call, open question Q4.) Serves H.

### D17: Repo and tooling

`code/any-mcp`: `src/any_mcp/` layout, uv, hatchling, ruff, pytest, mise `lint`/`test`/`fmt`
tasks, GitHub Actions CI on push and pull request running `mise run lint` and `mise run test`. (user
decision.) Serves F.

### D18: A standard pip-installable package, installed like claude-code-wrapper

any-mcp is a plain hatchling pyproject package named `any-mcp` with the console script `any-mcp`
(`any_mcp.cli:main`), so `pip install any-mcp` (from a package index), `pip install
git+https://github.com/szymonrychu/any-mcp`, `pip install .`, `pipx install any-mcp` and `uv tool install
any-mcp` all work and `any-mcp --version` prints the version. The README Installation section
lists those forms in the shape of `code/claude-code-wrapper/README.md` lines 46-54. A test builds the
wheel with `uv build --wheel`, installs it into a fresh venv and runs `any-mcp --version`; others
install from `git+file://` at `HEAD` and with `uv tool install`. Publishing to PyPI is not in scope:
claude-code-wrapper does not publish either (its workflows have no index upload). (user decision.)
Serves I.

## Research

| Lens | Ran or skipped | Adopted ideas | Rejected ideas |
|---|---|---|---|
| research-code-internal | skipped: new repo with no code to reuse; sibling conventions read directly (`code/claude-code-wrapper/pyproject.toml`, `mise.toml`) | ruff, pytest-asyncio and mise task layout from claude-code-wrapper; exit 78 on invalid config (claude-code-wrapper README) | none |
| research-code-external | ran: prior-art brief (FastMCP, MCP SDK, IBM context-forge, simonw/llm, Stainless, mcpo) | Provider seam and raw-schema `Tool` (F3, F4); pre/post hook vocabulary with modify-or-block (O7); entry points plus `module:Class` (D1, D4); allowlist and tag filters (O3); schema normalising and name limits (O4); response budget (C1); deterministic cacheable lists (P3) | pluggy (D2: sync only); directory scan (D4: path traversal surface); FastMCP `Namespace` transform (own naming owns truncation); meta-tool dynamic mode (O4: "can struggle to provide the correct properties"); config-file hot reload (O10: restart covers config changes) |
| research-papers | skipped: no algorithmic or scientific core | none | none |
| research-docs | ran: docs brief (MCP 2026-07-28 spec, `mcp` 2.x, FastMCP 4.x, Claude Code MCP docs) | dual-era server (spec versioning, FastMCP whats-new); stdout discipline and EOF exit (stdio transport spec); `ttlMs`/`cacheScope` (SEP-2549); `isError` vs `-32602` split (tools spec error handling); TextContent copy of structured content; Origin validation and loopback bind (streamable HTTP spec); Claude Code stdio registration forms (code.claude.com/docs/en/mcp) | HTTP+SSE transport (deprecated, SEP-2596); per-session tool sets (non-conformant for modern clients) |

## Research inputs

| Source | Entry | Lands in |
|---|---|---|
| prior-art Plan inputs | build on `fastmcp>=4.1,<5`, one adapter module | fastmcp-adapter, scaffold |
| prior-art Plan inputs | plugin ABC sketch (setup, teardown, load_tools, credentials, before_call, call, shape_response, on_error, reload_every) | plugin-abc, core-types |
| prior-art Plan inputs | `ToolSpec` with `HttpBinding` and handler | core-types, http-binding |
| prior-art Plan inputs | `@tool` decorator sugar | plugin-abc |
| prior-art Plan inputs | `OpenAPIPlugin` in-house with `$ref` inlining and cycle cutting | openapi-plugin, schemas-and-validation |
| prior-art Plan inputs | core owns arg validation and exception mapping | schemas-and-validation, call-pipeline |
| prior-art Plan inputs | namespacing, deterministic order, `ttlMs`/`cacheScope` | registry, fastmcp-adapter |
| prior-art Plan inputs | reload diffing, notify only on change | registry, fastmcp-adapter |
| prior-art Plan inputs | schema client profiles, name truncation and uniqueness | schemas-and-validation, registry |
| prior-art Plan inputs | response size budget | response-shaping |
| prior-art Plan inputs | allowlist and tag filters | registry, openapi-plugin |
| prior-art Plan inputs | opt-in meta-tool dynamic mode | rejected: allowlist and tag filters cover context size; Stainless reports dynamic mode struggles with properties (O4) |
| prior-art Plan inputs | stdio default and `--transport http` | cli-stdio, http-transport |
| prior-art Plan inputs | inbound auth via FastMCP auth providers | http-transport (static bearer token only; OAuth rejected: non-goal "no auth gateway") |
| prior-art Plan inputs | structured logging to stderr | cli-stdio, call-pipeline |
| prior-art Plan inputs | entry-point group `any_mcp.plugins` plus `module:Class`; no pluggy | plugin-discovery |
| prior-art Plan inputs | dev-only directory scan | rejected: `python_path` plus `module:Class` covers unpackaged plugins with no scan surface |
| prior-art Plan inputs | outbound secrets per plugin from config or env | plugin-abc, http-binding, openapi-plugin |
| prior-art Plan inputs | opt-in inbound bearer forwarding; header forwarding allowlist | rejected: user decision, client tokens are never forwarded (D11) |
| prior-art Plan inputs | docs and examples: small, medium, big, group, testing page | examples-small-medium, examples-big-group, docs-authoring |
| prior-art Plan inputs | open: does FastMCP 4 auto-notify on provider change | fastmcp-adapter (probe test) |
| prior-art Plan inputs | open: resources and prompts in v1 | D15, Q2 |
| prior-art Plan inputs | open: MRTR for plugins in v1 | D15, Q3 |
| prior-art Traps 1 | blind header or token passthrough | http-transport AC (inbound Authorization never reaches the upstream) |
| prior-art Traps 2 | exceptions out of handlers become -32603 | call-pipeline AC |
| prior-art Traps 3 | trusting declared schemas | call-pipeline AC |
| prior-art Traps 4 | mirroring a whole API | openapi-plugin AC (filter required) |
| prior-art Traps 5 | relying on list_changed | fastmcp-adapter AC (next list is current with no notification) |
| prior-art Traps 6 | plugins coupled to fastmcp | fastmcp-adapter AC (import boundary test) |
| prior-art Traps 7 | sync plugin frameworks | plugin-abc AC (all hooks async) |
| prior-art Traps 8 | server-initiated sampling, roots, logging | D15 (not in the API) |
| prior-art Traps 9 | unbounded directory scan | rejected with directory scan above |
| prior-art Traps 10 | per-session state | registry AC (one global list) |
| docs Plan inputs | pins: `fastmcp` 4.1.x, `mcp>=2.2,<3`, Python >=3.10 | scaffold (Python >=3.12 to match the agent image base) |
| docs Plan inputs | library decision | fastmcp-adapter (D1) |
| docs Plan inputs | notifications under one lock, both eras | registry, fastmcp-adapter |
| docs Plan inputs | tool list shape: global, sorted, `[A-Za-z0-9_.-]{1,128}`, object schemas, TextContent copy, `isError` | registry, schemas-and-validation, response-shaping, call-pipeline |
| docs Plan inputs | entrypoint: argv `--transport stdio|http`, loopback, Origin, no SSE, stderr logs, EOF exit | cli-stdio, http-transport |
| docs Plan inputs | Claude Code install forms (`claude mcp add`, `.mcp.json`, `--mcp-config`) | docs-reference (`docs/transports.md`) |
| docs Plan inputs | context gauge signals | rejected: belongs to the agent-orchestrator and claude-code-wrapper epics |
| docs Plan inputs | open gap: legacy `initialize` over stdio | cli-stdio AC |
| docs Plan inputs | open gap: FastMCP list_changed for out-of-request changes | fastmcp-adapter AC |
| docs Plan inputs | open gap: Claude Code v2 opens `subscriptions/listen` over stdio | rejected: client behaviour; D8 makes correctness independent of it |

## Decision coverage

| Decision | Tasks |
|---|---|
| D1 FastMCP behind the ABC | fastmcp-adapter, scaffold |
| D2 plugin contract | plugin-abc, core-types |
| D3 HTTP binding and default call | http-binding, plugin-abc |
| D4 discovery | plugin-discovery, cli-stdio |
| D5 config file | config-model, plugin-discovery |
| D6 tool list | schemas-and-validation, registry, fastmcp-adapter |
| D7 call pipeline and errors | core-types, call-pipeline, schemas-and-validation |
| D8 reload | registry, fastmcp-adapter |
| D9 response shaping | response-shaping |
| D10 transports | cli-stdio, http-transport |
| D11 no credential forwarding | http-binding, http-transport |
| D12 OpenAPIPlugin | openapi-plugin |
| D13 testing harness | testing-harness, examples-small-medium, examples-big-group |
| D14 documentation | docs-readme-concepts, docs-authoring, docs-reference |
| D15 tools only | fastmcp-adapter |
| D16 release tag | release |
| D17 repo and tooling | scaffold |
| D18 pip-installable package | scaffold, cli-stdio, release, docs-readme-concepts |

## Contracts

| Part | Owner | Consumers | Where defined |
|---|---|---|---|
| `tool-types` | core-types | http-binding, response-shaping, schemas-and-validation, plugin-abc, registry, call-pipeline, openapi-plugin | `code/any-mcp/src/any_mcp/types.py` |
| `tool-errors` | core-types | config-model, plugin-abc, call-pipeline | `code/any-mcp/src/any_mcp/errors.py` |
| `http-executor` | http-binding | plugin-abc | `code/any-mcp/src/any_mcp/http.py` |
| `response-shaper` | response-shaping | plugin-abc | `code/any-mcp/src/any_mcp/response.py` |
| `schema-tools` | schemas-and-validation | registry, openapi-plugin | `code/any-mcp/src/any_mcp/schema.py` |
| `arg-validator` | schemas-and-validation | call-pipeline | `code/any-mcp/src/any_mcp/validation.py` |
| `plugin-abc` | plugin-abc | plugin-discovery, registry, call-pipeline, openapi-plugin, testing-harness, examples-small-medium, examples-big-group | `code/any-mcp/src/any_mcp/plugin.py` |
| `any-mcp-config` | config-model | plugin-discovery, registry, cli-stdio, http-transport, docs-reference | `code/any-mcp/src/any_mcp/config.py` |
| `plugin-loader` | plugin-discovery | registry, cli-stdio, testing-harness | `code/any-mcp/src/any_mcp/discovery.py` |
| `tool-registry` | registry | call-pipeline, fastmcp-adapter | `code/any-mcp/src/any_mcp/registry.py` |
| `call-pipeline` | call-pipeline | fastmcp-adapter | `code/any-mcp/src/any_mcp/pipeline.py` |
| `fastmcp-adapter` | fastmcp-adapter | cli-stdio, http-transport, testing-harness | `code/any-mcp/src/any_mcp/_fastmcp_adapter.py` |
| `any-mcp-cli` | cli-stdio | http-transport, examples-small-medium, examples-big-group, docs-reference, release | `code/any-mcp/src/any_mcp/cli.py` |
| `plugin-harness` | testing-harness | openapi-plugin, examples-small-medium, examples-big-group, docs-authoring | `code/any-mcp/src/any_mcp/testing.py` |
| `openapi-plugin` | openapi-plugin | examples-big-group | `code/any-mcp/src/any_mcp/openapi.py` |

Cross-epic contracts in `docs/plans/contracts.json` (owner epic any-mcp, consumer epic
agent-orchestrator): `any-mcp-cli` (`any-mcp --config <path>`, stdio default, `--help` exits 0),
`any-mcp-config` (the YAML schema the orchestrator's ConfigMap renders), `any-mcp-release` (tag
`v0.1.0` installable with `pip install "any-mcp @ git+https://github.com/szymonrychu/any-mcp@v0.1.0"`).

## Review focus

- `_fastmcp_adapter.py`: the only FastMCP surface; check that invalid arguments yield `isError`
  results (not FastMCP's own `-32602` validation), that `ttlMs`/`cacheScope` are on the wire, and
  that the tools capability is the only one declared.
- `pipeline.py`: no exception path escapes as a JSON-RPC error; no arguments, headers or
  credentials in logs or error text.
- `registry.py`: reload locking, diffing and the failed-reload path; names stay unique and stable
  across reloads.
- `http-transport`: Origin check, bearer check, and the end-to-end proof that an inbound
  `Authorization` never reaches the upstream.
- The import-boundary test: no module but the adapter imports `fastmcp` or `mcp`, examples included.

## Left to the builder

- Internal class names, private helpers and module splits inside a task's files, as long as the
  public names in each task's Interfaces stay.
- How the adapter maps FastMCP 4.1 internals (Provider versus `add_tool`, which notification call),
  provided the ACs hold; probe results go into `docs/transports.md`.
- Log line format on stderr (plain text or JSON lines), consistent across modules.
- The exact public API used for the single-endpoint example (any keyless public JSON API), as long
  as its test runs offline.

## Assumptions and unknowns

- FastMCP 4.1 `Tool` subclasses accept a raw `parameters` schema and `run(arguments)` (docs brief
  3.3, medium): probed by the first fastmcp-adapter test; fallback is D1's `MCPServer` path.
- FastMCP's own input validation might reject bad arguments before any-mcp's pipeline: probed by
  the adapter test for invalid arguments; the adapter disables or bypasses it.
- Out-of-request tool-list notifications are undocumented for the 2026-07-28 era (docs brief 3.5):
  the adapter test pins what is sent; correctness does not depend on it (D8).
- `httpx` and FastMCP's HTTP client coexist in one environment: confirmed by `uv lock` in scaffold.
- The orchestrator creates `szymonrychu/any-mcp` on GitHub with an MIT `LICENSE` and the Python
  `.gitignore` (`gh repo create --public --license mit --gitignore Python`) and adds the
  `code/any-mcp` submodule before phase 4; the scaffold task fills it.
- The agent-orchestrator image base runs Python 3.12 (claude-code-wrapper pins 3.12 in `mise.toml`).

## Open questions
- Q1: Build on FastMCP 4.x (fastmcp>=4.1,<5) behind any-mcp's own plugin ABC, with one adapter module the only importer of fastmcp? [answer: yes: FastMCP 4 behind own ABC]
- Q2: Keep v1 tools-only, with plugin resources and prompts not in the v1 API? [answer: yes: tools only (no resources or prompts)]
- Q3: Keep MRTR (InputRequiredResult) out of the v1 plugin API? [recommended: yes]
- Q4: Make the first release tag v0.1.0? [recommended: yes, v0.1.0]
- Q5: Make the OpenAPI plugin refuse to load without an allow or tags filter, so mirroring a whole API needs an explicit allow of every operation? [recommended: yes]

## Irreversible operations in scope

- Creating the public GitHub repository `szymonrychu/any-mcp` and pushing to it: the code becomes
  public. Covered by the gate approval of item F; done by the orchestrator before phase 4.
- Pushing tag `v0.1.0` to the public origin after the epic closes on `main`: a published tag is
  never moved (agent-orchestrator pins it). Covered by the gate approval of item H; the release
  workflow run on the tag is its check.
