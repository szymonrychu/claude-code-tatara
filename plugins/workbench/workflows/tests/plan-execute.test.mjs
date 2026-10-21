// Control-flow tests for plan-execute.js. Every rule here was derived from a
// measured failure in docs/process-cost-audit.
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { test } from 'node:test'
import { fileURLToPath } from 'node:url'
import { runWorkflow } from './harness.mjs'

const SCRIPT = fileURLToPath(new URL('../plan-execute.js', import.meta.url))
const IMPLEMENTER_MD = readFileSync(fileURLToPath(new URL('../../agents/implementer.md', import.meta.url)), 'utf8')
const BRIEF = { what: 'a plugin', how: 'workflows and hooks', why: 'reliable delivery' }

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

const deliverable = (id) => ({
  taskId: id,
  complete: true,
  summary: 'did it',
  filesChanged: ['src/a.py'],
  branch: `b-${id}`,
  tests: { added: ['tests/test_a.py'], wroteTestFirst: true, red: { command: 'pytest', output: 'FAILED tests/test_a.py::test_x' } },
  verification: { command: 'pytest tests/test_a.py', passed: true, evidence: '3 passed' },
})

const finding = (summary, extra = {}) => ({
  severity: 'high',
  file: 'src/a.py',
  line: 10,
  summary,
  requirement: 'nothing is silently discarded by the notifier',
  ...extra,
})

const cleanAudit = { complete: true, missing: [] }
const okMerge = { merged: true, conflict: false, head: 'def456', verification: { command: 'x', passed: true, evidence: 'ok' } }
const okVerify = { head: 'abc123', clean: true, command: 'pytest', passed: true, evidence: '3 passed', debtMarkers: [], diffstat: { files: 2, addedNonTest: 40, addedTest: 10 }, acs: [{ id: 'AC1', met: true, how: 'ok' }] }

// Fake agent routed by label prefix. `review` may be a function of the round.
function fakeAgent({ review, audit = () => cleanAudit, verify } = {}) {
  let auditN = 0
  return async (prompt, opts) => {
    const c = { opts }
    const label = opts.label
    if (role(c) === 'impl' || role(c) === 'fix') return deliverable(label.split(':')[2])
    if (is(c, 'review:')) {
      const round = Number(label.split('#')[1])
      return { filesRead: ['src/a.py'], ...(review ? review(round, prompt) : { clean: true, findings: [] }) }
    }
    if (is(c, 'verify:')) return { ...okVerify, ...(verify ? verify(prompt, label) : {}) }
    if (is(c, 'merge:')) return okMerge
    if (is(c, 'scope-audit')) return audit(++auditN, prompt)
    throw new Error(`unexpected agent ${label}`)
  }
}

// Labels are <name>:<role>:<short>[#round][+continuation]. `is` takes the old
// role prefixes ('impl:', 'scope-audit', 'cont:') so assertions read as before;
// a continuation counts as 'cont:', never as its role.
const isCont = (c) => /\+\d+$/.test(c.opts.label)
const role = (c) => c.opts.label.split(':')[1]
const is = (c, p) => {
  if (p === 'cont:') return isCont(c)
  const want = p === 'scope-audit' ? 'audit' : p.replace(/:$/, '')
  return role(c) === want && !isCont(c)
}
const count = (calls, prefix) => calls.filter((c) => is(c, prefix)).length
const run = (args, agent) => runWorkflow(SCRIPT, { args: { brief: BRIEF, ...args }, agent })

// ---------------------------------------------------------------- rec 1: cap
test('review loop stops after 3 rounds and escalates the findings', async () => {
  let n = 0
  const r = await run(
    { tasks: [task('T1')] },
    // a different finding every round, so only the cap can stop it
    fakeAgent({ review: () => ({ clean: false, findings: [finding(`issue ${++n}`, { file: `src/f${n}.py` })] }) }),
  )
  assert.equal(r.error, undefined)
  assert.equal(count(r.calls, 'review:'), 3)
  assert.equal(count(r.calls, 'fix:'), 2)
  const t = r.result.tasks.find((x) => x.id === 'T1')
  assert.equal(t.stopped, 'round-cap')
  assert.equal(r.result.escalated.length, 1)
  assert.equal(r.result.escalated[0].id, 'T1')
  assert.equal(r.result.escalated[0].findings.length, 1)
  assert.equal(r.result.finished, false)
})

// ---------------------------------------------------------------- rec 2: blocked
test('a reviewer-reported external blocker exits the loop without a fixer', async () => {
  const r = await run(
    { tasks: [task('T1')] },
    fakeAgent({
      review: () => ({
        clean: false,
        findings: [],
        blocked: { reason: 'PR #45 needs a human merge', whoCanClear: 'user' },
      }),
    }),
  )
  assert.equal(count(r.calls, 'review:'), 1)
  assert.equal(count(r.calls, 'fix:'), 0)
  assert.equal(r.result.blocked.length, 1)
  assert.match(r.result.blocked[0].reason, /human merge/)
  assert.equal(r.result.finished, false)
})

test('the review schema offers a blocked channel', async () => {
  const r = await run({ tasks: [task('T1')] }, fakeAgent())
  const rev = r.calls.find((c) => is(c, 'review:'))
  assert.ok(rev.opts.schema.properties.blocked)
})

test('deferred work is judged by the reviewer, not auto-promoted to a finding', async () => {
  const r = await run({ tasks: [task('T1')] }, fakeAgent())
  const rev = r.calls.find((c) => is(c, 'review:'))
  assert.doesNotMatch(rev.prompt, /automatically a\s+finding/)
  // when to use blocked rides on the schema the review call carries
  assert.match(rev.opts.schema.properties.blocked.description, /external blocker.*instead of a finding/)
})

// ---------------------------------------------------------------- rec 3: no-progress
test('a reworded repeat of the same finding escalates instead of looping', async () => {
  const wordings = ['toast overwrites notices', 'notices are overwritten by toast', 'toast() clobbers text']
  const r = await run(
    { tasks: [task('T1')] },
    fakeAgent({ review: (round) => ({ clean: false, findings: [finding(wordings[round - 1])] }) }),
  )
  assert.equal(count(r.calls, 'review:'), 2)
  assert.equal(count(r.calls, 'fix:'), 1)
  assert.equal(r.result.tasks[0].stopped, 'no-progress')
  assert.equal(r.result.escalated.length, 1)
})

// ---------------------------------------------------------------- rec 4: models
test('every role runs on sonnet by default, including the scope audit', async () => {
  const r = await run(
    { tasks: [task('T1')] },
    fakeAgent({ review: (round) => (round === 1 ? { clean: false, findings: [finding('x')] } : { clean: true, findings: [] }) }),
  )
  for (const c of r.calls) assert.equal(c.opts.model, is(c, 'verify:') ? 'haiku' : 'sonnet', c.opts.label)
})

test('an opus-implemented task is still reviewed on sonnet, as is the audit', async () => {
  const r = await run(
    { tasks: [task('T1', { model: 'opus' })] },
    fakeAgent({ review: (round) => (round === 1 ? { clean: false, findings: [finding('x')] } : { clean: true, findings: [] }) }),
  )
  // the verifier only runs a script: haiku whatever tier implemented the task
  for (const c of r.calls) assert.equal(c.opts.model, is(c, 'verify:') ? 'haiku' : is(c, 'review:') || is(c, 'scope-audit') ? 'sonnet' : 'opus', c.opts.label)
  assert.equal(count(r.calls, 'review:'), 2)
})

test('only the implementer follows t.model; reviews and the audit are sonnet', async () => {
  const r = await run({ tasks: [task('T1', { model: 'opus' }), task('T2')] }, fakeAgent())
  const m = Object.fromEntries(r.calls.map((c) => [c.opts.label.replace(/^pe:/, ''), c.opts.model]))
  assert.equal(m['impl:task-t1'], 'opus')
  assert.equal(m['review:task-t1#1'], 'sonnet')
  assert.equal(m['impl:task-t2'], 'sonnet')
  assert.equal(m['review:task-t2#1'], 'sonnet')
  assert.equal(m['audit:scope'], 'sonnet')
})

// ---------------------------------------------------------------- run + agent names
test('labels are <name>:<role>:<short title>, prefixed by args.name', async () => {
  const r = await run(
    { name: 'auth', tasks: [task('T1', { title: 'Add token refresh to the API client' }), task('T2', { short: 'notifier' })] },
    fakeAgent(),
  )
  assert.equal(r.error, undefined)
  assert.deepEqual(r.calls.map((c) => c.opts.label).sort(), [
    'auth:audit:scope', 'auth:impl:add-token-refresh', 'auth:impl:notifier',
    'auth:review:add-token-refresh#1', 'auth:review:notifier#1',
    'auth:verify:add-token-refresh#1', 'auth:verify:notifier#1',
  ])
})

test('derived short titles are capped at 20 chars and made unique by task id', async () => {
  const r = await run(
    { tasks: [task('T1', { title: 'Reconcile notifications everywhere' }), task('T2', { title: 'Reconcile notifications everywhere else' })] },
    fakeAgent(),
  )
  const impls = r.calls.filter((c) => is(c, 'impl:')).map((c) => c.opts.label).sort()
  assert.deepEqual(impls, ['pe:impl:reconcile-notificati-t1', 'pe:impl:reconcile-notificati-t2'])
})

test('remediation and the second audit keep the short title with a round marker', async () => {
  const r = await run(
    { tasks: [task('T1')] },
    fakeAgent({ audit: (n) => (n === 1 ? { complete: false, missing: [{ item: 'gap', taskId: 'T1', evidence: 'e' }] } : cleanAudit) }),
  )
  assert.deepEqual(r.calls.map((c) => c.opts.label), [
    'pe:impl:task-t1', 'pe:verify:task-t1#1', 'pe:review:task-t1#1', 'pe:audit:scope',
    'pe:impl:task-t1-r1', 'pe:verify:task-t1-r1#1', 'pe:review:task-t1-r1#1', 'pe:audit:scope-r2',
  ])
})

test('a run name or short title that is not a label-safe slug fails before any agent', async () => {
  for (const args of [{ name: 'Auth Run', tasks: [task('T1')] }, { tasks: [task('T1', { short: 'a:b' })] }]) {
    const r = await run(args, fakeAgent())
    assert.match(String(r.error), /name|short/)
    assert.equal(r.calls.length, 0)
  }
})

// ---------------------------------------------------------------- rec 5: targeted tests
test('implementers run targeted tests, not the full suite', async () => {
  const r = await run({ tasks: [task('T1', { verify: 'pytest tests/test_a.py && mise run lint' })] }, fakeAgent())
  const impl = r.calls.find((c) => is(c, 'impl:')).prompt
  assert.match(impl, /pytest tests\/test_a\.py && mise run lint/)
  assert.match(impl, /not the full suite/i)
})

test('fixers run targeted tests too', async () => {
  const r = await run(
    { tasks: [task('T1', { verify: 'pytest tests/test_a.py' })] },
    fakeAgent({ review: (round) => (round === 1 ? { clean: false, findings: [finding('x')] } : { clean: true, findings: [] }) }),
  )
  const fix = r.calls.find((c) => is(c, 'fix:')).prompt
  assert.match(fix, /pytest tests\/test_a\.py/)
  assert.match(fix, /not the full suite/i)
  assert.doesNotMatch(fix, /no round budget/i)
})

// ---------------------------------------------------------------- rec 7: context pack
test('the discovery brief path reaches implementers and reviewers', async () => {
  const r = await run({ tasks: [task('T1')], contextPack: '/ws/docs/brief.md' }, fakeAgent())
  for (const p of ['impl:', 'review:']) {
    const c = r.calls.find((x) => is(x, p))
    assert.match(c.prompt, /\/ws\/docs\/brief\.md/, p)
  }
})

// ---------------------------------------------------------------- rec 8: auditor vocabulary
test('the audit prompt names the legal task ids', async () => {
  const r = await run({ tasks: [task('T1'), task('T2')] }, fakeAgent())
  const a = r.calls.find((c) => is(c, 'scope-audit')).prompt
  assert.match(a, /T1, T2/)
})

test('wave-level gaps go back to the orchestrator and are never dispatched', async () => {
  const r = await run(
    { tasks: [task('T1')] },
    fakeAgent({
      audit: (n) =>
        n === 1
          ? { complete: false, missing: [{ item: 'land PR #45', taskId: 'WAVE1', evidence: 'open' }], waveLevel: [{ item: 'baseline not on a shared ref', evidence: 'd3f8c0f' }] }
          : cleanAudit,
    }),
  )
  assert.equal(count(r.calls, 'impl:'), 1)
  assert.equal(r.result.waveLevel.length, 2)
  assert.equal(r.result.finished, false)
})

test('remediation ids never become legal audit ids', async () => {
  const r = await run(
    { tasks: [task('T1')] },
    fakeAgent({ audit: (n) => (n === 1 ? { complete: false, missing: [{ item: 'gap', taskId: 'T1', evidence: 'e' }] } : cleanAudit) }),
  )
  const audits = r.calls.filter((c) => is(c, 'scope-audit'))
  assert.equal(audits.length, 2)
  for (const a of audits) assert.match(a.prompt, /Legal taskId values: T1\n/)
  assert.equal(r.result.finished, true)
})

// ---------------------------------------------------------------- rec 9: audit budget
test('a run makes at most two scope audits, the second scoped to the gaps', async () => {
  const r = await run(
    { tasks: [task('T1')] },
    fakeAgent({ audit: () => ({ complete: false, missing: [{ item: 'still missing', taskId: 'T1', evidence: 'e' }] }) }),
  )
  assert.equal(count(r.calls, 'scope-audit'), 2)
  const second = r.calls.filter((c) => is(c, 'scope-audit'))[1].prompt
  assert.match(second, /still missing/)
  assert.match(second, /only/i)
  assert.equal(r.result.finished, false)
  assert.equal(r.result.escalated.some((e) => e.id === 'T1'), true)
})

// ---------------------------------------------------------------- rec 10: report caps
test('every agent prompt caps the report length', async () => {
  const r = await run(
    { tasks: [task('T1')] },
    fakeAgent({ review: (round) => (round === 1 ? { clean: false, findings: [finding('x')] } : { clean: true, findings: [] }) }),
  )
  // impl and fix carry the cap in agents/implementer.md, the agent they run as.
  assert.match(IMPLEMENTER_MD, /at most \d+ words/)
  for (const c of r.calls) {
    if (c.opts.agentType === 'workbench:implementer') continue
    assert.match(c.prompt, /at most \d+ words/, c.opts.label)
  }
})

// ---------------------------------------------------------------- rec 11: size gate
test('a small evidenced task skips review but is still audited', async () => {
  const r = await run({ tasks: [task('T1', { files: ['src/a.py', 'tests/test_a.py'], review: undefined, ac: [{ id: 'AC1', text: 'it works', evidence: { kind: 'test', ref: 'x' } }] })] }, fakeAgent())
  assert.equal(count(r.calls, 'review:'), 0)
  assert.equal(count(r.calls, 'scope-audit'), 1)
  assert.equal(r.result.finished, true)
})

test('a small task can force review', async () => {
  const r = await run({ tasks: [task('T1', { files: ['src/a.py'], review: true })] }, fakeAgent())
  assert.equal(count(r.calls, 'review:'), 1)
})

// ---------------------------------------------------------------- incident: files as a string
test('malformed args fail before any agent is spent', async () => {
  const r = await run({ tasks: [task('T1', { files: 'src/a.py' })] }, fakeAgent())
  assert.match(String(r.error), /files/)
  assert.equal(r.calls.length, 0)
})

// ---------------------------------------------------------------- tech debt (user's step 4)
test('review and audit both treat TODOs and deferred work as undelivered scope', async () => {
  const r = await run({ tasks: [task('T1')] }, fakeAgent())
  // the review's method, debt markers included, is the checklist the reviewer agent reads
  assert.equal(r.calls.find((x) => is(x, 'review:')).opts.agentType, 'workbench:reviewer')
  assert.match(readFileSync(fileURLToPath(new URL('../../agents/reviewer.md', import.meta.url)), 'utf8'), /review-checklist\.md/)
  assert.match(readFileSync(fileURLToPath(new URL('../../skills/start-review/references/review-checklist.md', import.meta.url)), 'utf8'), /^- Debt markers: /m)
  // the audit's method, TODOs included, is the scope-auditor agent's
  assert.match(readFileSync(fileURLToPath(new URL('../../agents/scope-auditor.md', import.meta.url)), 'utf8'), /a TODO/)
})

test('the implementer is told to commit, without a contradicting line', async () => {
  const r = await run({ tasks: [task('T1')] }, fakeAgent())
  const impl = r.calls.find((c) => is(c, 'impl:')).prompt
  assert.doesNotMatch(impl, /Do NOT commit/)
})

test('a clean verified run finishes with one agent per role', async () => {
  const r = await run({ tasks: [task('T1')] }, fakeAgent())
  assert.equal(r.error, undefined)
  assert.deepEqual(r.calls.map((c) => c.opts.label), ['pe:impl:task-t1', 'pe:verify:task-t1#1', 'pe:review:task-t1#1', 'pe:audit:scope'])
  assert.equal(r.result.finished, true)
})

// ---------------------------------------------------------------- worktrees
test('implementers work in the skill-created tree by path, never via EnterWorktree', async () => {
  const r = await run({ tasks: [task('T1')] }, fakeAgent())
  for (const c of r.calls) assert.doesNotMatch(c.prompt, /EnterWorktree with path/, c.opts.label)
  const impl = r.calls.find((c) => is(c, 'impl:'))
  assert.equal(impl.opts.agentType, 'workbench:implementer')
  assert.match(IMPLEMENTER_MD, /Do not call the built-in EnterWorktree/)
  assert.match(IMPLEMENTER_MD, /absolute path/)
  assert.match(impl.prompt, /\/wt\/T1/)
})

// ---------------------------------------------------------------- context ceiling + handoff
// peer-token-review (2026-09-27): implement agents ran a median 172 turns at 229k mean
// context, peaks to 966k; context above 300k was 4.5B of 19B tokens.
const handoff = (id, n) => ({
  taskId: id,
  complete: false,
  status: 'handoff',
  summary: `partial ${n}`,
  filesChanged: ['src/a.py'],
  branch: `b-${id}`,
  tests: { added: ['tests/test_a.py'], wroteTestFirst: true, red: { command: 'pytest', output: 'FAILED tests/test_a.py::test_x' } },
  verification: { command: 'pytest tests/test_a.py', passed: false, evidence: '1 failed, 2 passed' },
  handoff: {
    doneSoFar: `slice ${n} of the notifier`,
    remaining: ['the retry path', 'the error branch test'],
    nextStep: 'write the failing retry test',
    testState: '1 failed (expected: retry not built), 2 passed',
    wipCommit: `abc${n}`,
  },
})

// impl/fix agents hand off `hand` times before delivering; continuation labels end in +<n>
function handoffAgent(hand, { review } = {}) {
  let n = 0
  return async (prompt, opts) => {
    const c = { opts }
    const l = opts.label
    if (role(c) === 'impl' || role(c) === 'fix') {
      const id = l.split(':')[2].split(/[#+]/)[0]
      return ++n <= hand ? handoff(id, n) : deliverable(id)
    }
    if (is(c, 'review:')) return { filesRead: ['src/a.py'], ...(review ? review(Number(l.split('#')[1])) : { clean: true, findings: [] }) }
    if (is(c, 'verify:')) return okVerify
    if (is(c, 'merge:')) return okMerge
    if (is(c, 'scope-audit')) return cleanAudit
    throw new Error(`unexpected agent ${l}`)
  }
}

test('implement and fix prompts carry the context ceiling and the WIP handoff instruction', async () => {
  const r = await run(
    { tasks: [task('T1')] },
    fakeAgent({ review: (round) => (round === 1 ? { clean: false, findings: [finding('x')] } : { clean: true, findings: [] }) }),
  )
  // The ceiling is method: agents/implementer.md, which impl and fix run as.
  assert.match(IMPLEMENTER_MD, /300k/)
  assert.match(IMPLEMENTER_MD, /\b150 tool calls\b/)
  assert.match(IMPLEMENTER_MD, /WIP/)
  assert.match(IMPLEMENTER_MD, /status: "handoff"|status "handoff"|`handoff`/)
  for (const p of ['impl:', 'fix:']) {
    const c = r.calls.find((x) => is(x, p))
    assert.equal(c.opts.agentType, 'workbench:implementer', p)
    assert.ok(c.opts.schema.properties.handoff, p)
    assert.deepEqual(c.opts.schema.properties.status.enum, ['complete', 'incomplete', 'handoff'], p)
  }
})

test('the deliverable schema stays backward compatible: status and handoff are optional', async () => {
  const r = await run({ tasks: [task('T1')] }, fakeAgent())
  const s = r.calls.find((c) => is(c, 'impl:')).opts.schema
  assert.ok(!s.required.includes('status'))
  assert.ok(!s.required.includes('handoff'))
  for (const k of ['doneSoFar', 'remaining', 'nextStep', 'testState', 'wipCommit']) assert.ok(s.properties.handoff.required.includes(k), k)
})

test('a handoff dispatches a continuation with the requirement verbatim plus the handoff, then reviews the result', async () => {
  const r = await run({ tasks: [task('T1', { requirement: 'EXACT REQUIREMENT TEXT line one\nline two' })] }, handoffAgent(2))
  assert.equal(r.error, undefined)
  assert.deepEqual(r.calls.map((c) => c.opts.label), ['pe:impl:task-t1', 'pe:impl:task-t1+1', 'pe:impl:task-t1+2', 'pe:verify:task-t1#1', 'pe:review:task-t1#1', 'pe:audit:scope'])
  const c2 = r.calls.find((c) => c.opts.label === 'pe:impl:task-t1+2')
  assert.match(c2.prompt, /EXACT REQUIREMENT TEXT line one\nline two/)
  assert.match(c2.prompt, /slice 2 of the notifier/)
  assert.match(c2.prompt, /the retry path/)
  assert.match(c2.prompt, /write the failing retry test/)
  assert.match(c2.prompt, /1 failed \(expected: retry not built\)/)
  assert.match(c2.prompt, /abc2/)
  assert.equal(c2.opts.model, 'sonnet')
  assert.equal(c2.opts.schema.properties.handoff !== undefined, true)
  assert.equal(r.result.finished, true)
})

test('a small task that handed off still goes through the continuation before the size gate', async () => {
  const r = await run({ tasks: [task('T1', { files: ['src/a.py'], review: undefined, ac: [{ id: 'AC1', text: 'it works', evidence: { kind: 'test', ref: 'x' } }] })] }, handoffAgent(1))
  assert.deepEqual(r.calls.map((c) => c.opts.label), ['pe:impl:task-t1', 'pe:impl:task-t1+1', 'pe:verify:task-t1#1', 'pe:audit:scope'])
  assert.equal(r.result.finished, true)
})

test('a fixer handoff is continued with the findings and requirement, and the loop keeps reviewing', async () => {
  let fixSeen = false
  const agent = handoffAgent(0, { review: (round) => (round === 1 ? { clean: false, findings: [finding('toast overwrites')] } : { clean: true, findings: [] }) })
  const r = await run({ tasks: [task('T1')] }, async (p, o, calls) => {
    if (is({ opts: o }, 'fix:') && !fixSeen) { fixSeen = true; return handoff('T1', 1) }
    return agent(p, o, calls)
  })
  assert.deepEqual(r.calls.map((c) => c.opts.label), ['pe:impl:task-t1', 'pe:verify:task-t1#1', 'pe:review:task-t1#1', 'pe:fix:task-t1#1', 'pe:fix:task-t1#1+1', 'pe:verify:task-t1#2', 'pe:review:task-t1#2', 'pe:audit:scope'])
  const cont = r.calls.find((c) => c.opts.label === 'pe:fix:task-t1#1+1').prompt
  assert.match(cont, /toast overwrites/)
  assert.match(cont, /requirement for T1/)
  assert.match(cont, /abc1/)
  assert.equal(r.result.finished, true)
})

test('continuations are bounded; at the cap the task escalates with its handoff, never dropped', async () => {
  const r = await run({ tasks: [task('T1')] }, handoffAgent(99))
  assert.equal(r.error, undefined)
  assert.equal(count(r.calls, 'cont:'), 2)
  assert.equal(count(r.calls, 'review:'), 0)
  const e = r.result.escalated.find((x) => x.id === 'T1')
  assert.equal(e.reason, 'handoff-cap')
  assert.match(JSON.stringify(e.handoff), /the retry path/)
  assert.equal(r.result.tasks[0].stopped, 'handoff-cap')
  assert.equal(r.result.finished, false)
})

test('per-task prompts say to grep status.md and MEMORY.md by topic, never read them whole', async () => {
  const r = await run(
    { tasks: [task('T1')] },
    fakeAgent({ review: (round) => (round === 1 ? { clean: false, findings: [finding('x')] } : { clean: true, findings: [] }) }),
  )
  for (const p of ['impl:', 'fix:', 'review:']) {
    const c = r.calls.find((x) => is(x, p))
    assert.match(c.prompt, /grep/i, p)
    assert.match(c.prompt, /status\.md/, p)
    assert.match(c.prompt, /MEMORY\.md/, p)
    assert.match(c.prompt, /never read them whole/i, p)
  }
})

test('status "handoff" without a handoff object still continues, pointing the agent at git log', async () => {
  let first = true
  const agent = handoffAgent(0)
  const r = await run({ tasks: [task('T1')] }, async (p, o, calls) => {
    if (is({ opts: o }, 'impl:') && first) {
      first = false
      const d = handoff('T1', 1)
      delete d.handoff
      return d
    }
    return agent(p, o, calls)
  })
  assert.equal(r.error, undefined)
  assert.deepEqual(r.calls.map((c) => c.opts.label).slice(0, 2), ['pe:impl:task-t1', 'pe:impl:task-t1+1'])
  assert.match(r.calls[1].prompt, /not reported/)
  assert.doesNotMatch(r.calls[1].prompt, /undefined/)
  assert.equal(r.result.finished, true)
})

test('a handoff object with status missing and complete=false is treated as a handoff', async () => {
  let first = true
  const agent = handoffAgent(0)
  const r = await run({ tasks: [task('T1')] }, async (p, o, calls) => {
    if (is({ opts: o }, 'impl:') && first) {
      first = false
      const d = handoff('T1', 1)
      delete d.status
      return d
    }
    return agent(p, o, calls)
  })
  assert.deepEqual(r.calls.map((c) => c.opts.label).slice(0, 2), ['pe:impl:task-t1', 'pe:impl:task-t1+1'])
  assert.match(r.calls[1].prompt, /abc1/)
})
