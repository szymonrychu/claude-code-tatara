// The implementer agent (design D5): plan-execute's implementation and fixer calls
// run as workbench:implementer at their per-call model, the generic method lives
// in agents/implementer.md, and the impl and fix prompts carry only per-call inputs
// (the scope-auditor pattern of plan-execute-epic-audit.test.mjs).
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { test } from 'node:test'
import { fileURLToPath } from 'node:url'
import { runWorkflow } from './harness.mjs'

const SCRIPT = fileURLToPath(new URL('../plan-execute.js', import.meta.url))
const AGENT_FILE = fileURLToPath(new URL('../../agents/implementer.md', import.meta.url))
const BRIEF = { what: 'a plugin', how: 'workflows and hooks', why: 'reliable delivery' }

const task = (id, extra = {}) => ({
  id,
  title: `task ${id}`,
  repo: 'api',
  worktree: `/wt/${id}`,
  requirement: `requirement for ${id}`,
  value: 'worth it',
  files: [`src/${id}-a.py`, `src/${id}-b.py`, `tests/test_${id}.py`],
  review: 'full',
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
const okMerge = { merged: true, conflict: false, head: 'def456', verification: { command: 'x', passed: true, evidence: 'ok' } }
const finding = {
  severity: 'high',
  file: 'src/a.py',
  line: 10,
  summary: 'the notifier drops errors on the floor',
  requirement: 'nothing is silently discarded by the notifier',
}

// The first review raises one finding and the second is clean: one impl call and one fix call per task.
function fakeAgent() {
  return async (prompt, opts) => {
    const [, role, rest] = opts.label.split(':')
    if (role === 'impl' || role === 'fix') return deliverable(rest.split('#')[0])
    if (role === 'review') return { filesRead: ['src/a.py'], ...(opts.label.endsWith('#1') ? { clean: false, findings: [finding] } : { clean: true, findings: [] }) }
    if (role === 'verify') return okVerify
    if (role === 'merge') return okMerge
    if (role === 'audit') return { complete: true, missing: [] }
    return {}
  }
}
const run = (args) => runWorkflow(SCRIPT, { args: { brief: BRIEF, ...args }, agent: fakeAgent() })
const ofRole = (r, role) => r.calls.filter((c) => c.opts.label.split(':')[1] === role)

// One sentinel phrase per block that moved out of implPrompt and fixPrompt. Each
// must be gone from both prompts and present in agents/implementer.md.
const MOVED = [
  'Do not call the built-in EnterWorktree', // tree rules
  'is not that checkout, stop and report', // own-checkout-only
  'never pass `git -C` a path outside your own tree', // staying in your own tree
  'Implement every part of the requirement', // Rules
  'the interesting 80%', // Rules
  'Boy scout rule', // boy scout
  'Write the test FIRST', // Test-driven
  'Red evidence is part of the deliverable', // Test-driven, red evidence
  'Never report a pass you did not observe', // Verify before returning
  '`complete: true` requires `verification.passed: true`', // Verify before returning
  'Do not push or merge', // Committing
  'tried and could not deliver', // the undelivered rule
  'a parallel reimplementation is not', // REUSE_RULES
  'parking wording is never accepted', // DELIVERABLE_FIELDS
  'Context ceiling - hand off, do not push on', // CEILING
  'tool calls', // CEILING, the tool-call budget
  'trimmed to the last 30 lines', // REPORT_CAP
  'the reviewer is not authoritative', // fixer: judge each finding
  'failing test that reproduces each real finding', // fixer: failing test first
]

const runWithFix = (extra = {}) =>
  run({
    tasks: [task('T1', extra)],
    contextPack: '/tmp/pack.md',
    designDoc: 'docs/design.md',
    planDoc: 'docs/plan.md',
    doNotBuild: [{ name: 'a second cache', reason: 'the first one covers it' }],
    approvals: [{ id: 'A1', text: 'the notifier never drops errors', tasks: ['T1'] }],
  })

test('impl and fix calls run under workbench:implementer', async () => {
  const r = await runWithFix()
  assert.equal(r.error, undefined)
  const impl = ofRole(r, 'impl')
  const fix = ofRole(r, 'fix')
  assert.equal(impl.length, 1)
  assert.equal(fix.length, 1)
  for (const c of [...impl, ...fix]) assert.equal(c.opts.agentType, 'workbench:implementer', c.opts.label)
})

test('the other roles never run as the implementer', async () => {
  const r = await runWithFix()
  for (const c of r.calls.filter((x) => !['impl', 'fix'].includes(x.opts.label.split(':')[1]))) {
    assert.notEqual(c.opts.agentType, 'workbench:implementer', c.opts.label)
  }
  for (const c of ofRole(r, 'verify')) assert.equal(c.opts.agentType, 'workbench:verifier', c.opts.label)
  for (const c of ofRole(r, 'audit')) assert.equal(c.opts.agentType, 'workbench:scope-auditor', c.opts.label)
})

test('implementer model is unchanged: sonnet by default, the task model when set', async () => {
  const dflt = await runWithFix()
  for (const c of [...ofRole(dflt, 'impl'), ...ofRole(dflt, 'fix')]) assert.equal(c.opts.model, 'sonnet', c.opts.label)
  const opus = await runWithFix({ model: 'opus' })
  const calls = [...ofRole(opus, 'impl'), ...ofRole(opus, 'fix')]
  assert.equal(calls.length, 2)
  for (const c of calls) assert.equal(c.opts.model, 'opus', c.opts.label)
})

test('a continuation keeps the implementer agent type', async () => {
  let n = 0
  const r = await runWorkflow(SCRIPT, {
    args: { brief: BRIEF, tasks: [task('T1', { review: 'none' })] },
    agent: async (prompt, opts) => {
      const role = opts.label.split(':')[1]
      if (role === 'impl' && ++n === 1) return { ...deliverable('T1'), complete: false, status: 'handoff', handoff: { doneSoFar: 'half', remaining: ['AC2'], nextStep: 'x', testState: 'y', wipCommit: 'abc' } }
      return fakeAgent()(prompt, opts)
    },
  })
  const impl = ofRole(r, 'impl')
  assert.equal(impl.length, 2)
  for (const c of impl) assert.equal(c.opts.agentType, 'workbench:implementer', c.opts.label)
})

test('prompts carry only per-call inputs', async () => {
  const r = await runWithFix({ verify: 'pytest tests/test_T1.py', notes: 'mind the cache', owns: ['notifier'] })
  const [impl] = ofRole(r, 'impl')
  const [fix] = ofRole(r, 'fix')
  const both = [
    '/wt/T1',
    'cd "$(if [ -d "/wt/T1/api" ]',
    'T1',
    'What: a plugin',
    'Value of this task: worth it',
    'requirement for T1',
    'This task delivers approved item(s) A1',
    'You own: notifier',
    'a second cache: the first one covers it',
    'pytest tests/test_T1.py',
    'docs/design.md',
    'docs/plan.md',
  ]
  for (const s of [
    ...both,
    'Repo: api',
    'Task T1: task T1',
    '/tmp/pack.md',
    'src/T1-a.py',
    'mind the cache',
  ]) assert.ok(impl.prompt.includes(s), `impl prompt lacks ${s}`)
  for (const s of [...both, 'the notifier drops errors on the floor', 'src/a.py:10']) assert.ok(fix.prompt.includes(s), `fix prompt lacks ${s}`)
})

test('the impl and fix prompts no longer carry the moved method text', async () => {
  const r = await runWithFix()
  for (const c of [...ofRole(r, 'impl'), ...ofRole(r, 'fix')]) {
    for (const method of MOVED) assert.ok(!c.prompt.includes(method), `${c.opts.label} carries method text: ${method}`)
  }
})

test('agent file holds the implementer method', () => {
  const md = readFileSync(AGENT_FILE, 'utf8')
  for (const method of MOVED) assert.ok(md.includes(method), `agents/implementer.md lacks: ${method}`)
  const front = md.split('\n---')[0]
  assert.match(front, /^---\nname: implementer\n/)
  assert.match(front, /\ndescription: /)
  assert.match(front, /\nmodel: sonnet\b/)
  const tools = front.match(/\ntools: \[(.*)\]/)
  assert.ok(tools, 'tools list missing')
  for (const t of ['Edit', 'Write', 'Bash', 'Read']) assert.ok(tools[1].split(/,\s*/).includes(t), `tools lack ${t}`)
})
