// validate-tasks.mjs --epic mid-epic: done tasks stay known ids; a derive failure is reported once.
import assert from 'node:assert/strict'
import { spawnSync } from 'node:child_process'
import { mkdirSync, mkdtempSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { test } from 'node:test'
import { fileURLToPath } from 'node:url'

const CLI = fileURLToPath(new URL('../validate-tasks.mjs', import.meta.url))
const README = `---\ntitle: Alpha\nblockers: []\nstage: build\nrepos: [api]\ncreated: 2026-10-17\n---\n\n# Alpha\n\n## Project brief\n\nWhat: a\nHow: b\nWhy: c\n\n## Description\n\nd\n\n## Goals\n\n- g\n\n## Non-goals\n\n- n\n`
const TASK = (fm = {}) => {
  const f = { title: 'X', status: 'todo', repo: 'api', value: 'worth it', files: '[src/x.py]', verify: 'pytest tests/test_x.py', depends_on: '[]', owns: '[]', uses: '[]', ...fm }
  const head = Object.entries(f).map(([k, v]) => `${k}: ${v}`).join('\n')
  return `---\n${head}\n---\n\n# X\n\n## Requirement\n\nBuild.\n\n## Acceptance conditions\n\n- a1: works [evidence: test:tests/test_x.py::test_a]\n\n## Files\n\n- src/x.py\n\n## Expected outcome\n\nx\n\n## Steps\n\n- go\n`
}
const DESIGN = `# D\n\n## Decisions\n\n### D1: first\n\ntext\n\n### D2: second\n\ntext\n\n## Decision coverage\n\n| Decision | Tasks |\n|---|---|\n| D1 first | t-one |\n| D2 second | t-two |\n\n## Contracts\n\n| Part | Owner | Consumers | Where defined |\n|---|---|---|---|\n| \`part-a\` | t-one | t-two | \`src/x.py\` |\n`
const LEDGER = [{ id: 'A', text: 'x', decisions: ['D1', 'D2'], tasks: ['t-one', 't-two'], status: 'approved' }]
const epic = (tasks, approvals = LEDGER) => {
  const root = mkdtempSync(join(tmpdir(), 'vt-done-'))
  const d = join(root, 'in-progress', 'alpha')
  mkdirSync(join(d, 'tasks'), { recursive: true })
  writeFileSync(join(d, 'README.md'), README)
  writeFileSync(join(d, 'design.md'), DESIGN)
  writeFileSync(join(d, 'approvals.json'), JSON.stringify(approvals))
  for (const [slug, text] of Object.entries(tasks)) writeFileSync(join(d, 'tasks', `${slug}.md`), text)
  return d
}
const cli = (...a) => spawnSync(process.execPath, [CLI, ...a], { encoding: 'utf8' })
const lines = (r) => r.stderr.trim().split('\n').filter(Boolean)

test('approvals naming done tasks lint ok', () => {
  const d = epic({
    't-one': TASK({ status: 'done', owns: '[part-a]' }),
    't-two': TASK({ uses: '[part-a]', depends_on: '[t-one]', files: '[src/y.py]' }),
  })
  const r = cli('--epic', d)
  assert.equal(r.status, 0, r.stderr)
  assert.match(r.stdout, /^ok: /)
})

test('derive failure is reported once', () => {
  const d = epic({ 't-one': TASK({ owns: '[part-a]' }).replace('Build.', ''), 't-two': TASK({ uses: '[part-a]', files: '[src/y.py]' }) },
    [...LEDGER, { id: 'B', text: 'y', decisions: ['D1'], tasks: ['t-two'], status: 'approved' }])
  const r = cli('--epic', d)
  assert.equal(r.status, 1)
  assert.doesNotMatch(r.stderr, /names unknown task/)
  assert.equal(lines(r).filter((l) => l.startsWith('tasks:')).length, 1, r.stderr)
})
