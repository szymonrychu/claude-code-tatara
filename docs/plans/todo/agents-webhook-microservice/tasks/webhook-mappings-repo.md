---
title: webhook mappings repo
status: todo
repo: agents-webhook
value: "events are matched to the most specific preset mapping, and mappings can be created and removed"
files: [src/agents_webhook/db/__init__.py, src/agents_webhook/db/mappings.py, tests/test_mappings_repo.py]
verify: "uv run pytest tests/test_mappings_repo.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [webhook-schema-settings, webhook-normalize]
owns: [webhook-mapping-match]
uses: [webhook-events-schema, agents-common-db, webhook-normalized-event]
model: ""
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

# webhook mappings repo

## Requirement

Mapping storage and matching (design D7). Paths are in code/agents-webhook.

- `db/mappings.py`: `create(conn, MappingIn) -> Mapping`, `delete(conn, id) -> bool`, `list_all(conn) -> list[Mapping]`, `get(conn, id)`, `match(conn, event: NormalizedEvent) -> Mapping | None`.
- Matching: same `source` and `kind` (a comment also matches a mapping of kind `comment` only); `repo` equal or null; for alerts every key/value of `labels` present in the event labels. Specificity score = (repo set ? 1 : 0) + number of labels; highest wins, ties to the lowest id.
- Validation on create: `repo` only for forge sources, `labels` only for grafana, kind/source pairs valid (alert only with grafana); `ValueError` names the field.
- `tests/test_mappings_repo.py`: create, list, delete; any-repo vs exact-repo specificity; label subset matching and specificity; ties to the oldest; invalid pairs rejected; deleting a mapping sets `events.mapping_id` to null (FK behaviour).

## Acceptance conditions

- AC1: the most specific mapping wins and ties go to the oldest [evidence: command:uv run pytest tests/test_mappings_repo.py -q -k specific]
- AC2: Grafana mappings match on a label subset [evidence: command:uv run pytest tests/test_mappings_repo.py -q -k labels]
- AC3: invalid source, kind, repo or labels combinations are rejected naming the field [evidence: command:uv run pytest tests/test_mappings_repo.py -q -k invalid]
- AC4: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

## Files

- `src/agents_webhook/db/__init__.py`
- `src/agents_webhook/db/mappings.py`
- `tests/test_mappings_repo.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
