// In-run landing (D4, Q1): with args.epic and args.mainCheckout, every released task is
// landed on the epic integration branch by one serialised worktree-merger agent before
// any dependent starts; dependents merge the epic branch instead of each dependency branch.
import assert from 'node:assert/strict'
import { test } from 'node:test'
import { fileURLToPath } from 'node:url'
import { runWorkflow, TEST_PLUGIN_ROOT } from './harness.mjs'

const SCRIPT = fileURLToPath(new URL('../plan-execute.js', import.meta.url))
const BRIEF = { what: 'a plugin', how: 'workflows and hooks', why: 'reliable delivery' }
const MAIN = '/repo'
const EPIC = { name: 'epic-x', epic: 'epic-x', baseRef: 'epic-x', mainCheckout: MAIN }

const task = (id, extra = {}) => ({
  id,
  title: `task ${id}`,
  repo: 'api',
  worktree: `/wt/epic-x-${id}`,
  requirement: `requirement for ${id}`,
  value: 'worth it',
  short: id,
  files: [`src/${id}-a.py`, `tests/test_${id}.py`],
  verify: `pytest tests/test_${id}.py`,
  review: 'full',
  ...extra,
})
const red = { command: 'pytest', output: 'FAILED tests/test_a.py::test_x' }
const deliverable = (id) => ({
  taskId: id,
  complete: true,
  summary: 'did it',
  filesChanged: ['src/a.py'],
  branch: `epic-x-${id}`,
  tests: { added: ['tests/test_a.py'], wroteTestFirst: true, red },
  verification: { command: 'pytest tests/test_a.py', passed: true, evidence: '3 passed' },
})
const okVerify = { head: 'abc', clean: true, command: 'pytest', passed: true, evidence: '3 passed', debtMarkers: [] }
const okLand = (id) => ({
  landed: true,
  head: `land-${id}`,
  conflict: false,
  verification: { command: `pytest tests/test_${id}.py`, passed: true, evidence: '3 passed' },
  notes: 'merged 1 commit(s)',
})
const finding = (summary) => ({ severity: 'high', kind: 'wrong', file: 'src/a.py', line: 1, summary, requirement: 'r', evidence: 'e' })
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

// b[id]: { land(id) -> result, landDelay, escalate, blocked, failFirstVerify, implDelay }.
// events records starts and ends in order, so tests can check what happened before what.
function fakeAgent(b = {}) {
  const events = []
  let active = 0
  let maxActive = 0
  const fn = async (prompt, opts) => {
    const [, role, rest] = opts.label.split(':')
    const id = rest.split(/[#+]/)[0]
    const n = Number(rest.split('#')[1] || 0)
    const o = b[id] || {}
    events.push(`${role}-start:${id}`)
    if (role === 'impl' || role === 'fix') {
      if (o.implDelay) await sleep(o.implDelay)
      return deliverable(id)
    }
    if (role === 'verify') {
      if (o.blocked) return { ...okVerify }
      return o.failFirstVerify && n === 1 ? { ...okVerify, passed: false, exit: 1, evidence: '1 failed' } : okVerify
    }
    if (role === 'review') {
      if (o.blocked) return { clean: false, findings: [], filesRead: ['src/a.py'], blocked: { reason: 'needs a credential', whoCanClear: 'the user' } }
      if (o.escalate) return { clean: false, findings: [finding(`bug ${opts.label}`)], filesRead: ['src/a.py'] }
      return { clean: true, findings: [], filesRead: ['src/a.py'] }
    }
    if (role === 'false-finding') return { verdicts: [{ index: 0, verdict: 'real', reason: 'unproven' }] }
    if (role === 'triage') return { repeated: [] }
    if (role === 'land') {
      active++
      maxActive = Math.max(maxActive, active)
      await sleep(o.landDelay ?? 5)
      active--
      events.push(`land-end:${id}`)
      return o.land ? o.land(id) : okLand(id)
    }
    if (role === 'audit') return { complete: true, missing: [] }
    throw new Error(`unexpected agent ${opts.label}`)
  }
  return { fn, events, max: () => maxActive }
}
const run = async (args, behaviours) => {
  const a = fakeAgent(behaviours)
  const r = await runWorkflow(SCRIPT, { args: { brief: BRIEF, ...args }, agent: a.fn })
  return { ...r, events: a.events, maxActive: a.max() }
}
const ofRole = (r, role, id) => r.calls.filter((c) => c.opts.label.split(':')[1] === role && (!id || c.opts.label.split(':')[2].split(/[#+]/)[0] === id))
const result = (r, id) => r.result.tasks.find((t) => t.id === id)
const MERGE_PY = `'${TEST_PLUGIN_ROOT}/skills/worktree-merge/scripts/merge.py'`

test('land-dispatches-merge-into-epic', async () => {
  const r = await run({ ...EPIC, tasks: [task('a')] })
  assert.equal(r.error, undefined)
  const land = ofRole(r, 'land')
  assert.equal(land.length, 1)
  const { opts, prompt } = land[0]
  assert.equal(opts.label, 'epic-x:land:a')
  assert.equal(opts.phase, 'Land')
  assert.equal(opts.agentType, 'workbench:worktree-merger')
  assert.equal(opts.model, 'haiku')
  assert.deepEqual(opts.schema.required, ['landed', 'head', 'conflict', 'verification', 'notes'])
  assert.equal(opts.schema.properties.landed.type, 'boolean')
  assert.equal(opts.schema.properties.head.type, 'string')
  assert.equal(opts.schema.properties.conflict.type, 'boolean')
  assert.deepEqual(opts.schema.properties.verification.required, ['command', 'passed', 'evidence'])
  assert.equal(opts.schema.properties.notes.type, 'string')
  const cmd = `cd '${MAIN}' && python3 ${MERGE_PY} --name 'epic-x-a' --base 'epic-x' --keep --no-suites --verify 'pytest tests/test_a.py'`
  assert.ok(prompt.includes(cmd), prompt)
  assert.ok(!prompt.includes('--repo'), prompt)
  assert.match(prompt, /never run `git checkout`/i)
  // the land runs after the task settled clean and verified
  assert.ok(r.events.indexOf('land-start:a') > r.events.lastIndexOf('review-start:a'))
})

test('land-dispatches-merge-into-epic: a component tree passes --repo', async () => {
  const r = await run({ ...EPIC, tasks: [task('a', { worktree: '/wt/epic-x-a/api' })] })
  assert.equal(r.error, undefined)
  const prompt = ofRole(r, 'land')[0].prompt
  assert.ok(prompt.includes(`--name 'epic-x-a' --base 'epic-x' --repo 'api' --keep --no-suites --verify 'pytest tests/test_a.py'`), prompt)
})

test('land-dependent-merges-epic-branch', async () => {
  const r = await run({ ...EPIC, tasks: [task('a'), task('b', { dependsOn: ['a'] }), task('c', { dependsOn: ['a', 'b'] })] })
  assert.equal(r.error, undefined)
  assert.ok(r.events.indexOf('land-end:a') < r.events.indexOf('impl-start:b'), r.events.join(' '))
  assert.ok(r.events.indexOf('land-end:b') < r.events.indexOf('impl-start:c'), r.events.join(' '))
  for (const id of ['b', 'c']) {
    const p = ofRole(r, 'impl', id)[0].prompt
    assert.ok(p.includes(`git merge --no-edit epic-x\``), p)
    assert.ok(!/git merge --no-edit epic-x-/.test(p), p)
    assert.equal(p.split('git merge --no-edit').length - 1, 1, 'one merge line for all same-repo dependencies')
    assert.ok(p.includes(`cd "$D" && [ "$(git rev-parse --show-toplevel)" = "$(pwd -P)" ]`), p)
    assert.ok(p.includes(`/wt/epic-x-${id}`), p)
  }
  const c = ofRole(r, 'impl', 'c')[0].prompt
  assert.match(c, /FIRST, before anything else/)
  assert.ok(c.includes('a (task a)') && c.includes('b (task b)'), c)
})

test('land-dependent-merges-epic-branch: a cross-repo dependency still lands with the integration', async () => {
  const r = await run({ ...EPIC, tasks: [task('a', { repo: 'web' }), task('b', { dependsOn: ['a'] })] })
  assert.equal(r.error, undefined)
  const p = ofRole(r, 'impl', 'b')[0].prompt
  assert.match(p, /- a \(task a\): in web on branch epic-x-a; it lands with the integration/)
  assert.ok(!p.includes('git merge --no-edit'), p)
})

test('land-serialised-one-at-a-time', async () => {
  const r = await run({ ...EPIC, tasks: [task('a'), task('b'), task('c'), task('d', { dependsOn: ['a'] })] }, {
    a: { landDelay: 20 },
    b: { landDelay: 20 },
    c: { landDelay: 20 },
  })
  assert.equal(r.error, undefined)
  assert.equal(ofRole(r, 'land').length, 4)
  assert.equal(r.maxActive, 1)
  const order = r.events.filter((e) => e.startsWith('land-'))
  for (let i = 0; i < order.length; i += 2) {
    assert.equal(order[i].replace('land-start:', ''), order[i + 1].replace('land-end:', ''), order.join(' '))
  }
})

test('land-failure-escalates-and-fails-dependents', async () => {
  const failed = (id) => ({ ...okLand(id), landed: false, conflict: true, verification: { command: 'pytest', passed: false, evidence: 'conflict in src/a.py' }, notes: 'rebase conflict: src/a.py' })
  const r = await run({ ...EPIC, tasks: [task('a'), task('b', { dependsOn: ['a'] }), task('c')] }, { a: { land: failed } })
  assert.equal(r.error, undefined)
  const a = result(r, 'a')
  assert.equal(a.clean, false)
  assert.equal(a.stopped, 'land-failed')
  assert.deepEqual(a.land, failed('a'))
  const e = r.result.escalated.find((x) => x.id === 'a')
  assert.equal(e.reason, 'land-failed')
  assert.deepEqual(e.land, failed('a'))
  assert.equal(result(r, 'b').stopped, 'dependency-failed')
  assert.deepEqual(r.result.escalated.find((x) => x.id === 'b').waitingOn, ['a'])
  assert.equal(ofRole(r, 'impl', 'b').length, 0)
  assert.deepEqual(r.result.landed, [{ id: 'c', head: 'land-c' }])
  assert.equal(r.result.finished, false)
})

test('land-failure-escalates-and-fails-dependents: landed without a passing verify, or no result, is a failure', async () => {
  const unverified = (id) => ({ ...okLand(id), verification: { command: 'pytest', passed: false, evidence: '1 failed' } })
  const r = await run({ ...EPIC, tasks: [task('a'), task('b', { dependsOn: ['a'] }), task('c'), task('d', { dependsOn: ['c'] })] }, {
    a: { land: unverified },
    c: { land: () => null },
  })
  assert.equal(r.error, undefined)
  assert.equal(result(r, 'a').stopped, 'land-failed')
  assert.equal(result(r, 'c').stopped, 'land-failed')
  assert.equal(result(r, 'c').land, null)
  assert.equal(result(r, 'b').stopped, 'dependency-failed')
  assert.equal(result(r, 'd').stopped, 'dependency-failed')
  assert.deepEqual(r.result.landed, [])
})

test('land-skips-escalated-tasks', async () => {
  const r = await run({ ...EPIC, tasks: [task('a'), task('b'), task('c', { dependsOn: ['a'] })] }, {
    a: { escalate: true },
    b: { blocked: true },
  })
  assert.equal(r.error, undefined)
  assert.ok(['round-cap', 'no-progress'].includes(result(r, 'a').stopped), result(r, 'a').stopped)
  assert.equal(result(r, 'b').stopped, 'blocked')
  assert.equal(ofRole(r, 'land').length, 0)
  assert.equal(result(r, 'c').stopped, 'dependency-failed')
  assert.deepEqual(r.result.landed, [])
})

test('land-records-landed-head', async () => {
  const r = await run({ ...EPIC, tasks: [task('a'), task('b', { dependsOn: ['a'] })] })
  assert.equal(r.error, undefined)
  assert.equal(result(r, 'a').verification.head, 'land-a')
  assert.equal(result(r, 'a').verification.passed, true)
  assert.equal(result(r, 'a').verified, true)
  assert.equal(result(r, 'a').clean, true)
  assert.equal(result(r, 'a').stopped, null)
  assert.deepEqual(r.result.landed, [{ id: 'a', head: 'land-a' }, { id: 'b', head: 'land-b' }])
  assert.equal(r.result.finished, true)
})

test('land-off-without-epic-or-main-checkout', async () => {
  // epic without mainCheckout: dependency-branch merges, no landing
  const noMain = await run({ name: 'epic-x', epic: 'epic-x', baseRef: 'epic-x', tasks: [task('a'), task('b', { dependsOn: ['a'] })] })
  assert.equal(noMain.error, undefined)
  assert.equal(ofRole(noMain, 'land').length, 0)
  assert.ok(ofRole(noMain, 'impl', 'b')[0].prompt.includes('git merge --no-edit epic-x-a`'))
  assert.equal('landed' in noMain.result, false)
  // mainCheckout without epic: the same
  const plain = (id, extra) => task(id, { short: undefined, worktree: `/wt/${id}`, ...extra })
  const noEpic = await run({ mainCheckout: MAIN, audit: 'off', tasks: [plain('a'), plain('b', { dependsOn: ['a'] })] })
  assert.equal(noEpic.error, undefined)
  assert.equal(ofRole(noEpic, 'land').length, 0)
  assert.ok(ofRole(noEpic, 'impl').find((c) => c.opts.label === 'pe:impl:task-b').prompt.includes('git merge --no-edit epic-x-task-a`'))
  assert.equal('landed' in noEpic.result, false)
  // auditOnly with both set: one audit, nothing lands
  const close = await run({ ...EPIC, auditOnly: true, epicReadme: '/repo/docs/plans/in-progress/epic-x/README.md', tasks: [task('a')] })
  assert.equal(close.error, undefined)
  assert.equal(ofRole(close, 'land').length, 0)
  assert.deepEqual(close.calls.map((c) => c.opts.label.split(':')[1]), ['audit'])
})

test('land-off-without-epic-or-main-checkout: mainCheckout must be an absolute path', async () => {
  for (const bad of ['repo', 42, '']) {
    const r = await run({ ...EPIC, mainCheckout: bad, tasks: [task('a')] })
    assert.match(String(r.error && r.error.message), /mainCheckout/)
    assert.equal(r.calls.length, 0)
  }
})

test('land-every-role-shares-the-task-tree', async () => {
  const r = await run({ ...EPIC, tasks: [task('a'), task('b')] }, { a: { failFirstVerify: true } })
  assert.equal(r.error, undefined)
  const roles = ['impl', 'verify', 'review', 'fix', 'land']
  for (const role of roles) {
    const calls = ofRole(r, role, 'a')
    assert.ok(calls.length >= 1, `a ran a ${role} agent`)
    for (const c of calls) {
      assert.ok(c.prompt.includes('/wt/epic-x-a'), `${c.opts.label} names the task tree`)
      assert.ok(!c.prompt.includes('/wt/epic-x-b'), `${c.opts.label} names no other tree`)
    }
  }
  const land = ofRole(r, 'land', 'a')[0].prompt
  assert.ok(land.includes(`Main checkout: ${MAIN}`), land)
  assert.ok(land.includes('Task worktree: /wt/epic-x-a'), land)
})

test('land-quotes-name-base-and-repo', async () => {
  const r = await run({ ...EPIC, baseRef: 'epic-x', tasks: [task('a', { repo: 'ap i', worktree: '/wt/epic-x-a/ap i' })] })
  const prompt = ofRole(r, 'land')[0].prompt
  assert.ok(prompt.includes(`--name 'epic-x-a' --base 'epic-x' --repo 'ap i' --keep`), prompt)
})
