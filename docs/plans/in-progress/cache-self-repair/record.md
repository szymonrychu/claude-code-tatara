# cache self repair record

## Asked

User decision 2026-10-26 ("cache repair- start empty"), from the workspace-s3-cache open question: a workspace cache archive that cannot be read must repair itself. Restore wipes the workdir and the session starts empty; the discard save then overwrites the bad archive, instead of the key staying blocked until someone deletes the object.

## Shipped

One task, built in agents-orchestrator. Epic review verdict: pass (2026-10-26), AC1-AC5 verified, 940 passed, lint clean. Merged as PR https://github.com/szymonrychu/agents-orchestrator/pull/20 (rebase) as ab37f1e; main CI run 40274861549 green including e2e. Superrepo pins agents-orchestrator ab37f1e (commit 5962c5e).

Deployed: the agents-helmfile re-pin to ab37f1e was carried by epic agents-matrix-connector-depl (commit 2a8376b, task orchestrator-repin-ab37f1e), because that epic held helmfile.yaml.gotmpl. Applied from its tree at 72b381e on 2026-10-26: `mise run apply` exit 0, `mise run smoke` exit 0 "smoke: OK", including the cache restore round trip. Logs: /Users/szymonri/Documents/claude-code-tatara/.logs/apply-matrix-72b381e.log and /Users/szymonri/Documents/claude-code-tatara/.logs/smoke-matrix-72b381e.log. The smoke covers the normal round trip; a live corrupt-archive repair was not exercised (unknown).

## Tasks

The plan-execute return value was not provided, so the independent verifier head, red evidence, declined, cannotVerify and forwardMerged could not be read. Verified head is the task file's verified_head (6ec2d89, the pre-rebase commit; the merged commit is ab37f1e). Rounds and verification tail are from the epic review note.

| Task | Status | Verified head | Points | Rounds | Verification tail |
|---|---|---|---|---|---|
| restore-resets-workdir-on-un | done | 6ec2d89 | 3/3 | unknown (reviewer pass) | 940 passed, lint clean |

Approvals ledger: the epic dir has no approvals.json, so no ledger rows (status unknown). The decision is the user's 2026-10-26 "cache repair- start empty".

## Rulings

- Only ExtractError resets (archive unreadable or untrusted). Transport drops and OSError (for example ENOSPC) stay `failed` with the save skipped. Why: the stored archive may be good, and wiping and overwriting it would destroy a valid cache. Cost if wrong: a truly corrupt archive hit only through such an error stays blocked until the object is deleted.
- agents-web is unchanged: it has no hard-coded cache states, so the new `reset` state needs no edit there. Cost if wrong: an unrecognised state string shown raw in the UI.
- `reset` is added to SAVE_OK_RESTORE_STATES, keeping the allow-list shape (fail safe) per D11. Cost if wrong: a reset session's save is skipped and the bad archive persists.
- Deploy carried by another epic: the helmfile re-pin rode with agents-matrix-connector-depl rather than a separate epic. Why: that epic held helmfile.yaml.gotmpl. Cost if wrong: none to scope; the deploy is traceable only through that epic.

## Discovered and blocked

none

## Not pushed

none known. The superrepo pin commit 5962c5e and the helmfile commit 2a8376b belong to other epics' pushes; their push state is unknown.

## Lessons routed to

none
