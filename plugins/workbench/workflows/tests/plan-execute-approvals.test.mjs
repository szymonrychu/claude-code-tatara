// The approval ledger in plan-execute.js: an approved item is delivered in full or
// stopped by a named external blocker. An undelivered entry on an approved task is a
// finding that goes to the fixer, the audit checks every approved item by id, and
// the return reports each item's status.
import assert from 'node:assert/strict'
import { spawnSync } from 'node:child_process'
import { mkdtempSync, readFileSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { test } from 'node:test'
import { fileURLToPath } from 'node:url'
import { runWorkflow } from './harness.mjs'

const SCRIPT = fileURLToPath(new URL('../plan-execute.js', import.meta.url))
const BRIEF = { what: 'a plugin', how: 'workflows and hooks', why: 'reliable delivery' }
const TEXT_A = 'the parser reads every card'

const task = (id, extra = {}) => ({
  id,
  title: `task ${id}`,
  repo: 'api',
  worktree: `/wt/${id}`,
  requirement: `requirement for ${id}`,
  value: 'worth it',
  files: [`src/${id}-a.py`, `src/${id}-b.py`, `tests/test_${id}.py`],
  review: 'full', // the review loop under test; tier rules live in plan-execute-tier
  ...extra,
})
const small = (id) => task(id, { review: undefined, files: [`src/${id}.py`, `tests/test_${id}.py`] })
const LEDGER = [{ id: 'A', text: TEXT_A, tasks: ['T1'] }]

const deliverable = (id, extra = {}) => ({
  taskId: id,
  complete: true,
  summary: 'did it',
  filesChanged: ['src/a.py'],
  branch: `b-${id}`,
  tests: { added: ['tests/test_a.py'], wroteTestFirst: true, red: { command: 'pytest', output: 'FAILED tests/test_a.py::test_x' } },
  verification: { command: 'pytest tests/test_a.py', passed: true, evidence: '3 passed' },
  ...extra,
})

const okVerify = { head: 'abc123', clean: true, command: 'pytest', passed: true, evidence: '3 passed', debtMarkers: [], diffstat: { files: 2, addedNonTest: 40, addedTest: 10 } }
const cleanAudit = { complete: true, missing: [] }
const okMerge = { merged: true, conflict: false, head: 'def456', verification: { command: 'pytest', passed: true, evidence: '3 passed' } }

// Routed on the label's role. Every hook gets (rest-of-label, prompt) and returns
// the result, or undefined for the default.
function fakeAgent(h = {}) {
  return async (prompt, opts) => {
    const [, role, rest] = opts.label.split(':')
    const id = rest.split(/[#+]/)[0].replace(/^task-/, '').toUpperCase()
    const pick = (fn, dflt) => {
      const v = fn ? fn(rest, prompt) : undefined
      return v === undefined ? dflt : v
    }
    if (role === 'impl') return pick(h.impl, deliverable(id))
    if (role === 'fix') return pick(h.fix, deliverable(id))
    if (role === 'verify') return pick(h.verify, okVerify)
    if (role === 'review') return pick(h.review, { clean: true, findings: [], filesRead: ['src/a.py'] })
    if (role === 'merge') return pick(h.merge, okMerge)
    if (role === 'audit') return pick(h.audit, cleanAudit)
    throw new Error(`unexpected agent ${opts.label}`)
  }
}
const run = (args, agent) => runWorkflow(SCRIPT, { args: { brief: BRIEF, ...args }, agent })
const ofRole = (r, role) => r.calls.filter((c) => c.opts.label.split(':')[1] === role)
const byLabel = (r, l) => r.calls.find((c) => c.opts.label === l)

test('a ledger naming a task not in the run throws before any agent', async () => {
  const r = await run({ tasks: [task('T1')], approvals: [{ id: 'A', text: TEXT_A, tasks: ['T1', 'T9'] }] }, fakeAgent())
  assert.equal(r.error && r.error.message, 'plan-execute: approval A names task T9 which is not in this run')
  assert.equal(r.calls.length, 0)
})

test('a malformed ledger throws before any agent', async () => {
  for (const approvals of [
    { id: 'A' },
    'A',
    [null],
    [{ id: '', text: TEXT_A, tasks: ['T1'] }],
    [{ id: 'A', text: ' ', tasks: ['T1'] }],
    [{ id: 'A', tasks: ['T1'] }],
    [{ id: 'A', text: TEXT_A, tasks: [] }],
    [{ id: 'A', text: TEXT_A }],
    [{ id: 'A', text: TEXT_A, tasks: [1] }],
    [{ id: 'A', text: TEXT_A, tasks: 'T1' }],
  ]) {
    const r = await run({ tasks: [task('T1')], approvals }, fakeAgent())
    assert.equal(r.error && r.error.message, 'plan-execute: args.approvals must be an array of {id, text, tasks}', JSON.stringify(approvals))
    assert.equal(r.calls.length, 0)
  }
})

test('a duplicate approval id throws before any agent', async () => {
  const r = await run({ tasks: [task('T1')], approvals: [...LEDGER, { id: 'A', text: 'again', tasks: ['T1'] }] }, fakeAgent())
  assert.equal(r.error && r.error.message, 'plan-execute: duplicate approval id A')
  assert.equal(r.calls.length, 0)
})

const UNDELIVERED = [{ what: 'the parser', why: 'ran out of time' }]

test('an undelivered entry on an approved task goes to the fixer as a finding', async () => {
  const r = await run(
    { tasks: [task('T1')], approvals: LEDGER },
    fakeAgent({ impl: (rest) => deliverable('T1', { undelivered: UNDELIVERED }) }),
  )
  assert.equal(r.error, undefined)
  const fix = ofRole(r, 'fix')
  assert.equal(fix.length, 1)
  assert.equal(fix[0].opts.label, 'pe:fix:task-t1#1')
  assert.ok(fix[0].prompt.includes('Approved item A not delivered (undelivered): the parser (ran out of time)'))
  assert.ok(fix[0].prompt.includes('approved items are delivered in full; only a named external blocker (blocked with whoCanClear) is accepted'))
  assert.ok(fix[0].prompt.includes('evidence: undelivered: ran out of time'))
  assert.ok(fix[0].prompt.includes('(approved scope)'))
  assert.ok(ofRole(r, 'review')[0].prompt.includes('Approved item A not delivered'))
  assert.equal(r.result.approvals[0].status, 'delivered')
  assert.equal(r.result.finished, true)
})

test('an undelivered entry from a fixer on an approved task is a finding in the next round', async () => {
  let fixes = 0
  const r = await run(
    { tasks: [task('T1')], approvals: LEDGER },
    fakeAgent({
      verify: (rest) => (rest.endsWith('#1') ? { ...okVerify, passed: false, evidence: '1 failed' } : undefined),
      fix: () => deliverable('T1', fixes++ === 0 ? { undelivered: UNDELIVERED } : {}),
    }),
  )
  assert.equal(r.error, undefined)
  const fix = ofRole(r, 'fix')
  assert.equal(fix.length, 2)
  assert.ok(!fix[0].prompt.includes('Approved item A not delivered'))
  assert.ok(fix[1].prompt.includes('Approved item A not delivered (undelivered): the parser (ran out of time)'))
})

test('the impl and fix prompts of an approved task name the item and the rule', async () => {
  const r = await run(
    { tasks: [task('T1')], approvals: LEDGER },
    fakeAgent({ verify: (rest) => (rest.endsWith('#1') ? { ...okVerify, passed: false, evidence: '1 failed' } : undefined) }),
  )
  assert.equal(r.error, undefined)
  const rule = 'Approved means delivered in full. The only acceptable non-delivery is an external blocker no agent in this run can clear, named in blocked (reason, whoCanClear); never deferred, never "later".'
  for (const c of [byLabel(r, 'pe:impl:task-t1'), byLabel(r, 'pe:fix:task-t1#1')]) {
    assert.ok(c, 'dispatched')
    assert.ok(c.prompt.includes(`This task delivers approved item(s) A:\n- A: ${TEXT_A}\n${rule}`), c.opts.label)
    assert.ok(c.prompt.includes('never deferred'))
  }
})

test('several approvals on one task are each listed', async () => {
  const r = await run(
    { tasks: [task('T1')], approvals: [...LEDGER, { id: 'B', text: 'the writer', tasks: ['T1'] }] },
    fakeAgent(),
  )
  assert.ok(byLabel(r, 'pe:impl:task-t1').prompt.includes(`This task delivers approved item(s) A, B:\n- A: ${TEXT_A}\n- B: the writer\n`))
})

const BLOCKER = { reason: 'needs the prod credential', whoCanClear: 'the user' }

test('a deliverable naming an external blocker ends the task with no fixer', async () => {
  const r = await run({ tasks: [task('T1')], approvals: LEDGER }, fakeAgent({ impl: () => deliverable('T1', { blocked: BLOCKER }) }))
  assert.equal(r.error, undefined)
  assert.equal(ofRole(r, 'fix').length, 0)
  assert.equal(ofRole(r, 'review').length, 0)
  assert.deepEqual(r.result.blocked, [{ id: 'T1', ...BLOCKER, approvals: ['A'] }])
  assert.equal(r.result.tasks[0].stopped, 'blocked')
  assert.equal(r.result.approvals[0].status, 'blocked')
  assert.equal(r.result.finished, false)
})

test('a fixer naming an external blocker ends the loop with no further review or fix', async () => {
  const r = await run(
    { tasks: [task('T1')], approvals: LEDGER },
    fakeAgent({
      verify: (rest) => (rest.endsWith('#1') ? { ...okVerify, passed: false, evidence: '1 failed' } : undefined),
      fix: () => deliverable('T1', { blocked: BLOCKER }),
    }),
  )
  assert.equal(r.error, undefined)
  assert.equal(ofRole(r, 'fix').length, 1)
  assert.equal(ofRole(r, 'review').length, 1)
  assert.deepEqual(r.result.blocked, [{ id: 'T1', ...BLOCKER, approvals: ['A'] }])
  assert.equal(r.result.finished, false)
})

test('a blocked task with no approval returns approvals: []', async () => {
  const r = await run({ tasks: [task('T1')] }, fakeAgent({ impl: () => deliverable('T1', { blocked: BLOCKER }) }))
  assert.deepEqual(r.result.blocked, [{ id: 'T1', ...BLOCKER, approvals: [] }])
})

test('the audit prompt carries the ledger and the per-item instruction', async () => {
  const r = await run({ tasks: [task('T1'), task('T2')], approvals: [{ id: 'A', text: TEXT_A, tasks: ['T1', 'T2'] }] }, fakeAgent())
  const p = byLabel(r, 'pe:audit:scope').prompt
  assert.ok(p.includes(`=== APPROVED ITEMS (the ledger) ===\n- A (tasks T1, T2): ${TEXT_A}`))
  assert.ok(p.includes('For every approved item, report {id, landed, evidence} in approvals; landed is false when any part of it is missing in the trees.'))
})

test('the audit prompt has no ledger block without approvals', async () => {
  const r = await run({ tasks: [task('T1')] }, fakeAgent())
  assert.ok(!byLabel(r, 'pe:audit:scope').prompt.includes('APPROVED ITEMS'))
})

test('an approved item the audit finds not landed goes to remediation, then the re-check', async () => {
  const r = await run(
    { tasks: [task('T1')], approvals: LEDGER },
    fakeAgent({
      audit: (rest) =>
        rest === 'scope'
          ? { complete: false, missing: [], approvals: [{ id: 'A', landed: false, evidence: 'no parser' }] }
          : { complete: true, missing: [], approvals: [{ id: 'A', landed: true, evidence: 'src/parser.py:1' }] },
    }),
  )
  assert.equal(r.error, undefined)
  const rem = byLabel(r, 'pe:impl:task-t1-r1')
  assert.ok(rem, 'remediation dispatched')
  assert.ok(rem.prompt.includes('Approved item A not landed: no parser'))
  assert.ok(rem.prompt.includes(`This task delivers approved item(s) A:\n- A: ${TEXT_A}`))
  const re = byLabel(r, 'pe:audit:scope-r2').prompt
  assert.ok(re.includes('- [T1] Approved item A not landed: no parser'))
  assert.ok(re.includes(`=== APPROVED ITEMS (the ledger) ===\n- A (tasks T1): ${TEXT_A}`))
  assert.ok(re.includes('report {id, landed, evidence} in approvals'))
  assert.deepEqual(r.result.approvals, [{ id: 'A', text: TEXT_A, tasks: ['T1'], status: 'delivered' }])
  assert.equal(r.result.finished, true)
})

test('an approved item still not landed at the re-check is escalated', async () => {
  const r = await run(
    { tasks: [task('T1')], approvals: LEDGER },
    fakeAgent({ audit: () => ({ complete: false, missing: [], approvals: [{ id: 'A', landed: false, evidence: 'no parser' }] }) }),
  )
  assert.equal(r.error, undefined)
  assert.ok(r.result.escalated.some((e) => e.id === 'T1' && e.reason === 'audit-gap-persisted'))
  assert.equal(r.result.approvals[0].status, 'escalated')
  assert.equal(r.result.finished, false)
})

test('a not-landed entry already reported as missing is not doubled', async () => {
  const item = 'Approved item A not landed: no parser'
  const r = await run(
    { tasks: [task('T1')], approvals: LEDGER },
    fakeAgent({
      audit: (rest) =>
        rest === 'scope'
          ? { complete: false, missing: [{ item, evidence: 'no parser', taskId: 'T1' }], approvals: [{ id: 'A', landed: false, evidence: 'no parser' }] }
          : cleanAudit,
    }),
  )
  const p = byLabel(r, 'pe:impl:task-t1-r1').prompt
  assert.equal(p.split(item).length - 1, 1)
})

test('an audit approvals entry for an id not in the ledger is ignored', async () => {
  const r = await run(
    { tasks: [task('T1')], approvals: LEDGER },
    fakeAgent({ audit: () => ({ complete: true, missing: [], approvals: [{ id: 'Z', landed: false, evidence: 'x' }] }) }),
  )
  assert.equal(byLabel(r, 'pe:impl:task-t1-r1'), undefined)
  assert.equal(r.result.finished, true)
})

test('a task escalated at the round cap makes its approval escalated', async () => {
  const r = await run(
    { tasks: [task('T1')], approvals: LEDGER },
    fakeAgent({
      review: (rest, prompt) => {
        const n = /Round (\d+) of/.exec(prompt)[1]
        return {
          clean: false,
          filesRead: ['src/a.py'],
          findings: [{ severity: 'high', kind: 'wrong', file: 'src/a.py', summary: 's', requirement: `requirement number ${n}`, evidence: 'e' }],
        }
      },
    }),
  )
  assert.equal(r.error, undefined)
  assert.ok(r.result.escalated.some((e) => e.id === 'T1' && e.reason === 'round-cap'))
  assert.equal(r.result.approvals[0].status, 'escalated')
  assert.equal(r.result.finished, false)
})

test('a task whose implementer returned nothing makes its approval escalated (impl-agent-died)', async () => {
  const r = await run({ tasks: [task('T1')], approvals: LEDGER }, fakeAgent({ impl: () => null }))
  assert.equal(r.error, undefined)
  assert.equal(r.result.approvals[0].status, 'escalated')
  assert.equal(r.result.finished, false)
})

test('the AUDIT schema offers approvals and the DELIVERABLE schema offers blocked', async () => {
  const r = await run({ tasks: [task('T1')], approvals: LEDGER }, fakeAgent())
  assert.deepEqual(byLabel(r, 'pe:audit:scope').opts.schema.properties.approvals, {
    type: 'array',
    items: {
      type: 'object',
      required: ['id', 'landed', 'evidence'],
      properties: { id: { type: 'string' }, landed: { type: 'boolean' }, evidence: { type: 'string' } },
    },
  })
  assert.deepEqual(byLabel(r, 'pe:impl:task-t1').opts.schema.properties.blocked, {
    type: 'object',
    required: ['reason', 'whoCanClear'],
    properties: { reason: { type: 'string' }, whoCanClear: { type: 'string' } },
    description: 'set ONLY for an external blocker no agent in this run can clear (a credential, a permission, a human merge); it ends the loop and escalates',
  })
})

test('without args.approvals the return has approvals: [] and finished as before', async () => {
  const r = await run({ tasks: [task('T1')] }, fakeAgent({ impl: () => deliverable('T1') }))
  assert.equal(r.error, undefined)
  assert.deepEqual(r.result.approvals, [])
  assert.equal(ofRole(r, 'fix').length, 0)
  assert.equal(r.result.finished, true)
})

// --- validate-tasks passes the ledger to plan-execute's own validation ----------
const CLI = fileURLToPath(new URL('../validate-tasks.mjs', import.meta.url))
const dir = mkdtempSync(join(tmpdir(), 'pe-approvals-'))
const write = (name, content) => {
  const p = join(dir, name)
  writeFileSync(p, JSON.stringify(content))
  return p
}
const cliTask = (id) => ({ id, title: `task ${id}`, repo: 'api', requirement: `r ${id}`, value: 'v', files: [`src/${id}.py`] })
const ledgerEntry = (extra = {}) => ({ id: 'A', text: 'x', decisions: ['D1'], tasks: ['T1'], status: 'approved', ...extra })
const cli = (ledger) =>
  spawnSync(process.execPath, [CLI, write('t.json', [cliTask('T1'), cliTask('T2')]), '--approvals', write('a.json', ledger)], { encoding: 'utf8' })

test('validate-tasks runs plan-execute\'s ledger validation with --approvals', () => {
  const unknown = cli([ledgerEntry({ tasks: ['T1', 'T9'] })])
  assert.equal(unknown.status, 1)
  assert.match(unknown.stderr, /plan-execute: approval A names task T9 which is not in this run/)
  const dup = cli([ledgerEntry(), ledgerEntry()])
  assert.equal(dup.status, 1)
  assert.match(dup.stderr, /plan-execute: duplicate approval id A/)
  const ok = cli([ledgerEntry(), ledgerEntry({ id: 'B', tasks: ['T1', 'T2'] })])
  assert.equal(ok.status, 0, ok.stderr)
  assert.match(ok.stdout, /ok: 2 task\(s\), approvals checked/)
})

// --- the scope auditor reads the ledger -----------------------------------------
test('the scope auditor reads the approval ledger right after extracting the item list', () => {
  const md = readFileSync(fileURLToPath(new URL('../../agents/scope-auditor.md', import.meta.url)), 'utf8')
  const step = 'Read the approval ledger when one is given (an approvals JSON path, or the === APPROVED ITEMS === block in your prompt): every approved item is an item in your list, and an approved item with no evidence in the files is reported by its id.'
  const flat = md.replace(/\s+/g, ' ')
  assert.ok(flat.includes(step), 'ledger step missing')
  const i1 = flat.indexOf('1. **Extract the item list.**')
  const iStep = flat.indexOf(step)
  const i3 = flat.indexOf('**Verify each item against the files')
  assert.ok(i1 !== -1 && i1 < iStep && iStep < i3, 'ledger step must follow step 1')
  assert.ok(flat.slice(i1, iStep).includes(' 2. '), 'ledger step is step 2')
  assert.match(md, /^---\nname: scope-auditor\n/)
  assert.match(md, /\ntools: \[Read, Grep, Glob, Bash\]\nmodel: sonnet\n---\n/)
})

// --- an item spanning tasks: the other task's share is not this task's undelivered ---
const SHARED = [{ id: 'A1', text: TEXT_A, tasks: ['T1', 'T2'] }]

test('the approval block names the other tasks and says "your share"', async () => {
  const r = await run({ tasks: [small('T1'), small('T2')], approvals: SHARED }, fakeAgent())
  const p = ofRole(r, 'impl').find((c) => c.opts.label.includes('t1')).prompt
  assert.ok(p.includes('Your share of it is your requirement below; the rest is delivered by tasks T2. Do not list their parts in `undelivered`.'))
})

test('an undelivered entry naming another task of the run is misattributed, not a finding', async () => {
  const r = await run(
    { tasks: [small('T1'), small('T2')], approvals: SHARED },
    fakeAgent({ impl: (rest) => (rest.includes('t1') ? deliverable('T1', { undelivered: [{ what: 'T2 install.sh (owned by T2)', why: 'belongs to T2' }] }) : undefined) }),
  )
  assert.equal(r.error, undefined)
  assert.equal(ofRole(r, 'fix').length, 0)
  assert.ok(ofRole(r, 'impl').some((c) => c.opts.label.includes('t2')))
  const t1 = r.result.tasks.find((t) => t.id === 'T1')
  assert.equal(t1.clean, true)
  assert.equal(r.result.misattributed.length, 1)
  assert.equal(r.result.misattributed[0].taskId, 'T1')
  assert.equal(r.result.misattributed[0].ownerTaskId, 'T2')
  assert.equal(r.result.undelivered.length, 0)
})

test('reviewer and audit prompts do not list a misattributed entry as undelivered scope', async () => {
  const r = await run(
    { tasks: [small('T1'), small('T2')], approvals: SHARED },
    fakeAgent({ impl: (rest) => (rest.includes('t1') ? deliverable('T1', { undelivered: [{ what: 'T2 install.sh (owned by T2)', why: 'belongs to T2' }] }) : undefined) }),
  )
  assert.equal(r.error, undefined)
  for (const c of [...ofRole(r, 'review'), ...ofRole(r, 'audit')]) {
    assert.ok(!c.prompt.includes('T2 install.sh'), c.opts.label)
  }
})

test('an undelivered entry whose path another task owns is misattributed', async () => {
  const r = await run(
    { tasks: [small('T1'), small('T2')], approvals: SHARED },
    fakeAgent({ impl: (rest) => (rest.includes('t1') ? deliverable('T1', { undelivered: [{ what: 'edit src/T2.py', why: 'x' }] }) : undefined) }),
  )
  assert.equal(r.result.misattributed.length, 1)
  assert.equal(r.result.misattributed[0].ownerTaskId, 'T2')
})

test('an undelivered entry naming a shared part another task owns is misattributed', async () => {
  const r = await run(
    { tasks: [small('T1'), task('T2', { review: undefined, files: ['src/x.py'], owns: ['lib/shared_helper'] })], approvals: SHARED },
    fakeAgent({ impl: (rest) => (rest.includes('t1') ? deliverable('T1', { undelivered: [{ what: 'build lib/shared_helper', why: 'x' }] }) : undefined) }),
  )
  assert.equal(r.result.misattributed.length, 1)
  assert.equal(r.result.misattributed[0].ownerTaskId, 'T2')
  assert.equal(ofRole(r, 'fix').length, 0)
})

test('an undelivered entry whose where field is a file another task lists is misattributed', async () => {
  const r = await run(
    { tasks: [small('T1'), task('T2', { review: undefined, files: ['pkg/other_module.py'] })], approvals: SHARED },
    fakeAgent({ impl: (rest) => (rest.includes('t1') ? deliverable('T1', { undelivered: [{ what: 'wire the hook', where: 'pkg/other_module.py', why: 'x' }] }) : undefined) }),
  )
  assert.equal(r.result.misattributed.length, 1)
  assert.equal(r.result.misattributed[0].ownerTaskId, 'T2')
  assert.equal(ofRole(r, 'fix').length, 0)
})

test('an undelivered entry naming no other task still yields the approved-item finding', async () => {
  const r = await run(
    { tasks: [small('T1'), small('T2')], approvals: SHARED },
    fakeAgent({ impl: (rest) => (rest.includes('t1') ? deliverable('T1', { undelivered: UNDELIVERED }) : undefined) }),
  )
  assert.equal(ofRole(r, 'fix').length, 1)
  assert.ok(ofRole(r, 'fix')[0].prompt.includes('Approved item A1 not delivered'))
  assert.equal((r.result.misattributed || []).length, 0)
})

test('a gap naming a file the reporting task also lists is its own finding, not misattributed', async () => {
  const r = await run(
    { tasks: [task('T1', { review: undefined, files: ['SKILL.md', 'a.py'] }), task('T2', { review: undefined, files: ['SKILL.md'], dependsOn: ['T1'] })], approvals: SHARED },
    fakeAgent({ impl: (rest) => (rest.includes('t1') ? deliverable('T1', { undelivered: [{ what: 'section in SKILL.md', where: 'SKILL.md', why: 'x' }] }) : undefined) }),
  )
  assert.equal(r.error, undefined)
  assert.equal((r.result.misattributed || []).length, 0)
  assert.equal(ofRole(r, 'fix').length, 1)
})

test('a short file path does not match inside a longer path of another task', async () => {
  const r = await run(
    { tasks: [small('T1'), task('T2', { review: undefined, files: ['a.py'] })], approvals: SHARED },
    fakeAgent({ impl: (rest) => (rest.includes('t1') ? deliverable('T1', { undelivered: [{ what: 'finish data.py', why: 'x' }] }) : undefined) }),
  )
  assert.equal((r.result.misattributed || []).length, 0)
  assert.equal(ofRole(r, 'fix').length, 1)
})

test('a reviewed task: the review prompt does not carry a misattributed entry as undelivered', async () => {
  const r = await run(
    { tasks: [task('T1'), small('T2')], approvals: SHARED },
    fakeAgent({ impl: (rest) => (rest.includes('t1') ? deliverable('T1', { undelivered: [{ what: 'T2 install.sh (owned by T2)', why: 'belongs to T2' }] }) : undefined) }),
  )
  assert.equal(r.error, undefined)
  const reviews = ofRole(r, 'review').filter((c) => c.opts.label.includes('t1'))
  assert.ok(reviews.length > 0, 'a review call must happen for the reviewed task')
  for (const c of reviews) assert.ok(!c.prompt.includes('T2 install.sh'), c.opts.label)
})
