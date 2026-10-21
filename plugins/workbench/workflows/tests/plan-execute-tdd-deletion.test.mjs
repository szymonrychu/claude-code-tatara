// The named TDD exception "deletion pinned by a retirement test" (remark 2.4):
// a pure deletion pinned by a retirement test must not cycle to round-cap.
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { test } from 'node:test'
import { fileURLToPath } from 'node:url'
import { runWorkflow } from './harness.mjs'

const SCRIPT = fileURLToPath(new URL('../plan-execute.js', import.meta.url))
const read = (rel) => readFileSync(fileURLToPath(new URL(rel, import.meta.url)), 'utf8')
const PHRASE = 'deletion pinned by a retirement test'
const BRIEF = { what: 'a plugin', how: 'workflows and hooks', why: 'reliable delivery' }

const task = (id) => ({
  id,
  title: `task ${id}`,
  repo: 'api',
  worktree: `/wt/${id}`,
  requirement: `requirement for ${id}`,
  value: 'worth it',
  files: [`src/${id}-a.py`, `src/${id}-b.py`, `tests/test_${id}.py`],
  review: 'full',
})

const okVerify = { head: 'abc123', clean: true, command: 'pytest', passed: true, evidence: '3 passed', debtMarkers: [], diffstat: { files: 2, addedNonTest: 0, addedTest: 10 }, acs: [{ id: 'AC1', met: true, how: 'ok' }] }
const NOTE = `${PHRASE}: legacy.py removed`
const TESTS = { added: ['tests/test_retired.py'], wroteTestFirst: false, note: NOTE }

function fakeAgent({ changed }) {
  return async (prompt, opts) => {
    const [, role, rest] = opts.label.split(':')
    const id = rest.split(/[#+]/)[0]
    if (role === 'impl' || role === 'fix') {
      return { taskId: id, complete: true, summary: 'did it', filesChanged: ['src/legacy.py'], branch: `b-${id}`, tests: TESTS, verification: { command: 'pytest', passed: true, evidence: '3 passed' } }
    }
    if (role === 'verify') return { ...okVerify, changed }
    if (role === 'review') return { clean: true, findings: [], filesRead: ['src/legacy.py'] }
    if (role === 'audit') return { complete: true, missing: [] }
    throw new Error(`unexpected agent ${opts.label}`)
  }
}
const run = (changed) => runWorkflow(SCRIPT, { args: { brief: BRIEF, tasks: [task('T1')] }, agent: fakeAgent({ changed }) })
const fixes = (r) => r.calls.filter((c) => c.opts.label.split(':')[1] === 'fix')

test('deletion pinned by retirement test is exempt', async () => {
  const r = await run([{ file: 'src/legacy.py', status: 'D' }, { file: 'tests/test_retired.py', status: 'A' }])
  assert.equal(fixes(r).length, 0)
  assert.equal(r.result.tasks[0].clean, true)
})

test('a modified test file also pins the deletion', async () => {
  const r = await run([{ file: 'src/legacy.py', status: 'D' }, { file: 'tests/test_x.py', status: 'M' }])
  assert.equal(fixes(r).length, 0)
})

test('deletion reason with additions is not exempt', async () => {
  const r = await run([{ file: 'src/legacy.py', status: 'D' }, { file: 'src/new.py', status: 'A' }, { file: 'tests/test_retired.py', status: 'A' }])
  assert.ok(fixes(r).length >= 1)
  assert.match(fixes(r)[0].prompt, /TDD skipped/)
})

test('a non-test modification, rename or missing change list keeps the finding', async () => {
  for (const changed of [
    [{ file: 'src/a.py', status: 'M' }, { file: 'tests/test_retired.py', status: 'A' }],
    [{ file: 'src/a.py', status: 'R' }, { file: 'tests/test_retired.py', status: 'A' }],
    undefined,
  ]) {
    const r = await run(changed)
    assert.ok(fixes(r).length >= 1, JSON.stringify(changed))
  }
})

test('no test file added or changed keeps the finding; a deleted test does not pin', async () => {
  for (const changed of [[{ file: 'src/legacy.py', status: 'D' }], [{ file: 'src/legacy.py', status: 'D' }, { file: 'tests/test_old.py', status: 'D' }]]) {
    const r = await run(changed)
    assert.ok(fixes(r).length >= 1, JSON.stringify(changed))
  }
})

test('the three texts name the exception with the same phrase', () => {
  assert.ok(read('../../rules/tdd.md').replace(/\s+/g, ' ').includes(PHRASE))
  assert.ok(read('../../agents/implementer.md').replace(/\s+/g, ' ').includes(PHRASE))
  assert.ok(read('../plan-execute.js').includes(PHRASE))
})
