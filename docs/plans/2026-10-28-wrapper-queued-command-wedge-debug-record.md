# Debug record: wrapper wedged busy on queued_command turns (2026-10-28, cct2)

## Defect

User: "there is something wrong with claude-code-tatara session, it's session never loads queued
messages". Both claude-code-tatara wrappers stayed `busy` on turns Claude had finished (tatara-0
since 16:07:47Z, tatara-1 since 17:27:04Z); every later Stop was logged `ignoring stale Stop`; the
orchestrator only delivers to an idle leader, so mx-34's messages (#206, #214, #216, #219, #224,
#228) never reached tatara.

## Loop

`.scratchpad/tatara-queue-debug/loop.sh` (read-only GETs of orchestrator and wrapper state plus the
transcript): red 4/4 on tatara (`RED: leader turn wedged: its marker is only in a queued_command
attachment; 1 queued message(s) older than 5.0m undelivered`), green on cct2. Unit repro:
`.scratchpad/tatara-queue-debug/harness_parse.py` (same marker: `['turn-...']` from a user line,
`[]` from the attachment line).

## Hypotheses

1. Turn prompt absorbed mid-turn lands as a `queued_command` attachment the parser drops: CONFIRMED.
2. Orchestrator claim hold on the leader: refuted (the wrapper itself reports busy).
3. Wrapper version skew: refuted (tatara-1 on 0.3.2 wedged the same way).
4. Ingester stale or detached: refuted (live wrapper GET also says busy).
5. Genuinely long turn: refuted (both transcripts show the final Stop).

## Root cause

A background task-notification wakes Claude while the wrapper reports ready; the wrapper pastes the
next turn, Claude absorbs it mid-turn and records it as a `queued_command` attachment line;
`parse_line` (claude-code-wrapper `transcript.py`) dropped attachment lines, so the turn marker was
never matched (router) and every later Stop was treated as stale (session), with no turn timeout.

## Regression tests and fix

- `tests/test_transcript.py::test_queued_command_attachment_yields_the_user_prompt_event`,
  `tests/test_stop_gate.py::test_stop_ends_a_turn_whose_prompt_is_a_queued_command_attachment`,
  plus `test_other_attachment_types_yield_nothing`. Red before the fix (`assert [] ==
  [UserPrompt(...)]`, `assert 0 == 1`); revert proof by the reviewer (old transcript.py: both red;
  restored: green).
- Fix commit a9a05b6 (claude-code-wrapper PR #8, merge 62187b4); release bump PR #9 (a7b9c19), tag
  v0.3.3 (release run 40755350967).
- Deploy: agents-helmfile PR #40 (6548e1f) plus #42 (260bdc2, test guard follow-up); applied under
  the lease 20:23-20:55Z, smoke passed.

## Clearing the live wedge

- tatara-0: wrapper interrupt 18:11:55Z; the reconciler replaced the idle outdated pod 18:12:21Z and
  it resumed the same Claude session (`--resume 294ef4ee...`).
- tatara-1: quiet-gated interrupt (approved via mx-34), running after the 0.3.3 deploy; transcript
  copy `.logs/tatara-1-transcript-pre-interrupt.jsonl` (sha256 380210fc...) kept until tatara
  confirms Matrix resumed.
- cct2-1 (tatara, 2026-10-29, mx-34 #310): wedged on 0.3.2, last turn ended 21:49:47Z, DB busy
  since 18:51Z, 9 queued (240-295). Quiet-gated interrupt (one POST, 200); free at 02:23:39Z and
  msg 240 dispatched at once, the rest queued serially. No roll: it went busy again before the
  reconciler could replace it, so it stays on 0.3.2 in the same session until its next idle
  reconcile. Record: tatara `.scratchpad/cct2-wedge/record.md`.

## Follow-up (not started)

- A 0.3.3 wrapper fix does not help a pod still on 0.3.2 that the orchestrator thinks is busy,
  because it never rolls. Follow-up: an orchestrator-side stale-busy detector (busy with no wrapper
  progress past a threshold gets flagged or interrupted).

## Out of scope (noted)

- The race itself (wrapper accepting a turn while Claude handles a background wake); harmless after
  the fix.
- agents-helmfile has no CI test job, so a red main was not caught at PR time.
- The PR watcher's `--deploy` mode reported "no pipeline launched" for a running wrapper main run.
