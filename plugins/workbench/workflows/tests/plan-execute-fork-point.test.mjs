// Fork point diffs: a landed task's diffs are taken from its recorded fork point.
import assert from 'node:assert/strict'
import { test } from 'node:test'
import { fileURLToPath } from 'node:url'
import { runWorkflow } from './harness.mjs'

const SCRIPT = fileURLToPath(new URL('../plan-execute.js', import.meta.url))
const BRIEF = { what: 'a plugin', how: 'workflows and hooks', why: 'reliable delivery' }
const EPIC = { name: 'epic-x', epic: 'epic-x', baseRef: 'epic-x', mainCheckout: '/repo' }
const task = (id, extra = {}) => ({
  id, title: `task ${id}`, repo: 'api', worktree: `/wt/epic-x-${id}`, requirement: `requirement for ${id}`,
  value: 'worth it', short: id, files: [`src/${id}-a.py`], verify: `pytest tests/test_${id}.py`, review: 'full', ...extra,
})
const red = { command: 'pytest', output: 'FAILED tests/test_a.py::test_x' }
const deliverable = (id, tests = { added: ['tests/test_a.py'], wroteTestFirst: true, red }) => ({
  taskId: id, complete: true, summary: 'did it', filesChanged: ['src/a.py'], branch: `epic-x-${id}`, tests,
  verification: { command: 'pytest tests/test_a.py', passed: true, evidence: '3 passed' },
})
const okVerify = { head: 'abc', clean: true, command: 'pytest', passed: true, evidence: '3 passed', debtMarkers: [] }
const verification = { command: 'pytest', passed: true, evidence: '3 passed' }
const agent = (land) => async (prompt, opts) => {
  const [, role, rest] = opts.label.split(':')
  const id = rest.split(/[#+]/)[0]
  if (role === 'impl' || role === 'fix') return deliverable(id)
  if (role === 'verify') return okVerify
  if (role === 'review') return { clean: true, findings: [], filesRead: ['src/a.py'] }
  if (role === 'false-finding') return { verdicts: [] }
  if (role === 'triage') return { repeated: [] }
  if (role === 'land') return land(id)
  if (role === 'audit') return { complete: true, missing: [] }
  throw new Error(`unexpected agent ${opts.label}`)
}
const landed = (extra = {}) => () => ({ landed: true, head: 'h', base: 'base1', conflict: false, verification, notes: '', ...extra })
const run = (tasks, land, args = {}) => runWorkflow(SCRIPT, { args: { brief: BRIEF, ...EPIC, ...args, tasks }, agent: agent(land) })
const prompts = (r, role, id) => r.calls.filter((c) => c.opts.label.split(':')[1] === role && c.opts.label.includes(`:${id}`)).map((c) => c.prompt)
const result = (r, id) => r.result.tasks.find((t) => t.id === id)

test('fork-point-arg-seeds-diff-bases', async () => {
  const r = await run([task('a', { forkPoint: 'abc1234' })], landed({ contained: true }))
  assert.equal(r.error, undefined)
  const review = prompts(r, 'review', 'a')[0]
  assert.ok(review.includes('git diff abc1234..HEAD'), review)
  assert.ok(!review.includes('git merge-base'), review)
  assert.ok(prompts(r, 'verify', 'a')[0].includes('--base abc1234 '))
})

test('fork-point-absent-keeps-merge-base', async () => {
  const r = await run([task('a')], landed({ landed: false, contained: true }))
  assert.ok(prompts(r, 'review', 'a')[0].includes('git diff $(git merge-base HEAD epic-x)..HEAD'))
  assert.ok(prompts(r, 'verify', 'a')[0].includes('--base epic-x '))
  assert.equal(result(r, 'a').forkPoint, undefined)
  assert.equal(r.result.landed[0].forkPoint, undefined)
})

test('fork-point-recorded-from-land-base', async () => {
  const r = await run([task('a')], landed())
  assert.deepEqual(r.result.landed, [{ id: 'a', head: 'h', forkPoint: 'base1' }])
  assert.equal(result(r, 'a').forkPoint, 'base1')
})

test('fork-point-contained-keeps-prior', async () => {
  const r = await run([task('a', { forkPoint: 'old1' })], landed({ landed: false, contained: true, base: 'new1' }))
  assert.equal(r.result.landed[0].forkPoint, 'old1')
  assert.equal(result(r, 'a').forkPoint, 'old1')
})

test('fork-point-land-schema-and-prompt-carry-base', async () => {
  const r = await run([task('a')], landed())
  const c = r.calls.find((x) => x.opts.label.split(':')[1] === 'land')
  assert.ok(c.opts.schema.properties.base)
  assert.match(c.prompt, /baseBefore/)
})

test('fork-point-tdd-recipe-uses-fork-point', async () => {
  const noRed = { added: ['tests/test_a.py'], wroteTestFirst: false }
  const a = async (p, o) => (o.label.split(':')[1] === 'impl' ? deliverable('a', noRed) : agent(landed({ contained: true }))(p, o))
  const r = await runWorkflow(SCRIPT, { args: { brief: BRIEF, ...EPIC, tasks: [task('a', { forkPoint: 'abc1234' })] }, agent: a })
  const all = r.calls.map((c) => c.prompt).join('\n')
  assert.ok(all.includes('git show abc1234:<path>'), 'recipe names the fork point')
})
