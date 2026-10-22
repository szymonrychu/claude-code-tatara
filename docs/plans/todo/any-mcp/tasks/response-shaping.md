---
title: Response shaping
status: todo
repo: any-mcp
value: "Every API response becomes a predictable, size-bounded MCP result without plugin code"
files: [src/any_mcp/response.py, tests/test_response.py]
verify: "uv run --frozen pytest tests/test_response.py -q && mise run lint"
depends_on: [core-types]
owns: [response-shaper]
uses: [tool-types]
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

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
