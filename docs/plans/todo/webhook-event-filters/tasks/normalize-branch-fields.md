---
title: normalize branch fields
status: todo
repo: agents-webhook
value: PR/MR source and target branch names become filterable event fields
files: [src/agents_webhook/normalize.py, tests/test_normalize.py, tests/payloads.py]
verify: "uv run pytest tests/test_normalize.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: []
model: sonnet
review: ""
verified_head: ""
points: 2
expected_minutes: 9
expected_tokens: 546295
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
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

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
