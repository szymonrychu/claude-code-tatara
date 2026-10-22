// validate-tasks.mjs --epic: a todo task whose verify is the full suite fails the lint (D10, D11, D13).
import assert from 'node:assert/strict'
import { readFileSync, writeFileSync } from 'node:fs'
import { join } from 'node:path'
import { test } from 'node:test'
import { cli, epic } from './overlap-epic-fixture.mjs'

const setTask = (d, name, verify, status) => {
  const p = join(d, 'tasks', `${name}.md`)
  let md = readFileSync(p, 'utf8').replace(/^verify: .*$/m, `verify: ${verify}`)
  if (status) md = md.replace(/^status: .*$/m, `status: ${status}`)
  writeFileSync(p, md)
}
const MSG = /task t-one: verify '.*' runs the full suite; name the test files or the component suite \(run-tests\.sh --only <component>\) plus lint, and split the task if that is not enough/

test('full-suite-verify-on-todo-task-fails', () => {
  const d = epic('README.md')
  setTask(d, 't-one', 'mise run test')
  const r = cli(d)
  assert.equal(r.status, 1, r.stderr)
  assert.match(r.stderr, MSG)
})

test('a leading cd part is skipped', () => {
  const d = epic('README.md')
  setTask(d, 't-one', 'cd plugins/workbench && bash scripts/run-tests.sh')
  assert.match(cli(d).stderr, MSG)
})

test('repo-suites-entry-counts-as-full', () => {
  const d = epic('README.md', JSON.stringify({ suites: ['npm run everything'] }))
  setTask(d, 't-one', 'npm run everything')
  assert.match(cli(d).stderr, MSG)
})

test('targeted-verify-passes', () => {
  const d = epic('README.md')
  setTask(d, 't-one', 'cd plugins/workbench && bash scripts/run-tests.sh --only workflows')
  const r = cli(d)
  assert.doesNotMatch(r.stderr, /runs the full suite/, r.stderr)
})

test('full-suite-verify-on-started-task-warns', () => {
  const d = epic('README.md')
  setTask(d, 't-one', 'mise run test', 'in-progress')
  const r = cli(d)
  assert.doesNotMatch(r.stderr, /^task t-one: verify/m)
  assert.match(r.stderr, /warning: task t-one: verify '.*' runs the full suite/)
})

test('no-estimate-warning', () => {
  const d = epic('README.md')
  const p = join(d, 'tasks', 't-one.md')
  writeFileSync(p, readFileSync(p, 'utf8').replace(/^verify:/m, 'estimate: 200\nverify:'))
  assert.doesNotMatch(cli(d).stderr, /consider splitting/)
})

test('fullSuiteExamples in estimator.json classify the same as the estimator', () => {
  const { fullSuiteExamples } = JSON.parse(readFileSync(new URL('../../scripts/lib/estimator.json', import.meta.url), 'utf8'))
  assert.ok(fullSuiteExamples.length >= 7)
  for (const { command, full } of fullSuiteExamples) {
    const d = epic('README.md')
    setTask(d, 't-one', command)
    const r = cli(d)
    assert.equal(/runs the full suite/.test(r.stderr), full, `${command}: ${r.stderr}`)
  }
})
