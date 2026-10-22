---
title: Heartbeat quiet
status: in-progress
repo: workbench
value: "The waiting orchestrator wakes only on END, STALL or real progress, with no haiku per beat"
files: [plugins/workbench/skills/heartbeat/scripts/heartbeat.py, plugins/workbench/skills/heartbeat/SKILL.md, plugins/workbench/skills/heartbeat/tests/test_heartbeat.py, plugins/workbench/skills/heartbeat/tests/test_heartbeat_run.py, AGENTS.md]
verify: "bash mise-tasks/lint/agents-md && python3 scripts/harness/setup.py --check && cd plugins/workbench && bash scripts/run-tests.sh --only heartbeat && ruff check skills"
depends_on: []
owns: []
uses: []
model: sonnet
estimate: 6
actual: ""
review: ""
worktree: ""
branch: ""
verified_head: ""
run: ""
provides: []
---

# Heartbeat quiet

## Requirement

Make the heartbeat quiet by default (design D3, gate question Q1).

- heartbeat.py keeps polling every `--interval` seconds (default 600). New `--report-every` seconds (default 1800): a progress line prints only when the journal digest differs from the digest last printed and at least report-every seconds passed since the last printed line (the first changed beat after arming prints). An unchanged digest prints nothing.
- STALL (journal size unchanged for `--stall-beats` polls, default 3) and END print at once, whatever the report interval. `waiting for run <id>` prints at most once per report interval.
- The haiku ETA runs only with the new `--eta` flag; `--no-eta` is still accepted and changes nothing; by default no `claude` process is started.
- `--keepalive` (5-minute cache) prints every beat as today, because its purpose is the wake.
- `skills/heartbeat/SKILL.md`: the description, the arm command and a new `## Quiet by default` section state the default: silent while nothing changes, a progress line at most every 30 minutes, STALL and END at once, ETA opt-in with `--eta`.
- Root `AGENTS.md` ground rule 4 gets one sentence: the heartbeat of a plan-execute run is the bounded watcher for that wait; it prints END and STALL at once and progress at most every 30 minutes, so silence between its lines is not a broken watcher.

## Acceptance conditions

- AC1: a beat with an unchanged digest prints nothing [evidence: test:plugins/workbench/skills/heartbeat/tests/test_heartbeat_run.py::test_unchanged_digest_prints_nothing]
- AC2: a changed digest prints at most once per report interval [evidence: test:plugins/workbench/skills/heartbeat/tests/test_heartbeat_run.py::test_progress_line_at_most_every_report_interval]
- AC3: STALL and END print at once [evidence: test:plugins/workbench/skills/heartbeat/tests/test_heartbeat_run.py::test_stall_and_end_print_immediately]
- AC4: no claude call by default; --eta makes it [evidence: test:plugins/workbench/skills/heartbeat/tests/test_heartbeat.py::test_eta_is_opt_in]
- AC5: --keepalive still prints every beat [evidence: test:plugins/workbench/skills/heartbeat/tests/test_heartbeat_run.py::test_keepalive_still_prints_every_beat]
- AC6: the skill documents the quiet default [evidence: doc-section:plugins/workbench/skills/heartbeat/SKILL.md#Quiet by default]
- AC7: AGENTS.md names the heartbeat bound and stays under its size limit [evidence: command:grep -q 'progress at most every 30 minutes' AGENTS.md && bash mise-tasks/lint/agents-md && python3 scripts/harness/setup.py --check]

## Files

- `plugins/workbench/skills/heartbeat/scripts/heartbeat.py`
- `plugins/workbench/skills/heartbeat/SKILL.md`
- `plugins/workbench/skills/heartbeat/tests/test_heartbeat.py`
- `plugins/workbench/skills/heartbeat/tests/test_heartbeat_run.py`
- `AGENTS.md`

## Interfaces

- CLI: `heartbeat.py (--run <id> | --journal <path>) [--interval S] [--report-every S] [--stall-beats N] [--eta] [--no-eta] [--keepalive] ...`; the line formats (`~<pct>% done...`, `STALL <n>m no journal change`, `END ...`) are unchanged.

## Expected outcome

A waiting orchestrator wakes when a run ends or stalls and otherwise at most twice an hour, with no haiku call per beat.

## Steps

- Red: add AC1-AC5 to `skills/heartbeat/tests/test_heartbeat_run.py` and `test_heartbeat.py` (inject the clock and sleep as the existing tests do); run `cd plugins/workbench && bash scripts/run-tests.sh --only heartbeat`; expect failures.
- Green: the report gate in `main`, the `--eta` flag, the SKILL.md section, the AGENTS.md sentence.
- Run the task verify; expect green.

## Notes

- If the user answers no to Q1, the orchestrator amends this task to `--report-every 600` before the run; nothing else changes.
- AGENTS.md line 87 (ground rule 4) is outside the generated `workbench:rules` block; edit only that rule's text.
- Keep the STALL arithmetic on polls, not on printed lines.
