---
title: filter rules engine
status: todo
repo: agents-webhook
value: "allow and deny rules per endpoint type, validated and evaluated on RE2 so no user regex can stall ingest"
files: [src/agents_webhook/filters.py, tests/test_filters.py, pyproject.toml, uv.lock]
verify: "uv sync && uv run pytest tests/test_filters.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [normalize-branch-fields]
model: opus
review: ""
verified_head: ""
points: 5
expected_minutes: 14
expected_tokens: 1860143
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# filter rules engine

## Requirement

Build the filter rules engine: per-endpoint allow and deny rules over the normalized event fields, validated on save and evaluated without any I/O (design D2, D3, D4). User request 2026-10-25, verbatim: "for each of supported webhooks add whiltelisting/blacklisting ability- e.g. grafana webhooks should blacklist if a label X consist of value Y, or issue/mr webhook will be received but internall ignorred if author is not one of the usernames from the list (or repos)- in general whitelist/blacklist capability for webhooks allowing for greater granularity in how to react to webhook events." Follow-up, verbatim: "other fields: title regex, branch name, etc". Constraint: "user-supplied regex on a public ingest path must not allow ReDoS. Pick a safe engine or bounds, and name it." Paths are in code/agents-webhook.

New module `src/agents_webhook/filters.py`:

- `FIELDS: dict[str, tuple[str, ...]]`, exactly design D3: `github-issue` and `gitlab-issue`: author, actor, repo, labels, title, body, comment, kind, action; `github-pr` and `gitlab-mr`: the same plus source_branch, target_branch; `grafana-alert`: labels, title, body. Field to event attribute: author -> `author`, actor -> `actor`, repo -> `repo`, labels -> `labels`, title -> `title`, body -> `body`, comment -> `comment_body`, kind -> `kind`, action -> `action`, source_branch -> `source_branch`, target_branch -> `target_branch`.
- `MATCHES = ("equals", "regex")`; `EMPTY = {"allow": [], "deny": []}`; `DENIED = "filter_denied"`; `NOT_ALLOWED = "filter_not_allowed"`; bounds `MAX_RULES = 20` per list, `MAX_VALUES = 50` per rule, `MAX_VALUE_LENGTH = 256`, `MAX_TEXT = 65536` characters read from a text field.
- `validate(endpoint_type: str, data: Any) -> dict`: returns the canonical form `{"allow": [{"field", "match", "values"}], "deny": [...]}` (`match` defaults to `"equals"`, `None` or a missing list means empty) or raises `ValueError` whose message starts with the path, for example `filters.deny[0].field: 'repo' does not apply to grafana-alert`, `filters.allow[1].values[2]: not a valid RE2 pattern (...)`. It refuses: a non-object, unknown top-level keys, an unknown rule key, a field outside `FIELDS[endpoint_type]`, a match outside `MATCHES`, more than `MAX_RULES` rules in a list, zero or more than `MAX_VALUES` values, a value that is not a string or is empty or longer than `MAX_VALUE_LENGTH`, a Grafana `labels` value without `=` or with an empty key, and any regex RE2 does not compile (backreferences, lookaround).
- `evaluate(event: NormalizedEvent, filters: Mapping) -> str | None` (filters in the canonical form, the endpoint type is `event.type`): the first deny rule in order that matches returns `"filter_denied: <field>"`; otherwise the first allow rule that does not match returns `"filter_not_allowed: <field>"`; otherwise None. Compiled rule sets are cached per canonical JSON (bounded).
- Matching, design D2: a rule matches when any of its values matches. An absent field value (None) never matches. List fields (forge `labels`) match when any element matches. `equals` is case-insensitive (casefold) for author, actor, repo and forge labels and case-sensitive for every other field. `regex` is an unanchored RE2 search on the first `MAX_TEXT` characters. Grafana `labels` (a dict): a value `key=value` splits on the first `=`; `equals` compares `labels[key]` exactly, `regex` searches `labels[key]` with the part after `=`; a key absent from the dict never matches.
- The regex engine is RE2 through the `google-re2` package (module `re2`), added to `pyproject.toml` dependencies and `uv.lock`. stdlib `re` is never used on a user pattern.

## Acceptance conditions

- AC1: FIELDS lists exactly the fields of design D3 for each of the five endpoint types [evidence: test:tests/test_filters.py::test_fields_per_type]
- AC2: validate returns the canonical form with match defaulting to equals and missing lists empty [evidence: test:tests/test_filters.py::test_validate_canonical_form]
- AC3: validate refuses each invalid input listed in the requirement with a ValueError whose message starts with the rule path [evidence: test:tests/test_filters.py::test_validate_rejects_with_path]
- AC4: validate refuses a field that does not apply to the endpoint type (repo on grafana-alert, source_branch on github-issue) [evidence: test:tests/test_filters.py::test_validate_rejects_field_for_type]
- AC5: validate refuses patterns RE2 does not support, a backreference and a lookahead [evidence: test:tests/test_filters.py::test_validate_rejects_non_re2_patterns]
- AC6: validate enforces MAX_RULES, MAX_VALUES and MAX_VALUE_LENGTH [evidence: test:tests/test_filters.py::test_validate_bounds]
- AC7: a matching deny rule returns filter_denied: <field>, the first in list order, before any allow rule is checked [evidence: test:tests/test_filters.py::test_deny_first_match_wins]
- AC8: allow rules AND together and a rule's values OR together; the first failing allow rule returns filter_not_allowed: <field> [evidence: test:tests/test_filters.py::test_allow_rules_and_values_or]
- AC9: an absent field fails an allow rule and never matches a deny rule [evidence: test:tests/test_filters.py::test_absent_field_fails_allow_not_deny]
- AC10: equals is case-insensitive for author, actor, repo and forge labels and case-sensitive for branches and title [evidence: test:tests/test_filters.py::test_equals_case_rules]
- AC11: regex is an unanchored search, honours (?i), and reads only the first MAX_TEXT characters of a text field [evidence: test:tests/test_filters.py::test_regex_search_semantics]
- AC12: Grafana label rules match key=value with equals and key=<regex> with regex, and a missing key never matches [evidence: test:tests/test_filters.py::test_grafana_label_rules]
- AC13: the pattern (a+)+$ against 100000 'a' characters followed by '!' evaluates in under one second [evidence: test:tests/test_filters.py::test_catastrophic_pattern_is_linear]
- AC14: no stdlib re call compiles a user pattern in filters.py [evidence: command:! grep -nE '^\s*import re$|re\.(compile|search|match|fullmatch)\(' src/agents_webhook/filters.py]
- AC15: google-re2 is a locked runtime dependency [evidence: command:grep -q 'google-re2' pyproject.toml && grep -q 'name = "google-re2"' uv.lock]
- AC16: the filters suite and lint pass [evidence: command:uv run pytest tests/test_filters.py -q && uv run ruff check . && uv run ruff format --check .]

## Files

- `src/agents_webhook/filters.py`
- `tests/test_filters.py`
- `pyproject.toml`
- `uv.lock`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
