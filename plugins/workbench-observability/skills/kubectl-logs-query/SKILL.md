---
name: kubectl-logs-query
description: "Read-only kubectl dig into a workload Loki does not capture: pod logs, --previous crash logs, events, describe. Use when a Loki query comes back empty, or metrics point at a pod whose own stdout is the missing evidence."
---

# kubectl-logs-query

Some workloads run in the cluster but never reach Loki (no promtail
scrape, stdout-only apps writing to files, sidecar-less pods). When the
grafana funnel stalls at "logs empty for a namespace that clearly exists",
go to the source: `kubectl` against the live cluster. This is a read-only
companion to `grafana-debugging-start`, not a replacement - metrics and
Loki still lead; kubectl fills the log gap.

Use the current kubectl context (`kubectl config current-context`) and
never switch it. Requires `kubectl` and `stern` on PATH (mise-pinned in
the project when used).

## Hard rule: read-only

Only ever run observing verbs:

- `kubectl get`, `logs`, `describe`, `events`, `top`
- `kubectl exec <pod> -- <read-only cmd>` (e.g. `cat`, `ls`, `tail` of an
  in-container log file) - reads only, never a command that writes,
  deletes, restarts, or changes state.
- `stern` for multi-pod / multi-container log tailing.

Never `apply`, `create`, `delete`, `edit`, `patch`, `scale`, `rollout
restart`, `cordon`, `drain`, `label`, `annotate`, or any `exec` that
mutates. If a fix needs a write, hand it back to the user - this skill
only diagnoses.

## Procedure

1. **Locate the pod.** Metrics or the grafana investigation already named
   the namespace and workload; resolve the exact pod:
   ```
   kubectl -n <ns> get pods -o wide            # note node, restarts, age
   kubectl -n <ns> get pods -l app=<app> -o name
   ```
   `RESTARTS` and `AGE` alone often answer "did it crash in the window?".

2. **Time-bound to the incident.** Never dump a whole log. Scope with
   `--since` / `--since-time` to the bad window and add timestamps:
   ```
   kubectl -n <ns> logs <pod> --since=20m --timestamps
   kubectl -n <ns> logs <pod> --since-time=2026-07-11T19:00:00Z --timestamps
   ```
   Pod clocks may print local time; convert to the same UTC window the
   grafana report uses before correlating.

3. **Crash / restart reason** comes from the *previous* container plus
   events, not the running one:
   ```
   kubectl -n <ns> logs <pod> --previous --timestamps      # pre-restart stdout
   kubectl -n <ns> describe pod <pod>                       # last state, exit code, OOMKilled
   kubectl -n <ns> get events --sort-by=.lastTimestamp | grep <pod-or-app>
   ```

4. **Multi-container / multi-pod.** Pick the container with `-c`; sweep a
   whole app with stern:
   ```
   kubectl -n <ns> logs <pod> -c <container> --since=20m
   stern -n <ns> <app> --since 20m --no-follow
   ```

5. **App error detail not on stdout.** Many apps log to files inside the
   container (application logs, web server error logs). Read them
   in place - still read-only:
   ```
   kubectl -n <ns> exec <pod> -- ls -t /var/log/app/ | head
   kubectl -n <ns> exec <pod> -- cat /var/log/app/<newest>.log
   ```

6. **Narrow-first, then grep.** Filter to the signal; save anything large
   to the scratchpad instead of flooding context:
   ```
   kubectl -n <ns> logs <pod> --since=30m | grep -iE 'error|fail|exit code|panic'
   ```

## Correlate back

A kubectl finding is evidence, same bar as a grafana one: quote the exact
line (error string, exit code, `OOMKilled`, event reason) and the UTC time,
and line it up against the metric/Loki window already in the investigation
report. Add it as a claim there rather than concluding from the log alone.
