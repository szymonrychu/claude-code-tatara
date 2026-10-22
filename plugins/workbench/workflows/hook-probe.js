export const meta = {
  name: 'hook-probe',
  description: 'Probe which workbench hooks fire inside Workflow subagents: recorder, stop guard, bash guard, plugin agent type',
  whenToUse: 'To measure whether PostToolUse, SubagentStop and PreToolUse plugin hooks and plugin agentType names work inside Workflow subagents. Run on a throwaway agent worktree, then count the transcript with scripts/hook-evidence.py.',
  phases: [
    { title: 'Recorder', detail: 'run a test command, then look for the verify record' },
    { title: 'Stop guard', detail: 'leave a file uncommitted and end the turn' },
    { title: 'Bash guard', detail: 'run a command guard-bash blocks' },
    { title: 'Agent type', detail: 'dispatch with a plugin agent name as agentType' },
    { title: 'Cache static-first', detail: 'args.probe=cache: three serial agents, shared static block first' },
    { title: 'Cache task-first', detail: 'args.probe=cache: the same three with the varying line first' },
  ],
}

const cacheProbe = async () => {
  const staticBlock = Array.from(
    { length: 80 },
    (_, i) => `Static context line ${i + 1}: this block is identical for every probe agent so the prompt cache can reuse it.`,
  ).join('\n')
  const labels = []
  const dispatch = async (kind, phaseTitle, taskFirst) => {
    phase(phaseTitle)
    for (let n = 1; n <= 3; n++) {
      const label = `probe:cache:${kind}#${n}`
      const line = `Probe ${n}: reply with ok true`
      labels.push(label)
      await agent(taskFirst ? `${line}\n${staticBlock}` : `${staticBlock}\n${line}`, {
        label,
        phase: phaseTitle,
        agentType: 'workbench:implementer',
        model: 'sonnet',
        effort: 'low',
        schema: { type: 'object', required: ['ok'], properties: { ok: { type: 'boolean' } } },
      })
    }
  }
  await dispatch('static', 'Cache static-first', false)
  await dispatch('task', 'Cache task-first', true)
  return { probe: 'cache', labels }
}

if (args && args.probe === 'cache') return await cacheProbe()

const worktree = args && args.worktree
if (typeof worktree !== 'string' || !(worktree.includes('.claude/worktrees/') || worktree.includes('.worktrees/'))) {
  throw new Error('hook-probe: args.worktree must be an agent worktree path')
}
const agentTypeName = typeof args.agentType === 'string' && args.agentType ? args.agentType : 'workbench:verifier'

const probe = (label, phaseTitle, schema, prompt, extra = {}) =>
  agent(prompt, { label, phase: phaseTitle, model: 'sonnet', effort: 'low', schema, ...extra })

phase('Recorder')
const recorder = await probe(
  'probe:recorder',
  'Recorder',
  {
    type: 'object',
    required: ['recordFound', 'recordCommand'],
    properties: { recordFound: { type: 'boolean' }, recordCommand: { type: 'string' }, note: { type: 'string' } },
  },
  `Run exactly this command: cd ${worktree} && pytest --version\n` +
    `Then run: cat "$(cd ${worktree} && git rev-parse --absolute-git-dir)/workbench-verify.json"\n` +
    'Report whether that file exists (recordFound) and the value of its "command" field (recordCommand, empty if absent).',
)
log(`recorder: ${recorder ? `recordFound=${recorder.recordFound}` : 'no result'}`)

phase('Stop guard')
const stopGuard = await probe(
  'probe:stop-guard',
  'Stop guard',
  {
    type: 'object',
    required: ['sawBlock', 'committed'],
    properties: { sawBlock: { type: 'boolean' }, reasonExcerpt: { type: 'string' }, committed: { type: 'boolean' } },
  },
  `Write the line "probe" into ${worktree}/probe.txt. Do not stage or commit it. Then end your turn.\n` +
    'A hook may block your stop; if it does, do what the hook says (commit the file with the message "probe: stop guard").\n' +
    'Then report whether a block was seen (sawBlock), the first 200 characters of its reason (reasonExcerpt), and whether you committed (committed).',
)
log(`stop guard: ${stopGuard ? `sawBlock=${stopGuard.sawBlock}` : 'no result'}`)

phase('Bash guard')
const bashGuard = await probe(
  'probe:bash-guard',
  'Bash guard',
  {
    type: 'object',
    required: ['blocked'],
    properties: { blocked: { type: 'boolean' }, message: { type: 'string' } },
  },
  `Run this command once: cd ${worktree} && git stash drop\n` +
    'Report whether a hook blocked it (blocked) and the hook message (message).',
)
log(`bash guard: ${bashGuard ? `blocked=${bashGuard.blocked}` : 'no result'}`)

phase('Agent type')
let agentType
try {
  const r = await probe(
    'probe:agent-type',
    'Agent type',
    { type: 'object', required: ['ok'], properties: { ok: { type: 'boolean' } } },
    'Reply with ok true and nothing else.',
    { agentType: agentTypeName },
  )
  agentType = r ? { resolved: true, name: agentTypeName } : { resolved: false, name: agentTypeName, error: 'null result' }
} catch (e) {
  agentType = { resolved: false, name: agentTypeName, error: e && e.message ? e.message : String(e) }
}
log(`agent type ${agentTypeName}: resolved=${agentType.resolved}`)

return { recorder, stopGuard, bashGuard, agentType }
