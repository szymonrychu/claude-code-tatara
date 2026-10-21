// Forward-merge after remediation. Round-1 evidence: audit:scope-r2 found the
// remediation commits c57fd05 and bc528c8 only on their task branches, never in
// the trees of the tasks that depended on them, so a dependent's green verify
// was measured without the fix it was built on.
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { test } from 'node:test'
import { fileURLToPath } from 'node:url'
import { runWorkflow } from './harness.mjs'

const SCRIPT = fileURLToPath(new URL('../plan-execute.js', import.meta.url))
const BRIEF = { what: 'a plugin', how: 'workflows and hooks', why: 'reliable delivery' }

const task = (id, extra = {}) => ({
  id,
  title: `task ${id}`,
  repo: 'api',
  worktree: `/wt/${id}`,
  requirement: `requirement for ${id}`,
  value: 'worth it',
  files: [`src/${id}-a.py`, `src/${id}-b.py`, `tests/test_${id}.py`],
  verify: `pytest tests/test_${id}.py`,
  ...extra,
})

// short label task-t1-r1 -> T1-r1
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
const gapOnT1 = { complete: false, missing: [{ item: 'retry path', taskId: 'T1', evidence: 'src/T1-a.py has no retry' }] }

// verify(short, n) and merge(short) override per task; audits: first reports a gap on T1.
function fakeAgent({ verify, merge, firstAudit = gapOnT1 } = {}) {
  let audits = 0
  return async (prompt, opts) => {
    const [, role, rest] = opts.label.split(':')
    const short = rest.split(/[#+]/)[0]
    if (role === 'impl' || role === 'fix') return deliverable(idOf(short))
    if (role === 'verify') return verify ? verify(short, Number(rest.split('#')[1])) : okVerify
    if (role === 'review') return { clean: true, findings: [], filesRead: ['src/a.py'] }
    if (role === 'merge') return merge ? merge(short) : okMerge
    if (role === 'audit') return ++audits === 1 ? firstAudit : { complete: true, missing: [] }
    throw new Error(`unexpected agent ${opts.label}`)
  }
}
const run = (args, agent) => runWorkflow(SCRIPT, { args: { brief: BRIEF, ...args }, agent })
const ofRole = (r, role) => r.calls.filter((c) => c.opts.label.split(':')[1] === role)

const chain = (extra = []) => [task('T1'), task('T2', { dependsOn: ['T1'] }), task('T3', { dependsOn: ['T2'] }), ...extra]

test('a clean remediation is merged into its same-repo dependents, dependencies first', async () => {
  const r = await run({ tasks: chain() }, fakeAgent())
  assert.equal(r.error, undefined)
  const m = ofRole(r, 'merge')
  assert.deepEqual(m.map((c) => c.opts.label), ['pe:merge:task-t2', 'pe:merge:task-t3'])
  for (const c of m) {
    assert.equal(c.opts.phase, 'Merge')
    assert.equal(c.opts.model, 'sonnet')
    assert.deepEqual(c.opts.schema.required, ['merged', 'conflict', 'head', 'verification'])
    assert.equal(c.opts.schema.properties.merged.type, 'boolean')
    assert.equal(c.opts.schema.properties.conflict.type, 'boolean')
    assert.equal(c.opts.schema.properties.head.type, 'string')
    assert.deepEqual(c.opts.schema.properties.verification.required, ['command', 'passed', 'evidence'])
    assert.ok(c.prompt.includes('Do not resolve a conflict by discarding either side; report it'))
    assert.ok(c.prompt.includes('at most 150 words'))
  }
  assert.ok(m[0].prompt.includes('else echo "/wt/T2"; fi)') && m[0].prompt.includes('git merge --no-edit b-T1-r1'))
  assert.ok(m[0].prompt.includes('pytest tests/test_T2.py'))
  assert.ok(m[1].prompt.includes('else echo "/wt/T3"; fi)') && m[1].prompt.includes('git merge --no-edit b-T1-r1'))
  assert.ok(m[1].prompt.includes('pytest tests/test_T3.py'))
  // after the remediation, before the re-audit
  const idx = (label) => r.calls.findIndex((c) => c.opts.label === label)
  assert.ok(idx('pe:impl:task-t1-r1') < idx('pe:merge:task-t2'))
  assert.ok(idx('pe:merge:task-t3') < idx('pe:audit:scope-r2'))

  assert.deepEqual(r.result.forwardMerged, [
    { into: 'T2', from: 'T1', branch: 'b-T1-r1', head: 'def456' },
    { into: 'T3', from: 'T1', branch: 'b-T1-r1', head: 'def456' },
  ])
  const t2 = r.result.tasks.find((t) => t.id === 'T2')
  assert.deepEqual(t2.verification, { command: 'x', passed: true, evidence: 'ok', head: 'def456' })
  assert.equal(r.result.finished, true)
})

test('a dependent processed before its own dependent even when listed later', async () => {
  const tasks = [task('T1'), task('T3', { dependsOn: ['T2'] }), task('T2', { dependsOn: ['T1'] })]
  const r = await run({ tasks }, fakeAgent())
  assert.deepEqual(ofRole(r, 'merge').map((c) => c.opts.label), ['pe:merge:task-t2', 'pe:merge:task-t3'])
})

test('a conflicting merge escalates the dependent as forward-merge-failed', async () => {
  const conflict = { merged: false, conflict: true, head: 'aaa', verification: { command: 'x', passed: false, evidence: 'CONFLICT src/a.py' } }
  const r = await run({ tasks: chain() }, fakeAgent({ merge: (s) => (s === 'task-t3' ? conflict : okMerge) }))
  assert.equal(r.error, undefined)
  const e = r.result.escalated.find((x) => x.id === 'T3')
  assert.equal(e.reason, 'forward-merge-failed')
  assert.deepEqual(e.findings, [])
  assert.deepEqual(e.merge, conflict)
  assert.deepEqual(r.result.forwardMerged.map((x) => x.into), ['T2'])
  assert.equal(r.result.finished, false)
})

test('a merge that reports merged but fails verification also escalates', async () => {
  const red = { ...okMerge, verification: { command: 'x', passed: false, evidence: '1 failed' } }
  const r = await run({ tasks: chain() }, fakeAgent({ merge: (s) => (s === 'task-t2' ? red : okMerge) }))
  assert.equal(r.result.escalated.find((x) => x.id === 'T2').reason, 'forward-merge-failed')
  assert.equal(r.result.finished, false)
})

test('a merge agent returning nothing escalates with merge null', async () => {
  const r = await run({ tasks: chain() }, fakeAgent({ merge: () => null }))
  const e = r.result.escalated.find((x) => x.id === 'T2')
  assert.equal(e.reason, 'forward-merge-failed')
  assert.equal(e.merge, null)
})

test('a dependent in another repo is not merged into', async () => {
  const r = await run({ tasks: chain([task('T4', { repo: 'web', dependsOn: ['T1'] })]) }, fakeAgent())
  const labels = ofRole(r, 'merge').map((c) => c.opts.label)
  assert.ok(!labels.includes('pe:merge:task-t4'))
  assert.deepEqual(labels, ['pe:merge:task-t2', 'pe:merge:task-t3'])
})

test('an escalated dependent is skipped', async () => {
  // T3's verifier dies: verify-agent-died
  const r = await run({ tasks: chain() }, fakeAgent({ verify: (s) => (s === 'task-t3' ? null : okVerify) }))
  assert.equal(r.error, undefined)
  assert.deepEqual(ofRole(r, 'merge').map((c) => c.opts.label), ['pe:merge:task-t2'])
  assert.equal(r.result.escalated.find((x) => x.id === 'T3').reason, 'verify-agent-died')
})

test('the re-audit still runs after the forward merges', async () => {
  const r = await run({ tasks: chain() }, fakeAgent({ merge: () => null }))
  assert.deepEqual(ofRole(r, 'audit').map((c) => c.opts.label), ['pe:audit:scope', 'pe:audit:scope-r2'])
})

test('no merge when the remediation did not finish clean', async () => {
  const r = await run({ tasks: chain() }, fakeAgent({ verify: (s) => (s === 'task-t1-r1' ? null : okVerify) }))
  assert.equal(ofRole(r, 'merge').length, 0)
  assert.deepEqual(r.result.forwardMerged, [])
})

test('no remediation, no merge, and forwardMerged is empty', async () => {
  const r = await run({ tasks: chain() }, fakeAgent({ firstAudit: { complete: true, missing: [] } }))
  assert.equal(ofRole(r, 'merge').length, 0)
  assert.deepEqual(r.result.forwardMerged, [])
})

test('both audit prompts list the same-repo dependency pairs; the auditor checks their ancestry', async () => {
  const r = await run({ tasks: chain() }, fakeAgent())
  const line = 'Same-repo dependencies to check for ancestry (dependency -> dependent): T1 -> T2, T2 -> T3'
  const a = ofRole(r, 'audit')
  assert.equal(a.length, 2)
  for (const c of a) assert.ok(c.prompt.includes(line), `${c.opts.label} lacks the ancestry pairs`)
  const md = readFileSync(fileURLToPath(new URL('../../agents/scope-auditor.md', import.meta.url)), 'utf8').replace(/\s+/g, ' ')
  assert.ok(md.includes('`git merge-base --is-ancestor <dependency branch> HEAD` in the dependent\'s tree. A dependency commit absent from a dependent is a `waveLevel` entry.'))
})

test('the merge prompt installs missing dependencies before the command', async () => {
  const r = await run({ tasks: chain() }, fakeAgent())
  const p = ofRole(r, 'merge')[0].prompt
  assert.ok(p.includes('node_modules'))
  assert.ok(p.indexOf('node_modules') < p.indexOf('Run exactly this command'))
})
