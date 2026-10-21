// The epic-close audit in plan-execute.js: args.audit 'run'|'off' (off by default on
// an epic run), args.auditOnly for the one audit at epic close, and every audit
// dispatch on the scope-auditor agent type at sonnet with the method in the agent.
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { test } from 'node:test'
import { fileURLToPath } from 'node:url'
import { runWorkflow } from './harness.mjs'

const SCRIPT = fileURLToPath(new URL('../plan-execute.js', import.meta.url))
const AUDITOR = fileURLToPath(new URL('../../agents/scope-auditor.md', import.meta.url))
const BRIEF = { what: 'a plugin', how: 'workflows and hooks', why: 'reliable delivery' }
const README = '/repo/docs/plans/in-progress/epic-x/README.md'

const task = (id, extra = {}) => ({
  id,
  title: `task ${id}`,
  repo: 'api',
  worktree: `/wt/epic-x-${id}`,
  requirement: `requirement for ${id}`,
  value: 'worth it',
  files: [`src/${id}-a.py`, `src/${id}-b.py`, `tests/test_${id}.py`],
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
const okVerify = { head: 'abc123', clean: true, command: 'pytest', passed: true, evidence: '3 passed', debtMarkers: [] }

function fakeAgent(audit) {
  return async (prompt, opts) => {
    const [, role] = opts.label.split(':')
    if (role === 'impl' || role === 'fix') { const sh = opts.label.split(':')[2]; return deliverable(sh.startsWith('task-') ? sh.replace(/^task-/, '').toUpperCase() : sh) }
    if (role === 'verify') return okVerify
    if (role === 'review') return { clean: true, findings: [], filesRead: ['src/a.py'] }
    if (role === 'audit') return audit ? audit(prompt, opts) : { complete: true, missing: [] }
    throw new Error(`unexpected agent ${opts.label}`)
  }
}
const run = (args, audit) => runWorkflow(SCRIPT, { args: { brief: BRIEF, ...args }, agent: fakeAgent(audit) })
const ofRole = (r, role) => r.calls.filter((c) => c.opts.label.split(':')[1] === role)

const closing = (extra = {}) => ({
  name: 'epic-x',
  epic: 'epic-x',
  auditOnly: true,
  epicReadme: README,
  tasks: [
    task('parser', {
      short: 'parser',
      branch: 'epic-x-parser',
      verifiedHead: 'aaa111',
      ac: [
        { id: 'AC1', text: 'parses every card', evidence: { kind: 'test', ref: 'tests/test_parser.py::test_all' } },
        { id: 'AC2', text: 'reads like the old one', evidence: { kind: 'judgement' } },
      ],
      acsForAudit: ['AC2'],
    }),
    task('writer', { short: 'writer', branch: 'epic-x-writer', verifiedHead: 'bbb222' }),
  ],
  ...extra,
})

// ---------------------------------------------------------------- args.audit
test('args.audit defaults to run without args.epic: one audit, remediation as today', async () => {
  let n = 0
  const r = await run({ tasks: [task('T1')] }, () =>
    ++n === 1 ? { complete: false, missing: [{ item: 'x', taskId: 'T1', evidence: 'e' }] } : { complete: true, missing: [] },
  )
  assert.equal(r.error, undefined)
  assert.deepEqual(ofRole(r, 'audit').map((c) => c.opts.label), ['pe:audit:scope', 'pe:audit:scope-r2'])
  assert.ok(r.calls.some((c) => c.opts.label === 'pe:impl:task-t1-r1'), 'remediation ran')
})

test('args.audit defaults to off with args.epic: no audit and no remediation', async () => {
  const r = await run({ name: 'epic-x', epic: 'epic-x', tasks: [task('t1', { short: 't1' })] }, () => {
    throw new Error('no audit may run')
  })
  assert.equal(r.error, undefined)
  assert.equal(ofRole(r, 'audit').length, 0)
  assert.ok(!r.calls.some((c) => /-r1/.test(c.opts.label)), 'no remediation')
  assert.equal(r.result.audit, 'off')
  assert.equal(r.result.scopeAudit, null)
  assert.equal(r.result.finished, true)
})

test("args.audit 'off' without an epic dispatches no audit; 'run' with an epic does", async () => {
  const off = await run({ tasks: [task('T1')], audit: 'off' })
  assert.equal(ofRole(off, 'audit').length, 0)
  assert.equal(off.result.finished, true)
  const on = await run({ name: 'epic-x', epic: 'epic-x', tasks: [task('t1', { short: 't1' })], audit: 'run' })
  assert.deepEqual(ofRole(on, 'audit').map((c) => c.opts.label), ['epic-x:audit:scope'])
  assert.equal(on.result.audit, 'run')
})

test('args.audit off still never reports an unverified task as finished', async () => {
  const r = await runWorkflow(SCRIPT, {
    args: { brief: BRIEF, tasks: [task('T1')], audit: 'off' },
    agent: async (prompt, opts) => (opts.label.split(':')[1] === 'verify' ? { ...okVerify, passed: false } : fakeAgent()(prompt, opts)),
  })
  assert.equal(ofRole(r, 'audit').length, 0)
  assert.equal(r.result.finished, false)
})

test('args.audit must be run or off', async () => {
  const r = await run({ tasks: [task('T1')], audit: 'sometimes' })
  assert.equal(r.error && r.error.message, "plan-execute: args.audit must be 'run' or 'off'")
  assert.equal(r.calls.length, 0)
})

// ---------------------------------------------------------------- auditOnly
test('auditOnly needs args.epicReadme', async () => {
  const r = await run(closing({ epicReadme: undefined }))
  assert.equal(r.error && r.error.message, 'plan-execute: args.auditOnly needs args.epicReadme (the epic README path)')
  assert.equal(r.calls.length, 0)
})

test('auditOnly dispatches exactly one audit and no implement, verify, review or remediation', async () => {
  const r = await run(closing(), () => ({ complete: false, missing: [{ item: 'writer lacks the flush', taskId: 'writer', evidence: 'src/w.py:1' }] }))
  assert.equal(r.error, undefined)
  assert.deepEqual(r.calls.map((c) => c.opts.label), ['epic-x:audit:epic'])
})

test('auditOnly returns {auditOnly, gaps, approvals, duplicates} and nothing else', async () => {
  const dup = { part: 'card reader', taskIds: ['parser', 'writer'], evidence: 'src/a.py:read, src/b.py:read' }
  const r = await run(
    closing({ approvals: [{ id: 'A', text: 'cards parse', tasks: ['parser'] }] }),
    () => ({
      complete: false,
      missing: [{ item: 'writer lacks the flush', taskId: 'writer', evidence: 'src/w.py:1' }],
      waveLevel: [{ item: 'branches not merged', evidence: 'git branch --no-merged' }],
      approvals: [{ id: 'A', landed: false, evidence: 'no parser' }],
      duplicates: [dup],
    }),
  )
  assert.equal(r.error, undefined)
  assert.deepEqual(Object.keys(r.result).sort(), ['approvals', 'auditOnly', 'duplicates', 'gaps'])
  assert.equal(r.result.auditOnly, true)
  assert.deepEqual(r.result.gaps, [
    { item: 'writer lacks the flush', evidence: 'src/w.py:1', taskId: 'writer' },
    { item: 'Approved item A not landed: no parser', evidence: 'no parser', taskId: 'parser' },
    { item: 'branches not merged', evidence: 'git branch --no-merged', taskId: null },
  ])
  assert.deepEqual(r.result.approvals, [{ id: 'A', landed: false, evidence: 'no parser' }])
  assert.deepEqual(r.result.duplicates, [dup])
})

test('an un-landed approval is one gap, on the task whose files own the evidence path', async () => {
  const r = await run(
    closing({ approvals: [{ id: 'A', text: 'cards flush', tasks: ['parser', 'writer'] }] }),
    () => ({ complete: false, missing: [], approvals: [{ id: 'A', landed: false, evidence: 'src/writer-a.py:3 never flushes' }] }),
  )
  assert.deepEqual(r.result.gaps, [
    { item: 'Approved item A not landed: src/writer-a.py:3 never flushes', evidence: 'src/writer-a.py:3 never flushes', taskId: 'writer' },
  ])
})

test('an un-landed approval with no owning path goes to the first mapped task that is not clean, never to all', async () => {
  const r = await run(
    closing({ approvals: [{ id: 'A', text: 'cards flush', tasks: ['parser', 'writer'] }] }),
    () => ({ complete: false, missing: [], approvals: [{ id: 'A', landed: false, evidence: 'nothing flushes' }] }),
  )
  assert.deepEqual(r.result.gaps.map((g) => g.taskId), ['parser'])
})

test('a run attributes an un-landed approval to the first non-clean mapped task, one gap per (taskId, item)', async () => {
  const r = await run(
    { tasks: [task('T1'), task('T2')], approvals: [{ id: 'A', text: 'both', tasks: ['T1', 'T2'] }] },
    (prompt, opts) =>
      opts.label === 'pe:audit:scope'
        ? { complete: false, missing: [], approvals: [{ id: 'A', landed: false, evidence: 'missing' }] }
        : { complete: true, missing: [], approvals: [{ id: 'A', landed: true, evidence: 'ok' }] },
  )
  const rem = ofRole(r, 'impl').filter((c) => /-r1/.test(c.opts.label))
  assert.deepEqual(rem.map((c) => c.opts.label), ['pe:impl:task-t1-r1'])
})

test('with the first mapped task clean and the second not, the gap goes to the second, not the first mapped', async () => {
  const base = fakeAgent((prompt, opts) =>
    opts.label === 'pe:audit:scope'
      ? { complete: false, missing: [], approvals: [{ id: 'A', landed: false, evidence: 'missing' }] }
      : { complete: true, missing: [], approvals: [{ id: 'A', landed: true, evidence: 'ok' }] },
  )
  const agent = async (prompt, opts) =>
    opts.label.split(':')[1] === 'review' && /task-t2/.test(opts.label) ? { clean: true, findings: [], filesRead: [], diffRead: false } : base(prompt, opts)
  const r = await runWorkflow(SCRIPT, {
    args: { brief: BRIEF, tasks: [task('T1'), task('T2')], approvals: [{ id: 'A', text: 'both', tasks: ['T1', 'T2'] }] },
    agent,
  })
  const rem = ofRole(r, 'impl').filter((c) => /-r1/.test(c.opts.label))
  assert.deepEqual(rem.map((c) => c.opts.label), ['pe:impl:task-t2-r1'])
})

test('auditOnly with a clean audit returns no gaps', async () => {
  const r = await run(closing())
  assert.deepEqual(r.result, { auditOnly: true, gaps: [], approvals: [], duplicates: [] })
})

test('auditOnly with no auditor result reports the audit itself as the gap', async () => {
  const r = await run(closing(), () => null)
  assert.equal(r.result.auditOnly, true)
  assert.deepEqual(r.result.gaps, [{ item: 'epic-close audit did not run', evidence: 'auditor agent returned nothing', taskId: null }])
})

test('the audit-only prompt carries the README, tasks with branch and verified head, the AC table, the ledger and the duplicate sweep', async () => {
  const r = await run(closing({ approvals: [{ id: 'A', text: 'cards parse', tasks: ['parser', 'writer'] }] }))
  const p = r.calls[0].prompt
  assert.ok(p.includes(`Epic README (its Goals and Non-goals are the definition of done): ${README}`))
  assert.ok(p.includes('- parser: task parser | worktree /wt/epic-x-parser | branch epic-x-parser | verified head aaa111'))
  assert.ok(p.includes('- writer: task writer | worktree /wt/epic-x-writer | branch epic-x-writer | verified head bbb222'))
  assert.ok(p.includes('=== ACCEPTANCE CONDITIONS ==='))
  assert.ok(p.includes('| parser | AC1 | parses every card | test: tests/test_parser.py::test_all | verifier settled |'))
  assert.ok(p.includes('| parser | AC2 | reads like the old one | judgement | open: judge it |'))
  assert.ok(p.includes('| writer | (none) | | | |'))
  assert.ok(p.includes('=== APPROVED ITEMS (the ledger) ===\n- A (tasks parser, writer): cards parse'))
  assert.ok(p.includes('Run the duplicate sweep across these task trees.'))
  assert.ok(p.includes('Legal taskId values: parser, writer'))
  assert.ok(p.includes('never edit or commit'))
})

test('the audit-only prompt carries only inputs, never the method text', async () => {
  const r = await run(closing())
  assert.equal(r.calls[0].opts.label, 'epic-x:audit:epic')
  const p = r.calls[0].prompt
  for (const method of ['completeness critic', 'Verify by reading the actual files', 'built more than once', 'merge-base --is-ancestor']) {
    assert.ok(!p.includes(method), `audit-only prompt carries method text: ${method}`)
  }
})

// ---------------------------------------------------------------- every audit dispatch
test('every audit dispatch runs as workbench:scope-auditor on sonnet, even after opus tasks', async () => {
  let n = 0
  const runMode = await run({ tasks: [task('T1', { model: 'opus' }), task('T2')] }, () =>
    ++n === 1 ? { complete: false, missing: [{ item: 'x', taskId: 'T1', evidence: 'e' }] } : { complete: true, missing: [] },
  )
  const only = await run(closing({ tasks: [task('parser', {
      short: 'parser', model: 'opus' })] }))
  const audits = [...ofRole(runMode, 'audit'), ...ofRole(only, 'audit')]
  assert.equal(audits.length, 3)
  for (const c of audits) {
    assert.equal(c.opts.agentType, 'workbench:scope-auditor', c.opts.label)
    assert.equal(c.opts.model, 'sonnet', c.opts.label)
  }
})

test('the run-mode audit prompts carry only inputs, never the method text', async () => {
  let n = 0
  const r = await run({ tasks: [task('T1')] }, () =>
    ++n === 1 ? { complete: false, missing: [{ item: 'x', taskId: 'T1', evidence: 'e' }] } : { complete: true, missing: [] },
  )
  for (const c of ofRole(r, 'audit')) {
    for (const method of ['completeness critic', 'Verify by reading the actual files', 'they are claims, not evidence']) {
      assert.ok(!c.prompt.includes(method), `${c.opts.label} carries method text: ${method}`)
    }
  }
})

// ---------------------------------------------------------------- the agent
test('scope-auditor.md carries the AC table, ledger-by-id, duplicate sweep, ancestry and epic-close method', () => {
  const md = readFileSync(AUDITOR, 'utf8')
  const flat = md.replace(/\s+/g, ' ')
  assert.match(md, /^---\nname: scope-auditor\n/)
  assert.match(md, /\nmodel: sonnet\n/)
  for (const s of [
    'completeness critic',
    'they are claims, not evidence',
    '## The AC table',
    'open: judge it',
    'A `met: false` acceptance condition is a `missing` entry',
    '## The ledger by id',
    'report every approved item by its id',
    '## The duplicate sweep',
    'built more than once',
    'A `reimplemented` entry with a reason that holds is not a duplicate',
    'git merge-base --is-ancestor <dependency branch> HEAD',
    '## Epic close',
    'Goals and Non-goals',
    'gaps become new tasks in the same epic, never follow-ups',
  ]) {
    assert.ok(flat.includes(s), `scope-auditor.md lacks: ${s}`)
  }
})

const SKILL_URL = new URL('../../skills/start-development/SKILL.md', import.meta.url)

// SKILL.md plus the reference files its blocks moved to (references first, so a section heading
// resolves to its full text rather than the pointer left in SKILL.md).
const readSkillWithReferences = (skillUrl) => {
  const refs = ['phases-1-3.md', 'phase-4-execute.md', 'phases-5-7.md', 'non-negotiables.md']
  return [...refs.map((n) => readFileSync(fileURLToPath(new URL(`references/${n}`, skillUrl.href.replace(/SKILL\.md$/, ''))), 'utf8')), readFileSync(fileURLToPath(skillUrl), 'utf8')].join('\n')
}

test('SKILL.md Phase 4 names the cost mechanics and the Scope section the ledger rule', () => {
  const md = readSkillWithReferences(SKILL_URL)
  const phase4 = md.split('## Phase 4 - Execute')[1].split('## Phase 5')[0]
  for (const w of ['verify-task.py', 'light', 'panel', 'gate-repeat', 'processOnly']) assert.ok(phase4.includes(w), `Phase 4 lacks ${w}`)
  const scope = md.split('## Scope is not negotiable')[1].split('\n## ')[0]
  for (const w of ['acceptance condition', 'undelivered', 'strikes the ledger item']) assert.ok(scope.includes(w), `Scope lacks ${w}`)
  assert.ok(!/deferred/i.test(md.replace(/never deferred/gi, '')), 'SKILL.md still says deferred')
})
