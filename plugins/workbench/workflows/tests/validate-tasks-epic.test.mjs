// validate-tasks.mjs --epic <dir>: the epic directory lint (README, task files, ledger, design, check).
import assert from 'node:assert/strict'
import { spawnSync } from 'node:child_process'
import { mkdirSync, mkdtempSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { test } from 'node:test'
import { fileURLToPath } from 'node:url'

const CLI = fileURLToPath(new URL('../validate-tasks.mjs', import.meta.url))

const README = (over = {}) => {
  const fm = { title: 'Alpha', blockers: '[]', stage: 'build', repos: '[api]', created: '2026-10-17', ...over.fm }
  const head = Object.entries(fm).filter(([, v]) => v !== null).map(([k, v]) => `${k}: ${v}`).join('\n')
  const sec = { brief: 'What: a thing\nHow: by code\nWhy: value', description: 'Does it.', goals: '- g1', nonGoals: '- n1', ...over.sec }
  const parts = [
    ['Project brief', sec.brief], ['Description', sec.description], ['Goals', sec.goals], ['Non-goals', sec.nonGoals],
  ].filter(([, v]) => v !== null).map(([h, v]) => `## ${h}\n\n${v}\n`)
  return `---\n${head}\n---\n\n# Alpha\n\n${parts.join('\n')}`
}
const TASK = (over = {}) => {
  const sec = {
    Requirement: 'Build the thing.',
    'Acceptance conditions': '- a1: it works [evidence: test:tests/test_x.py::test_a]',
    Files: '- src/x.py',
    'Expected outcome': 'x works',
    Steps: '- write the test',
    ...over.sec,
  }
  const body = Object.entries(sec).filter(([, v]) => v !== null).map(([h, v]) => `## ${h}\n\n${v}\n`).join('\n')
  const fm = { title: 'X', status: 'todo', repo: 'api', value: 'worth it', files: '[src/x.py]', verify: 'pytest', depends_on: '[]', owns: '[]', uses: '[]', ...over.fm }
  const head = Object.entries(fm).filter(([, v]) => v !== null).map(([k, v]) => `${k}: ${v}`).join('\n')
  return `---\n${head}\n---\n\n# X\n\n${body}`
}
const DESIGN = `# D\n\n## Decisions\n\n### D1: first\n\ntext\n\n### D2: second\n\ntext\n\n## Decision coverage\n\n| Decision | Tasks |\n|---|---|\n| D1 first | t-one |\n| D2 second | t-two |\n\n## Contracts\n\n| Part | Owner | Consumers | Where defined |\n|---|---|---|---|\n| \`part-a\` | t-one | t-two | \`src/x.py\` |\n`
const LEDGER = [{ id: 'A', text: 'x', decisions: ['D1', 'D2'], tasks: ['t-one', 't-two'], status: 'approved' }]

// Builds <tmp>/docs/plans/in-progress/alpha and returns its path.
const epic = ({ readme = README(), tasks, approvals = LEDGER, design } = {}) => {
  const root = mkdtempSync(join(tmpdir(), 'vt-epic-'))
  const d = join(root, 'in-progress', 'alpha')
  mkdirSync(join(d, 'tasks'), { recursive: true })
  writeFileSync(join(d, 'README.md'), readme)
  const ts = tasks ?? { 't-one': TASK({ fm: { owns: '[part-a]' } }), 't-two': TASK({ fm: { uses: '[part-a]', depends_on: '[t-one]', files: '[src/y.py]' } }) }
  for (const [slug, text] of Object.entries(ts)) writeFileSync(join(d, 'tasks', `${slug}.md`), text)
  if (approvals !== null) writeFileSync(join(d, 'approvals.json'), typeof approvals === 'string' ? approvals : JSON.stringify(approvals))
  if (design !== undefined) writeFileSync(join(d, 'design.md'), design)
  return d
}
const cli = (...a) => spawnSync(process.execPath, [CLI, ...a], { encoding: 'utf8' })
const lines = (r) => r.stderr.trim().split('\n').filter(Boolean)

test('a valid epic passes and prints the ok line', () => {
  const r = cli('--epic', epic())
  assert.equal(r.status, 0, r.stderr)
  assert.match(r.stdout, /^ok: 2 task\(s\), epic checked, approvals checked\s*$/)
})

test('a valid epic with design.md prints design checked', () => {
  const r = cli('--epic', epic({ design: DESIGN }))
  assert.equal(r.status, 0, r.stderr)
  assert.match(r.stdout, /ok: 2 task\(s\), epic checked, approvals checked, design checked/)
})

test('README frontmatter keys missing are each reported on their own line', () => {
  const r = cli('--epic', epic({ readme: README({ fm: { title: null, stage: null, created: null } }) }))
  assert.equal(r.status, 1)
  for (const k of ['title', 'stage', 'created']) assert.ok(lines(r).some((l) => l.includes(`README frontmatter is missing ${k}`)), k)
  assert.ok(!r.stderr.includes('missing blockers'))
})

test('README sections missing or empty are each reported', () => {
  const r = cli('--epic', epic({ readme: README({ sec: { brief: 'What: only what', description: '{{description}}', goals: null, nonGoals: '' } }) }))
  assert.equal(r.status, 1)
  const out = lines(r)
  for (const m of ['Project brief is missing How', 'Project brief is missing Why', 'README ## Description is empty', 'README ## Goals is missing', 'README ## Non-goals is empty']) {
    assert.ok(out.some((l) => l.includes(m)), m + '\n' + r.stderr)
  }
  assert.ok(!r.stderr.includes('missing What'))
})

test('each task file section that is missing or empty is reported with the task slug', () => {
  const r = cli('--epic', epic({ tasks: { 't-one': TASK({ sec: { 'Expected outcome': null, Steps: '' } }), 't-two': TASK({ sec: { Files: '{{files}}' } }) } }))
  assert.equal(r.status, 1)
  const out = lines(r)
  for (const m of ['task t-one: ## Expected outcome is missing', 'task t-one: ## Steps is empty', 'task t-two: ## Files is empty']) {
    assert.ok(out.some((l) => l.includes(m)), m + '\n' + r.stderr)
  }
})

test('a task with no acceptance line fails the required ac', () => {
  const r = cli('--epic', epic({ tasks: { 't-one': TASK({ sec: { 'Acceptance conditions': 'it just works' } }) }, approvals: [{ ...LEDGER[0], tasks: ['t-one'] }] }))
  assert.equal(r.status, 1)
  assert.match(r.stderr, /Acceptance conditions line is not/)
})

test('an ac that parks work is reported', () => {
  const r = cli('--epic', epic({ tasks: { 't-one': TASK({ sec: { 'Acceptance conditions': '- a1: handle this as a follow-up [evidence: judgement]' } }) }, approvals: [{ ...LEDGER[0], tasks: ['t-one'] }] }))
  assert.equal(r.status, 1)
  assert.match(r.stderr, /tasks: t-one parks work: "follow-up"/)
})

test('approvals.json is required', () => {
  const r = cli('--epic', epic({ approvals: null }))
  assert.equal(r.status, 1)
  assert.match(r.stderr, /approvals: missing approvals\.json/)
})

test('the ledger is linted with task slugs as ids', () => {
  const r = cli('--epic', epic({ approvals: [{ id: 'A', text: 'x', tasks: ['T1'], status: 'approved' }] }))
  assert.equal(r.status, 1)
  assert.match(r.stderr, /approvals: item A names unknown task T1/)
})

test('a design decision without a coverage row, or named by no approved item, is reported', () => {
  const design = DESIGN.replace('| D2 second | t-two |\n', '')
  const r = cli('--epic', epic({ design, approvals: [{ ...LEDGER[0], decisions: ['D1'] }] }))
  assert.equal(r.status, 1)
  assert.match(r.stderr, /design: decision D2 has no row in Decision coverage/)
  assert.match(r.stderr, /approvals: design decision D2 is covered by no approved item/)
})

test('a coverage row naming an unknown task, and a contract with the wrong owner or consumer, are reported', () => {
  const design = DESIGN.replace('| D1 first | t-one |', '| D1 first | t-ghost |').replace('| `part-a` | t-one | t-two |', '| `part-a` | t-two | t-one |')
  const r = cli('--epic', epic({ design }))
  assert.equal(r.status, 1)
  const out = lines(r)
  for (const m of ['design: Decision coverage names unknown task t-ghost', 'design: contract part-a owner t-two does not own it', 'design: contract part-a consumer t-one does not use it']) {
    assert.ok(out.some((l) => l.includes(m)), m + '\n' + r.stderr)
  }
})

test('ticket.py check hard failure fails the lint, one line per failure', () => {
  const d = epic()
  // a second epic whose in-progress task shares t-one's file
  const other = join(d, '..', 'beta')
  mkdirSync(join(other, 'tasks'), { recursive: true })
  writeFileSync(join(other, 'README.md'), README())
  writeFileSync(join(other, 'tasks', 'clash.md'), TASK({ fm: { files: '[src/x.py]' } }))
  const r = cli('--epic', d)
  assert.equal(r.status, 1)
  assert.match(r.stderr, /check: .*file 'src\/x\.py' is also in task 'clash' of in-progress epic 'beta'/)
})

test('a missing epic directory exits 1', () => {
  const r = cli('--epic', join(tmpdir(), 'no-such-epic-dir'))
  assert.equal(r.status, 1)
  assert.match(r.stderr, /no-such-epic-dir/)
})

test('--epic cannot be combined with a tasks file or --plan', () => {
  const r = cli('--epic', epic(), '--plan', 'x.md')
  assert.equal(r.status, 1)
  assert.match(r.stderr, /usage:[\s\S]*--epic/)
})


test('an estimate over 90 minutes warns as a split hint but does not fail', () => {
  const r = cli('--epic', epic({ tasks: { 't-one': TASK({ fm: { owns: '[part-a]', estimate: 120 } }), 't-two': TASK({ fm: { uses: '[part-a]', depends_on: '[t-one]', files: '[src/y.py]', estimate: 90 } }) } }))
  assert.equal(r.status, 0, r.stderr)
  assert.match(r.stdout, /^ok: 2 task\(s\)/)
  assert.match(r.stderr, /warning: task t-one: estimate 120 > 90 minutes; consider splitting/)
  assert.ok(!/estimate.*t-two|t-two.*estimate/.test(r.stderr))
})

test('no warning when every estimate is at most 90 or absent', () => {
  const r = cli('--epic', epic())
  assert.equal(r.status, 0, r.stderr)
  assert.ok(!r.stderr.includes('estimate'))
})
