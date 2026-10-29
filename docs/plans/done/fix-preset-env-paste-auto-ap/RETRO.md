# Fix preset .env paste: auto-apply on save, accept secret-named keys retro

<!-- retro:generated:begin -->
## Tasks

Delivery order; written by `ticket.py retro`.

| Task | Points (estimate) | Points (post-delivery) | Minutes (expected) | Minutes (actual) | Tokens (expected) | Tokens (actual) |
|---|---|---|---|---|---|---|
| web env paste fix | 3 | 3 | 8 | 12 | 1003544 | 657541 |
| Total | 3 | 3 | 8 | 12 | 1003544 | 657541 |

## Deltas

| Task | Points (post-delivery - estimate) | Minutes (actual / expected) | Tokens (actual / expected) |
|---|---|---|---|
| web env paste fix | 0 | 1.50 | 0.66 |

- MdAPE points: 0.0%
- MdAPE minutes: 33.3%
- MdAPE tokens: 52.6%
<!-- retro:generated:end -->

## Retro

| Went well | Went bad / could be improved |
|---|---|
| web-env-paste-fix closed in 0 fix rounds: red 7 failed/44 passed, green 51/51, reviewer clean, `mise run test` 648 passed, lint ok. | |
| Points held: estimate 3, post-delivery 3 (MdAPE 0.0%). | Minutes 12 actual vs 8 expected (1.50x, MdAPE 33.3%); tokens 657541 vs 1003544 (0.66x, MdAPE 52.6%): the tokens seed was high for a one-file web fix. |
| Scope audit found goals 1-3 and AC1-AC7 delivered with no duplicates; goal 4 (deploy) verified live: image agents-web:ab78d97 rolled out, live bundle has no secret-key rule. Lean epic took about 75 min from the mx-34 request (12:46Z) to live. | |
| Deploy was safe and clean up after: lease taken and deleted, selector-scoped apply (`--selector name=agents-web`) left the orchestrator pin untouched, temp kubeconfig, GNUPGHOME and registry login removed. | The helmfile pin (agents-helmfile PR #51, 1906b61) ran outside the ticket system: `ticket.py new-task` refused it over a file overlap with hive-decoupling helmfile-deploy-pin, so it has no task, points or deltas. |
| | Environment friction cost time: push needed `gh auth git-credential` as the git credential helper; gpg-agent failed under the long scratchpad path (socket length) and needed a short /tmp GNUPGHOME; mise kube-context needed a built in-cluster-sa kubeconfig. |
| | Noted, not done: web RESERVED_KEY lacks the ORCH_* keys the orchestrator rejects, so a pasted ORCH_* key passes the web check and fails server-side. |

## Improvements

- Code:
  - code/agents-web (preset env paste validation, RESERVED_KEY): add the ORCH_* keys the orchestrator rejects, with a test, so the web and server rules agree.
- Delivered differently than expected:
  - The helmfile pin (agents-helmfile PR #51) was delivered outside a ticket task, not as a planned task: `ticket.py new-task` refused it over a file overlap with the in-progress hive-decoupling helmfile-deploy-pin task. No other deviation from the requirement, design or plan was recorded.
- Tech debt introduced:
  - The web/orchestrator reserved-key mismatch (ORCH_*) above stays open; it lives in the agents-web RESERVED_KEY list and is removed by sharing or mirroring the orchestrator's list.
- Workflow:
  - recurring (matrix-connector-agent-initi, deploy-safe-agent-sessions, file-download-in-file-browse): git push needed the gh credential helper again. Change: the harness setup or SessionStart hook configures `gh auth setup-git` (https push URLs) so no agent sets it by hand.
  - `ticket.py new-task` refuses a task on a file overlap with another epic's in-progress task, with no path to record deploy work that must touch the same file: let `new-task` accept an explicit overlap override with a note, or let the pin go through `ticket.py amend` on the owning epic, so the work keeps points and deltas.
  - Deploy tooling in a scratchpad session: gpg-agent fails when the scratchpad path exceeds the socket length, and mise kube-context needs a built in-cluster-sa kubeconfig. Change: the deploy checklist or `mise run apply` preflight sets a short GNUPGHOME under /tmp and builds the kubeconfig.
