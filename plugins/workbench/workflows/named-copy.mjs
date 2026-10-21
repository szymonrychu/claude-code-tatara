// Usage: node named-copy.mjs <workflow> <run-name> <out-dir> [--args <file.json>]
//
// Writes <out-dir>/<workflow>-<run-name>.js, a copy of this directory's
// <workflow>.js whose meta.name is '<workflow>:<run-name>', and prints its path.
// The copy always embeds pluginRoot (the absolute path of this directory's parent)
// in its default args; with --args it also embeds that JSON. Runtime args override
// both, so the task text never passes through the orchestrator. An --args file whose
// tasks is missing, not an array or empty is refused.
// Run it with Workflow({ scriptPath }). meta.name must be a pure literal and the
// Workflow tool ignores a passed title, so a copy is the only way to name a run.
import { readFileSync, writeFileSync } from 'node:fs'
import { join } from 'node:path'
import { fileURLToPath } from 'node:url'

const argv = process.argv.slice(2)
const flag = argv.indexOf('--args')
const argsFile = flag === -1 ? undefined : argv.splice(flag, 2)[1]
const [wf, name, outDir] = argv
const fail = (msg) => {
  process.stderr.write(`named-copy: ${msg}\n`)
  process.exit(1)
}
if (!wf || !name || !outDir) fail('usage: node named-copy.mjs <workflow> <run-name> <out-dir> [--args <file.json>]')
if (flag !== -1 && !argsFile) fail('--args needs a file')
if (!/^[a-z0-9][a-z0-9-]*$/.test(name)) fail(`run name must be a lowercase slug, got ${JSON.stringify(name)}`)

let src
try {
  src = readFileSync(fileURLToPath(new URL(`./${wf}.js`, import.meta.url)), 'utf8')
} catch {
  fail(`no workflow named ${JSON.stringify(wf)}`)
}
const line = `\n  name: '${wf}',\n`
if (!src.includes(line)) fail(`${wf}.js has no meta line  name: '${wf}',`)

let copy = src.replace(line, `\n  name: '${wf}:${name}',\n`)
// pluginRoot is always embedded: Workflow agents' shells have no CLAUDE_PLUGIN_ROOT.
const pluginRoot = fileURLToPath(new URL('..', import.meta.url)).replace(/\/$/, '')
const ARGS_LINE = "const ARGS = (typeof args !== 'undefined' && args) || {}"
if (argsFile !== undefined || copy.split('\n').includes(ARGS_LINE)) {
  if (!copy.split('\n').includes(ARGS_LINE)) fail(`${wf}.js has no ARGS line`)
  let embedded = {}
  if (argsFile !== undefined) {
    try {
      embedded = JSON.parse(readFileSync(argsFile, 'utf8'))
    } catch (e) {
      fail(`${argsFile}: ${e.message}`)
    }
    // A run with zero tasks has nothing to execute; refuse before writing a copy.
    if (!Array.isArray(embedded?.tasks) || !embedded.tasks.length) fail('args.tasks is empty - nothing to execute')
  }
  const json = JSON.stringify({ ...embedded, pluginRoot })
  const merged = `const ARGS = Object.assign({}, ${json}, (typeof args !== 'undefined' && args) || {})`
  copy = copy.split('\n').map((l) => (l === ARGS_LINE ? merged : l)).join('\n')
}
const out = join(outDir, `${wf}-${name}.js`)
writeFileSync(out, copy)
process.stdout.write(`${out}\n`)
