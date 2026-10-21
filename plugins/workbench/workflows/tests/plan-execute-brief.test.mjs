// The project brief (what, how, why) and the task's value reach every agent
// prompt, and every role may use read-only or tree-local helper subagents.
import assert from 'node:assert/strict'
import { test } from 'node:test'
import { fileURLToPath } from 'node:url'
import { runWorkflow } from './harness.mjs'

const SCRIPT = fileURLToPath(new URL('../plan-execute.js', import.meta.url))

const BRIEF = { what: 'W', how: 'H', why: 'Y' }
const BRIEF_LINES = ['Project brief:', '- What: W', '- How: H', '- Why: Y']

const task = (id, extra = {}) => ({
  id,
  title: `task ${id}`,
  repo: 'api',
  worktree: `/wt/${id}`,
  requirement: `requirement for ${id}`,
  value: `V${id === 'T1' ? '' : id}`,
  files: [`src/${id}-a.py`, `src/${id}-b.py`, `tests/test_${id}.py`],
  verify: `pytest tests/test_${id}.py`,
  ...extra,
})

const idOf = (short) => short.replace('task-', '').replace(/^t(\d+)/, 'T$1')

const deliverable = (id) => ({
  taskId: id,
  complete: true,
  summary: 'did it',
  filesChanged: ['src/a.py'],
  branch: `b-${id}`,
  tests: { added: ['tests/test_a.py'], wroteTestFirst: true, red: { command: 'pytest', output: 'FAILED tests/test_a.py::test_x' } },
  verification: { command: 'pytest tests/test_a.py', passed: true, evidence: '3 passed' },
})
const okVerify = { head: 'abc123', clean: true, command: 'pytest', passed: true, evidence: '3 passed', debtMarkers: [] }
const okMerge = { merged: true, conflict: false, head: 'def456', verification: { command: 'x', passed: true, evidence: 'ok' } }
const finding = { severity: 'high', kind: 'wrong', file: 'src/a.py', summary: 'wrong', requirement: 'r', evidence: 'e' }

// Label-routed fake. forceFinding: first review of each task reports a finding.
// auditGap: first audit reports a gap on T1. handoff: first impl hands off.
function fakeAgent({ forceFinding = false, auditGap = false, handoff = false } = {}) {
  const reviews = new Map()
  let audits = 0
  let impls = 0
  return async (prompt, opts) => {
    const [, role, rest] = opts.label.split(':')
    const short = (rest || '').split(/[#+]/)[0]
    if (role === 'impl' || role === 'fix') {
      if (handoff && role === 'impl' && ++impls === 1) {
        return { ...deliverable(idOf(short)), complete: false, status: 'handoff', handoff: { doneSoFar: 'x', remaining: ['y'], nextStep: 'z', testState: 't', wipCommit: 'abc' } }
      }
      return deliverable(idOf(short))
    }
    if (role === 'verify') return okVerify
    if (role === 'merge') return okMerge
    if (role === 'review') {
      const n = (reviews.get(short) || 0) + 1
      reviews.set(short, n)
      return { clean: !(forceFinding && n === 1), findings: forceFinding && n === 1 ? [finding] : [], filesRead: ['src/a.py'] }
    }
    if (role === 'audit') {
      return auditGap && ++audits === 1
        ? { complete: false, missing: [{ item: 'retry path', taskId: 'T1', evidence: 'no retry' }] }
        : { complete: true, missing: [] }
    }
    throw new Error(`unexpected agent ${opts.label}`)
  }
}
const run = (args, agent) => runWorkflow(SCRIPT, { args, agent })
const ofRole = (r, role) => r.calls.filter((c) => c.opts.label.split(':')[1] === role)

const BRIEF_ERR = 'plan-execute: args.brief needs what, how and why'

test('a run without a brief throws before any agent is spent', async () => {
  const r = await run({ tasks: [task('T1')] }, fakeAgent())
  assert.equal(r.error && r.error.message, BRIEF_ERR)
  assert.equal(r.calls.length, 0)
})

test('a brief missing a field throws the same', async () => {
  for (const brief of [{ what: 'W', how: 'H' }, { what: 'W', how: 'H', why: '' }, { what: 'W', how: 5, why: 'Y' }, 'text']) {
    const r = await run({ brief, tasks: [task('T1')] }, fakeAgent())
    assert.equal(r.error && r.error.message, BRIEF_ERR)
    assert.equal(r.calls.length, 0)
  }
})

test('a task without a value throws naming the task', async () => {
  const r = await run({ brief: BRIEF, tasks: [task('T1'), task('T2', { value: undefined })] }, fakeAgent())
  assert.equal(r.error && r.error.message, 'plan-execute: task T2 needs a string value')
  assert.equal(r.calls.length, 0)
  const e = await run({ brief: BRIEF, tasks: [task('T1', { value: '' })] }, fakeAgent())
  assert.equal(e.error && e.error.message, 'plan-execute: task T1 needs a string value')
})

test('impl, review, fix, verify and audit prompts carry the brief; all but audit carry the value', async () => {
  const r = await run({ brief: BRIEF, tasks: [task('T1')] }, fakeAgent({ forceFinding: true }))
  assert.equal(r.error, undefined)
  for (const role of ['impl', 'review', 'fix', 'verify', 'audit']) {
    const calls = ofRole(r, role)
    assert.ok(calls.length > 0, `no ${role} call`)
    for (const c of calls) {
      for (const l of BRIEF_LINES) assert.ok(c.prompt.includes(l), `${role} prompt lacks: ${l}`)
      if (role === 'audit') {
        assert.ok(c.prompt.includes('  value: V'), 'audit lacks the value line')
        assert.ok(!c.prompt.includes('Value of this task:'))
      } else {
        assert.ok(c.prompt.includes('Value of this task: V'), `${role} prompt lacks the value`)
      }
    }
  }
})

test('the forward-merge prompt carries the brief and the dependent value', async () => {
  const r = await run({ brief: BRIEF, tasks: [task('T1'), task('T2', { dependsOn: ['T1'] })] }, fakeAgent({ auditGap: true }))
  assert.equal(r.error, undefined)
  const m = ofRole(r, 'merge')
  assert.equal(m.length, 1)
  for (const l of BRIEF_LINES) assert.ok(m[0].prompt.includes(l), `merge prompt lacks: ${l}`)
  assert.ok(m[0].prompt.includes('Value of this task: VT2'))
})

const HELPER = [
  'MAY spawn helper subagents',
  'Partition their work by file',
  'You remain accountable',
  'sonnet for lookups and mechanical work, opus only for hard reasoning',
  "cap each helper's report",
]

test('all six prompts carry the helper rules for their role', async () => {
  const r = await run(
    { brief: BRIEF, tasks: [task('T1'), task('T2', { dependsOn: ['T1'] })] },
    fakeAgent({ forceFinding: true, auditGap: true }),
  )
  assert.equal(r.error, undefined)
  for (const role of ['impl', 'fix', 'review', 'verify', 'merge', 'audit']) {
    const calls = ofRole(r, role)
    assert.ok(calls.length > 0, `no ${role} call`)
    for (const c of calls) {
      for (const s of HELPER) assert.ok(c.prompt.includes(s), `${role} prompt lacks: ${s}`)
      if (['review', 'verify', 'audit'].includes(role)) assert.ok(c.prompt.includes('never edit or commit'), `${role} lacks read-only`)
      if (role === 'merge') assert.ok(c.prompt.includes("Helpers work in this task's tree"))
      if (role === 'merge') assert.ok(!c.prompt.includes('never edit or commit'))
    }
  }
})

test('a continuation prompt inherits the brief and the value', async () => {
  const r = await run({ brief: BRIEF, tasks: [task('T1')] }, fakeAgent({ handoff: true }))
  const impls = ofRole(r, 'impl')
  assert.ok(impls.length >= 2)
  assert.ok(impls[1].prompt.includes('CONTINUATION'))
  for (const l of BRIEF_LINES) assert.ok(impls[1].prompt.includes(l))
  assert.ok(impls[1].prompt.includes('Value of this task: V'))
})
