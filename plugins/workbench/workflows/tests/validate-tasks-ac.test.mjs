// The ac[] task field: plan-execute shape errors, the one debt-marker list, the one
// test-file pattern, and the ac lint (workflows/ac-lint.mjs).
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { test } from 'node:test'
import { fileURLToPath } from 'node:url'
import { debtMarkers, lintAc, parkingMatches } from '../ac-lint.mjs'
import { runWorkflow } from './harness.mjs'

const SCRIPT = fileURLToPath(new URL('../plan-execute.js', import.meta.url))
const SRC = readFileSync(SCRIPT, 'utf8')
const BRIEF = { what: 'a plugin', how: 'workflows and hooks', why: 'reliable delivery' }

const task = (id, extra = {}) => ({
  id,
  title: `task ${id}`,
  repo: 'api',
  worktree: `/wt/${id}`,
  requirement: `requirement for ${id}`,
  value: 'worth it',
  files: [`src/${id}.py`],
  ...extra,
})
const ac = (id, extra = {}) => ({ id, text: `condition ${id}`, evidence: { kind: 'test', ref: 'tests/test_a.py::test_x' }, ...extra })
const STOP = 'stop-at-first-agent'
const run = (tasks) =>
  runWorkflow(SCRIPT, {
    args: { brief: BRIEF, tasks },
    agent: async () => {
      throw new Error(STOP)
    },
  })
const shapeError = async (acs) => {
  const r = await run([task('T1', { ac: acs })])
  assert.ok(r.error, 'expected a throw')
  assert.notEqual(r.error.message, STOP, 'must throw before any agent')
  assert.equal(r.calls.length, 0)
  return r.error.message
}

test('a task without ac reaches the first agent', async () => {
  const r = await run([task('T1')])
  assert.ok(r.calls.length > 0)
})

test('a well-formed ac reaches the first agent, judgement needs no ref', async () => {
  const r = await run([task('T1', { ac: [ac('AC1'), ac('AC2', { evidence: { kind: 'judgement' } })] })])
  assert.ok(r.calls.length > 0)
})

test('ac that is not an array throws naming the task', async () => {
  assert.match(await shapeError({ id: 'AC1' }), /task T1 .*ac.* array/)
})

test('an entry without id or text throws', async () => {
  assert.match(await shapeError([ac('AC1'), { text: 'x', evidence: { kind: 'test', ref: 'r' } }]), /task T1 .*non-empty `id`/)
  assert.match(await shapeError([ac('AC1', { text: '  ' })]), /task T1 AC AC1 .*non-empty `text`/)
})

test('a duplicate id throws naming it', async () => {
  assert.match(await shapeError([ac('AC1'), ac('AC1')]), /task T1 .*duplicate AC id AC1/)
})

test('an evidence kind outside the five throws', async () => {
  assert.match(await shapeError([ac('AC1', { evidence: { kind: 'vibes', ref: 'x' } })]), /task T1 AC AC1 .*evidence\.kind/)
  assert.match(await shapeError([ac('AC1', { evidence: undefined })]), /task T1 AC AC1 .*evidence\.kind/)
})

test('an empty ref throws for every kind but judgement', async () => {
  for (const kind of ['test', 'symbol', 'command', 'doc-section']) {
    assert.match(await shapeError([ac('AC1', { evidence: { kind, ref: ' ' } })]), /task T1 AC AC1 .*evidence\.ref/)
  }
})

test('DEBT_MARKERS is one line, parsed by debtMarkers(), and includes nice to have', () => {
  assert.equal(SRC.split('\n').filter((l) => /^const DEBT_MARKERS = '.*'$/.test(l)).length, 1)
  const list = debtMarkers()
  for (const m of ['TODO', 'FIXME', 'XXX', 'HACK', 'follow-up', 'for later', 'phase 2', 'nice to have', 'round N (any number)', 'xfail']) {
    assert.ok(list.includes(m), m)
  }
  assert.equal(list.length, new Set(list).size)
})

test('no other source file copies the marker words', () => {
  for (const f of ['../ac-lint.mjs', '../validate-tasks.mjs']) {
    assert.ok(!/left as an exercise/.test(readFileSync(fileURLToPath(new URL(f, import.meta.url)), 'utf8')), f)
  }
})

test('TEST_FILE_RE is one line and isTestFile keeps today\'s behaviour', () => {
  assert.equal(SRC.split('\n').filter((l) => /^const TEST_FILE_RE = \/.*\/$/.test(l)).length, 1)
  const re = new RegExp(/^const TEST_FILE_RE = \/(.*)\/$/m.exec(SRC)[1])
  for (const f of ['tests/a.py', 'src/test/b.js', 'a/tests/deep/c.txt', 'test_x.py', 'pkg/test_x.py', 'a.test.js', 'a.spec.ts', 'a_test.go', 'a_spec.rb']) {
    assert.ok(re.test(f), f)
  }
  for (const f of ['src/a.py', 'testing/a.py', 'test_x.js', 'contest.py', 'src/latest.js', 'mytests/a.py', 'a.tests.js']) {
    assert.ok(!re.test(f), f)
  }
  assert.match(SRC, /const isTestFile = \(f\) => TEST_FILE_RE\.test\(f\)/)
})

test('parkingMatches: uppercase code markers are case-sensitive', () => {
  assert.deepEqual(parkingMatches('add a TODO here'), ['TODO'])
  assert.deepEqual(parkingMatches('the todo phase and a hack for fixme'), [])
  assert.deepEqual(parkingMatches('FIXME and XXX and HACK'), ['FIXME', 'XXX', 'HACK'])
})

test('parkingMatches: phrases are case-insensitive, round N is any number', () => {
  assert.deepEqual(parkingMatches('Follow-Up work, Nice To Have'), ['follow-up', 'nice to have'])
  assert.deepEqual(parkingMatches('handle it in round 3'), ['round 3'])
  assert.deepEqual(parkingMatches('around the round table'), [])
})

test('parkingMatches ignores text inside backticks', () => {
  assert.deepEqual(parkingMatches('the `TODO` marker and `for later` words'), [])
  assert.deepEqual(parkingMatches('phase `todo` then for later'), ['for later'])
})

test('lintAc with require: missing or empty ac is a message', () => {
  const msgs = lintAc([task('T1'), task('T2', { ac: [] }), task('T3', { ac: [ac('A')] })], { require: true })
  assert.deepEqual(msgs, ['tasks: T1 has no acceptance conditions (ac)', 'tasks: T2 has no acceptance conditions (ac)'])
})

test('lintAc without require never demands ac', () => {
  assert.deepEqual(lintAc([task('T1'), task('T2', { ac: [] })], { require: false }), [])
  assert.deepEqual(lintAc([task('T1')]), [])
})

test('lintAc flags parking in requirement, AC text and notes, with or without require', () => {
  const t = task('T1', { requirement: 'do it, follow-up later', notes: 'phase 2 will finish', ac: [ac('A', { text: 'fix the FIXME' })] })
  const msgs = lintAc([t], { require: false })
  assert.deepEqual(msgs, ['tasks: T1 parks work: "follow-up"', 'tasks: T1 parks work: "FIXME"', 'tasks: T1 parks work: "phase 2"'])
})

test('lintAc ignores parking words in a task with no ac', () => {
  assert.deepEqual(lintAc([task('T1', { requirement: 'for later' })], { require: false }), [])
})
