---
title: normalize branch fields
status: done
repo: agents-webhook
value: PR/MR source and target branch names become filterable event fields
files: [src/agents_webhook/normalize.py, tests/test_normalize.py, tests/payloads.py]
verify: "uv run pytest tests/test_normalize.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: []
model: sonnet
review: ""
verified_head: efacbaa
points: 2
expected_minutes: 9
expected_tokens: 546295
points_actual: 2
actual_minutes: 4
actual_tokens: 502921
actual_roles: "impl 3, review 1"
actual_role_tokens: "impl 426443, review 76478"
---

# normalize branch fields

## Requirement

Add the PR/MR branch names to the normalized event, so endpoint filters can match them (design D3; user follow-up 2026-10-25, verbatim: "other fields: title regex, branch name, etc"; user decision: "branch name (source/target for PR/MR)"). Paths are in code/agents-webhook.

- `NormalizedEvent` gains `source_branch: str | None = None` and `target_branch: str | None = None` (defaults, so `ingest/app.py:_unparsed` and `db/events.py:to_normalized` keep constructing it unchanged).
- GitHub (`github-pr` endpoints): `pull_request`, `pull_request_review` and `pull_request_review_comment` set `source_branch` from `pull_request.head.ref` and `target_branch` from `pull_request.base.ref`. `issue_comment` on a PR carries no branch: both stay None. `github-issue` events: both None.
- GitLab (`gitlab-mr` endpoints): `Merge Request Hook` sets them from `object_attributes.source_branch` and `object_attributes.target_branch`; `Note Hook` on a merge request from `merge_request.source_branch` and `merge_request.target_branch`. `gitlab-issue` events: both None.
- Grafana: both None.
- A missing or non-string ref yields None, never an exception.
- The branches are not stored as event columns and not added to the prompt context (design D3: the payload already holds them).

## Acceptance conditions

- AC1: a GitHub pull_request event carries head.ref as source_branch and base.ref as target_branch [evidence: test:tests/test_normalize.py::test_github_pr_branches]
- AC2: GitHub pull_request_review and pull_request_review_comment events carry both branches; issue_comment on a PR and github-issue events carry None [evidence: test:tests/test_normalize.py::test_github_branches_per_event]
- AC3: a GitLab Merge Request Hook and a Note Hook on a merge request carry both branches; gitlab-issue events carry None [evidence: test:tests/test_normalize.py::test_gitlab_mr_branches]
- AC4: grafana-alert events and payloads with a missing or non-string ref carry None without raising [evidence: test:tests/test_normalize.py::test_branches_absent_are_none]
- AC5: the existing normalize suite and lint pass [evidence: command:uv run pytest tests/test_normalize.py -q && uv run ruff check . && uv run ruff format --check .]

## Files

- `src/agents_webhook/normalize.py`
- `tests/test_normalize.py`
- `tests/payloads.py`

## Interfaces

- `src/agents_webhook/normalize.py:NormalizedEvent`: adds `source_branch: str | None = None`, `target_branch: str | None = None` after `changed` (contract `webhook-normalized-event`, consumed by filter-rules-engine).
- `normalize(endpoint_type, headers, payload)` signature unchanged.

## Expected outcome

`normalize("github-pr", ...)` and `normalize("gitlab-mr", ...)` return events whose `source_branch` and `target_branch` are the PR/MR head and base branch names; every other event has None.

## Steps

- Red: add the four tests to `tests/test_normalize.py`, extending the builders in `tests/payloads.py` with `head`/`base` refs (GitHub) and `source_branch`/`target_branch` (GitLab MR attrs and the Note Hook `merge_request`). Run `uv run pytest tests/test_normalize.py -q`: the new tests fail with `AttributeError` or `TypeError` on the missing fields.
- Green: add the two fields and set them in `_github` and `_gitlab`. Run the verify: all pass, lint clean.

## Notes

- `_event(...)` passes `**fields` into `NormalizedEvent`; add the branches as keyword fields there.
- GitHub: in `_github`, `item` is `payload["pull_request"]` for the three PR events; for `issue_comment`, `item` is the issue and has no `head`.
- GitLab: in `_gitlab`, `item` is `object_attributes` for MR hooks and `payload["merge_request"]` for notes.
- Use a small helper that returns the value only when it is a non-empty `str`.

- 2026-10-25 done
