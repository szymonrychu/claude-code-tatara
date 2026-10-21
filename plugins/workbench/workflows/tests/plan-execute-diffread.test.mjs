// Reviewer read gate via one diff read (design D22): a review that reports
// diffRead=true with diffLines>0 counts every changed file as read.
import assert from 'node:assert/strict'
import { test } from 'node:test'
import { fileURLToPath } from 'node:url'
import { runWorkflow } from './harness.mjs'

const SCRIPT = fileURLToPath(new URL('../plan-execute.js', import.meta.url))
const BRIEF = { what: 'a plugin', how: 'workflows and hooks', why: 'reliable delivery' }
const task = (id) => ({ id, title: `task ${id}`, repo: 'api', worktree: `/wt/${id}`, requirement: `req ${id}`, value: 'worth it', files: ['src/a.py', 'src/b.py'] })
const okVerify = { head: 'abc123', clean: true, command: 'pytest', passed: true, evidence: '3 passed', debtMarkers: [] }

function fakeAgent(review) {
  return async (prompt, opts) => {
    const [, role, rest] = opts.label.split(':')
    if (role === 'impl' || role === 'fix') {
      return {
        taskId: rest.split(/[#+]/)[0], complete: true, summary: 'did it', filesChanged: ['src/a.py', 'src/b.py', 'tests/test_a.py'], branch: 'b',
        tests: { added: ['tests/test_a.py'], wroteTestFirst: true, red: { command: 'pytest', output: 'FAILED' } },
        verification: { command: 'pytest', passed: true, evidence: '3 passed' },
      }
    }
    if (role === 'review') return { clean: true, findings: [], filesRead: [], ...review(opts.label) }
    if (role === 'verify') return okVerify
    if (role === 'audit') return { complete: true, missing: [] }
    throw new Error(`unexpected agent ${opts.label}`)
  }
}
const run = (review) => runWorkflow(SCRIPT, { args: { brief: BRIEF, tasks: [task('T1')] }, agent: fakeAgent(review) })
const reviews = (r) => r.calls.filter((c) => c.opts.label.split(':')[1] === 'review')

test('the review schema offers diffRead and diffLines', async () => {
  const r = await run(() => ({ diffRead: true, diffLines: 5 }))
  const p = reviews(r)[0].opts.schema.properties
  assert.equal(p.diffRead.type, 'boolean')
  assert.equal(p.diffLines.type, 'integer')
})

test('the prompt makes one merge-base diff of the non-test changed files the first step', async () => {
  const r = await run(() => ({ diffRead: true, diffLines: 5 }))
  assert.match(reviews(r)[0].prompt, /git diff \$\(git merge-base HEAD main\)\.\.HEAD -- src\/a\.py src\/b\.py\n/)
  assert.doesNotMatch(reviews(r)[0].prompt, /tests\/test_a\.py\n.*git diff/)
})

test('diffRead with lines passes the gate without filesRead', async () => {
  const r = await run(() => ({ diffRead: true, diffLines: 40 }))
  assert.equal(reviews(r).length, 1)
  assert.equal(r.result.finished, true)
})

test('no diffRead and a missed file triggers the reread', async () => {
  const r = await run((l) => (l.endsWith('#1') ? { filesRead: ['src/a.py'] } : { filesRead: ['src/a.py', 'src/b.py'] }))
  assert.deepEqual(reviews(r).map((c) => c.opts.label), ['pe:review:task-t1#1', 'pe:review:task-t1#1-reread'])
  assert.match(reviews(r)[1].prompt, /- src\/b\.py/)
})

test('diffLines 0 does not count as a read', async () => {
  const r = await run(() => ({ diffRead: true, diffLines: 0 }))
  assert.equal(reviews(r).length, 2)
  assert.equal(r.result.tasks[0].stopped, 'review-shallow')
})

test('diffRead false with filesRead covering everything still passes', async () => {
  const r = await run(() => ({ diffRead: false, filesRead: ['src/a.py', 'src/b.py'] }))
  assert.equal(reviews(r).length, 1)
})
