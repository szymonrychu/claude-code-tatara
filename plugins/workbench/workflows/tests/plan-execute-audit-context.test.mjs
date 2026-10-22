// Audit context (D11, D12): task files instead of inlined requirements, the settled AC rows on
// one haiku auditor call, and the mechanical roles (merge, land) on haiku.
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { test } from 'node:test'
import { fileURLToPath } from 'node:url'
import { runWorkflow } from './harness.mjs'

const SCRIPT = fileURLToPath(new URL('../plan-execute.js', import.meta.url))
const AUDITOR = fileURLToPath(new URL('../../agents/scope-auditor.md', import.meta.url))
const BRIEF = { what: 'a plugin', how: 'workflows and hooks', why: 'reliable delivery' }
const README = '/repo/docs/plans/in-progress/epic-x/README.md'
const BIG = 'R'.repeat(900)

const task = (id, extra = {}) => ({
  id, short: id, title: `task ${id}`, repo: 'api', worktree: `/wt/epic-x-${id}`, requirement: BIG, value: 'worth it',
  files: [`src/${id}.py`], branch: `epic-x-${id}`, verifiedHead: `h-${id}`,
  taskFile: `/repo/docs/plans/in-progress/epic-x/tasks/${id}.md`, ...extra,
})
const settledAc = (n) => [{ id: `AC${n}`, text: 'does it', evidence: { kind: 'test', ref: `tests/test_${n}.py::test_it` } }]
const closing = (tasks) => ({ brief: BRIEF, name: 'epic-x', epic: 'epic-x', auditOnly: true, epicReadme: README, tasks })
const audits = (r) => r.calls.filter((c) => c.opts.label.split(':')[1] === 'audit')

test('epic audit prompt lists task files and inlines no requirement text', async () => {
  const tasks = Array.from({ length: 21 }, (_, i) => task(`t${i}`, { ac: settledAc(i), acsForAudit: ['AC0'] }))
  const r = await runWorkflow(SCRIPT, { args: closing(tasks), agent: async () => ({ complete: true, missing: [] }) })
  const sonnet = audits(r).find((c) => c.opts.model === 'sonnet')
  assert.ok(sonnet.prompt.length < 10000, `prompt is ${sonnet.prompt.length} chars`)
  assert.ok(!sonnet.prompt.includes(BIG.slice(0, 50)))
  assert.match(sonnet.prompt, /- t0: task t0 \| tree \/wt\/epic-x-t0 \| task file \/repo\/docs\/plans\/in-progress\/epic-x\/tasks\/t0\.md/)
  assert.match(sonnet.prompt, /## Requirement/)
  assert.match(sonnet.prompt, /## Acceptance conditions/)
})

test('without taskFile the epic audit prompt inlines requirements as before', async () => {
  const r = await runWorkflow(SCRIPT, {
    args: closing([task('a', { taskFile: undefined }), task('b')]),
    agent: async () => ({ complete: true, missing: [] }),
  })
  assert.ok(audits(r)[0].prompt.includes(`a requirement: ${BIG}`))
})

test('per-run audit prompt lists task files and drops the requirement line', async () => {
  const r = await runWorkflow(SCRIPT, {
    args: { brief: BRIEF, tasks: [task('t1', { verifiedHead: undefined })], audit: 'run' },
    agent: async (p, o) => {
      const role = o.label.split(':')[1]
      if (role === 'impl') return { taskId: 't1', complete: true, summary: 's', filesChanged: ['a'], branch: 'b', tests: { added: ['t'], wroteTestFirst: true, red: { command: 'c', output: 'FAILED x' } }, verification: { command: 'c', passed: true, evidence: 'ok' } }
      if (role === 'verify') return { head: 'abc', clean: true, command: 'c', passed: true, evidence: 'ok', debtMarkers: [] }
      if (role === 'review') return { clean: true, findings: [], filesRead: ['a'] }
      return { complete: true, missing: [] }
    },
  })
  assert.equal(r.error, undefined)
  const p = audits(r)[0].prompt
  assert.match(p, /task file \/repo\/docs\/plans\/in-progress\/epic-x\/tasks\/t1\.md/)
  assert.ok(!p.includes(BIG.slice(0, 50)))
})

test('settled rows go to one haiku call, open rows and the ledger to sonnet, results merge', async () => {
  const tasks = [
    task('s1', { ac: settledAc(1) }),
    task('s2', { ac: settledAc(2) }),
    task('o1', { ac: [{ id: 'AC3', text: 'judge', evidence: { kind: 'judgement' } }], acsForAudit: ['AC3'] }),
    task('sub', { ac: [{ id: 'AC4', text: 'x', evidence: { kind: 'test', ref: 't' }, matchedBy: 'substring' }] }),
  ]
  const r = await runWorkflow(SCRIPT, {
    args: closing(tasks),
    agent: async (p, o) =>
      o.model === 'haiku'
        ? { complete: false, missing: [{ item: 'ref gone', taskId: 's1', evidence: 'e' }] }
        : { complete: false, missing: [{ item: 'judged', taskId: 'o1', evidence: 'e2' }] },
  })
  const a = audits(r)
  assert.equal(a.length, 2)
  const h = a.find((c) => c.opts.model === 'haiku')
  const s = a.find((c) => c.opts.model === 'sonnet')
  assert.equal(h.opts.label, 'epic-x:audit:settled')
  assert.match(h.prompt, /\| s1 \| AC1/)
  assert.match(h.prompt, /\| s2 \| AC2/)
  assert.ok(!/\| o1 \| AC3/.test(h.prompt) && !/\| sub \| AC4/.test(h.prompt))
  assert.match(s.prompt, /\| o1 \| AC3/)
  assert.match(s.prompt, /\| sub \| AC4/)
  assert.ok(!/\| s1 \| AC1/.test(s.prompt))
  assert.deepEqual(r.result.gaps.map((g) => g.item).sort(), ['judged', 'ref gone'])
})

test('no settled rows: no haiku call', async () => {
  const r = await runWorkflow(SCRIPT, {
    args: closing([task('o1', { ac: [{ id: 'AC3', text: 'j', evidence: { kind: 'judgement' } }], acsForAudit: ['AC3'] })]),
    agent: async () => ({ complete: true, missing: [] }),
  })
  assert.deepEqual(audits(r).map((c) => c.opts.model), ['sonnet'])
})

test('the scope-auditor agent documents task-file reading and the settled-rows mode', () => {
  const md = readFileSync(AUDITOR, 'utf8')
  assert.match(md, /## Reading task files/)
  assert.match(md, /settled-rows mode/i)
})

// ---- merge and land on haiku
const EPIC = { name: 'epic-x', epic: 'epic-x', baseRef: 'epic-x', mainCheckout: '/repo' }
const lt = (id, extra = {}) => ({ id, title: `task ${id}`, repo: 'api', worktree: `/wt/epic-x-${id}`, requirement: 'req', value: 'v', short: id, files: [`src/${id}.py`], verify: 'pytest', review: 'full', ...extra })
const verification = { command: 'pytest', passed: true, evidence: '3 passed' }
const landAgent = (land) => async (p, o) => {
  const [, role, rest] = o.label.split(':')
  const id = (rest || '').split(/[#+]/)[0]
  if (role === 'impl') return { taskId: id, complete: true, summary: 's', filesChanged: ['a'], branch: `epic-x-${id}`, tests: { added: ['t'], wroteTestFirst: true, red: { command: 'c', output: 'FAILED x' } }, verification: { command: 'c', passed: true, evidence: 'ok' } }
  if (role === 'verify') return { head: 'abc', clean: true, command: 'pytest', passed: true, evidence: 'ok', debtMarkers: [] }
  if (role === 'review') return { clean: true, findings: [], filesRead: ['a'] }
  if (role === 'land') return land(o)
  if (role === 'audit') return { complete: true, missing: [] }
  return { verdicts: [], repeated: [] }
}
const lands = (r) => r.calls.filter((c) => c.opts.label.split(':')[1] === 'land')

test('land runs on haiku', async () => {
  const r = await runWorkflow(SCRIPT, { args: { brief: BRIEF, ...EPIC, tasks: [lt('a')] }, agent: landAgent(() => ({ landed: true, head: 'h', conflict: false, verification, notes: '' })) })
  assert.deepEqual(lands(r).map((c) => c.opts.model), ['haiku'])
})

test('a land conflict is re-dispatched once on sonnet', async () => {
  const r = await runWorkflow(SCRIPT, {
    args: { brief: BRIEF, ...EPIC, tasks: [lt('a')] },
    agent: landAgent((o) => (o.model === 'haiku' ? { landed: false, head: '', conflict: true, verification, notes: 'src/a.py' } : { landed: true, head: 'h', conflict: false, verification, notes: '' })),
  })
  assert.deepEqual(lands(r).map((c) => c.opts.model), ['haiku', 'sonnet'])
  assert.notEqual(r.result.tasks.find((t) => t.id === 'a').stopped, 'land-failed')
})

test('a conflict on the sonnet retry too ends land-failed after exactly two dispatches', async () => {
  const r = await runWorkflow(SCRIPT, {
    args: { brief: BRIEF, ...EPIC, tasks: [lt('a')] },
    agent: landAgent(() => ({ landed: false, head: '', conflict: true, verification, notes: 'src/a.py' })),
  })
  assert.equal(lands(r).length, 2)
  assert.equal(r.result.tasks.find((t) => t.id === 'a').stopped, 'land-failed')
})
