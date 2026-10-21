---
name: grafana-debugging-start
description: "Debug a live incident, firing alert, or spike in latency, error rate, or saturation via the grafana MCP server - Prometheus metrics, Loki logs, Pyroscope profiles. Triggers on golden-signal regressions and unknown root cause."
---

# Grafana debugging start

## Overview

Investigate broad to narrow: one signal narrows the search space for the
next, never the reverse. Start at the golden-signal level (rate, errors,
duration / utilization, saturation, errors), let each result pick the next
stage of the funnel, and never assert a claim that isn't backed by a tool
call recorded in the report. This skill scaffolds that discipline; it does
not replace judgment about which branch to take.

## Before you start

1. Call `list_datasources` first, every time. Datasource uids and which
   types exist (Prometheus, Loki, Pyroscope, Tempo) can change - never
   assume from memory.
2. If the project added `references/<project>-topology.md`, consult it for
   known datasource uids, job/app labels, and dashboards, but re-verify
   against the live `list_datasources` / `list_prometheus_label_values` /
   `search_dashboards` output before relying on it. Treat it as a fast-path
   hint, not ground truth.
3. Open a report before making any investigative call:
   `python ${CLAUDE_PLUGIN_ROOT}/skills/grafana-debugging-start/scripts/investigation.py init <slug>`
   This writes `docs/grafana-investigations/YYYY-MM-DD-<slug>.md`
   (gitignored). Keep the returned path; every later step references it.

## The funnel

Work these stages in order. Skip a stage only when its question is
already answered by a preceding stage's result - never skip forward to
guess.

| # | Stage | Question | Typical tool |
|---|---|---|---|
| 0 | Discover | What datasources and services actually exist right now? | `list_datasources`, `list_prometheus_label_values`, `search_dashboards` |
| 1 | Golden signals | Which service, and which of rate/errors/duration or utilization/saturation/errors is abnormal? | `query_prometheus`, `get_dashboard_summary` on the relevant dashboard |
| 2 | Latency shape | Is it a tail-latency problem (p99/p95) or broad? | `query_prometheus_histogram` |
| 3 | Logs | What is the service actually saying during the bad window? | `query_loki_logs`, `query_loki_patterns` |
| 4 | Correlate | Does a log pattern, deploy annotation, or dependency metric line up with the bad window? | `get_annotations`, `query_prometheus` on dependencies |
| 5 | Profile (if a Pyroscope datasource exists) | Where is CPU/memory actually spent inside the process? | `query_pyroscope`, `list_pyroscope_profile_types` |
| 6 | Trace (if a Tempo/tracing datasource exists) | Which downstream hop owns the latency/error? | exemplar-linked trace lookup via the tracing datasource |

Exact params for every tool above are in
`references/mcp-tool-cheatsheet.md` - do not duplicate them here, and do
not guess casing at call time; read the tool's live JSON schema.

A code defect found through the funnel continues in `start-debugging` phase 1, with the query as the feedback loop.

Stages 5 and 6 are conditional: on a Grafana with no Pyroscope or Tempo
datasource (confirmed via stage 0), state that explicitly in the report
and stop the funnel at stage 4 correlation rather than fabricating a
profile or trace result.

## Branch decision table

| Symptom | Next signal | Tool shape |
|---|---|---|
| Firing alert | The alert's own PromQL expression, same window | `query_prometheus` with the alert's `expr` |
| Elevated error rate | Error logs for the same service/window | `query_loki_logs` with `{app="..."} \|= "error"` scoped narrow first |
| High p99, low mean | Histogram buckets, not the average | `query_prometheus_histogram` |
| Saturation (CPU/mem/queue) | Resource metric for the same pod/job | `query_prometheus` on `container_*` / queue-depth metric |
| Unknown root cause after logs+metrics agree on a window | CPU/memory profile, if Pyroscope exists | `query_pyroscope` |
| Cross-service latency, single hop suspected | Trace for the exemplar in that window, if Tempo exists | tracing datasource lookup |
| Empty result at any stage | Re-check the label/uid used, not the absence of the problem | `list_*_label_values` for the label just queried |

## Query discipline (hard rules)

- Narrow-first. Scope every query to the smallest label set that answers
  the question (namespace + job/app at minimum) before adding more
  conditions.
- Confirm existence before querying: check a metric name, label, or log
  stream exists (`list_prometheus_metric_names`, `list_loki_label_values`,
  `query_loki_stats`) before spending a call on the real query.
- Trust live schema over memory. Params are camelCase; confirm exact
  names from the tool's own JSON schema at call time - never guess from a
  cheatsheet or a prior investigation.
- Use p99/p95 for latency, never the mean. Never average percentiles
  across series or windows - average buckets, then compute the percentile,
  or use `query_prometheus_histogram` directly.
- Rate windows must be at least 4x the scrape interval (for example,
  `rate(...[1m])` needs at most a 15s scrape interval; default to `5m` if
  the scrape interval is unknown).
- In Loki, filter label-before-line-before-parser: narrow with label
  selectors first, then line filters (`|=`), then a parser stage - never
  open with a high-cardinality label matcher (pod, trace id) as the
  primary selector.

## Phase-gate loop

1. Plan first. Before any tool call in a phase, write down in the report
   what question this phase answers and which stage of the funnel it is.
2. Per-phase self-check: after each call, ask "is this enough to answer
   the phase's question?" If not, narrow and re-query; if yes, move to the
   next phase.
3. Apply five-whys once a proximate cause is found - keep asking why
   until the answer is a concrete, tool-verified fact, not "seems like."
4. Mandatory final review: before closing, run
   `python ${CLAUDE_PLUGIN_ROOT}/skills/grafana-debugging-start/scripts/investigation.py finalize <report> --claim "text::evidence"`
   for every claim in the report. A claim with no evidence prints flagged
   as missing - do not close the investigation until every claim has a
   tool-call citation.

Log every meaningful step as you make it, not retroactively:
`python ${CLAUDE_PLUGIN_ROOT}/skills/grafana-debugging-start/scripts/investigation.py append <report> --phase N --stage S --tool T --query Q --finding F`

## Guardrails

- Read-only. Never call a write tool (`update_dashboard`, `create_dashboard`,
  `alerting_manage_rules`, `alerting_manage_routing`, or any other mutating
  tool) during an investigation. This skill only observes.
- Tool-budget stop rule: if 8 tool calls pass without narrowing the
  hypothesis (each result still leaves the same set of candidate causes),
  stop and re-plan instead of continuing to probe.
- Empty-result disambiguation: an empty result means either the wrong
  label/uid was used, or the condition genuinely does not occur - always
  check which with a `list_*_label_values` / `query_loki_stats` call
  before concluding "absent."
- Multi-datasource ambiguity: when more than one datasource of the same
  type exists (for example two Loki datasources), confirm which one is
  actually wired to the target service before trusting its result - do
  not assume the first one returned by `list_datasources`.
- Correlation is a hypothesis, not a cause. Two signals moving together in
  the same window is evidence to investigate further, not a claim to
  finalize without a mechanism.

## Project topology fast-path

A project may add `references/<project>-topology.md` to this skill, listing
its previously-probed datasource uids, job/app label mappings, and dashboard
uids. When present, use it to skip straight to stage 1 of the funnel - but
always re-verify via `list_datasources` / `list_prometheus_label_values` /
`search_dashboards` first, since these values drift and the file should state
its own probe date. No topology file ships with the pack.

## When Loki has no logs for the workload

If stage 3 comes back empty because the workload ships nothing to Loki (no
promtail scrape, stdout-only app, logs written to files) - not because the
label was wrong - the `kubectl-logs-query` skill is a read-only fallback:
pod logs, `--previous` crash logs, events, and in-container log files
straight from the cluster, time-bounded to the same window. Weak
suggestion, not a required stage: reach for it only once metrics and Loki
have narrowed to a specific pod and its own logs are the missing evidence.

Two variants, pick by what you already know:

- **You know which pod.** Use the `kubectl-logs-query` skill inline - it is a
  targeted dig at a known workload and the output is already narrow.
- **You do not know which pod, or several look wrong.** Dispatch the
  `k8s-triage` agent instead. It sweeps every unhealthy workload read-only,
  pulls the relevant events and log tails itself, and returns the cause with
  one evidence line per workload - so the raw sweep never enters this context.
