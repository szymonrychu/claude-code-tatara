---
title: Response shaping
status: done
repo: any-mcp
value: "Every API response becomes a predictable, size-bounded MCP result without plugin code"
files: [src/any_mcp/response.py, tests/test_response.py]
verify: "uv run --frozen pytest tests/test_response.py -q && mise run lint"
depends_on: [core-types]
model: sonnet
review: ""
verified_head: 58062304fb74846de59abb3fda0bb62641ad5449
points: 1
expected_minutes: 5
expected_tokens: 750000
points_actual: ""
actual_minutes: 1
actual_tokens: 174195
actual_roles: "impl 1, review 1"
actual_role_tokens: "impl 137988, review 36207"
---

# Response shaping

## Requirement

Turn a `RawResponse` into a `ToolResult` with the default shaping rules and a size budget (design D9).

- `shape_default(raw, *, budget_chars=40000, output_schema=None) -> ToolResult`.
- JSON (`application/json`, any `+json` type, or a handler value wrapped by `RawResponse.from_value`): `structured` is the parsed value and `text` is its compact JSON dump (`ensure_ascii=False`, separators `(",", ":")`). A handler `str` value is plain text with no structured content.
- `text/*`: text only, decoded with `RawResponse.text()`.
- Other content types: text `<n> bytes of <content type>`, no structured content.
- Empty body: text `OK (<status>)`.
- Over `budget_chars`: text cut to the budget plus `\n[truncated: <shown> of <total> chars]`, structured dropped; when `output_schema` is given the result is instead `is_error=True` with a text naming the response size and the budget, because structured content must conform to the output schema.

## Acceptance conditions

- AC1: a JSON body gives structured content plus a compact JSON text copy [evidence: test:tests/test_response.py::test_json_body]
- AC2: a +json content type is treated as JSON [evidence: test:tests/test_response.py::test_json_suffix_content_type]
- AC3: a text body gives text only [evidence: test:tests/test_response.py::test_text_body]
- AC4: a binary body gives the one-line size and content type description [evidence: test:tests/test_response.py::test_binary_body]
- AC5: an empty body gives OK with the status [evidence: test:tests/test_response.py::test_empty_body]
- AC6: handler str values give text, dict and list values give structured content [evidence: test:tests/test_response.py::test_handler_values]
- AC7: an over-budget response is truncated with the marker and loses structured content [evidence: test:tests/test_response.py::test_over_budget_truncates]
- AC8: an over-budget response of a tool with an output schema is an error result naming size and budget [evidence: test:tests/test_response.py::test_over_budget_with_output_schema_is_error]
- AC9: lint passes [evidence: command:mise run lint]

## Files

- `src/any_mcp/response.py`
- `tests/test_response.py`

## Interfaces

`any_mcp.response.shape_default(raw: RawResponse, *, budget_chars: int = 40000, output_schema: Mapping[str, Any] | None = None) -> ToolResult`: the `response-shaper` part, called by the default `Plugin.shape_response`.

## Expected outcome

Every response kind has one predictable MCP shape, and no single response can exceed the configured budget.

## Steps

- Write `tests/test_response.py`; run `uv run --frozen pytest tests/test_response.py -q`; expect import errors.
- Implement `src/any_mcp/response.py`; rerun (all pass), then `mise run lint`.

## Notes

The JSON text copy exists for clients that ignore `structuredContent` (MCP tools spec, structured content backwards compatibility). The 40000 default sits under Claude Code's 10k-token output warning.
