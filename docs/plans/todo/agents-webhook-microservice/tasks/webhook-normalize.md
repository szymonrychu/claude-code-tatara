---
title: webhook normalize
status: todo
repo: agents-webhook
value: "GitHub, GitLab and Grafana payloads become one event shape with the requested dedup keys and ignore reasons"
files: [src/agents_webhook/normalize.py, tests/payloads.py, tests/test_normalize.py]
verify: "uv run pytest tests/test_normalize.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [webhook-scaffold]
owns: [webhook-normalized-event]
uses: []
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

# webhook normalize

## Requirement

Pure parsing of provider payloads into `NormalizedEvent` plus the ignore classification (design D4; tatara-new parity F1). Paths are in code/agents-webhook. No I/O.

- `NormalizedEvent` dataclass: `source, kind (mr|issue|comment|alert), action, repo, number, title, body, comment_body, url, author, actor, labels (dict for alerts, list for forge labels), dedup_key, priority (0 alert, 1 otherwise)`.
- `normalize_github(event_header, payload)`: `pull_request` -> mr; `issues` -> issue; `issue_comment` -> comment (on an MR when `issue.pull_request` is set, still keyed on the issue/PR number); `pull_request_review_comment` (created only) and `pull_request_review` (submitted) -> comment. Dedup keys: `github/<owner/repo>/mr/<n>` for PR and PR comments, `github/<owner/repo>/issue/<n>` for issues and issue comments.
- `normalize_gitlab(event_header, payload)`: Merge Request Hook -> mr (`update` -> synchronize), Issue Hook -> issue, Note Hook -> comment on an MR or issue; keys `gitlab/<path_with_namespace>/mr/<iid>`, `gitlab/<path>/issue/<iid>`.
- `normalize_grafana(payload)`: kind alert, title from `commonLabels.alertname`, body from `commonAnnotations.summary`/`description`, `labels = commonLabels`; key `grafana/` + sha256 of the canonical JSON of the sorted `commonLabels`, first 16 hex.
- `classify(event, *, bot_logins, allowed_authors) -> str | None` returns the ignore reason or None: `self_event` (actor in bot_logins), `author_not_allowed` (issue or comment, allowlist set, author not in it), `action_ignored` (closed, merged, labeled, unlabeled, draft PRs, review dismissals, `edited` whose `changes` holds only `title`), `resolved` (Grafana status not `firing`). Unsupported provider events raise `Unsupported`.
- `tests/payloads.py`: minimal realistic payload builders per provider and event; `tests/test_normalize.py`: every mapping above, every key format, each ignore reason, a title-only edit ignored and a body edit accepted, label order not changing the Grafana key.

## Acceptance conditions

- AC1: GitHub PR, issue and comment events normalise with keys github/<repo>/mr|issue/<n> [evidence: command:uv run pytest tests/test_normalize.py -q -k github]
- AC2: GitLab MR, issue and note hooks normalise with keys gitlab/<repo>/mr|issue/<iid> [evidence: command:uv run pytest tests/test_normalize.py -q -k gitlab]
- AC3: Grafana alerts key on the sorted common labels and resolved alerts are ignored [evidence: command:uv run pytest tests/test_normalize.py -q -k grafana]
- AC4: each ignore reason is classified [evidence: command:uv run pytest tests/test_normalize.py -q -k classify]
- AC5: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

## Files

- `src/agents_webhook/normalize.py`
- `tests/payloads.py`
- `tests/test_normalize.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
