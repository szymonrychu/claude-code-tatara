// hook-probe.js dispatches four probe agents so a real run shows which workbench
// hooks fire inside Workflow subagents (design D14).
import assert from 'node:assert/strict'
import { test } from 'node:test'
import { fileURLToPath } from 'node:url'
import { runWorkflow } from './harness.mjs'

const SCRIPT = fileURLToPath(new URL('../hook-probe.js', import.meta.url))
const WT = '/repo/.claude/worktrees/probe-1'

const results = {
  'probe:recorder': { recordFound: true, recordCommand: 'pytest --version' },
  'probe:stop-guard': { sawBlock: true, reasonExcerpt: 'uncommitted file', committed: true },
  'probe:bash-guard': { blocked: true, message: 'guard-bash: x' },
  'probe:agent-type': { ok: true },
}

const fake = (over = {}) => async (_prompt, opts) => {
  if (opts.label in over) {
    const v = over[opts.label]
    if (v instanceof Error) throw v
    return v
  }
  return results[opts.label]
}
const run = (args, agent = fake()) => runWorkflow(SCRIPT, { args, agent })
const call = (r, label) => r.calls.find((c) => c.opts.label === label)

test('four agents in order with phases, sonnet and low effort', async () => {
  const r = await run({ worktree: WT })
  assert.equal(r.error, undefined)
  assert.deepEqual(r.calls.map((c) => c.opts.label), ['probe:recorder', 'probe:stop-guard', 'probe:bash-guard', 'probe:agent-type'])
  assert.deepEqual(r.calls.map((c) => c.opts.phase), ['Recorder', 'Stop guard', 'Bash guard', 'Agent type'])
  for (const c of r.calls) {
    assert.equal(c.opts.model, 'sonnet')
    assert.equal(c.opts.effort, 'low')
  }
  assert.deepEqual(r.result, {
    recorder: results['probe:recorder'],
    stopGuard: results['probe:stop-guard'],
    bashGuard: results['probe:bash-guard'],
    agentType: { resolved: true, name: 'workbench:verifier' },
  })
  assert.equal(r.logs.length >= 4, true)
})

test('prompts carry the probe commands', async () => {
  const r = await run({ worktree: WT })
  const rec = call(r, 'probe:recorder').prompt
  assert.match(rec, /pytest --version/)
  assert.match(rec, /workbench-verify\.json/)
  assert.ok(rec.includes(WT))
  const stop = call(r, 'probe:stop-guard').prompt
  assert.match(stop, /probe\.txt/)
  assert.match(stop, /do what the hook says/)
  assert.match(stop, /probe: stop guard/)
  assert.match(call(r, 'probe:bash-guard').prompt, /git stash drop/)
})

test('schemas require the reported fields', async () => {
  const r = await run({ worktree: WT })
  assert.deepEqual(call(r, 'probe:recorder').opts.schema.required, ['recordFound', 'recordCommand'])
  assert.deepEqual(call(r, 'probe:stop-guard').opts.schema.required, ['sawBlock', 'committed'])
  assert.deepEqual(call(r, 'probe:bash-guard').opts.schema.required, ['blocked'])
  assert.deepEqual(call(r, 'probe:agent-type').opts.schema.required, ['ok'])
})

test('agentType defaults to workbench:verifier and honours args', async () => {
  const d = await run({ worktree: WT })
  assert.equal(call(d, 'probe:agent-type').opts.agentType, 'workbench:verifier')
  const x = await run({ worktree: WT, agentType: 'x:y' })
  assert.equal(call(x, 'probe:agent-type').opts.agentType, 'x:y')
  assert.deepEqual(x.result.agentType, { resolved: true, name: 'x:y' })
})

test('a throwing agent-type call is recorded, other results intact', async () => {
  const r = await run({ worktree: WT }, fake({ 'probe:agent-type': new Error('unknown agent type') }))
  assert.equal(r.error, undefined)
  assert.deepEqual(r.result.agentType, { resolved: false, name: 'workbench:verifier', error: 'unknown agent type' })
  assert.deepEqual(r.result.recorder, results['probe:recorder'])
  assert.deepEqual(r.result.stopGuard, results['probe:stop-guard'])
  assert.deepEqual(r.result.bashGuard, results['probe:bash-guard'])
})

test('a null agent-type result is unresolved', async () => {
  const r = await run({ worktree: WT }, fake({ 'probe:agent-type': null }))
  assert.deepEqual(r.result.agentType, { resolved: false, name: 'workbench:verifier', error: 'null result' })
})

test('null results of the other agents come back as null', async () => {
  const r = await run({ worktree: WT }, fake({ 'probe:recorder': null }))
  assert.equal(r.result.recorder, null)
})

test('a missing or non-worktree path throws', async () => {
  for (const args of [{}, { worktree: '/tmp/plain' }]) {
    const r = await run(args)
    assert.match(r.error.message, /hook-probe: args.worktree must be an agent worktree path/)
    assert.equal(r.calls.length, 0)
  }
  const ok = await run({ worktree: '/r/.worktrees/b/repo' })
  assert.equal(ok.error, undefined)
})
