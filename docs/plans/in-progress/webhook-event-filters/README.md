---
title: webhook event filters
blockers: [agents-webhook-microservice]
stage: build
owner: Szymon Richert
repos: [agents-webhook, agents-web, agents-helmfile]
created: 2026-10-25
---

# webhook event filters

## Project brief

What: Per-endpoint allowlist/denylist filters for every supported webhook type (grafana-alert, github-issue, github-pr, gitlab-issue, gitlab-mr): for example drop a Grafana alert when label X has value Y, or ignore an issue/PR/MR unless its author is in a username list or its repo is in a repo list; a delivery that fails a filter is accepted and stored as ignored with a reason instead of starting an agent.
How: Filter rules stored per endpoint in the agents-webhook database, evaluated at ingest after normalization and the built-in ignore rules against the normalized event fields (author, repository, labels including Grafana alert labels, title regex, PR/MR branches and more, design D3), regex on RE2, managed through the endpoints API and the agents-web Webhooks UI, deployed through agents-helmfile.
Why: User request 2026-10-25: finer control over which webhook events start agents: 'small epic- for each of supported webhooks add whiltelisting/blacklisting ability- e.g. grafana webhooks should blacklist if a label X consist of value Y, or issue/mr webhook will be received but internall ignorred if author is not one of the usernames from the list (or repos)- in general whitelist/blacklist capability for webhooks allowing for greater granularity in how to react to webhook events.'

## Description

Each agents-webhook endpoint gets allow and deny rules over the normalized fields of its type (design D3: author, actor, repo, labels with Grafana `key=value`, title, body, comment, kind, action, and PR/MR source and target branch). Rules match by `equals` or by an RE2 `regex`. Ingest evaluates them after the built-in ignore rules; a delivery that fails is answered 202 and stored `ignored` with `filter_denied: <field>` or `filter_not_allowed: <field>`. The UI API sets filters on create, replaces them with `PUT /webhooks/api/v1/endpoints/{id}/filters`, serves the field catalogue in `GET /meta`, and the template preview reports whether an example passes. agents-web edits filters in the New endpoint dialog and in a Filters dialog per endpoint. The global `WEBHOOK_ALLOWED_AUTHORS` is retired; `WEBHOOK_BOT_LOGINS` stays. agents-helmfile pins the new builds and the smoke checks filters without ingesting a runnable delivery. Design: `design.md`.

## Goals

- G1: every endpoint type has per-endpoint allow and deny rules over the fields of design D3, including author, repository, labels (Grafana `key=value`), title regex and PR/MR source and target branch.
- G2: a delivery that fails a filter answers 202 and is stored `ignored` with reason `filter_denied: <field>` or `filter_not_allowed: <field>`; it is never dispatched.
- G3: filters are set on create and replaced later through the endpoints API; the agents-web Webhooks UI edits them on create and on an existing endpoint, and its example-JSON preview shows whether the example passes.
- G4: regex rules run on RE2 (linear time) within the bounds of design D4; a pattern RE2 refuses, or a rule outside the bounds, is rejected on save with 422 naming the rule.
- G5: `WEBHOOK_ALLOWED_AUTHORS` and the reason `author_not_allowed` are gone; `WEBHOOK_BOT_LOGINS` and `self_event` stay.
- G6: the live namespace runs the new agents-webhook and agents-web builds and the extended smoke is green.

## Non-goals

- Filters over raw payload JSON paths, Grafana annotations or per-alert Grafana labels.
- Boolean expressions or OR-groups across rules.
- Re-evaluating events already queued when filters change.
- Editing other endpoint fields (type, preset, template).
- Filter hit counters or metrics.
- Changing the built-in ignore rules.

## Review

Filled when the epic reaches stage `review`: the verdict, the findings acted on, the findings dropped.

## Time

Estimate: 0 min | Actual: 0 min | Remaining estimate: 0 min
