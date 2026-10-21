// validate-tasks.mjs --epic: overlapIgnore from workbench.py config reaches the run-level overlap rule (D3).
import assert from 'node:assert/strict'
import { test } from 'node:test'
import { cli, epic } from './overlap-epic-fixture.mjs'

test('two tasks sharing only a doc file pass the epic lint', () => {
  const r = cli(epic('README.md'))
  assert.doesNotMatch(r.stderr, /both list/, r.stderr)
})

test('a shared non-doc file still fails the epic lint', () => {
  const r = cli(epic('src/shared.py'))
  assert.equal(r.status, 1, r.stderr)
  assert.match(r.stderr, /both list src\/shared\.py/)
})

test('a repo overlapIgnore entry reaches the lint', () => {
  const r = cli(epic('src/shared.py', JSON.stringify({ overlapIgnore: ['src/shared.py'] })))
  assert.doesNotMatch(r.stderr, /both list/, r.stderr)
})

test('a failing workbench config call is reported', () => {
  const r = cli(epic('README.md', '{ not json'))
  assert.equal(r.status, 1, r.stderr)
  assert.match(r.stderr, /workbench config for api/)
})
