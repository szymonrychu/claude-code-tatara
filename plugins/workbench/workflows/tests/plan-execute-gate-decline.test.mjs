// A debt-marker or parking gate finding that repeats after the fixer declined it with
// evidence (file:line in its summary or a declined entry) gets a second opinion from
// the Haiku triage agent running triage.py parking. No parking lines back: the finding
// is dropped and the loop goes on. A flag, a failure or no evidence: gate-repeat as before.
import assert from 'node:assert/strict'
import { test } from 'node:test'
import { fileURLToPath } from 'node:url'
import { runWorkflow } from './harness.mjs'

const SCRIPT = fileURLToPath(new URL('../plan-execute.js', import.meta.url))
const BRIEF = { what: 'a plugin', how: 'workflows and hooks', why: 'reliable delivery' }
const task = { id: 'T1', title: 't', repo: 'api', worktree: '/wt/T1', requirement: 'req', value: 'v', files: ['SKILL.md'], review: 'full' }
const deliverable = (extra = {}) => ({
  taskId: 'T1',
  complete: true,
  summary: 'did it',
  filesChanged: ['SKILL.md'],
  branch: 'b-T1',
  tests: { added: ['t'], wroteTestFirst: true, red: { command: 'pytest', output: 'FAILED t' } },
  verification: { command: 'pytest', passed: true, evidence: '3 passed' },
  ...extra,
})
const okVerify = { head: 'abc123', clean: true, command: 'pytest', passed: true, evidence: '3 passed', debtMarkers: [] }
const debt = { debtMarkers: [{ file: 'SKILL.md', line: 7, marker: 'later' }] }
const parked = { parking: [{ file: 'SKILL.md', line: 7, text: 'later is banned', reason: 'defers' }] }

function fakeAgent({ gate, fixImpl, triage }) {
  let verifies = 0
  return async (prompt, opts) => {
    const role = opts.label.split(':')[1]
    if (role === 'impl') return deliverable()
    if (role === 'fix') return deliverable(fixImpl)
    if (role === 'review') return { clean: true, findings: [], filesRead: ['SKILL.md'] }
    if (role === 'verify') {
      verifies++
      return { ...okVerify, ...(verifies <= 2 ? gate : {}) }
    }
    if (role === 'triage') return triage(prompt, opts)
    if (role === 'audit') return { complete: true, missing: [] }
    throw new Error(`unexpected agent ${opts.label}`)
  }
}
const run = (agent) => runWorkflow(SCRIPT, { args: { brief: BRIEF, tasks: [task] }, agent })
const triages = (r) => r.calls.filter((c) => c.opts.label.split(':')[1] === 'triage')
const declinedFix = { summary: 'declined: SKILL.md:7 quotes the forbidden word, it documents the rule' }

for (const [name, gate] of [['debt-marker', debt], ['parking', parked]]) {
  test(`a repeated ${name} finding the fixer declined with evidence is dropped when the classifier sees no parking`, async () => {
    const r = await run(fakeAgent({ gate, fixImpl: declinedFix, triage: () => ({ lines: [], reason: null }) }))
    assert.equal(triages(r).length, 1)
    const p = triages(r)[0].prompt
    assert.match(p, /\/scripts\/triage\.py'? parking/)
    assert.match(p, /SKILL\.md/)
    const t = r.result.tasks[0]
    assert.notEqual(t.stopped, 'gate-repeat')
    assert.equal(t.clean, true)
  })

  test(`a repeated ${name} finding still stops gate-repeat when the classifier flags it`, async () => {
    const flag = () => ({ lines: [{ file: 'SKILL.md', line: 7, text: 'x', reason: 'defers' }], reason: null })
    const r = await run(fakeAgent({ gate, fixImpl: declinedFix, triage: flag }))
    assert.equal(triages(r).length, 1)
    assert.equal(r.result.tasks[0].stopped, 'gate-repeat')
  })

  test(`a repeated ${name} finding still stops gate-repeat when the classifier fails`, async () => {
    const r = await run(fakeAgent({ gate, fixImpl: declinedFix, triage: () => ({ lines: null, reason: 'claude timed out' }) }))
    assert.equal(r.result.tasks[0].stopped, 'gate-repeat')
    const r2 = await run(fakeAgent({ gate, fixImpl: declinedFix, triage: () => { throw new Error('boom') } }))
    assert.equal(r2.result.tasks[0].stopped, 'gate-repeat')
  })
}

test('a repeat without decline evidence never asks the classifier', async () => {
  const r = await run(fakeAgent({ gate: debt, fixImpl: { summary: 'tried again' }, triage: () => ({ lines: [], reason: null }) }))
  assert.equal(triages(r).length, 0)
  assert.equal(r.result.tasks[0].stopped, 'gate-repeat')
})

test('a declined entry naming file:line counts as decline evidence', async () => {
  const r = await run(
    fakeAgent({ gate: debt, fixImpl: { declined: [{ what: 'SKILL.md:7', why: 'it documents the rule' }] }, triage: () => ({ lines: [], reason: null }) }),
  )
  assert.equal(triages(r).length, 1)
  assert.equal(r.result.tasks[0].clean, true)
})

test('a gate the classifier cleared stays cleared when reviewer findings keep the loop going', async () => {
  let verifies = 0
  let reviews = 0
  const rf = (n) => ({ severity: 'high', kind: 'wrong', file: `f${n}.js`, summary: `bug ${n}`, requirement: `requirement number ${n} words`, evidence: 'e' })
  const agent = async (prompt, opts) => {
    const role = opts.label.split(':')[1]
    if (role === 'impl') return deliverable()
    if (role === 'fix') return deliverable(declinedFix)
    if (role === 'review') {
      reviews++
      return reviews <= 2 ? { clean: false, findings: [rf(reviews)], filesRead: ['SKILL.md'] } : { clean: true, findings: [], filesRead: ['SKILL.md'] }
    }
    if (role === 'verify') {
      verifies++
      return { ...okVerify, ...(verifies <= 4 ? debt : {}) }
    }
    if (role === 'triage') return /triage\.py'? parking/.test(prompt) ? { lines: [], reason: null } : { repeated: [] }
    if (role === 'audit') return { complete: true, missing: [] }
    throw new Error(`unexpected agent ${opts.label}`)
  }
  const r = await run(agent)
  const t = r.result.tasks[0]
  assert.notEqual(t.stopped, 'round-cap')
  assert.equal(t.clean, true)
})
