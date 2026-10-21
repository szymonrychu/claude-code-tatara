// Gate-only fix rounds (design D18): a round whose findings all come from the
// deterministic gates runs fixer, verifier and gates only once the last LLM review
// was clean; the reviewer comes back only, and scoped, for non-test files the fix
// touched outside every finding's file. A gate finding seen in two consecutive
// rounds escalates at once (gate-repeat), and reviewer repeats are judged by one
// Haiku triage agent running triage.py equivalence, with findingKey as fallback.
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { test } from 'node:test'
import { fileURLToPath } from 'node:url'
import { runWorkflow } from './harness.mjs'

const SCRIPT = fileURLToPath(new URL('../plan-execute.js', import.meta.url))
const BRIEF = { what: 'a plugin', how: 'workflows and hooks', why: 'reliable delivery' }
const GATES = ['verify-failed', 'dirty-tree', 'debt-marker', 'parking', 'ac-unmet', 'no-red-evidence', 'tdd-skipped', 'approved-item', 'undelivered', 'tests-changed', 'review-shallow']

const task = (id, extra = {}) => ({
  id,
  title: `task ${id}`,
  repo: 'api',
  worktree: `/wt/${id}`,
  requirement: `requirement for ${id}`,
  value: 'worth it',
  files: [`src/${id}-a.py`, `tests/test_${id}.py`],
  review: 'full',
  ...extra,
})

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

const okVerify = { head: 'abc123', clean: true, command: 'pytest', passed: true, evidence: '3 passed', debtMarkers: [] }
const debt = (file = 'src/a.py') => ({ debtMarkers: [{ file, line: 3, marker: 'TODO' }] })
const finding = (summary, extra = {}) => ({ severity: 'high', file: 'src/a.py', line: 1, summary, requirement: 'the notifier keeps every notice', ...extra })

// review(round, prompt), verify(n, prompt), triage(n, prompt), impl(role, n): partial results by call number.
function fakeAgent({ review, verify, triage, impl } = {}) {
  const n = { review: 0, verify: 0, triage: 0, fix: 0, impl: 0 }
  return async (prompt, opts) => {
    const role = opts.label.split(':')[1]
    if (role in n) n[role]++
    if (role === 'impl' || role === 'fix') return deliverable('T1', impl ? impl(role, n[role]) : {})
    if (role === 'review') {
      const round = Number(/#(\d+)/.exec(opts.label)[1])
      return { clean: true, findings: [], filesRead: ['src/a.py'], ...(review ? review(round, prompt) : {}) }
    }
    if (role === 'verify') return { ...okVerify, ...(verify ? verify(n.verify, prompt) : {}) }
    if (role === 'triage') {
      if (!triage) throw new Error('unexpected triage')
      return triage(n.triage, prompt)
    }
    if (role === 'audit') return { complete: true, missing: [] }
    throw new Error(`unexpected agent ${opts.label}`)
  }
}
const run = (agent, t = task('T1'), args = {}) => runWorkflow(SCRIPT, { args: { brief: BRIEF, tasks: [t], ...args }, agent })
const ofRole = (r, role) => r.calls.filter((c) => c.opts.label.split(':')[1] === role)

// ---------------------------------------------------------------- gate tags
test('the closed gate set is defined once in plan-execute.js', () => {
  const src = readFileSync(SCRIPT, 'utf8')
  assert.match(src, /const GATES = \[\.\.\.MECHANICAL_GATES, \.\.\.WORK_GATES, 'review-shallow'\]/)
})

test('every finding created in code carries its gate tag', async () => {
  const ledger = [{ id: 'A', text: 'approved thing', tasks: ['T1'] }]
  const r = await run(
    fakeAgent({
      impl: () => ({ tests: { added: [], wroteTestFirst: false }, deferred: [{ what: 'half', why: 'hard' }] }),
      verify: () => ({
        passed: false,
        clean: false,
        evidence: '1 failed',
        ...debt(),
        parking: [{ file: 'src/a.py', line: 4, text: 'for later' }],
        acs: [{ id: 'AC1', met: false, how: 'no test' }],
        changedSincePrevious: [{ status: 'M', file: 'tests/test_old.py' }],
      }),
    }),
    task('T1', { ac: [{ id: 'AC1', text: 'it works', evidence: { kind: 'test', ref: 'x' } }] }),
    { approvals: ledger },
  )
  const e = r.result.escalated.find((x) => x.id === 'T1')
  assert.equal(e.reason, 'gate-repeat')
  const gates = new Set(e.findings.map((f) => f.gate))
  for (const g of ['verify-failed', 'dirty-tree', 'debt-marker', 'parking', 'ac-unmet', 'tdd-skipped', 'approved-item', 'tests-changed']) assert.ok(gates.has(g), g)
  assert.ok(e.findings.every((f) => GATES.includes(f.gate)))
})

test('missing red evidence is tagged no-red-evidence', async () => {
  const r = await run(fakeAgent({ impl: () => ({ tests: { added: ['tests/test_a.py'], wroteTestFirst: true } }) }))
  // verified with only a process finding open: reported as processGaps, not escalated
  assert.deepEqual(r.result.processGaps.map((f) => f.gate), ['no-red-evidence'])
})

test('a review-shallow escalation carries a review-shallow gate finding', async () => {
  const r = await run(fakeAgent({ review: () => ({ filesRead: [] }) }))
  assert.equal(r.result.tasks[0].stopped, 'review-shallow')
  const g = r.result.processGaps.filter((f) => f.gate === 'review-shallow')
  assert.equal(g.length, 1)
  assert.match(g[0].what, /src\/a\.py/)
})

test('reviewer findings never carry a gate tag', async () => {
  const r = await run(fakeAgent({ review: (round) => ({ clean: false, findings: [finding(`issue ${round}`, { file: `src/f${round}.py` })] }), triage: () => ({ repeated: [] }) }))
  const e = r.result.escalated.find((x) => x.id === 'T1')
  assert.equal(e.reason, 'round-cap')
  assert.ok(e.findings.every((f) => f.gate === undefined))
})

// ---------------------------------------------------------------- gate-only rounds
test('after a clean review, a gate-only round runs fixer and verifier, no reviewer', async () => {
  const r = await run(fakeAgent({ verify: (n) => (n === 1 ? debt() : {}) }))
  assert.equal(ofRole(r, 'review').length, 1)
  assert.equal(ofRole(r, 'fix').length, 1)
  assert.equal(ofRole(r, 'verify').length, 2)
  assert.equal(r.result.tasks[0].clean, true)
  assert.equal(r.result.tasks[0].reviewsSkippedGateOnly, 1)
  assert.equal(r.result.reviewsSkippedGateOnly, 1)
  assert.equal(r.result.finished, true)
})

test('a round after a review with findings re-reviews in full', async () => {
  const r = await run(fakeAgent({ review: (round) => (round === 1 ? { clean: false, findings: [finding('bug')] } : {}) }))
  assert.equal(ofRole(r, 'review').length, 2)
  assert.doesNotMatch(ofRole(r, 'review')[1].prompt, /Scoped re-review/)
  assert.equal(r.result.reviewsSkippedGateOnly, 0)
  assert.equal(r.result.finished, true)
})

test('two gate-only rounds in a row skip the reviewer twice', async () => {
  const r = await run(fakeAgent({ verify: (n) => (n === 1 ? debt('src/a.py') : n === 2 ? debt('src/b.py') : {}) }))
  assert.equal(ofRole(r, 'review').length, 1)
  assert.equal(ofRole(r, 'fix').length, 2)
  assert.equal(r.result.tasks[0].reviewsSkippedGateOnly, 2)
  assert.equal(r.result.tasks[0].clean, true)
})

test('light tier: after its single review, gate-only rounds continue without a reviewer', async () => {
  const r = await run(
    fakeAgent({ review: () => ({ clean: false, findings: [finding('bug')] }), verify: (n) => (n === 2 ? debt() : {}) }),
    task('T1', { review: 'light' }),
  )
  assert.equal(ofRole(r, 'review').length, 1)
  assert.equal(ofRole(r, 'fix').length, 2)
  assert.equal(r.result.tasks[0].clean, true)
  // round 2 (the debt marker) and round 3 (clean) both ran without a reviewer
  assert.equal(r.result.reviewsSkippedGateOnly, 2)
})

test('a mechanical gate fix touching only test files or the finding\'s file stays gate-only', async () => {
  const changed = [{ status: 'M', file: 'src/a.py' }, { status: 'A', file: 'tests/test_new.py' }, { status: 'M', file: './src/a.py' }]
  // a dirty tree on src/a.py (the task's first changed file)
  const r = await run(fakeAgent({ verify: (n) => (n === 1 ? { clean: false, evidence: 'M src/a.py' } : { changedSincePrevious: changed }) }))
  assert.equal(ofRole(r, 'review').length, 1)
  assert.equal(r.result.reviewsSkippedGateOnly, 1)
})

test('a work gate fix (debt-marker) changing the finding\'s own file gets one scoped review of it', async () => {
  const changed = [{ status: 'M', file: 'src/a.py' }, { status: 'A', file: 'tests/test_new.py' }]
  const r = await run(
    fakeAgent({
      verify: (n) => (n === 1 ? debt() : { head: 'def456', changedSincePrevious: changed }),
      review: (round) => (round === 2 ? { filesRead: ['src/a.py'] } : {}),
    }),
  )
  const reviews = ofRole(r, 'review')
  assert.equal(reviews.length, 2)
  const p = reviews[1].prompt
  const scope = p.slice(p.indexOf('Scoped re-review'), p.indexOf('Scoped re-review') + 400)
  assert.match(scope, /- src\/a\.py/)
  assert.doesNotMatch(scope, /tests\/test_new\.py/)
  assert.equal(r.result.reviewsSkippedGateOnly, 0)
})

test('the gate set splits into mechanical and work gates', () => {
  const src = readFileSync(SCRIPT, 'utf8')
  const list = (name) => new RegExp(`const ${name} = \\[([^\\]]*)\\]`).exec(src)[1].split(',').map((x) => x.trim().replace(/'/g, '')).filter(Boolean)
  assert.deepEqual(list('MECHANICAL_GATES'), ['verify-failed', 'dirty-tree', 'parking', 'tests-changed', 'no-red-evidence', 'tdd-skipped'])
  assert.deepEqual(list('WORK_GATES'), ['debt-marker', 'ac-unmet', 'undelivered', 'approved-item'])
})

// ---------------------------------------------------------------- scoped re-review
test('a fix touching a non-test file outside every finding\'s file brings the reviewer back, scoped to it and the work gate file', async () => {
  const changed = [
    { status: 'M', file: 'src/a.py' },
    { status: 'M', file: 'src/other.py' },
    { status: 'M', file: 'tests/test_a.py' },
  ]
  const r = await run(
    fakeAgent({
      verify: (n) => (n === 1 ? debt() : { head: 'def456', changedSincePrevious: changed }),
      review: (round) => (round === 2 ? { filesRead: ['src/other.py', 'src/a.py'] } : {}),
    }),
  )
  const reviews = ofRole(r, 'review')
  assert.equal(reviews.length, 2)
  assert.equal(reviews[1].opts.label, 'pe:review:task-t1#2')
  const p = reviews[1].prompt
  assert.match(p, /Scoped re-review/)
  const scope = p.slice(p.indexOf('Scoped re-review'), p.indexOf('Scoped re-review') + 400)
  assert.match(scope, /- src\/other\.py/)
  assert.match(scope, /- src\/a\.py/)
  assert.doesNotMatch(scope, /tests\/test_a\.py/)
  // the read gate asks only for the scoped file
  assert.equal(reviews.filter((c) => c.opts.label.endsWith('-reread')).length, 0)
  assert.equal(r.result.reviewsSkippedGateOnly, 0)
  assert.equal(r.result.tasks[0].clean, true)
})

test('a scoped review that did not read its scoped file is re-run once', async () => {
  const r = await run(
    fakeAgent({
      verify: (n) => (n === 1 ? debt() : { changedSincePrevious: [{ status: 'M', file: 'src/other.py' }] }),
      review: (round) => (round === 2 ? { filesRead: ['src/a.py'] } : {}),
    }),
  )
  const reviews = ofRole(r, 'review')
  assert.deepEqual(reviews.map((c) => c.opts.label), ['pe:review:task-t1#1', 'pe:review:task-t1#2', 'pe:review:task-t1#2-reread'])
  assert.match(reviews[2].prompt, /- src\/other\.py/)
  assert.equal(r.result.tasks[0].stopped, 'review-shallow')
})

test('a scoped review with findings sends them to the fixer, then the next round re-reviews', async () => {
  const r = await run(
    fakeAgent({
      verify: (n) => (n === 1 ? debt() : n === 2 ? { changedSincePrevious: [{ status: 'M', file: 'src/other.py' }] } : {}),
      review: (round) => (round === 2 ? { clean: false, findings: [finding('bad', { file: 'src/other.py' })], filesRead: ['src/other.py'] } : {}),
    }),
  )
  assert.equal(ofRole(r, 'review').length, 3)
  assert.match(ofRole(r, 'fix')[1].prompt, /src\/other\.py:1 - bad/)
  assert.equal(r.result.tasks[0].clean, true)
})

test('a fix that moved HEAD with no changedSincePrevious reported gets a full review, never a skip', async () => {
  const r = await run(fakeAgent({ verify: (n) => (n === 1 ? debt() : { head: 'def456' }) }))
  const reviews = ofRole(r, 'review')
  assert.equal(reviews.length, 2)
  assert.doesNotMatch(reviews[1].prompt, /Scoped re-review/)
  assert.equal(r.result.reviewsSkippedGateOnly, 0)
  assert.equal(r.result.tasks[0].clean, true)
})

test('a fix that left HEAD where it was needs no changedSincePrevious to skip the reviewer', async () => {
  const r = await run(fakeAgent({ verify: (n) => (n === 1 ? debt() : {}) }))
  assert.equal(ofRole(r, 'review').length, 1)
})

// ---------------------------------------------------------------- gate-repeat
test('a gate finding with the same key in two consecutive rounds escalates at once as gate-repeat', async () => {
  const r = await run(fakeAgent({ verify: () => debt() }))
  assert.equal(ofRole(r, 'review').length, 1)
  assert.equal(ofRole(r, 'fix').length, 1)
  assert.equal(ofRole(r, 'verify').length, 2)
  const t = r.result.tasks[0]
  assert.equal(t.stopped, 'gate-repeat')
  assert.equal(t.rounds, 2)
  const e = r.result.escalated.find((x) => x.id === 'T1')
  assert.equal(e.reason, 'gate-repeat')
  assert.equal(e.findings[0].gate, 'debt-marker')
  assert.equal(r.result.finished, false)
})

test('gate-repeat fires even when the round had a reviewer', async () => {
  const r = await run(fakeAgent({ verify: () => debt(), review: (round) => (round === 1 ? { clean: false, findings: [finding('bug')] } : {}) }))
  assert.equal(ofRole(r, 'review').length, 2)
  assert.equal(ofRole(r, 'fix').length, 1)
  assert.equal(r.result.tasks[0].stopped, 'gate-repeat')
})

test('different gates on the same file are not a repeat', async () => {
  const r = await run(fakeAgent({ verify: (n) => (n === 1 ? { passed: false, evidence: '1 failed' } : n === 2 ? { clean: false, evidence: 'dirty' } : {}) }))
  assert.equal(ofRole(r, 'fix').length, 2)
  assert.equal(r.result.tasks[0].clean, true)
})

// ---------------------------------------------------------------- triage
const twoRounds = (round) => ({ clean: false, findings: [finding(`issue ${round}`, { file: `src/f${round}.py` })] })

test('reviewer findings in two consecutive rounds with differing keys dispatch one Haiku triage agent', async () => {
  const r = await run(fakeAgent({ review: twoRounds, triage: (n, p) => ({ repeated: [{ cur: { file: 'src/f2.py' }, prev: { file: 'src/f1.py' } }] }) }))
  const tr = ofRole(r, 'triage')
  assert.equal(tr.length, 1)
  assert.equal(tr[0].opts.label, 'pe:triage:task-t1#1')
  assert.equal(tr[0].opts.model, 'haiku')
  assert.ok(tr[0].prompt.includes("python3 '/opt/test-plugin/scripts/triage.py' equivalence"))
  assert.ok(tr[0].prompt.includes('"prev":[{'))
  assert.ok(tr[0].prompt.includes('src/f1.py'))
  assert.ok(tr[0].prompt.includes('src/f2.py'))
  assert.equal(r.result.tasks[0].stopped, 'no-progress')
  assert.equal(ofRole(r, 'fix').length, 1)
  assert.equal(r.result.escalated.find((x) => x.id === 'T1').reason, 'no-progress')
})

test('triage with nothing repeated lets the loop continue; the counter numbers each dispatch', async () => {
  const r = await run(fakeAgent({ review: twoRounds, triage: () => ({ repeated: [] }) }))
  assert.deepEqual(ofRole(r, 'triage').map((c) => c.opts.label), ['pe:triage:task-t1#1', 'pe:triage:task-t1#2'])
  assert.equal(r.result.tasks[0].stopped, 'round-cap')
})

test('identical reviewer keys are no-progress without a triage call', async () => {
  const r = await run(fakeAgent({ review: (round) => ({ clean: false, findings: [finding(['a', 'b'][round - 1] + ' worded')] }) }))
  assert.equal(ofRole(r, 'triage').length, 0)
  assert.equal(r.result.tasks[0].stopped, 'no-progress')
})

test('reviewer findings in only one of two consecutive rounds dispatch no triage', async () => {
  const r = await run(fakeAgent({ review: (round) => (round === 1 ? twoRounds(1) : {}), verify: (n) => (n === 2 ? debt() : {}) }))
  assert.equal(ofRole(r, 'triage').length, 0)
  assert.equal(r.result.tasks[0].clean, true)
})

// round 1: [same-file finding, other], round 2: [reworded same-file finding] - the
// whole-list keys differ, but one finding's own key repeats.
const partialRepeat = (round) => ({
  clean: false,
  findings: round === 1 ? [finding('notices dropped'), finding('slow', { file: 'src/c.py', requirement: 'fast' })] : [finding('notices are dropped again')],
})

for (const [name, triage] of [
  ['returns nothing', () => null],
  ['throws', () => { throw new Error('agent crashed') }],
  ['reports a classifier failure', () => ({ repeated: [], reason: 'classifier failed: timeout; key equality only' })],
  ['returns no repeated list', () => ({ error: 'script missing' })],
]) {
  test(`a triage agent that ${name} falls back to findingKey`, async () => {
    const r = await run(fakeAgent({ review: partialRepeat, triage }))
    assert.equal(ofRole(r, 'triage').length, 1)
    assert.equal(r.result.tasks[0].stopped, 'no-progress')
    // The fallback, not round 3's identical whole-list key, stops the loop at round 2.
    assert.equal(ofRole(r, 'review').length, 2)
    assert.equal(ofRole(r, 'fix').length, 1)
  })
}

test('the findingKey fallback lets distinct findings continue', async () => {
  const r = await run(fakeAgent({ review: twoRounds, triage: () => null }))
  assert.equal(ofRole(r, 'triage').length, 2)
  assert.equal(r.result.tasks[0].stopped, 'round-cap')
})

// ---------------------------------------------------------------- handback doc
test('run-handback.md names every escalation reason and the reviewsSkippedGateOnly field', () => {
  const src = readFileSync(SCRIPT, 'utf8')
  const reasons = JSON.parse(src.match(/const ESCALATE = (\[[^\]]*\])/)[1].replace(/'/g, '"'))
  assert.ok(reasons.includes('gate-repeat'))
  const md = readFileSync(fileURLToPath(new URL('../../skills/start-development/references/run-handback.md', import.meta.url)), 'utf8')
  for (const reason of reasons) assert.ok(md.includes(`\`${reason}\``), `run-handback.md does not name escalation reason ${reason}`)
  assert.match(md, /`reviewsSkippedGateOnly`/)
})
