// AC evidence map (flow-speed D2): the implementer and fixer prompts carry the task's acceptance
// conditions, their result may return acEvidence, the verifier passes it on with --ac-evidence, and
// an AC the script matched by substring goes to the auditor as open.
// Measured: 58 of 104 fix rounds carried a ref-missing finding for a renamed test.
import assert from 'node:assert/strict'
import { test } from 'node:test'
import { fileURLToPath } from 'node:url'
import { runWorkflow } from './harness.mjs'

const SCRIPT = fileURLToPath(new URL('../plan-execute.js', import.meta.url))
const BRIEF = { what: 'a plugin', how: 'workflows and hooks', why: 'reliable delivery' }
const AC = [
  { id: 'A1', text: 'renamed tests resolve', evidence: { kind: 'test', ref: 'tests/test_a.py::test_old' } },
  { id: 'A2', text: 'docs say so', evidence: { kind: 'doc-section', ref: 'README.md#Usage' } },
]
const ACE = { A1: 'tests/test_a.py::test_new' }
const task = (id, extra = {}) => ({
  id,
  title: `task ${id}`,
  repo: 'api',
  worktree: `/wt/${id}`,
  requirement: `requirement for ${id}`,
  value: 'worth it',
  short: id,
  files: [`src/${id}.py`],
  review: 'full',
  ...extra,
})
const deliverable = (id, extra = {}) => ({
  taskId: id,
  complete: true,
  summary: 'did it',
  filesChanged: [`src/${id}.py`],
  branch: `b-${id}`,
  tests: { added: [`tests/test_${id}.py`], wroteTestFirst: true, red: { command: 'pytest', output: 'FAILED tests/test_x.py::test_x' } },
  verification: { command: 'mise run test', passed: true, evidence: '3 passed' },
  ...extra,
})
const okVerify = { head: 'abc1234', clean: true, command: 'pytest', passed: true, evidence: '3 passed', debtMarkers: [] }

async function run(tasks, b = {}) {
  const fn = async (prompt, opts) => {
    const role = opts.label.split(':')[1]
    const id = opts.label.split(':')[2].split(/[#+]/)[0]
    if (role === 'impl' || role === 'fix') return b.impl ? b.impl(id, role) : deliverable(id, { acEvidence: ACE })
    if (role === 'verify') return b.verify ? b.verify(id, opts.label) : okVerify
    if (role === 'review') return { clean: true, findings: [], filesRead: [`src/${id}.py`] }
    if (role === 'land') return { landed: true, head: `land-${id}`, conflict: false, verification: { command: 'x', passed: true, evidence: 'verify: pass' }, notes: '' }
    if (role === 'audit') return { complete: true, missing: [] }
    throw new Error(`unexpected agent ${opts.label}`)
  }
  return runWorkflow(SCRIPT, { args: { brief: BRIEF, tasks }, agent: fn })
}
const ofRole = (r, role) => r.calls.filter((c) => c.opts.label.split(':')[1] === role)

test('impl-and-fix-prompts-carry-the-ac-list', async () => {
  const r = await run([task('a', { ac: AC })])
  assert.equal(r.error, undefined)
  const p = ofRole(r, 'impl')[0].prompt
  assert.ok(p.includes('Acceptance conditions (prove each; return acEvidence):'), p)
  assert.ok(p.includes('A1: renamed tests resolve [test: tests/test_a.py::test_old]'), p)
  assert.ok(p.includes('A2: docs say so [doc-section: README.md#Usage]'), p)
  const none = await run([task('b')])
  assert.ok(!ofRole(none, 'impl')[0].prompt.includes('Acceptance conditions (prove each'))
})

test('fix-prompt-carries-acceptance-conditions', async () => {
  let reviews = 0
  const fn = async (prompt, opts) => {
    const role = opts.label.split(':')[1]
    if (role === 'impl' || role === 'fix') return deliverable('a')
    if (role === 'verify') return okVerify
    if (role === 'review') {
      reviews++
      const f = { severity: 'high', kind: 'missing', file: 'src/a.py', summary: 'gap', requirement: 'r' }
      return { clean: reviews > 1, findings: reviews > 1 ? [] : [f], filesRead: ['src/a.py'] }
    }
    if (role === 'land') return { landed: true, head: 'land-a', conflict: false, verification: { command: 'x', passed: true, evidence: 'verify: pass' }, notes: '' }
    return { complete: true, missing: [] }
  }
  const r = await runWorkflow(SCRIPT, { args: { brief: BRIEF, tasks: [task('a', { ac: AC })] }, agent: fn })
  const fixes = ofRole(r, 'fix')
  assert.ok(fixes.length >= 1)
  assert.ok(fixes[0].prompt.includes('A1: renamed tests resolve [test: tests/test_a.py::test_old]'), fixes[0].prompt)
})

test('verify-passes-ac-evidence-file', async () => {
  const r = await run([task('a', { ac: AC })])
  const p = ofRole(r, 'verify')[0].prompt
  assert.ok(p.includes('--ac-evidence "$ACE"'), p)
  assert.ok(p.includes('$ACE') && p.includes(JSON.stringify(ACE)), p)
  assert.ok(p.includes('--acs "$ACS"'), p)
  // No evidence returned: no flag.
  const bare = await run([task('b', { ac: AC })], { impl: (id) => deliverable(id) })
  assert.ok(!ofRole(bare, 'verify')[0].prompt.includes('--ac-evidence'))
})

test('substring-match-is-open-for-audit', async () => {
  const acs = [
    { id: 'A1', met: true, how: 'ref passed', matchedBy: 'substring', resolvedRef: 'tests/test_a.py::test_new' },
    { id: 'A2', met: true, how: 'heading found', plausible: 'yes' },
  ]
  const r = await run([task('a', { ac: AC })], { verify: () => ({ ...okVerify, acs }) })
  assert.equal(r.error, undefined)
  const res = (r.result && r.result.tasks ? r.result.tasks : r.tasks || []).find((x) => x.id === 'a')
  const audit = JSON.stringify(r)
  assert.ok(res ? res.acsForAudit.includes('A1') && !res.acsForAudit.includes('A2') : audit.includes('"acsForAudit":["A1"]'), audit.slice(0, 500))
})
