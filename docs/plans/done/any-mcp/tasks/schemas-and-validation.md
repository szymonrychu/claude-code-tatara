---
title: Schemas and validation
status: done
repo: any-mcp
value: "Client-safe tool names and schemas, and no unvalidated argument ever reaches a plugin"
files: [src/any_mcp/schema.py, src/any_mcp/validation.py, tests/test_schema.py]
verify: "uv run --frozen pytest tests/test_schema.py -q && mise run lint"
depends_on: [core-types]
model: sonnet
review: ""
verified_head: ecfba3da606af638502b8943ec1f728050a8df7a
points: 1
expected_minutes: 5
expected_tokens: 750000
points_actual: ""
actual_minutes: 7
actual_tokens: 845523
actual_roles: "impl 3, review 4"
actual_role_tokens: "impl 360745, review 484778"
---

# Schemas and validation

## Requirement

Normalise tool schemas and names for listing, and validate call arguments against the original schema (design D6, D7).

- `normalize_schema(schema, *, max_depth=8) -> dict`: inline local `$ref`s (`#/$defs/...`, `#/definitions/...`, `#/components/schemas/...`, given a root document to resolve against), drop `$defs` and `definitions` afterwards, replace a reference recursing deeper than `max_depth` with `{"type": "object", "description": "(recursive, truncated)"}`; an external or unresolvable `$ref` raises `SchemaError` naming the ref.
- `listing_schema(schema) -> dict`: a root `anyOf`/`oneOf` whose branches are all object schemas becomes one object schema (properties merged, `required` the intersection); a root without `type: object` otherwise raises `SchemaError`; `None` gives `{"type": "object", "additionalProperties": false}`.
- `exposed_name(namespace, tool, *, max_length=60) -> str`: `<namespace>_<tool>` (no prefix when the namespace is empty), every character outside `[A-Za-z0-9_.-]` replaced by `_`, and a name longer than `max_length` cut and suffixed with `_` plus the first 6 hex digits of the SHA-1 of the untruncated name, so the result is deterministic and at most `max_length` long.
- `SchemaError` subclasses `ConfigError`.
- `validate_arguments(schema, arguments) -> dict`: `None` means `{}`; validation with `jsonschema.Draft202012Validator`; every error is collected and raised as one `ToolInputError` with `(json path, message)` pairs sorted by path; a string value whose schema expects an object or array and that parses as JSON of that type is replaced by the parsed value before validation; returns the (possibly coerced) arguments.

## Acceptance conditions

- AC1: local refs under $defs, definitions and components/schemas are inlined and the definition maps are removed [evidence: test:tests/test_schema.py::test_inlines_local_refs]
- AC2: recursive refs are cut at max_depth with the truncation marker schema [evidence: test:tests/test_schema.py::test_cuts_recursive_refs]
- AC3: an external or unresolvable ref raises SchemaError naming it [evidence: test:tests/test_schema.py::test_rejects_external_refs]
- AC4: root object unions are flattened, non-object roots are rejected and a missing schema gives the closed empty object [evidence: test:tests/test_schema.py::test_root_shapes]
- AC5: exposed_name prefixes, sanitises and truncates with a stable hash suffix within max_length [evidence: test:tests/test_schema.py::test_exposed_name]
- AC6: validate_arguments collects every error with its JSON path and treats None as an empty object [evidence: test:tests/test_schema.py::test_validate_arguments_errors]
- AC7: stringified JSON is coerced only for object and array properties [evidence: test:tests/test_schema.py::test_validate_coerces_json_strings]
- AC8: draft 2020-12 keywords such as prefixItems and dependentRequired are enforced [evidence: test:tests/test_schema.py::test_validate_draft_2020_12]
- AC9: lint passes [evidence: command:mise run lint]

## Files

- `src/any_mcp/schema.py`
- `src/any_mcp/validation.py`
- `tests/test_schema.py`

## Interfaces

- `any_mcp.schema.normalize_schema(schema: Mapping[str, Any], *, root: Mapping[str, Any] | None = None, max_depth: int = 8) -> dict`, `listing_schema(schema: Mapping[str, Any] | None) -> dict`, `exposed_name(namespace: str, tool: str, *, max_length: int = 60) -> str`, `class SchemaError(ConfigError)`: the `schema-tools` part.
- `any_mcp.validation.validate_arguments(schema: Mapping[str, Any], arguments: Mapping[str, Any] | None) -> dict`: the `arg-validator` part.

## Expected outcome

Every listed tool has a self-contained object schema and a client-safe name; every call is validated before plugin code runs.

## Steps

- Write `tests/test_schema.py`; run `uv run --frozen pytest tests/test_schema.py -q`; expect import errors.
- Implement `src/any_mcp/schema.py` and `src/any_mcp/validation.py`; rerun (all pass), then `mise run lint`.

## Notes

Prior art: FastMCP could not resolve chained `$ref` -> `$defs` -> `$ref` (fastmcp#1372); test a chain. Claude Code mishandles a root `anyOf` and sometimes sends objects as JSON strings (Stainless lessons, prior-art O4). Cursor caps combined names at 60 characters, hence the default.
