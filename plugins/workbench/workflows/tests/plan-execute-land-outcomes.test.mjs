// Land outcomes: a task already contained in the epic, a rebase re-conflict, a legacy tree name.
import assert from 'node:assert/strict'
import { test } from 'node:test'
import { fileURLToPath } from 'node:url'
import { runWorkflow, TEST_PLUGIN_ROOT } from './harness.mjs'

const SCRIPT = fileURLToPath(new URL('../plan-execute.js', import.meta.url))
const BRIEF = { what: 'a plugin', how: 'workflows and hooks', why: 'reliable delivery' }
const MAIN = '/repo'
const EPIC = { name: 'epic-x', epic: 'epic-x', baseRef: 'epic-x', mainCheckout: MAIN }
const task = (id, extra = {}) => ({
  id, title: `task ${id}`, repo: 'api', worktree: `/wt/epic-x-${id}`, requirement: `requirement for ${id}`,
  value: 'worth it', short: id, files: [`src/${id}-a.py`], verify: `pytest tests/test_${id}.py`, review: 'full', ...extra,
})
const red = { command: 'pytest', output: 'FAILED tests/test_a.py::test_x' }
const deliverable = (id) => ({
  taskId: id, complete: true, summary: 'did it', filesChanged: ['src/a.py'], branch: `epic-x-${id}`,
  tests: { added: ['tests/test_a.py'], wroteTestFirst: true, red },
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
const run = (tasks, land) => runWorkflow(SCRIPT, { args: { brief: BRIEF, ...EPIC, tasks }, agent: agent(land) })
const landPrompt = (r) => r.calls.find((c) => c.opts.label.split(':')[1] === 'land').prompt
const result = (r, id) => r.result.tasks.find((t) => t.id === id)

test('land-outcomes-contained-counts-as-landed', async () => {
  const contained = () => ({ landed: false, contained: true, head: 'task-head', conflict: false, verification, notes: 'nothing to merge' })
  const r = await run([task('a'), task('b', { dependsOn: ['a'] })], contained)
  assert.equal(r.error, undefined)
  assert.notEqual(result(r, 'a').stopped, 'land-failed')
  assert.deepEqual(r.result.landed.map((x) => x.id), ['a', 'b'])
  assert.equal(r.result.landed[0].head, 'task-head')
  assert.ok(!r.result.escalated.some((e) => e.reason === 'land-failed'))
})

test('land-outcomes-contained-needs-passing-verify', async () => {
  const bad = () => ({ landed: false, contained: true, head: 'h', conflict: false, verification: { ...verification, passed: false }, notes: 'x' })
  const r = await run([task('a')], bad)
  assert.equal(result(r, 'a').stopped, 'land-failed')
})

test('land-outcomes-prompt-contained-head', async () => {
  const r = await run([task('a')], () => ({ landed: true, head: 'h', conflict: false, verification, notes: '' }))
  const p = landPrompt(r)
  assert.match(p, /contained/)
  assert.match(p, /task (tree|worktree) HEAD/i)
})

test('land-outcomes-prompt-reconflict-rules', async () => {
  const r = await run([task('a')], () => ({ landed: true, head: 'h', conflict: false, verification, notes: '' }))
  const p = landPrompt(r)
  assert.match(p, /drops its merge-of-epic-x commit/)
  assert.match(p, /both sides carry the same change/)
  assert.match(p, /exactly the dependency text already on epic-x/)
  assert.match(p, /rebase --abort/)
  assert.match(p, /every conflicting file/)
  assert.match(p, /once/)
})

test('land-outcomes-reconflict-escalation-names-files', async () => {
  const failed = () => ({ landed: false, conflict: true, head: '', verification: { ...verification, passed: false }, notes: 'conflict: src/a.py, src/b.py' })
  const r = await run([task('a')], failed)
  const e = r.result.escalated.find((x) => x.id === 'a')
  assert.equal(e.reason, 'land-failed')
  assert.match(e.land.notes, /src\/a\.py, src\/b\.py/)
  assert.equal(e.land.conflict, true)
})

test('land-outcomes-legacy-name', async () => {
  const r = await run([task('a', { worktree: '/wt/epic-x--a' })], () => ({ landed: true, head: 'h', conflict: false, verification, notes: '' }))
  assert.ok(landPrompt(r).includes('--name epic-x--a --base epic-x '), landPrompt(r))
  const c = await run([task('a', { worktree: '/wt/epic-x--a/api' })], () => ({ landed: true, head: 'h', conflict: false, verification, notes: '' }))
  assert.ok(landPrompt(c).includes('--name epic-x--a --base epic-x --repo api '), landPrompt(c))
})
