# Grafana MCP tool cheatsheet

**Params below are a memory aid. At call time, trust the tool's own JSON
schema; never guess casing. All params are camelCase.**

## Prometheus

`query_prometheus`
- `datasourceUid`, `expr`, `startTime`/`endTime` (RFC3339 or relative like
  `now-1h`), `stepSeconds`, `queryType` (`range`|`instant`).

`query_prometheus_histogram`
- `metric` (base name, no `_bucket` suffix), `percentile`, `labels`,
  `rateInterval` (default `5m`), `startTime`/`endTime` (default
  `now-1h`/`now`), `stepSeconds` (default `60`).

`list_prometheus_metric_names`
- `regex`, `limit`, `page`. Confirm a metric exists before querying it.

`list_prometheus_label_values`
- `matches`, `startRfc3339`/`endRfc3339`, `limit`. Use to discover real
  label values (job/namespace/pod/...) instead of guessing.

`list_prometheus_label_names`, `list_prometheus_metric_metadata`
- Schema discovery: what labels/metrics exist before writing PromQL.

## Loki

`query_loki_logs`
- `logql`, `startRfc3339`/`endRfc3339`, `limit` (default 10), `direction`
  (`forward`|`backward`), `queryType`, `stepSeconds`.

`query_loki_patterns`
- Cluster raw log lines into patterns - use to see log shape before writing
  a line filter or parser.

`query_loki_stats`
- Cheap: check the volume/cardinality of a stream selector before running
  a heavier query over it.

`analyze_loki_labels`
- Inspect label cardinality; use before adding a label matcher to avoid a
  high-cardinality selector.

`list_loki_label_names`, `list_loki_label_values`
- Schema discovery: confirm a label and its values exist before filtering
  on it.

`suggest_loki_alloy_label_config`
- Operator-facing config generation, not investigation - out of scope for
  this skill's read path.

## Pyroscope (only if a Pyroscope datasource exists)

`query_pyroscope`, `list_pyroscope_profile_types`, `list_pyroscope_label_names`,
`list_pyroscope_label_values`
- Profiling is disabled by default on many Grafana instances. Check
  `list_datasources` first; if no Pyroscope datasource is present, skip
  this tier entirely rather than guessing at a uid.

## Traces (only if a Tempo/tracing datasource exists)

- Exemplar -> trace hops depend on a tracing datasource being wired up.
  If `list_datasources` shows none, treat trace-level root-causing as
  unavailable and stop the funnel at logs/metrics correlation.

## Sift (disabled by default; needs write-tools/Editor)

`find_error_pattern_logs`, `find_slow_requests`, `list_sift_investigations`,
`get_sift_investigation`, `get_sift_analysis` (singular, not "analyses")
- Only usable if the Sift plugin and write-tools are enabled for this
  session. Do not assume availability.

## Dashboards

Token economy: prefer `get_dashboard_summary` and `get_dashboard_property`
(JSONPath into a dashboard) over pulling the full `get_dashboard_by_uid`
JSON, which is large.

- `search_dashboards` - find a dashboard by title/tag query.
- `get_dashboard_summary` - compact structure: panels, datasources.
- `get_dashboard_property` - JSONPath a single field out of a dashboard.
- `get_dashboard_panel_queries` - the PromQL/LogQL a panel actually runs;
  useful to steal a known-good query instead of writing one from scratch.
- `get_dashboard_by_uid` - full JSON; last resort, expensive.

## Datasources

`list_datasources`
- Always the first call of an investigation. Confirms which of
  Prometheus/Loki/Pyroscope/Tempo actually exist and their real `uid`s.

`get_datasource`
- Detail on a single datasource once its uid is known.

## Navigation

`generate_deeplink`
- Produce a navigable Grafana URL (dashboard, panel, or Explore query) to
  hand the user - lets them jump straight to the evidence.

## Annotations / snapshots (read-only use)

`get_annotations`, `get_annotation_tags`, `list_snapshots`, `get_snapshot`
- Useful for correlating a symptom window with a deploy/change annotation
  already on a dashboard.
