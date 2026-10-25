# Feedback loops

Loop types in preference order. Use the first one that can assert the exact symptom.

1. Failing test - write or find a unit/integration test asserting the symptom: `pytest path::test -q`.
2. curl - replay the request and assert status and body: `curl -sf -o /dev/null -w '%{http_code}' URL | grep -qx 500`.
3. CLI snapshot diff - run the CLI on a fixed input and `diff` against a saved good output.
4. Headless browser - script the page with Playwright and assert the DOM or console error.
5. Trace replay - capture the failing request or event stream once, replay it against the code.
6. Throwaway harness - a 20-line script calling the suspect function with the captured input; delete after.
7. Fuzz - generate inputs until the symptom fires, then shrink the case (hypothesis, `--seed`).
8. `git bisect run` - find the commit that introduced it:
   `git bisect start <bad> <good>` then `git bisect run <cmd>` (cmd exits 0 good, 1-124 bad, 125 skip); end with `git bisect reset`.
9. Differential - run the same input through the working and the broken version or environment and diff the outputs.
10. Live signals - when the workbench-observability pack is enabled, a Loki or Prometheus query via `grafana-debugging-start`; for pod-level evidence use `k8s-triage` and `kubectl-logs-query`. The query is the loop: assert on its output.
11. Interactive script for a human - last resort; the script prints exact steps and the expected output, and the human pastes the result back.

## Flaky

A failure at 50% is debuggable; 1% is not. Raise the rate first: tighten inputs, pin seeds, fix the clock, remove parallelism, add load or sleeps at the suspected race. Loop the command N times and count:

`for i in $(seq 50); do cmd >/dev/null 2>&1 || echo F; done | wc -l`

Report the rate before and after each change. Do not start phase 2 until the rate is high enough to read a result in under a minute.

## Proofs

Pristine-diff proof (the red was forced by a mutation):
1. Before mutating, copy the file: `cp f <workbench root>/.scratchpad/pristine-f`.
2. Mutate, run the test, see it red.
3. `diff <workbench root>/.scratchpad/pristine-f f` shows only the intended mutation.
4. Restore from the pristine copy and confirm `diff` is empty.

Revert proof (the fix is what turns the test green):
1. Test is green with the fix.
2. `git stash push -- <fix files>` (or `git revert --no-commit <fix>`): the test fails.
3. Restore (`git stash pop`): the test passes again.
4. Quote all three outputs in the record.
