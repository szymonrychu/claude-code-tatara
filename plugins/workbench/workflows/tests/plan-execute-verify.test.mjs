// Independent verification of plan-execute.js: a verifier re-runs each task's
// command on the committed HEAD after every implementer and fixer, and scans the
// diff for debt markers. Round-1 evidence: a docs commit made after the agent's
// test run broke a test, and the self-reported green hid it.
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

const okVerify = { head: 'abc123', clean: true, command: 'pytest', passed: true, evidence: '3 passed', debtMarkers: [], diffstat: { files: 2, addedNonTest: 40, addedTest: 10 }, acs: [{ id: 'AC1', met: true, how: 'ok' }] }
const cleanAudit = { complete: true, missing: [] }

// Routed on the full label. verify: (n, prompt) => result, n is the #n of the label.
function fakeAgent({ verify, review, implTests } = {}) {
  return async (prompt, opts) => {
    const [, role, rest] = opts.label.split(':')
    if (role === 'impl' || role === 'fix') return { ...deliverable(rest.split(/[#+]/)[0]), ...(implTests ? { tests: implTests } : {}) }
    if (role === 'verify') return verify ? verify(Number(rest.split('#')[1]), prompt) : okVerify
    if (role === 'review') return { clean: true, findings: [], filesRead: ['src/a.py'], ...(review ? review(prompt) : {}) }
    if (role === 'audit') return cleanAudit
    throw new Error(`unexpected agent ${opts.label}`)
  }
}
const run = (args, agent) => runWorkflow(SCRIPT, { args: { brief: BRIEF, ...args }, agent })
const ofRole = (r, role) => r.calls.filter((c) => c.opts.label.split(':')[1] === role)

test('the verify schema has the required shape', async () => {
  const r = await run({ tasks: [task('T1')] }, fakeAgent())
  const s = ofRole(r, 'verify')[0].opts.schema
  assert.deepEqual(s.required, ['head', 'clean', 'command', 'passed', 'evidence'])
  assert.equal(s.properties.head.type, 'string')
  assert.equal(s.properties.clean.type, 'boolean')
  assert.equal(s.properties.command.type, 'string')
  assert.equal(s.properties.passed.type, 'boolean')
  assert.equal(s.properties.evidence.type, 'string')
  assert.match(s.properties.evidence.description, /at most 150 words/)
  assert.equal(s.properties.note.type, 'string')
  const m = s.properties.debtMarkers
  assert.equal(m.type, 'array')
  assert.deepEqual(m.items.required, ['file', 'line', 'marker'])
  assert.equal(m.items.properties.file.type, 'string')
  assert.equal(m.items.properties.line.type, 'integer')
  assert.equal(m.items.properties.marker.type, 'string')
})

test('one verifier runs after a clean implementation, with the full prompt', async () => {
  const r = await run({ tasks: [task('T1', { verify: 'pytest -q tests/test_T1.py && ruff check' })] }, fakeAgent())
  const v = ofRole(r, 'verify')
  assert.equal(v.length, 1)
  assert.equal(v[0].opts.label, 'pe:verify:task-t1#1')
  assert.equal(v[0].opts.phase, 'Verify')
  assert.equal(v[0].opts.model, 'haiku')
  assert.equal(v[0].opts.effort, 'low')
  for (const s of [
    "else echo '/wt/T1'; fi)",
    "python3 '/opt/test-plugin/scripts/verify-task.py'",
    '--worktree',
    "--base 'main'",
    "--cmd 'pytest -q tests/test_T1.py && ruff check'",
    '--install',
    'Do not edit, commit, stash, reset or switch branches',
    'relay the JSON verbatim',
    'once',
  ]) {
    assert.ok(v[0].prompt.includes(s), `verify prompt lacks: ${s}`)
  }
  assert.ok(!v[0].prompt.includes('--acs'))
  assert.ok(!v[0].prompt.includes('--prev-head'))
  assert.ok(!v[0].prompt.includes('--tdd-revert'))
})

test('without t.verify the verifier runs verify-task --targeted, never the implementer\'s command', async () => {
  const r = await run({ tasks: [task('T1')] }, fakeAgent())
  const p = ofRole(r, 'verify')[0].prompt
  assert.ok(p.includes(' --targeted '), p)
  assert.ok(!p.includes('pytest tests/test_a.py'), p)
  assert.ok(!p.includes('--cmd'), p)
})

test('args.baseRef replaces main in the merge-base command', async () => {
  const r = await run({ baseRef: 'develop', tasks: [task('T1')] }, fakeAgent())
  const p = ofRole(r, 'verify')[0].prompt
  assert.ok(p.includes("--base 'develop'"))
  assert.ok(!p.includes("--base 'main'"))
})

test('the task result carries the verifier result and the implementer self-report', async () => {
  const r = await run({ tasks: [task('T1')] }, fakeAgent())
  const t = r.result.tasks[0]
  assert.equal(t.verification.head, 'abc123')
  assert.equal(t.selfVerification.command, 'pytest tests/test_a.py')
  assert.equal(t.verifyRuns, 1)
  assert.equal(t.verified, true)
})

test('a failing verifier sends the task to a fixer, then a second verifier', async () => {
  const r = await run(
    { tasks: [task('T1')] },
    fakeAgent({ verify: (n) => (n === 1 ? { ...okVerify, passed: false, evidence: '1 failed: test_record_follows_template' } : okVerify) }),
  )
  assert.equal(r.error, undefined)
  const fix = ofRole(r, 'fix')
  assert.equal(fix.length, 1)
  assert.equal(fix[0].opts.label, 'pe:fix:task-t1#1')
  assert.ok(fix[0].prompt.includes('Independent verification failed'))
  assert.ok(fix[0].prompt.includes('test_record_follows_template'))
  const v = ofRole(r, 'verify')
  assert.deepEqual(v.map((c) => c.opts.label), ['pe:verify:task-t1#1', 'pe:verify:task-t1#2'])
  const review = ofRole(r, 'review')[0]
  assert.ok(review.prompt.includes('Independent verification found:'))
  assert.ok(review.prompt.indexOf('Independent verification found:') > review.prompt.indexOf('Review through these lenses only'))
  assert.match(review.prompt, /- \[high\] src\/a\.py - Independent verification failed/)
  const t = r.result.tasks[0]
  assert.equal(t.verifyRuns, 2)
  assert.equal(t.clean, true)
  assert.equal(r.result.finished, true)
})

test('a dirty worktree is a finding too', async () => {
  const r = await run(
    { tasks: [task('T1')] },
    fakeAgent({ verify: (n) => (n === 1 ? { ...okVerify, clean: false } : okVerify) }),
  )
  assert.ok(ofRole(r, 'fix')[0].prompt.includes('Worktree not clean at verification'))
  assert.equal(r.result.tasks[0].clean, true)
})

test('a verifier that passes on a dirty tree leaves the task unverified', async () => {
  const r = await run({ tasks: [task('T1')] }, fakeAgent({ verify: () => ({ ...okVerify, clean: false }) }))
  assert.equal(r.result.tasks[0].verified, false)
  assert.equal(r.result.finished, false)
})

test('a debt marker becomes a finding in the fix prompt', async () => {
  const r = await run(
    { tasks: [task('T1')] },
    fakeAgent({ verify: (n) => (n === 1 ? { ...okVerify, debtMarkers: [{ file: 'src/a.py', line: 7, marker: 'TODO' }] } : okVerify) }),
  )
  const fix = ofRole(r, 'fix')[0]
  assert.ok(fix.prompt.includes('src/a.py:7'))
  assert.ok(fix.prompt.includes('Debt marker introduced: TODO'))
  assert.ok(fix.prompt.includes('no TODO, stub or skipped test stands in for the work'))
})

test('a small task with a clean verifier skips review', async () => {
  const r = await run({ tasks: [task('T1', { files: ['a.py', 'b.py'], review: undefined, ac: [{ id: 'AC1', text: 'it works', evidence: { kind: 'test', ref: 'x' } }] })] }, fakeAgent())
  assert.equal(ofRole(r, 'review').length, 0)
  assert.equal(ofRole(r, 'verify').length, 1)
  assert.equal(r.result.tasks[0].clean, true)
})

test('a small task with a debt marker gets one light review round and a fix', async () => {
  const r = await run(
    { tasks: [task('T1', { files: ['a.py', 'b.py'], review: undefined, ac: [{ id: 'AC1', text: 'it works', evidence: { kind: 'test', ref: 'x' } }] })] },
    fakeAgent({ verify: (n) => (n === 1 ? { ...okVerify, debtMarkers: [{ file: 'a.py', line: 3, marker: 'FIXME' }] } : okVerify) }),
  )
  // light: one review, one fixer, the verifier; no second review
  assert.equal(ofRole(r, 'review').length, 1)
  assert.equal(ofRole(r, 'fix').length, 1)
  assert.equal(r.result.tasks[0].clean, true)
})

test('a null verifier escalates as verify-agent-died', async () => {
  const r = await run({ tasks: [task('T1')] }, fakeAgent({ verify: () => null }))
  assert.equal(r.error, undefined)
  const t = r.result.tasks[0]
  assert.equal(t.stopped, 'verify-agent-died')
  assert.equal(r.result.escalated[0].reason, 'verify-agent-died')
  assert.deepEqual(r.result.escalated[0].findings, [])
  assert.equal(typeof r.result.escalated[0].rounds, 'number')
  assert.equal(r.result.finished, false)
})

test('a verifier dying after a fix also escalates', async () => {
  const r = await run(
    { tasks: [task('T1')] },
    fakeAgent({ verify: (n) => (n === 1 ? { ...okVerify, passed: false, evidence: 'boom' } : null) }),
  )
  assert.equal(r.result.tasks[0].stopped, 'verify-agent-died')
})

test('every impl, fix and verify prompt caps the report length', async () => {
  const r = await run(
    { tasks: [task('T1')] },
    fakeAgent({ verify: (n) => (n === 1 ? { ...okVerify, passed: false, evidence: 'x' } : okVerify) }),
  )
  // impl and fix run as workbench:implementer, whose agent file carries the cap.
  assert.ok(IMPLEMENTER_MD.includes('at most 200 words'), 'agents/implementer.md lacks the cap')
  for (const role of ['impl', 'fix']) {
    for (const c of ofRole(r, role)) assert.equal(c.opts.agentType, 'workbench:implementer', `${role} does not run as the implementer`)
  }
})

test('a passing verifier with empty evidence still sends the task back for evidence', async () => {
  const r = await run(
    { tasks: [task('T1')] },
    fakeAgent({ verify: (n) => (n === 1 ? { ...okVerify, evidence: '' } : okVerify) }),
  )
  const fix = ofRole(r, 'fix')
  assert.equal(fix.length, 1)
  assert.ok(fix[0].prompt.includes('No passing verification was reported'))
  assert.equal(r.result.tasks[0].clean, true)
})

test('the verify dispatch runs as workbench:verifier by default', async () => {
  const r = await run({ tasks: [task('T1')] }, fakeAgent())
  assert.equal(ofRole(r, 'verify')[0].opts.agentType, 'workbench:verifier')
})

test('args.verifierAgent replaces the agent type', async () => {
  const r = await run({ verifierAgent: 'other:agent', tasks: [task('T1')] }, fakeAgent())
  assert.equal(ofRole(r, 'verify')[0].opts.agentType, 'other:agent')
})

test('args.verifierAgent null (or empty) passes no agentType key', async () => {
  for (const verifierAgent of [null, '']) {
    const r = await run({ verifierAgent, tasks: [task('T1')] }, fakeAgent())
    assert.ok(!('agentType' in ofRole(r, 'verify')[0].opts), `verifierAgent ${JSON.stringify(verifierAgent)}`)
  }
})

test('a partial verifier result (no head, no passed) is treated as verify-agent-died', async () => {
  const r = await run(
    { tasks: [task('T1')] },
    fakeAgent({ verify: () => ({ clean: true, command: 'x', evidence: 'e' }) }),
  )
  assert.equal(r.result.escalated[0].reason, 'verify-agent-died')
  assert.equal(r.result.tasks[0].clean, false)
})

test('the verify prompt passes DEBT_MARKERS and TEST_FILE_RE.source to the script verbatim', async () => {
  const r = await run({ tasks: [task('T1')] }, fakeAgent())
  const p = ofRole(r, 'verify')[0].prompt
  const markers = 'TODO, FIXME, XXX, HACK, NotImplementedError, unimplemented!, .skip(, pytest.mark.skip, xfail, t.Skip(, follow-up, for later, next round, round N (any number), phase 2, out of scope for this pass, left as an exercise, nice to have'
  assert.ok(p.includes(`--markers '${markers}'`))
  const re = String.raw`(^|\/)(tests?\/|test_[^/]*\.py$|[^/]*\.(test|spec)\.[^/]*$|[^/]*_(test|spec)\.[^/]*$)`
  assert.ok(p.includes(`--test-re '${re}'`), 'test-re flag')
})

test('a fix-round verify prompt passes --prev-head with the previous head', async () => {
  const r = await run(
    { tasks: [task('T1')] },
    fakeAgent({ verify: (n) => (n === 1 ? { ...okVerify, head: 'abc1234', passed: false, evidence: '1 failed' } : { ...okVerify, head: 'def4567' }) }),
  )
  const v = ofRole(r, 'verify')
  assert.ok(!v[0].prompt.includes('--prev-head'))
  assert.ok(v[1].prompt.includes("--prev-head 'abc1234'"))
  assert.equal(v[0].opts.schema.properties.changedSincePrevious.type, 'array')
})

const AC = [
  { id: 'AC1', text: 'the flag exists', evidence: { kind: 'symbol', ref: 'flag' } },
  { id: 'AC2', text: 'docs mention it', evidence: { kind: 'judgement' } },
]

test('a task with ac gets the ac JSON written to a temp file and --acs', async () => {
  const r = await run({ tasks: [task('T1', { ac: AC })] }, fakeAgent())
  const p = ofRole(r, 'verify')[0].prompt
  assert.ok(p.includes('--acs "$ACS"'))
  assert.ok(p.includes(JSON.stringify(AC)))
  assert.ok(p.includes('outside the worktree'))
})

test('--tdd-revert is passed when wroteTestFirst is false or tests.red is missing', async () => {
  for (const implTests of [
    { added: [], wroteTestFirst: false, note: 'docs-only' },
    { added: ['tests/test_a.py'], wroteTestFirst: true },
  ]) {
    const r = await run({ tasks: [task('T1')] }, fakeAgent({ implTests }))
    assert.ok(ofRole(r, 'verify')[0].prompt.includes('--tdd-revert'), JSON.stringify(implTests))
  }
})

test('an unmet AC is a high missing finding in the fix prompt', async () => {
  const r = await run(
    { tasks: [task('T1', { ac: AC })] },
    fakeAgent({ verify: (n) => (n === 1 ? { ...okVerify, acs: [{ id: 'AC1', met: false }, { id: 'AC2', met: true }] } : okVerify) }),
  )
  const fix = ofRole(r, 'fix')
  assert.equal(fix.length, 1)
  assert.ok(fix[0].prompt.includes('Acceptance condition AC1 not met: the flag exists'))
  assert.ok(!fix[0].prompt.includes('Acceptance condition AC2'))
})

test('an unmet AC carries the verifier how verbatim as the finding evidence', async () => {
  const how = 'ref-missing: no test named `t_x` in tests/a.py; add or rename a test to exactly this name and file'
  const r = await run(
    { tasks: [task('T1', { ac: AC })] },
    fakeAgent({ verify: (n) => (n === 1 ? { ...okVerify, acs: [{ id: 'AC1', met: false, how, refMissing: true }] } : okVerify) }),
  )
  assert.ok(ofRole(r, 'fix')[0].prompt.includes(how))
})

test('met null or plausible no/unsure goes to acsForAudit, never to a fixer', async () => {
  const acs = [
    { id: 'AC1', met: null },
    { id: 'AC2', met: true, plausible: 'unsure' },
    { id: 'AC3', met: true, plausible: 'no' },
    { id: 'AC4', met: true, plausible: 'yes' },
  ]
  const r = await run({ tasks: [task('T1', { ac: [...AC, { ...AC[0], id: 'AC3' }, { ...AC[0], id: 'AC4' }] })] }, fakeAgent({ verify: () => ({ ...okVerify, acs }) }))
  assert.equal(ofRole(r, 'fix').length, 0)
  assert.deepEqual(r.result.tasks[0].acsForAudit, ['AC1', 'AC2', 'AC3'])
})

test('a task without ac keeps the old path: empty acsForAudit, no ac flags', async () => {
  const r = await run({ tasks: [task('T1')] }, fakeAgent())
  assert.deepEqual(r.result.tasks[0].acsForAudit, [])
  assert.ok(!ofRole(r, 'verify')[0].prompt.includes('--acs'))
  assert.equal(ofRole(r, 'fix').length, 0)
})

test('a parking entry is a high quality finding', async () => {
  const r = await run(
    { tasks: [task('T1')] },
    fakeAgent({ verify: (n) => (n === 1 ? { ...okVerify, parking: [{ file: 'src/a.py', line: 7, text: 'handle X in a later pass' }] } : okVerify) }),
  )
  const fix = ofRole(r, 'fix')
  assert.equal(fix.length, 1)
  assert.ok(fix[0].prompt.includes('Parking wording introduced: handle X in a later pass'))
})

test('the deliverable schema carries acs beside selfVerification', async () => {
  const r = await run({ tasks: [task('T1')] }, fakeAgent())
  const a = ofRole(r, 'impl')[0].opts.schema.properties.acs
  assert.equal(a.type, 'array')
  assert.deepEqual(a.items.required, ['id', 'met'])
})

test('the verify schema offers acs, parking, diffstat, tierHint and tdd', async () => {
  const r = await run({ tasks: [task('T1')] }, fakeAgent())
  const s = ofRole(r, 'verify')[0].opts.schema.properties
  for (const k of ['acs', 'parking', 'diffstat', 'tierHint', 'tdd']) assert.ok(s[k], k)
})

test('the verifier agent file is haiku, 8 turns, run-once relay', async () => {
  const { readFileSync } = await import('node:fs')
  const md = readFileSync(new URL('../../agents/verifier.md', import.meta.url), 'utf8')
  assert.match(md, /^model: haiku$/m)
  assert.match(md, /^maxTurns: 8$/m)
  assert.match(md, /once/)
  assert.match(md, /JSON/)
  assert.match(md, /never edit, commit, stash, reset or switch branches/i)
})

test('prompts run scripts by the shell-quoted absolute pluginRoot, never CLAUDE_PLUGIN_ROOT or a repo path', async () => {
  const r = await run({ pluginRoot: "/opt/my plugin", tasks: [task('A')] }, fakeAgent())
  const v = ofRole(r, 'verify')[0].prompt
  assert.ok(v.includes(`python3 '/opt/my plugin/scripts/verify-task.py'`))
  for (const c of r.calls) {
    assert.ok(!c.prompt.includes('CLAUDE_PLUGIN_ROOT'))
    assert.ok(!c.prompt.includes('/home/user/plugin'))
  }
})

test('missing or relative pluginRoot throws at start, before any agent runs', async () => {
  for (const pluginRoot of [undefined, '', 'plugin', './x']) {
    const r = await runWorkflow(SCRIPT, { args: { brief: BRIEF, pluginRoot, tasks: [task('A')] }, agent: fakeAgent() })
    assert.match(String(r.error), /pluginRoot/)
    assert.equal(r.calls.length, 0)
  }
})

test('the tier is read once: --no-tier is passed only when a previous head is set', async () => {
  const r = await run(
    { tasks: [task('T1')] },
    fakeAgent({ verify: (n) => (n === 1 ? { ...okVerify, head: 'abc1234', passed: false, evidence: '1 failed' } : okVerify) }),
  )
  const v = ofRole(r, 'verify')
  assert.ok(!v[0].prompt.includes('--no-tier'))
  assert.ok(v[1].prompt.includes('--no-tier'))
  assert.ok(v[1].prompt.includes("--prev-head 'abc1234'"))
})

test('triageUsage is summed per task and in the run return', async () => {
  const usage = { calls: 2, input_tokens: 100, output_tokens: 7 }
  const r = await run(
    { tasks: [task('T1')] },
    fakeAgent({ verify: (n) => (n === 1 ? { ...okVerify, passed: false, evidence: '1 failed', triageUsage: usage } : { ...okVerify, triageUsage: usage }) }),
  )
  assert.deepEqual(r.result.tasks[0].triageUsage, { calls: 4, input_tokens: 200, output_tokens: 14 })
  assert.deepEqual(r.result.triageUsage, { calls: 4, input_tokens: 200, output_tokens: 14 })
  const none = await run({ tasks: [task('T1')] }, fakeAgent())
  assert.deepEqual(none.result.triageUsage, { calls: 0, input_tokens: 0, output_tokens: 0 })
})

test('the verify schema carries triageUsage', async () => {
  const r = await run({ tasks: [task('T1')] }, fakeAgent())
  assert.ok(ofRole(r, 'verify')[0].opts.schema.properties.triageUsage)
})

test('verify-and-review-use-epic-base-ref', async () => {
  const epicTask = task('a', { short: 'a', worktree: '/wt/epic-x-a' })
  const r = await run({ name: 'epic-x', epic: 'epic-x', baseRef: 'epic-x', mainCheckout: '/repo', tasks: [epicTask] }, async (prompt, opts) => {
    const role = opts.label.split(':')[1]
    if (role === 'land') return { landed: true, head: 'land-a', conflict: false, verification: { command: 'pytest', passed: true, evidence: '3 passed' }, notes: '' }
    return fakeAgent()(prompt, opts)
  })
  assert.equal(r.error, undefined)
  const v = ofRole(r, 'verify')[0].prompt
  assert.ok(v.includes("--base 'epic-x' "), v)
  assert.ok(!v.includes("--base 'main'"), v)
  const rev = ofRole(r, 'review')[0].prompt
  assert.ok(rev.includes('git diff $(git merge-base HEAD epic-x)..HEAD'), rev)
  assert.ok(!rev.includes('merge-base HEAD main'), rev)
  const land = ofRole(r, 'land')[0].prompt
  assert.ok(land.includes("--base 'epic-x' "), land)
})
