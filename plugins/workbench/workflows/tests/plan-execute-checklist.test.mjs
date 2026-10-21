// The plan-execute reviewer applies the same checklist as every other reviewer
// in this plugin: the review call runs as workbench:reviewer, whose agent file
// reads review-checklist.md, so the prompt carries only the per-call inputs.
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { test } from 'node:test'
import { fileURLToPath } from 'node:url'
import { runWorkflow } from './harness.mjs'

const SCRIPT = fileURLToPath(new URL('../plan-execute.js', import.meta.url))
const SOURCE = readFileSync(SCRIPT, 'utf8')
const BRIEF = { what: 'a plugin', how: 'workflows and hooks', why: 'reliable delivery' }
const CHECKLIST_PATH = 'skills/start-review/references/review-checklist.md'
const CHECKLIST = readFileSync(new URL(`../../${CHECKLIST_PATH}`, import.meta.url), 'utf8')
const BULLETS = CHECKLIST.split('\n').filter((l) => l.startsWith('- ')).map((l) => l.slice(2))
const REVIEWER_MD = readFileSync(new URL('../../agents/reviewer.md', import.meta.url), 'utf8')

const task = {
  id: 'T1',
  title: 'task T1',
  repo: 'api',
  worktree: '/wt/T1',
  requirement: 'requirement for T1',
  value: 'worth it',
  files: ['src/a.py', 'src/b.py', 'tests/test_a.py'],
  review: 'full', // two rounds at full effort; tier rules live in plan-execute-tier
}

const finding = { severity: 'high', kind: 'wrong', file: 'src/a.py', line: 3, summary: 'drops the notice', requirement: 'keeps every notice', evidence: 'src/a.py:3' }

// the first review raises one finding, the second is clean
const agent = async (prompt, opts) => {
  const role = opts.label.split(':')[1]
  if (role === 'impl' || role === 'fix') {
    return {
      taskId: 'T1',
      complete: true,
      summary: 'did it',
      filesChanged: ['src/a.py'],
      branch: 'b-T1',
      tests: { added: ['tests/test_a.py'], wroteTestFirst: true, red: { command: 'pytest', output: 'FAILED tests/test_a.py::test_x' } },
      verification: { command: 'pytest', passed: true, evidence: '3 passed' },
    }
  }
  if (role === 'verify') return { head: 'abc', clean: true, command: 'pytest', passed: true, evidence: '3 passed', debtMarkers: [] }
  if (role === 'review') {
    return opts.label.endsWith('#1')
      ? { clean: false, findings: [finding], filesRead: ['src/a.py'] }
      : { clean: true, findings: [], filesRead: ['src/a.py'] }
  }
  if (role === 'audit') return { complete: true, missing: [] }
  throw new Error(`unexpected agent ${opts.label}`)
}

const reviews = async () => {
  const r = await runWorkflow(SCRIPT, { args: { brief: BRIEF, tasks: [task] }, agent })
  assert.equal(r.error, undefined)
  return r.calls.filter((c) => c.opts.label.split(':')[1] === 'review')
}

test('the checklist markdown has its heading and bullets', () => {
  assert.ok(CHECKLIST.split('\n').includes('# Review checklist'))
  assert.ok(BULLETS.length > 10)
})

test('reviewer agent reads the checklist file', () => {
  const body = REVIEWER_MD.split('\n---\n').slice(1).join('\n---\n')
  assert.ok(body.includes(CHECKLIST_PATH), 'agents/reviewer.md does not name the checklist path')
  // the checklist file, not the agent, holds the method bullets
  for (const b of ['Report filesRead: the files you actually opened, not the files you were pointed at.', 'A missing note, sweep, ratchet or approval line is a processGaps entry, never a finding.']) {
    assert.ok(BULLETS.includes(b), `checklist lacks: ${b}`)
    assert.ok(!REVIEWER_MD.includes(b), `agents/reviewer.md copies: ${b}`)
  }
  assert.ok(BULLETS.some((b) => b.startsWith('Debt markers: ')), 'checklist lacks the debt-marker bullet')
})

test('review call runs under workbench:reviewer', async () => {
  const calls = await reviews()
  // one call per round, two rounds
  assert.deepEqual(calls.map((c) => c.opts.label), ['pe:review:task-t1#1', 'pe:review:task-t1#2'])
  for (const c of calls) {
    assert.equal(c.opts.agentType, 'workbench:reviewer', c.opts.label)
    assert.equal(c.opts.model, 'sonnet', c.opts.label)
    assert.equal(c.opts.effort, 'high', c.opts.label)
  }
})

test('review prompt carries only per-call inputs', async () => {
  const calls = await reviews()
  for (const c of calls) {
    const p = c.prompt
    for (const b of BULLETS) assert.ok(!p.includes(b), `review prompt pastes the checklist bullet: ${b}`)
    for (const moved of ['Checklist (the one every reviewer', 'Report a finding ONLY when', 'A reviewer asked to find gaps', 'Each of these is undelivered scope', 'List every file you read in filesRead.']) {
      assert.ok(!p.includes(moved), `review prompt still carries: ${moved}`)
    }
    // the per-call inputs stay
    assert.ok(p.includes('a plugin'), 'brief')
    assert.ok(p.includes('Review plan task T1 in the worktree at: /wt/T1'), 'task')
    assert.ok(p.includes('Task requirement:\nrequirement for T1'), 'requirement')
    assert.ok(p.includes('Review through these lenses only: correctness, requirements-coverage.'), 'lenses')
    assert.match(p, /git diff \$\(git merge-base HEAD main\)\.\.HEAD -- src\/a\.py/)
    assert.ok(p.includes('never edit or commit'), 'read-only helper line')
  }
  assert.ok(calls[0].prompt.includes('Round 1 of at most 3.'))
  assert.ok(calls[1].prompt.includes('Round 2 of at most 3.'))
})

test('REVIEW_CHECKLIST left the script', () => {
  assert.ok(!SOURCE.includes('REVIEW_CHECKLIST'))
  for (const b of BULLETS) assert.ok(!SOURCE.includes(b), `plan-execute.js still holds: ${b}`)
})

// The method lines that left the prompt and are in neither the agent nor the
// checklist before: the external-blocker rule rides on the schema the call
// carries, and the clean-is-expected rule is a checklist bullet.
test('the review schema says when blocked applies, instead of the prompt', async () => {
  const [c] = await reviews()
  const d = c.opts.schema.properties.blocked.description
  for (const s of ['external blocker', 'human merge', 'credential', 'permission', 'instead of a finding', 'ends the loop']) assert.ok(d.includes(s), s)
})

test('the checklist says clean is the expected outcome for good work', () => {
  assert.ok(BULLETS.some((x) => x.includes('expected outcome for good work')), 'no clean-is-expected bullet')
  const only = BULLETS.find((x) => x.includes('correctness or a stated requirement'))
  assert.ok(only, 'no correctness-or-requirement bullet')
  for (const s of ['speculative hardening', '"consider also"']) assert.ok(only.includes(s), s)
})
