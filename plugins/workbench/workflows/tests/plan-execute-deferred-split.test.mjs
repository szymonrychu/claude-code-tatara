// `deferred` is split: `undelivered` (scope of this task not delivered) is a high
// `missing` finding on any task, approved or not; `discovered` (a gap outside the
// task's files) is never a finding and rides to the run return for ticket.py apply-run.
import assert from 'node:assert/strict'
import { test } from 'node:test'
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { runWorkflow } from './harness.mjs'

const SCRIPT = fileURLToPath(new URL('../plan-execute.js', import.meta.url))
const IMPLEMENTER_MD = readFileSync(fileURLToPath(new URL('../../agents/implementer.md', import.meta.url)), 'utf8')
const BRIEF = { what: 'a plugin', how: 'workflows and hooks', why: 'reliable delivery' }
const task = (id, extra = {}) => ({
  id, title: `task ${id}`, repo: 'api', worktree: `/wt/${id}`, requirement: `requirement for ${id}`, value: 'worth it',
  files: [`src/${id}-a.py`, `src/${id}-b.py`, `tests/test_${id}.py`], review: 'full', ...extra,
})
const deliverable = (id, extra = {}) => ({
  taskId: id, complete: true, summary: 'did it', filesChanged: ['src/a.py'], branch: `b-${id}`,
  tests: { added: ['tests/test_a.py'], wroteTestFirst: true, red: { command: 'pytest', output: 'FAILED x' } },
  verification: { command: 'pytest', passed: true, evidence: '3 passed' },
  undelivered: [], discovered: [],
  ...extra,
})
const okVerify = { head: 'abc', clean: true, command: 'pytest', passed: true, evidence: '3 passed', debtMarkers: [], diffstat: { files: 2, addedNonTest: 40, addedTest: 10 } }
function fakeAgent(h = {}) {
  return async (prompt, opts) => {
    const [, role, rest] = opts.label.split(':')
    const id = rest.split(/[#+]/)[0].replace(/^task-/, '').toUpperCase()
    const pick = (fn, d) => { const v = fn ? fn(rest, prompt) : undefined; return v === undefined ? d : v }
    if (role === 'impl') return pick(h.impl, deliverable(id))
    if (role === 'fix') return pick(h.fix, deliverable(id))
    if (role === 'verify') return okVerify
    if (role === 'review') return { clean: true, findings: [], filesRead: ['src/a.py'] }
    if (role === 'audit') return { complete: true, missing: [] }
    throw new Error(`unexpected agent ${opts.label}`)
  }
}
const run = (args, agent) => runWorkflow(SCRIPT, { args: { brief: BRIEF, ...args }, agent })
const ofRole = (r, role) => r.calls.filter((c) => c.opts.label.split(':')[1] === role)
const UND = [{ what: 'the parser', why: 'ran out of time' }]
const DISC = [{ what: 'fix the cache key', why: 'collides', where: 'src/other.py' }]

test('the deliverable schema requires undelivered and discovered, and has no deferred', async () => {
  const r = await run({ tasks: [task('T1')] }, fakeAgent())
  const s = ofRole(r, 'impl')[0].opts.schema
  assert.ok(s.required.includes('undelivered') && s.required.includes('discovered'))
  assert.equal(s.properties.deferred, undefined)
  for (const k of ['undelivered', 'discovered']) assert.equal(s.properties[k].type, 'array')
  assert.deepEqual(s.properties.discovered.items.required, ['what', 'why'])
})

test('undelivered on a task with no approval is a high missing finding', async () => {
  const r = await run({ tasks: [task('T1')] }, fakeAgent({ impl: () => deliverable('T1', { undelivered: UND }) }))
  assert.equal(r.error, undefined)
  const fix = ofRole(r, 'fix')
  assert.equal(fix.length, 1)
  assert.ok(fix[0].prompt.includes('the parser (ran out of time)'))
  assert.ok(fix[0].prompt.includes('undelivered'))
  assert.ok(!fix[0].prompt.includes('Approved item'))
})

test('discovered is never a finding, and the return carries it with the task id', async () => {
  const r = await run({ tasks: [task('T1')] }, fakeAgent({ impl: () => deliverable('T1', { discovered: DISC }) }))
  assert.equal(r.error, undefined)
  assert.equal(ofRole(r, 'fix').length, 0)
  assert.deepEqual(r.result.discovered, [{ taskId: 'T1', ...DISC[0] }])
  assert.equal(r.result.finished, true)
})

test('a deferred field from an old agent is treated as undelivered', async () => {
  const old = () => {
    const d = deliverable('T1')
    delete d.undelivered
    d.deferred = UND
    return d
  }
  const r = await run({ tasks: [task('T1')] }, fakeAgent({ impl: old }))
  assert.equal(ofRole(r, 'fix').length, 1)
  assert.ok(ofRole(r, 'fix')[0].prompt.includes('the parser (ran out of time)'))
})

test('impl and fix prompts explain both fields and that parking wording is a finding', async () => {
  const r = await run({ tasks: [task('T1')] }, fakeAgent({ impl: () => deliverable('T1', { undelivered: UND }) }))
  // The fields are explained in agents/implementer.md, which impl and fix run as.
  for (const c of [ofRole(r, 'impl')[0], ofRole(r, 'fix')[0]]) {
    assert.equal(c.opts.agentType, 'workbench:implementer', c.opts.label)
    assert.ok(!c.prompt.includes('name it in `deferred`'))
  }
  assert.match(IMPLEMENTER_MD, /`undelivered`/)
  assert.match(IMPLEMENTER_MD, /`discovered`/)
  assert.match(IMPLEMENTER_MD, /parking wording/)
  assert.match(IMPLEMENTER_MD, /fixed now|fix it now/)
  assert.ok(!IMPLEMENTER_MD.includes('name it in `deferred`'))
})

// SKILL.md plus the reference files its blocks moved to (references first, so a section heading
// resolves to its full text rather than the pointer left in SKILL.md).
const readSkillWithReferences = (skillUrl) => {
  const refs = ['phases-1-3.md', 'phase-4-execute.md', 'phases-5-7.md', 'non-negotiables.md']
  return [...refs.map((n) => readFileSync(fileURLToPath(new URL(`references/${n}`, skillUrl.href.replace(/SKILL\.md$/, ''))), 'utf8')), readFileSync(fileURLToPath(skillUrl), 'utf8')].join('\n')
}

test('SKILL.md Scope section names acceptance condition, undelivered and the ledger strike; no `deferred` anywhere', () => {
  const md = readSkillWithReferences(new URL('../../skills/start-development/SKILL.md', import.meta.url))
  const scope = md.split('## Scope is not negotiable')[1].split(/\n## /)[0]
  for (const w of ['acceptance condition', 'undelivered', 'strikes the ledger item']) assert.ok(scope.includes(w), w)
  assert.ok(!/deferred/i.test(md))
})
