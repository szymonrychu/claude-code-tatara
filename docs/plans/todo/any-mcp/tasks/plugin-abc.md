---
title: Plugin ABC
status: todo
repo: any-mcp
value: "Writing a plugin is one class with one method; every other hook has a working default"
files: [src/any_mcp/plugin.py, src/any_mcp/context.py, src/any_mcp/__init__.py, tests/test_plugin.py]
verify: "uv run --frozen pytest tests/test_plugin.py -q && mise run lint"
depends_on: [http-binding, response-shaping]
owns: [plugin-abc]
uses: [tool-types, tool-errors, http-executor, response-shaper]
model: sonnet
estimate: 6
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

# Plugin ABC

## Requirement

Build the plugin contract: `Plugin`, the `@tool` decorator, `PluginContext` and `NoConfig`, and the public package exports (design D2, D3). Plugins import only `any_mcp`.

- `Plugin(ABC)` class attributes: `name: ClassVar[str] = ""`, `Config: ClassVar[type[BaseModel]] = NoConfig`, `reload_every: ClassVar[float | None] = None`, `timeout: ClassVar[float] = 30.0`. Instance attribute `ctx: PluginContext`, set by the core before `setup()`; property `config` returns `ctx.config`.
- Async hooks with these defaults: `setup()` and `teardown()` do nothing; `load_tools()` returns the `ToolSpec`s of the class's `@tool` methods in definition order (inherited ones first); `credentials(call)` returns `{}`; `before_call(call)` returns `call`; `call(call)` runs `spec.handler` and wraps its value with `RawResponse.from_value`, or runs `execute_binding(ctx.http, call, headers=await self.credentials(call))` for `spec.http`, or raises `ConfigError` when the spec has neither; `shape_response(call, raw)` returns `shape_default(raw, budget_chars=ctx.response_budget_chars, output_schema=call.spec.output_schema)`; `on_error(call, exc)` returns `error_result(exc, plugin=ctx.name)`.
- `load_tools` is the one required hook: defining a concrete subclass that neither overrides `load_tools` nor has a `@tool` method raises `TypeError` naming `load_tools`, at class definition time.
- Every hook and every `@tool` method is `async`; `@tool` on a plain function raises `TypeError`.
- `@tool` and `@tool(name=None, description=None, tags=(), annotations=None)`: name from the function name, description from the docstring's first paragraph (a missing docstring raises `TypeError`), `input_model` built from the signature (defaults, `Optional`, `Annotated[..., Field(description=...)]`), `output_schema` from a return annotation that is a pydantic model, TypedDict or dataclass, and a `handler` that calls the bound method with the validated arguments.
- `PluginContext(name, namespace, config, http, log, response_budget_chars)` with `request_reload()`, which calls the callback the registry binds (`_bind_reload(cb)`); before binding it is a no-op that logs a debug line.
- `src/any_mcp/__init__.py` exports `Plugin`, `tool`, `ToolSpec`, `HttpBinding`, `ToolCall`, `RawResponse`, `ToolResult`, `Deny`, `UpstreamError`, `ToolInputError`, `PluginContext`, `NoConfig` and keeps `__version__`.

## Acceptance conditions

- AC1: a subclass with neither a load_tools override nor a tool method raises TypeError naming load_tools, and either one is accepted [evidence: test:tests/test_plugin.py::test_subclass_must_provide_tools]
- AC2: the tool decorator builds the ToolSpec name, description, input model, tags and output schema from the method [evidence: test:tests/test_plugin.py::test_tool_decorator_builds_spec]
- AC3: the tool decorator rejects non-async functions and functions without a docstring [evidence: test:tests/test_plugin.py::test_tool_requires_async_and_docstring]
- AC4: the default load_tools returns decorated specs in definition order with inherited ones first [evidence: test:tests/test_plugin.py::test_default_load_tools]
- AC5: the default call runs the handler, or the HTTP binding with credential headers, and raises ConfigError for a spec with neither [evidence: test:tests/test_plugin.py::test_default_call_paths]
- AC6: the default shape_response and on_error delegate to shape_default and error_result with the context budget and plugin name [evidence: test:tests/test_plugin.py::test_default_shape_and_error]
- AC7: ctx.request_reload calls the bound callback and plugin.config returns the validated Config instance [evidence: test:tests/test_plugin.py::test_context]
- AC8: a hello-world plugin of one class and one tool method works end to end through call and shape_response [evidence: test:tests/test_plugin.py::test_hello_world_minimal]
- AC9: the any_mcp package exports the public names listed in the requirement [evidence: test:tests/test_plugin.py::test_public_exports]
- AC10: lint passes [evidence: command:mise run lint]

## Files

- `src/any_mcp/plugin.py`
- `src/any_mcp/context.py`
- `src/any_mcp/__init__.py`
- `tests/test_plugin.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
