import assert from 'node:assert/strict'
import { spawnSync } from 'node:child_process'
import { mkdtempSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { test } from 'node:test'
import { fileURLToPath } from 'node:url'

const CLI = fileURLToPath(new URL('../validate-tasks.mjs', import.meta.url))
const dir = mkdtempSync(join(tmpdir(), 'validate-tasks-'))

const task = (id, extra = {}) => ({
  id,
  title: `task ${id}`,
  repo: 'api',
  requirement: `requirement for ${id}`,
  value: 'worth it',
  files: [`src/${id}.py`],
  ...extra,
})
const write = (name, content) => {
  const p = join(dir, name)
  writeFileSync(p, typeof content === 'string' ? content : JSON.stringify(content))
  return p
}
const cli = (...a) => spawnSync(process.execPath, [CLI, ...a], { encoding: 'utf8' })

test('a valid file exits 0 and prints the task count', () => {
  const r = cli(write('ok.json', [task('T1'), task('T2')]))
  assert.equal(r.status, 0, r.stderr)
  assert.match(r.stdout, /ok: 2 task\(s\)/)
})

test('tasks without a worktree are accepted', () => {
  const r = cli(write('nowt.json', [task('T1')]))
  assert.equal(r.status, 0, r.stderr)
})

test('a task without a value exits 1 with the thrown message', () => {
  const r = cli(write('noval.json', [task('T1', { value: undefined })]))
  assert.equal(r.status, 1)
  assert.match(r.stderr, /task T1 needs a string value/)
})

test('a 9-file task exits 1 with max 8 on stderr', () => {
  const files = Array.from({ length: 9 }, (_, i) => `src/f${i}.py`)
  const r = cli(write('big.json', [task('T1', { files })]))
  assert.equal(r.status, 1)
  assert.match(r.stderr, /max 8/)
})

test('an unordered overlap exits 1', () => {
  const r = cli(write('overlap.json', [task('T1', { files: ['a.py'] }), task('T2', { files: ['a.py'] })]))
  assert.equal(r.status, 1)
  assert.match(r.stderr, /both list a\.py/)
})

test('--existing is validated too', () => {
  const t = write('t.json', [task('T1')])
  assert.equal(cli(t, '--existing', write('e-ok.json', [{ name: 'a', where: 'b' }])).status, 0)
  const bad = cli(t, '--existing', write('e-bad.json', [{ name: 'a' }]))
  assert.equal(bad.status, 1)
  assert.match(bad.stderr, /args\.existing/)
})

test('--do-not-build is validated too', () => {
  const t = write('t2.json', [task('T1')])
  assert.equal(cli(t, '--do-not-build', write('d-ok.json', [{ name: 'a', reason: 'b' }])).status, 0)
  const bad = cli(t, '--do-not-build', write('d-bad.json', [{ name: 'a' }]))
  assert.equal(bad.status, 1)
  assert.match(bad.stderr, /args\.doNotBuild/)
})

test('a missing file exits 1 with a usage line', () => {
  const r = cli(join(dir, 'nope.json'))
  assert.equal(r.status, 1)
  assert.match(r.stderr, /usage: node validate-tasks\.mjs/)
})

test('invalid JSON exits 1 with a usage line', () => {
  const r = cli(write('bad.json', '{not json'))
  assert.equal(r.status, 1)
  assert.match(r.stderr, /usage: node validate-tasks\.mjs/)
})

test('no arguments exits 1 with a usage line', () => {
  const r = cli()
  assert.equal(r.status, 1)
  assert.match(r.stderr, /usage: node validate-tasks\.mjs/)
})

// --- --plan / --design ---------------------------------------------------
const planTasks = () => [
  task('T1', { owns: ['alpha'] }),
  task('T2', { uses: ['alpha'], dependsOn: ['T1'] }),
]
const BRIEF = '## Project brief\n\nWhat: a thing\nHow: by parts\nWhy: it pays\n\n'
const planDoc = ({ blocks = [1, 2], coverage = '| D1 first | T1, T2 |', contracts, sections = true, brief = BRIEF } = {}) => {
  const rows = contracts ?? '| `alpha` | T1 | T2 | `src/alpha.py` (a thing) |'
  const heads = blocks.map((n) => `### Task ${n}: block\n\nbody\n`).join('\n')
  const cov = sections
    ? `## Decision coverage\n\n| Decision | Tasks |\n|---|---|\n${coverage}\n\n## Contracts\n\n| Part | Owner | Consumers | Where defined |\n|---|---|---|---|\n${rows}\n\n`
    : `Mentions \`## Contracts\` and \`## Decision coverage\` only in prose.\n\n`
  return `# Plan\n\n${brief}${cov}## Review focus\n\n- x\n\n${heads}\n## Execution\n`
}
const designDoc = (ids = [1]) => `# Design\n\n## Decisions\n\n${ids.map((n) => `### D${n}: title ${n}\n\ntext\n`).join('\n')}`
const LEDGER = () => [{ id: 'A', text: 'x', decisions: ['D1'], tasks: ['T1', 'T2'], status: 'approved' }]
const planCli = (tasks, plan, design, ledger = LEDGER()) => {
  const args = [write('pt.json', tasks), '--plan', write('plan.md', plan), '--approvals', write('ap.json', ledger)]
  if (design !== undefined) args.push('--design', write('design.md', design))
  return cli(...args)
}
const ledgerCli = (ledger, ...more) => cli(write('lt.json', planTasks()), '--approvals', write('l.json', ledger), ...more)

test('a matching plan passes and prints plan checked', () => {
  const r = planCli(planTasks(), planDoc())
  assert.equal(r.status, 0, r.stderr)
  assert.match(r.stdout, /ok: 2 task\(s\), plan checked, approvals checked\s*$/)
})

test('--plan with --design prints design checked', () => {
  const r = planCli(planTasks(), planDoc(), designDoc([1]))
  assert.equal(r.status, 0, r.stderr)
  assert.match(r.stdout, /ok: 2 task\(s\), plan checked, approvals checked, design checked/)
})

test('a plan block with no JSON task fails naming it', () => {
  const r = planCli(planTasks(), planDoc({ blocks: [1, 2, 3] }))
  assert.equal(r.status, 1)
  assert.match(r.stderr, /plan: task block "Task 3" has no JSON task T3/)
})

test('a JSON task with no block fails naming it', () => {
  const r = planCli(planTasks(), planDoc({ blocks: [1] }))
  assert.equal(r.status, 1)
  assert.match(r.stderr, /plan: JSON task T2 has no "### Task 2" block/)
})

test('a JSON id not of the form T<n> is reported', () => {
  const r = planCli([task('alpha-task')], planDoc({ blocks: [1] }))
  assert.equal(r.status, 1)
  assert.match(r.stderr, /plan: JSON task alpha-task is not of the form T<n>/)
})

test('a missing Contracts section fails, prose mentions do not count', () => {
  const r = planCli(planTasks(), planDoc({ sections: false }))
  assert.equal(r.status, 1)
  assert.match(r.stderr, /plan: missing section ## Contracts/)
  assert.match(r.stderr, /plan: missing section ## Decision coverage/)
})

test('a contract whose owner does not own the part fails', () => {
  const r = planCli(planTasks(), planDoc({ contracts: '| `alpha` | T2 | none | `x` |' }))
  assert.equal(r.status, 1)
  assert.match(r.stderr, /plan: contract alpha owner T2 does not own it/)
})

test('a consumer that does not use the part fails', () => {
  const r = planCli(planTasks(), planDoc({ contracts: '| `alpha` | T1 | T1 | `x` |' }))
  assert.equal(r.status, 1)
  assert.match(r.stderr, /plan: contract alpha consumer T1 does not use it/)
})

test('a contract row with an empty consumers cell has no consumer check', () => {
  const r = planCli(planTasks(), planDoc({ contracts: '| `alpha` | T1 |  | `x` |' }))
  assert.equal(r.status, 0, r.stderr)
})

test('an unknown task id in Decision coverage fails', () => {
  const r = planCli(planTasks(), planDoc({ coverage: '| D1 first | T1, T9 |' }))
  assert.equal(r.status, 1)
  assert.match(r.stderr, /plan: ## Decision coverage names unknown task T9/)
})

test('an unknown task id in Contracts fails', () => {
  const r = planCli(planTasks(), planDoc({ contracts: '| `alpha` | T1 | T2, T8 | `x` |' }))
  assert.equal(r.status, 1)
  assert.match(r.stderr, /plan: ## Contracts names unknown task T8/)
})

test('--design with a decision absent from coverage fails', () => {
  const r = planCli(planTasks(), planDoc(), designDoc([1, 2]))
  assert.equal(r.status, 1)
  assert.match(r.stderr, /plan: design decision D2 has no row in Decision coverage/)
})

test('--plan without --design skips the decision check', () => {
  const r = planCli(planTasks(), planDoc())
  assert.equal(r.status, 0, r.stderr)
  assert.doesNotMatch(r.stdout, /design checked/)
})

test('--design without --plan exits 1 with the usage line listing all flags', () => {
  const r = cli(write('d.json', planTasks()), '--design', write('d.md', designDoc()))
  assert.equal(r.status, 1)
  assert.match(r.stderr, /usage: node validate-tasks\.mjs/)
  for (const f of ['--existing', '--do-not-build', '--plan', '--approvals', '--design']) assert.ok(r.stderr.includes(f), f)
})

test('several plan failures are all printed', () => {
  const r = planCli(planTasks(), planDoc({ blocks: [1, 3], coverage: '| D1 | T7 |', contracts: '| `alpha` | T2 | T1 | `x` |' }), designDoc([1, 2]))
  assert.equal(r.status, 1)
  for (const m of [/Task 3" has no JSON task T3/, /JSON task T2 has no/, /names unknown task T7/, /owner T2 does not own it/, /consumer T1 does not use it/, /D2 has no row/]) {
    assert.match(r.stderr, m)
  }
})

// --- --approvals ----------------------------------------------------------
const entry = (extra = {}) => ({ id: 'A', text: 'x', decisions: ['D1'], tasks: ['T1', 'T2'], status: 'approved', ...extra })

test('--plan without --approvals exits 1 with the usage line', () => {
  const r = cli(write('pa.json', planTasks()), '--plan', write('pa.md', planDoc()))
  assert.equal(r.status, 1)
  assert.match(r.stderr, /usage: node validate-tasks\.mjs/)
})

test('ledger-only mode passes and prints approvals checked', () => {
  const r = ledgerCli([entry()])
  assert.equal(r.status, 0, r.stderr)
  assert.match(r.stdout, /ok: 2 task\(s\), approvals checked\s*$/)
})

test('the JSON-only mode still prints just the count', () => {
  const r = cli(write('jo.json', planTasks()))
  assert.match(r.stdout, /ok: 2 task\(s\)\s*$/)
})

test('a non-array ledger fails with the expected message and usage', () => {
  const r = ledgerCli({ id: 'A' })
  assert.equal(r.status, 1)
  assert.match(r.stderr, /expected a JSON array of ledger entries/)
  assert.match(r.stderr, /usage: node validate-tasks\.mjs/)
})

test('a non-object ledger entry fails with the expected message', () => {
  const r = ledgerCli(['A'])
  assert.equal(r.status, 1)
  assert.match(r.stderr, /expected a JSON array of ledger entries/)
})

test('a duplicate ledger id fails', () => {
  const r = ledgerCli([entry(), entry()])
  assert.equal(r.status, 1)
  assert.match(r.stderr, /approvals: duplicate id A/)
})

test('a ledger item with empty text fails', () => {
  const r = ledgerCli([entry({ text: '  ' })])
  assert.equal(r.status, 1)
  assert.match(r.stderr, /approvals: item A has empty text/)
})

test('a ledger item mapped to no task fails', () => {
  for (const tasks of [[], undefined]) {
    const r = ledgerCli([entry({ tasks })])
    assert.equal(r.status, 1)
    assert.match(r.stderr, /approvals: item A maps to no task/)
  }
})

test('a ledger item naming an unknown task fails', () => {
  const r = ledgerCli([entry({ tasks: ['T1', 'T9'] })])
  assert.equal(r.status, 1)
  assert.match(r.stderr, /approvals: item A names unknown task T9/)
})

test('a ledger item that is not approved fails', () => {
  const r = ledgerCli([entry({ status: 'proposed' })])
  assert.equal(r.status, 1)
  assert.match(r.stderr, /approvals: item A has status proposed, only approved items are planned/)
})

test('--design: an item naming no decision fails', () => {
  const r = planCli(planTasks(), planDoc(), designDoc([1]), [entry({ decisions: [] })])
  assert.equal(r.status, 1)
  assert.match(r.stderr, /approvals: item A names no decision/)
})

test('--design: an unknown decision fails', () => {
  const r = planCli(planTasks(), planDoc(), designDoc([1]), [entry({ decisions: ['D1', 'D7'] })])
  assert.equal(r.status, 1)
  assert.match(r.stderr, /approvals: item A names unknown decision D7/)
})

test('--design: a design decision covered by no item fails', () => {
  const r = planCli(planTasks(), planDoc(), designDoc([1, 2]), [entry()])
  assert.equal(r.status, 1)
  assert.match(r.stderr, /approvals: design decision D2 is covered by no approved item/)
})

test('decision checks are skipped without --design', () => {
  const r = ledgerCli([entry({ decisions: [] })])
  assert.equal(r.status, 0, r.stderr)
})

test('a plan without ## Project brief fails', () => {
  const r = planCli(planTasks(), planDoc({ brief: '' }))
  assert.equal(r.status, 1)
  assert.match(r.stderr, /plan: missing section ## Project brief/)
})

test('a brief with an empty Why fails', () => {
  const r = planCli(planTasks(), planDoc({ brief: '## Project brief\n\nWhat: a\nHow: b\nWhy:\n\n' }))
  assert.equal(r.status, 1)
  assert.match(r.stderr, /plan: Project brief is missing Why/)
  assert.doesNotMatch(r.stderr, /missing What|missing How/)
})

test('several approvals failures print on separate lines', () => {
  const r = ledgerCli([entry({ text: '', tasks: ['T9'], status: 'draft' }), entry({ id: 'B', tasks: [] })])
  assert.equal(r.status, 1)
  const lines = r.stderr.trim().split('\n')
  for (const m of [/empty text/, /unknown task T9/, /has status draft/, /item B maps to no task/]) {
    assert.equal(lines.filter((l) => m.test(l)).length, 1, String(m))
  }
})
