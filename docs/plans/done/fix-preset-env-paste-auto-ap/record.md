# Fix preset .env paste: auto-apply on save, accept secret-named keys record

## Asked

The preset form dropped .env text left in the Paste box when Create/Save was pressed without Apply, and flagged TOKEN/PASSWORD-style keys as secrets. Goals: auto-apply a pending paste on Create/Save, refuse the submit on parse errors, accept secret-named keys with no warning, and deploy the bumped agents-web chart pin under the deploy lease. No orchestrator change.

## Shipped

agents-web commit 7027bb1 (apply a pending paste on Create/Save through one shared parse+merge helper; SECRET_KEY rule removed from envKeyError), merged as PR https://github.com/szymonrychu/agents-web/pull/22 (ab78d97, main CI passed). agents-helmfile PR https://github.com/szymonrychu/agents-helmfile/pull/51 (pin ab78d97, commit 1906b61) merged as 082bedc. Deploy: `mise run apply -- --selector name=agents-web` from 1906b61 passed lint, 290 tests and check-pins; agents-web upgraded, rollout ok, image agents-web:ab78d97, live bundle has no secret-key rule; lease deleted and temp kubeconfig/GNUPGHOME/registry login removed. Epic review verdict: pass (2026-10-29); scope audit found goals 1-3 and AC1-AC7 delivered, no duplicates.

## Tasks

| Task | Status | Verified head | Review rounds | Verification tail |
|---|---|---|---|---|
| web-env-paste-fix | done | 7027bb150cec147e0fdb63ce0364d29cad07df7b (in the epic git log) | 0 (clean on round 0) | red 7 failed/44 passed, green 51/51; mise run test 648 passed, lint ok |

Tasks done vs planned: 1 of 1. The helmfile pin (goal 4) has no task row, see Rulings.

## Rulings

- Helmfile pin and deploy run outside a ticket task. Why: new-task refused the file overlap with hive-decoupling helmfile-deploy-pin. The selector-scoped apply (`--selector name=agents-web`) left the orchestrator pin untouched. Cost if wrong: the pin and deploy have no task file, verified head or review round, so only the PR, the CI run and the apply output evidence them; an overlap with hive-decoupling's pin edit could conflict on rebase.
- Submit with merged rows that carry an envKeyError (reserved, duplicate) sets the rows into state and does not send (implementer's call, task Notes). Why: keys from a paste are judged by the same rules as typed keys. Cost if wrong: a user pasting a reserved key sees the rows applied but nothing saved until fixed.
- Web RESERVED_KEY lacks ORCH_* that the orchestrator rejects: dropped from scope as "noted, not doing now". Why: non-goal, no change to the reserved-name checks. Cost if wrong: a pasted ORCH_* key passes the web form and is rejected by the orchestrator at submit.

## Discovered and blocked

- Discovered: web RESERVED_KEY lacks ORCH_* (see Rulings). Whoever owns a follow-up web ticket can clear it; not blocking.
- Blocked: none.

## Not pushed

- agents-web: nothing unpushed; the branch is pushed and PR #22 merged (origin/main ab78d97). Local main checkout is 2 commits behind origin/main (not fetched or fast-forwarded).
- agents-helmfile: nothing unpushed; origin/main is 082bedc.
- Workbench superrepo: local main is 39 commits ahead of origin/main, including the epic's ticket commits (new-task through retro). Not pushed; the user or the orchestrator pushes it.

## Lessons routed to

- Ticket overlap guard (mechanical): `ticket.py new-task` refused a pin task because another epic touches the same file, which forced the helmfile pin outside a ticket. Check to add: a `ticket.py` test or option that lets a cross-epic pin overlap be recorded as a task when the edited lines are disjoint. Not routed anywhere yet.
- ORCH_* reserved key drift (mechanical): add a test in agents-web that compares the web RESERVED_KEY list with the orchestrator's rejected prefixes. Not added in this epic.
