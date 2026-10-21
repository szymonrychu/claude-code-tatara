// Runs a workflow script outside the Workflow runtime, with agent() and the
// other runtime globals replaced by fakes, so its control flow can be tested.
import { readFileSync } from 'node:fs'

const MAX_CALLS = 100
const AsyncFunction = (async () => {}).constructor

// The runtime forbids the clock in scripts (it breaks resume): Date.now() and new Date() throw.
const CLOCK_ERROR = 'Date.now() / new Date() are unavailable in workflow scripts (breaks resume). Stamp results after the workflow returns, or pass timestamps via args.'
const ForbiddenDate = new Proxy(Date, {
  construct() { throw new Error(CLOCK_ERROR) },
  get(target, prop) {
    if (prop === 'now') return () => { throw new Error(CLOCK_ERROR) }
    return Reflect.get(target, prop)
  },
})

export const TEST_PLUGIN_ROOT = '/opt/test-plugin'

// plan-execute needs ARGS.pluginRoot; an args object gets a default unless it names the key.
export async function runWorkflow(file, { args, agent }) {
  if (args && typeof args === 'object' && !('pluginRoot' in args)) args = { pluginRoot: TEST_PLUGIN_ROOT, ...args }
  const src = readFileSync(file, 'utf8').replace(/^export const meta/m, 'const meta')
  const calls = []
  const logs = []
  const fakeAgent = async (prompt, opts = {}) => {
    calls.push({ prompt, opts })
    // An uncapped loop never yields to the event loop and would OOM the runner.
    if (calls.length > MAX_CALLS) throw new Error(`runaway: more than ${MAX_CALLS} agent calls`)
    return agent(prompt, opts, calls)
  }
  const pipeline = (items, ...stages) =>
    Promise.all(
      items.map(async (item) => {
        let v = item
        for (let i = 0; i < stages.length; i++) v = await stages[i](i === 0 ? item : v, item)
        return v
      }),
    )
  const parallel = (fns) => Promise.all(fns.map((f) => f()))
  const fn = new AsyncFunction('args', 'agent', 'log', 'phase', 'pipeline', 'parallel', 'Date', src)
  let result
  let error
  try {
    result = await fn(args, fakeAgent, (m) => logs.push(String(m)), () => {}, pipeline, parallel, ForbiddenDate)
  } catch (e) {
    error = e
  }
  return { result, error, calls, logs }
}
