# Semver image tags at the end of main builds retro

## Review

- Final verify: agents-helmfile `mise run test` "313 passed in 562.07s"; lint "no leaks found"; superrepo `pytest scripts/tests/test_agents_md.py` "13 passed, 5 skipped"; chunk 1 repos all green (orchestrator 44, web pass 40 fail 0, webhook 30, schedule 27, matrix-connector 22).
- Fix rounds: one. The `Compute version` step swallowed a script failure (`echo "version=$(...)"`); fixed in all five repos by assigning the variable first. Acted on.
- Findings dropped: none.
- Pins match the released tags: orchestrator, web, webhook, matrix-connector 0.1.0 (8f92c7a, 127829f, 47ee475, 8130903), schedule 0.2.0 (1e2e2a8). Fake-ps test fix ee1111d judged boy-scout.

## What went well

- Script and workflow tests were identical across repos (byte-identical copies verified with cmp), so five reviews were one review.
- Tag-last ordering and the "contained in" skip make re-runs idempotent.
- Plan-level tests pin the absence of the retired tag path and of `secrets.GITHUB_TOKEN`.

## What went wrong or could improve

- The plan itself specified the swallowing `echo "version=$(...)"` line; plan snippets that run in CI need a failure-path check at planning time.
- helmfile `mise run test` takes about 9.5 minutes; reviews and fix rounds pay that each run.

## Recommendations

- Discovered and not built:
  - PR watcher reports "no pipeline launched" too early on a fresh main push.
  - `mise run init:refresh` rewrites MEMORY.md and docs/architecture.md with no change.
  - Harbor login 403 flake hit one images job.
- Out-of-scope ideas: none.
- Impossible at planning time: none.
