---
title: webhook normalize
status: in-progress
repo: agents-webhook
value: "GitHub, GitLab and Grafana payloads become one event shape with the requested dedup keys and ignore reasons"
files: [src/agents_webhook/normalize.py, tests/payloads.py, tests/test_normalize.py]
verify: "uv run pytest tests/test_normalize.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [webhook-scaffold]
model: ""
review: ""
verified_head: ""
points: 1
expected_minutes: 5
expected_tokens: 750000
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# webhook normalize

## Requirement

Pure parsing of provider payloads into `NormalizedEvent` for an endpoint's type, plus the ignore classification (design D4, D7; tatara-new parity F1; re-plan 2026-10-25: each endpoint has exactly one type of grafana-alert, gitlab-issue, gitlab-mr, github-issue, github-pr). Paths are in code/agents-webhook. No I/O.

- `NormalizedEvent` dataclass: `type, source, kind (mr|issue|comment|alert), action, repo, number, title, body, comment_body, url, author, actor, labels (dict for alerts, list for forge labels), delivery_id, dedup_key, priority (0 alert, 1 otherwise)`.
- `normalize(endpoint_type, headers, payload) -> NormalizedEvent`; raises `TypeMismatch` when the provider event is valid but belongs to another type, `Unsupported` when it is no supported provider event. Per type:
  - `github-pr` (`X-GitHub-Event`): `pull_request` -> mr; `pull_request_review_comment` (created) and `pull_request_review` (submitted) -> comment; `issue_comment` whose `issue.pull_request` is set -> comment. Key `github/<owner/repo>/mr/<n>`.
  - `github-issue`: `issues` -> issue; `issue_comment` without `issue.pull_request` -> comment. Key `github/<owner/repo>/issue/<n>`.
  - `gitlab-mr` (`X-Gitlab-Event`): Merge Request Hook -> mr (`update` -> synchronize); Note Hook on a merge request -> comment. Key `gitlab/<path_with_namespace>/mr/<iid>`.
  - `gitlab-issue`: Issue Hook -> issue; Note Hook on an issue -> comment. Key `gitlab/<path>/issue/<iid>`.
  - `grafana-alert`: a Grafana alert webhook body (`alerts`, `commonLabels`); kind alert, title from `commonLabels.alertname`, body from `commonAnnotations.summary`/`description`, `labels = commonLabels`; key `grafana/` + sha256 of the canonical JSON of the sorted `commonLabels`, first 16 hex.
  - `delivery_id` from `X-GitHub-Delivery` or `X-Gitlab-Event-UUID`; None for Grafana.
- `classify(event, *, bot_logins, allowed_authors) -> str | None` returns the ignore reason or None: `self_event` (actor in bot_logins), `author_not_allowed` (issue or comment, allowlist set, author not in it), `action_ignored` (closed, merged, labeled, unlabeled, draft PRs, review dismissals, `edited` whose `changes` holds only `title`), `resolved` (Grafana status not `firing`).
- `tests/payloads.py`: minimal realistic payload builders per provider and event; `tests/test_normalize.py`: every type above with each of its events, every key format, a PR event on a `github-issue` endpoint and an issue event on a `github-pr` endpoint raise `TypeMismatch` (and the same for GitLab and a forge body on `grafana-alert`), an unknown event raises `Unsupported`, each ignore reason, a title-only edit ignored and a body edit accepted, label order not changing the Grafana key, delivery ids read.

## Acceptance conditions

- AC1: github-pr and github-issue endpoints normalise their PR, issue and comment events with keys github/<repo>/mr|issue/<n> [evidence: command:uv run pytest tests/test_normalize.py -q -k github]
- AC2: gitlab-mr and gitlab-issue endpoints normalise MR, issue and note hooks with keys gitlab/<repo>/mr|issue/<iid> [evidence: command:uv run pytest tests/test_normalize.py -q -k gitlab]
- AC3: grafana-alert endpoints key on the sorted common labels and resolved alerts are ignored [evidence: command:uv run pytest tests/test_normalize.py -q -k grafana]
- AC4: an event of another type raises TypeMismatch and an unknown event Unsupported [evidence: command:uv run pytest tests/test_normalize.py -q -k mismatch]
- AC5: each ignore reason is classified [evidence: command:uv run pytest tests/test_normalize.py -q -k classify]
- AC6: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

## Files

- `src/agents_webhook/normalize.py`
- `tests/payloads.py`
- `tests/test_normalize.py`

## Interfaces

- Owns `webhook-normalized-event`: `agents_webhook.normalize.{NormalizedEvent, normalize_github, normalize_gitlab, normalize_grafana, classify, Unsupported}`.

## Expected outcome

Every supported payload yields one event and a dedup key; every unsupported one raises Unsupported.

## Steps

- Red: payload builders and tests; run: fail. Green: implement; run the verify command.

## Notes

- Parity sources: `TN/internal/scm/github.go:DetectAndVerify` L109-163, `ghNormalizeAction` L271, `TN/internal/scm/gitlab.go` L116-129 and L270-300, `TN/internal/webhook/grafana.go` L14-31 and L128-136, `server.go:isBotActor` L1181, L335-341 (TN = /Users/szymonri/Documents/tatara-new/code/tatara-operator).

- 2026-10-25 amended: re-plan 2026-10-25: per-webhook endpoints (/webhook/<suffix>, one type, one preset, basic auth) replace per-source secrets and mappings; agent reuse is opt-in per preset (design D3, D7, D16-D19)
