---
title: helmfile pin check
status: todo
repo: agents-helmfile
value: apply refuses to deploy any pinned build whose CI is not green
files: [scripts/check_pins.py, tests/test_check_pins.py, tests/fixtures/check_runs_agents_orchestrator.json, mise.toml, tests/test_mise_tasks.py, README.md, MEMORY.md]
verify: "uv run pytest -q tests/test_check_pins.py tests/test_mise_tasks.py && mise run lint"
depends_on: []
model: opus
review: ""
verified_head: ""
points: 5
expected_minutes: 8
expected_tokens: 1828146
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# helmfile pin check

## Requirement

Design D9, user decision verbatim: "Red builds: agents-orchestrator CI pushes images and publishes charts only after lint, test and e2e pass (split the push out of `images` or gate a retag; e2e must not need the pushed image if that is how it works today, check); agents-web image push and chart-publish need the `web` job. agents-helmfile gets a pin check (gh api check-runs, or reuse plugins/workbench/skills/_lib/scm.py reducers) for every pinned main-built commit (orchestrator, web, webhook, schedule, matrix-connector charts; wrapper release tag resolved to its commit) that apply depends on; no override flag. Its tests use fakes like tests/test_smoke_script.py."

Design D9 (my call), verbatim: "The pin check calls `gh api repos/szymonrychu/<repo>/commits/<ref>/check-runs` from a script in agents-helmfile: the submodule is an independent repo and cannot import the workbench's `_lib/scm.py`. A pin passes only when at least one check run exists and every one is `completed` with conclusion `success`, `neutral` or `skipped`. `0.1.0-main.<sha7>` resolves to that commit; a release version `X.Y.Z` (agents-schedule chart `0.1.0`, wrapper image `0.3.2`) resolves through tag `vX.Y.Z`. `mise run apply` depends on it."

Goal G8, verbatim: "No red main build is published or deployed: CI publish jobs need e2e/tests, and the agents-helmfile apply refuses pins whose commit checks are not green."

Scope (agents-helmfile):
- `scripts/check_pins.py` (run with `uv run`): reads the pins from `helmfile.yaml.gotmpl` (chart `version:` of agents-orchestrator, agents-web, agents-webhook, agents-schedule, agents-matrix-connector) and `values/agents-orchestrator/common.yaml` (`image.tag`, `agentImage`, `env.ORCH_AGENT_IMAGES`) and `values/agents-web/common.yaml` (`image.tag`); maps each to its GitHub repo (`szymonrychu/<repo>`, the wrapper image to `claude-code-wrapper`); resolves `0.1.0-main.<sha7>` or an image sha7 to the commit, `X.Y.Z` through tag `vX.Y.Z`; lists the commit's check runs through `gh api` (paginated); prints one line per pin and exits non-zero naming each refused pin (repo, version, commit, and the checks that are not green). A missing or unparsable pin is a refusal, never a pass. No flag or env var skips it.
- `mise.toml`: task `check-pins` (description names what it checks); `apply` depends on `check-pins`; `gh` pinned in `[tools]` if the repo does not already provide it (probe the version, never guess).
- `tests/test_check_pins.py`: a fake `gh` on PATH (the fakebin pattern of `tests/test_smoke_script.py`) serving responses built from a real `gh api repos/szymonrychu/agents-orchestrator/commits/<sha>/check-runs` response captured once and committed as `tests/fixtures/check_runs_agents_orchestrator.json` (retro: fakes must follow a captured real output).
- `tests/test_mise_tasks.py`: `apply` depends on `check-pins`.
- `README.md` (Operating) names the task; MEMORY.md dated entry.

Interfaces: `mise run check-pins` exit 0 only when every pin is green; output lines `pin <release> <version> <commit>: ok|refused (<reasons>)`.

Steps: capture the real response first (`gh api repos/szymonrychu/agents-orchestrator/commits/96e46f3/check-runs > tests/fixtures/check_runs_agents_orchestrator.json`, secrets-free); write the tests and see them fail; then the script and the task; run the verify.

Notes: against today's pins the check must refuse agents-orchestrator 96e46f3 (main CI run 40565058706, e2e failed), which is the incident this guards. `mise run apply` is never run by this task. gitleaks runs in lint: keep the fixture free of tokens.

## Acceptance conditions

- AC1: every pin source is resolved: orchestrator, web, webhook, schedule and matrix-connector charts, the orchestrator and web image tags, agentImage and ORCH_AGENT_IMAGES [evidence: test:tests/test_check_pins.py::test_every_pin_resolved]
- AC2: pins whose check runs are all completed success, neutral or skipped pass with exit 0 [evidence: test:tests/test_check_pins.py::test_green_pins_pass]
- AC3: a failed, cancelled, timed-out, in-progress or absent check run refuses with the repo, version, commit and check names and a non-zero exit [evidence: test:tests/test_check_pins.py::test_red_pin_refused]
- AC4: a release version X.Y.Z resolves through tag vX.Y.Z [evidence: test:tests/test_check_pins.py::test_release_version_resolves_through_tag]
- AC5: no flag or environment variable skips the check [evidence: test:tests/test_check_pins.py::test_no_override]
- AC6: the fake gh serves responses built from a captured real check-runs response [evidence: test:tests/test_check_pins.py::test_fixture_is_real_check_runs_shape]
- AC7: apply depends on check-pins [evidence: test:tests/test_mise_tasks.py::test_apply_depends_on_check_pins]
- AC8: README names every task, check-pins included [evidence: test:tests/test_mise_tasks.py::test_readme_names_every_task]
- AC9: against today's pins the live check refuses agents-orchestrator 96e46f3 [evidence: command:mise run check-pins 2>&1 | grep -q "agents-orchestrator.*96e46f3.*refused"]
- AC10: MEMORY.md records the decision [evidence: command:grep -q "check-pins" MEMORY.md]
- AC11: lint passes [evidence: command:mise run lint]

## Files

- `scripts/check_pins.py`
- `tests/test_check_pins.py`
- `tests/fixtures/check_runs_agents_orchestrator.json`
- `mise.toml`
- `tests/test_mise_tasks.py`
- `README.md`
- `MEMORY.md`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
