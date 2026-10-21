// Review read gate, process gaps, scoped continuations and doc-path args of
// plan-execute.js (EP-01-R2 run wf_fc395f5e: shallow reviews, bookkeeping findings,
// oversized continuations). The fake agent routes on the full label because a
// '-reread' suffix breaks the '#<round>' parse the older helpers use.
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { test } from 'node:test'
import { fileURLToPath } from 'node:url'
import { runWorkflow } from './harness.mjs'

const SCRIPT = fileURLToPath(new URL('../plan-execute.js', import.meta.url))
const IMPLEMENTER_MD = readFileSync(fileURLToPath(new URL('../../agents/implementer.md', import.meta.url)), 'utf8')
const REVIEWER_MD = readFileSync(fileURLToPath(new URL('../../agents/reviewer.md', import.meta.url)), 'utf8')
const CHECKLIST = readFileSync(fileURLToPath(new URL('../../skills/start-review/references/review-checklist.md', import.meta.url)), 'utf8')
const BRIEF = { what: 'a plugin', how: 'workflows and hooks', why: 'reliable delivery' }

const task = (id, extra = {}) => ({
  id,
  title: `task ${id}`,
  repo: 'api',
  worktree: `/wt/${id}`,
  requirement: `requirement for ${id}`,
  value: 'worth it',
  files: [`src/${id}-a.py`, `src/${id}-b.py`, `tests/test_${id}.py`],
  ...extra,
})

const deliverable = (id, filesChanged = ['src/a.py']) => ({
  taskId: id,
  complete: true,
  summary: 'did it',
  filesChanged,
  branch: `b-${id}`,
  tests: { added: ['tests/test_a.py'], wroteTestFirst: true, red: { command: 'pytest', output: 'FAILED tests/test_a.py::test_x' } },
  verification: { command: 'pytest tests/test_a.py', passed: true, evidence: '3 passed' },
})

const okVerify = { head: 'abc123', clean: true, command: 'pytest', passed: true, evidence: '3 passed', debtMarkers: [] }
const finding = (summary) => ({ severity: 'high', file: 'src/a.py', line: 1, summary, requirement: 'the notifier keeps every notice' })
const cleanAudit = { complete: true, missing: [] }

// review: (label, prompt) => partial review; filesRead defaults to ['src/a.py']
function fakeAgent({ review, filesChanged, impl, verify } = {}) {
  return async (prompt, opts) => {
    const l = opts.label
    const [, role, rest] = l.split(':')
    if (role === 'impl' || role === 'fix') return impl ? impl(l) : deliverable(rest.split(/[#+]/)[0], filesChanged)
    if (role === 'review') return { clean: true, findings: [], filesRead: ['src/a.py'], ...(review ? review(l, prompt) : {}) }
    if (role === 'verify') return { ...okVerify, ...(verify ? verify(l, prompt) : {}) }
    if (role === 'audit') return cleanAudit
    throw new Error(`unexpected agent ${l}`)
  }
}
const run = (args, agent) => runWorkflow(SCRIPT, { args: { brief: BRIEF, ...args }, agent })
const labels = (r) => r.calls.map((c) => c.opts.label)
const ofRole = (r, role) => r.calls.filter((c) => c.opts.label.split(':')[1] === role)

test('the review schema requires filesRead and offers processGaps', async () => {
  const r = await run({ tasks: [task('T1')] }, fakeAgent())
  const s = ofRole(r, 'review')[0].opts.schema
  assert.deepEqual(s.required, ['clean', 'findings', 'filesRead'])
  assert.deepEqual(s.properties.filesRead.items, { type: 'string' })
  const g = s.properties.processGaps
  assert.equal(g.type, 'array')
  assert.deepEqual(g.items.required, ['what', 'where'])
  assert.ok(!s.required.includes('processGaps'))
})

test('a review that read nothing is re-run once with the unread files named', async () => {
  const r = await run({ tasks: [task('T1')] }, fakeAgent({ review: (l) => (l.endsWith('#1') ? { filesRead: [] } : {}) }))
  assert.deepEqual(labels(r).filter((l) => l.includes('review')), ['pe:review:task-t1#1', 'pe:review:task-t1#1-reread'])
  const [first, second] = ofRole(r, 'review')
  assert.doesNotMatch(first.prompt, /You must read these before judging/)
  assert.match(second.prompt, /You must read these before judging - the previous review did not:\n- src\/a\.py/)
  assert.ok(second.prompt.startsWith(first.prompt))
  assert.equal(second.opts.model, first.opts.model)
  assert.equal(second.opts.schema, first.opts.schema)
  assert.equal(r.result.finished, true)
})

test('a second shallow review escalates as review-shallow, no fixer, never clean', async () => {
  const r = await run({ tasks: [task('T1')] }, fakeAgent({ review: () => ({ filesRead: [] }) }))
  assert.equal(ofRole(r, 'fix').length, 0)
  assert.equal(ofRole(r, 'review').length, 2)
  assert.equal(r.result.tasks[0].stopped, 'review-shallow')
  assert.equal(r.result.tasks[0].clean, false)
  // verified, only the process finding open: processOnly, reported as a gap and still escalated
  assert.equal(r.result.tasks[0].processOnly, true)
  assert.deepEqual(r.result.processGaps.map((f) => f.gate), ['review-shallow'])
  assert.deepEqual(r.result.escalated.map((e) => [e.id, e.reason]), [['T1', 'review-shallow']])
  assert.equal(r.result.finished, false)
})

test('a reviewer that read every non-test changed file proceeds', async () => {
  const r = await run({ tasks: [task('T1')] }, fakeAgent({ filesChanged: ['src/a.py', 'tests/test_a.py'] }))
  assert.equal(ofRole(r, 'review').length, 1)
  assert.equal(r.result.finished, true)
})

test('test-file shapes do not need to be read', async () => {
  const fc = ['src/a.py', 'test/x.py', 'pkg/test_b.py', 'web/a.test.ts', 'web/b_test.go', 'web/c.spec.js', 'lib/d_spec.rb']
  const r = await run({ tasks: [task('T1')] }, fakeAgent({ filesChanged: fc }))
  assert.equal(ofRole(r, 'review').length, 1)
})

test('globs and annotated entries are skipped, ./ is stripped', async () => {
  const r = await run(
    { tasks: [task('T1')] },
    fakeAgent({ filesChanged: ['./src/a.py', 'docs/*.md', 'src/gone.py (deleted)'], review: () => ({ filesRead: ['src/a.py'] }) }),
  )
  assert.equal(ofRole(r, 'review').length, 1)
})

test('a longer path in filesRead counts as reading the file', async () => {
  const r = await run({ tasks: [task('T1')] }, fakeAgent({ review: () => ({ filesRead: ['code/api/src/a.py'] }) }))
  assert.equal(ofRole(r, 'review').length, 1)
  assert.equal(r.result.finished, true)
})

test('blocked wins over shallow', async () => {
  const r = await run(
    { tasks: [task('T1')] },
    fakeAgent({ review: () => ({ clean: false, filesRead: [], blocked: { reason: 'needs a human merge', whoCanClear: 'user' } }) }),
  )
  assert.equal(ofRole(r, 'review').length, 1)
  assert.equal(r.result.tasks[0].stopped, 'blocked')
})

test('processGaps do not block clean and appear per task and top level, accumulated across rounds', async () => {
  const r = await run(
    { tasks: [task('T1', { review: 'full' })] },
    fakeAgent({
      review: (l) =>
        l.endsWith('#1')
          ? { clean: false, findings: [finding('bug')], processGaps: [{ what: 'no MEMORY.md note', where: 'MEMORY.md' }] }
          : { processGaps: [{ what: 'ratchet not run', where: 'scripts/ratchet.sh' }] },
    }),
  )
  assert.equal(r.result.finished, true)
  assert.equal(ofRole(r, 'fix').length, 1)
  assert.doesNotMatch(ofRole(r, 'fix')[0].prompt, /MEMORY\.md note/)
  assert.deepEqual(r.result.tasks[0].processGaps.map((g) => g.where), ['MEMORY.md', 'scripts/ratchet.sh'])
  assert.deepEqual(r.result.processGaps, [
    { taskId: 'T1', what: 'no MEMORY.md note', where: 'MEMORY.md' },
    { taskId: 'T1', what: 'ratchet not run', where: 'scripts/ratchet.sh' },
  ])
})

test('a gate-only round skips the reviewer and keeps the processGaps the last review reported', async () => {
  let verifies = 0
  const agent = fakeAgent({
    review: () => ({ processGaps: [{ what: 'no MEMORY.md note', where: 'MEMORY.md' }] }),
    verify: () => (++verifies === 1 ? { debtMarkers: [{ file: 'src/a.py', line: 2, marker: 'XXX' }] } : {}),
  })
  const r = await run({ tasks: [task('T1', { review: 'full' })] }, agent)
  // round 1 reviewed clean with a gate finding; round 2 ran fixer and verifier only
  assert.equal(ofRole(r, 'review').length, 1)
  assert.equal(ofRole(r, 'fix').length, 1)
  assert.equal(r.result.tasks[0].clean, true)
  assert.equal(r.result.tasks[0].reviewsSkippedGateOnly, 1)
  assert.deepEqual(r.result.processGaps, [{ taskId: 'T1', what: 'no MEMORY.md note', where: 'MEMORY.md' }])
})

test('a review with only processGaps is clean', async () => {
  const r = await run({ tasks: [task('T1')] }, fakeAgent({ review: () => ({ processGaps: [{ what: 'no approval line', where: 'status.md' }] }) }))
  assert.equal(ofRole(r, 'fix').length, 0)
  assert.equal(r.result.tasks[0].clean, true)
})

test('processGaps is an empty array on small-task and failure paths', async () => {
  const small = await run({ tasks: [task('T1', { files: ['src/a.py'] })] }, fakeAgent())
  assert.deepEqual(small.result.tasks[0].processGaps, [])
  assert.deepEqual(small.result.processGaps, [])
  const dead = await run({ tasks: [task('T1')] }, async (p, o) => (o.label.includes(':impl:') ? null : cleanAudit))
  assert.deepEqual(dead.result.tasks[0].processGaps, [])
})

test('the filesRead and process-gap rules come from the checklist the reviewer agent reads, not the prompt', async () => {
  const r = await run({ tasks: [task('T1')] }, fakeAgent())
  const p = ofRole(r, 'review')[0].prompt
  assert.equal(ofRole(r, 'review')[0].opts.agentType, 'workbench:reviewer')
  assert.ok(REVIEWER_MD.includes('skills/start-review/references/review-checklist.md'))
  for (const rule of ['Report filesRead: the files you actually opened, not the files you were pointed at.', 'A missing note, sweep, ratchet or approval line is a processGaps entry, never a finding.']) {
    assert.ok(CHECKLIST.includes(`- ${rule}`), rule)
    assert.ok(!p.includes(rule), rule)
  }
  assert.ok(!p.includes('List every file you read in filesRead.'))
})

// ---------------------------------------------------------------- continuations
const handoff = (n) => ({
  taskId: 'T1',
  complete: false,
  status: 'handoff',
  summary: `partial ${n}`,
  filesChanged: ['src/a.py'],
  branch: 'b-T1',
  tests: { added: [], wroteTestFirst: true, red: { command: 'pytest', output: 'FAILED tests/test_a.py::test_x' } },
  verification: { command: 'x', passed: false, evidence: 'f' },
  handoff: { doneSoFar: `slice ${n}`, remaining: ['the retry path'], nextStep: 'write the retry test', testState: '1 failed', wipCommit: `abc${n}` },
})

test('continuations are capped at 2, lead with the remaining list, and the cap escalation carries a split', async () => {
  let n = 0
  const r = await run({ tasks: [task('T1')] }, async (p, o) => (o.label.includes(':impl:') ? handoff(++n) : cleanAudit))
  const conts = r.calls.filter((c) => /\+\d+$/.test(c.opts.label))
  assert.equal(conts.length, 2)
  const p = conts[1].prompt
  const lines = p.split('\n')
  assert.equal(lines[0], '=== CONTINUATION 2 of at most 2 ===')
  assert.equal(lines[1], 'Deliver ONLY the remaining acceptance conditions below; everything else is done and committed:')
  assert.equal(lines[2], '- the retry path')
  assert.ok(p.indexOf('Deliver ONLY the remaining') < p.indexOf('requirement for T1'))
  assert.match(p, /WIP commit: abc2/)
  const e = r.result.escalated.find((x) => x.id === 'T1')
  assert.equal(e.reason, 'handoff-cap')
  assert.equal(e.split, 'split the remaining conditions into tasks of at most 8 files each')
  assert.equal(e.handoff.wipCommit, 'abc3')
})

test('a fixer that hits the continuation cap escalates with handoff and split', async () => {
  let n = 0
  const r = await run(
    { tasks: [task('T1')] },
    fakeAgent({
      review: (l) => (l.endsWith('#1') ? { clean: false, findings: [finding('bug')] } : {}),
      impl: (l) => (l.includes(':fix:') ? handoff(++n) : deliverable('T1')),
    }),
  )
  const e = r.result.escalated.find((x) => x.id === 'T1')
  assert.equal(e.reason, 'handoff-cap')
  assert.ok(e.handoff.wipCommit)
  assert.equal(e.split, 'split the remaining conditions into tasks of at most 8 files each')
})

// ---------------------------------------------------------------- doc paths
test('designDoc and planDoc reach impl, fix, review and audit prompts, and are absent otherwise', async () => {
  const agent = fakeAgent({ review: (l) => (l.endsWith('#1') ? { clean: false, findings: [finding('bug')] } : {}) })
  const withDocs = await run({ tasks: [task('T1')], designDoc: 'docs/d.md', planDoc: 'docs/p.md' }, agent)
  for (const role of ['impl', 'fix', 'review', 'audit']) {
    const p = ofRole(withDocs, role)[0].prompt
    assert.ok(p.includes('Spec (design doc): docs/d.md'), role)
    assert.ok(p.includes('Plan: docs/p.md - read the section for your task, not the whole file.'), role)
  }
  const none = await run({ tasks: [task('T1')] }, agent)
  for (const c of none.calls) {
    assert.doesNotMatch(c.prompt, /Spec \(design doc\)/, c.opts.label)
    assert.doesNotMatch(c.prompt, /^Plan: /m, c.opts.label)
  }
  const one = await run({ tasks: [task('T1')], planDoc: 'docs/p.md' }, agent)
  assert.doesNotMatch(ofRole(one, 'impl')[0].prompt, /Spec \(design doc\)/)
  assert.match(ofRole(one, 'impl')[0].prompt, /^Plan: docs\/p\.md/m)
})

// ---------------------------------------------------------------- fixer read set, prompt order
const firstThen = (first, then) => {
  let n = 0
  return (l) => (l.includes(':impl:') && !l.includes('+') && ++n === 1 ? first : then(l))
}

test('the fixer prompt lists the implementer handoff read set and the reviewer filesRead as already read', async () => {
  const h = handoff(1)
  h.handoff.readSet = [{ path: 'src/z.py', lines: '1-40', note: 'the parser' }]
  const r = await run(
    { tasks: [task('T1')] },
    fakeAgent({
      impl: firstThen(h, (l) => deliverable(l.split(':')[2].split(/[#+]/)[0])),
      review: (l) => (l.endsWith('#1') ? { clean: false, findings: [finding('bug')], filesRead: ['src/a.py', 'src/r.py'] } : {}),
    }),
  )
  const p = ofRole(r, 'fix')[0].prompt
  const at = p.search(/already read/i)
  assert.ok(at > 0, 'already read heading')
  assert.match(p, /- src\/z\.py:1-40 - the parser/)
  assert.match(p, /- src\/a\.py\n/)
  assert.match(p, /- src\/r\.py\n/)
  assert.ok(at < p.indexOf('1. [high'), 'read set precedes the findings')
})

test('a fixer prompt without any read set has no already-read block', async () => {
  const r = await run({ tasks: [task('T1')] }, fakeAgent({ review: (l) => (l.endsWith('#1') ? { clean: false, findings: [finding('bug')], filesRead: [] , diffRead: true, diffLines: 5 } : {}) }))
  assert.doesNotMatch(ofRole(r, 'fix')[0].prompt, /already read/i)
})

test('review prompt: static blocks first, then the task, then findings, scope and the round last', async () => {
  const r = await run(
    { tasks: [task('T1')] },
    fakeAgent({
      verify: (l) => (l.endsWith('#1') ? { debtMarkers: [{ file: 'src/a.py', line: 3, marker: 'XXX' }] } : { head: 'def456', changedSincePrevious: [{ status: 'M', file: 'src/other.py' }] }),
      review: (l) => (l.endsWith('#2') ? { filesRead: ['src/other.py'] } : {}),
    }),
  )
  const reviews = ofRole(r, 'review')
  assert.equal(reviews.length, 2)
  const inOrder = (p, order) => {
    const idx = order.map((m) => p.indexOf(m))
    assert.ok(idx.every((i) => i >= 0), JSON.stringify(idx))
    assert.deepEqual([...idx].sort((a, b) => a - b), idx)
  }
  inOrder(reviews[0].prompt, ['a plugin', 'Review through these lenses only', 'Task requirement:', 'Independent verification found:', `Round ${1} of at most`])
  const p = reviews[1].prompt
  inOrder(p, ['a plugin', 'Review through these lenses only', 'Task requirement:', 'Scoped re-review', `Round ${2} of at most`])
  for (const m of ['Review through these lenses only', 'Each finding summary is at most']) {
    assert.ok(p.indexOf(m) < p.indexOf('Task requirement:'), m)
  }
})

test('fix prompt: static blocks first, then the task, then the read set and the findings last', async () => {
  const r = await run(
    { tasks: [task('T1')] },
    fakeAgent({ review: (l) => (l.endsWith('#1') ? { clean: false, findings: [finding('bug')] } : {}) }),
  )
  const p = ofRole(r, 'fix')[0].prompt
  const order = ['a plugin', 'Helpers do NOT get worktrees', 'Original task requirement', '1. [high']
  const idx = order.map((m) => p.indexOf(m))
  assert.ok(idx.every((i) => i >= 0), JSON.stringify(idx))
  assert.deepEqual([...idx].sort((a, b) => a - b), idx)
  // The fixer method is agents/implementer.md, the agent the fix call runs as.
  assert.equal(ofRole(r, 'fix')[0].opts.agentType, 'workbench:implementer')
  for (const m of ['Judge each finding before acting', 'Add or extend a failing test']) assert.ok(IMPLEMENTER_MD.includes(m), m)
})
