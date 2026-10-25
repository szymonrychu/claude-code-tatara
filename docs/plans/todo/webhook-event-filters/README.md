---
title: webhook event filters
blockers: [agents-webhook-microservice]
stage: build
owner: ""
repos: [agents-webhook, agents-web, agents-helmfile]
created: 2026-10-25
---

# webhook event filters

## Project brief

What: Per-endpoint allowlist/denylist filters for every supported webhook type (grafana-alert, github-issue, github-pr, gitlab-issue, gitlab-mr): for example drop a Grafana alert when label X has value Y, or ignore an issue/PR/MR unless its author is in a username list or its repo is in a repo list; a delivery that fails a filter is accepted and stored as ignored with a reason instead of starting an agent.
How: Filter rules stored per endpoint in the agents-webhook database, evaluated at ingest after normalization against the normalized event fields (author, repository, labels, and Grafana alert labels), managed through the endpoints API and the agents-web Webhooks UI, deployed through agents-helmfile.
Why: User request 2026-10-25: finer control over which webhook events start agents: 'small epic- for each of supported webhooks add whiltelisting/blacklisting ability- e.g. grafana webhooks should blacklist if a label X consist of value Y, or issue/mr webhook will be received but internall ignorred if author is not one of the usernames from the list (or repos)- in general whitelist/blacklist capability for webhooks allowing for greater granularity in how to react to webhook events.'

## Description



## Goals



## Non-goals



## Review

Filled when the epic reaches stage `review`: the verdict, the findings acted on, the findings dropped.
