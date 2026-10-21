---
name: heartbeat
description: Progress line (% done + ETA) every 10 minutes while waiting on a workflow run, from one Monitor at near-zero orchestrator effort. Cache keepalive is OFF by default; enable --keepalive only on a 5-minute cache for a known idle gap under the break-even in this skill.
---

# heartbeat

Keepalive is off by default. Without `--keepalive` the beat is a progress
report every 600s, whatever the TTL.

One `Monitor`, one short line per beat. Each line wakes you for one turn; that
turn re-reads your cached prefix, which is what keeps a 5-minute cache alive.

## Is it worth it here

Prices relative to base input (platform.claude.com prompt-caching): 5m write
1.25x, 1h write 2x, read 0.1x (0.05x Opus/Sonnet 5.5, 0.025x Fable 5.1).
C = your context size, W = tokens you write per hour, r = read rate.

| Cache TTL | Verdict |
|---|---|
| 1h (subscription default for the main conversation) | No keepalive: the cache already lasts. Beats run every 600s and only replace the bounded-wait check you owe anyway. |
| 5m (API key, over plan limit, `FORCE_PROMPT_CACHING_5M`, or `promptCacheTtl: 5m`) | Keepalive pays: a beat costs r*C, a cold cache 1.25*C. With r=0.05 beats every 270s beat a miss for idle gaps up to ~110 min. Past that, stop beating and take the miss. |
| Switching 1h to 5m+heartbeat | Only when 0.75*W exceeds the beats' r*C*(60/4.5) per idle hour, i.e. W > ~0.9*C per idle hour. An orchestrator rarely writes that much while idle: keep 1h. |

The script detects the TTL (`--ttl auto`) from `FORCE_PROMPT_CACHING_5M`,
`CLAUDE_CODE_PROMPT_CACHE_TTL`, `promptCacheTtl` in `~/.claude/settings*.json`,
`ENABLE_PROMPT_CACHING_1H`, and `ANTHROPIC_API_KEY`, in the documented order.
Over-plan 5m cannot be detected; pass `--ttl 5m` when you know.

## Arm it - one call

```
Monitor({
  description: 'hb <run-name>',
  timeout_ms: 1800000,
  command: 'python3 ${CLAUDE_PLUGIN_ROOT}/skills/heartbeat/scripts/heartbeat.py --run <runId> --remaining-min <Remaining estimate from the epic README Time section> --total <task count>',
})
```

`--run <runId>` is the default way to arm, straight after launch: it finds the
run's journal and record under `~/.claude/projects` (override with
`--projects-dir` or `CLAUDE_PROJECTS_DIR`), prints `waiting for run <id>` until
the journal exists (bounded by `--wait-max` minutes, default 10, then
`END run <id> not found ...` and exit 2), and exits by itself with
`END <status> <done>/<total> tasks <duration>` when the run record appears, so
no stale monitor survives the run. A Monitor past its 30-minute expiry is
re-armed with the same `--run <id>` command. `--journal <journal.jsonl>` still works for a
known journal path and is mutually exclusive with `--run`. Add `--keepalive` only when the
table above says it pays (5m cache, idle gap under the break-even). `--remaining-min` feeds the ETA the epic's remaining estimate in minutes (ticket flow); the ETA reads it instead of the task count, which stays as the fallback when no estimates exist. Add `--no-eta` to skip the haiku
call (~600 tokens, $0.0002 per beat). Re-arm on expiry if still waiting.

Lines: `~78% done/12m left | 12/13 agents | run: impl:flow-wiring`,
`STALL 15m no journal change`, `END no journal`.

## On each beat - spend nothing

- `~<pct>% done...`: no tool call. Reply with nothing, or the line itself if the
  user is following along. Never a status dump.
- `STALL`: one check of the stalled item (its transcript mtime), then act.
- `END`, or the run's own completion notice: TaskStop the monitor.
- Stop beating when the wait is over, or past ~110 idle minutes on 5m.
