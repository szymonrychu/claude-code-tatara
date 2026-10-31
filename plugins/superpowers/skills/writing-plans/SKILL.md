---
name: writing-plans
description: "Use after the brainstorming gate, when the user has picked a rung and answered the open questions: the same plan writer records the agreed scope in plan.md and writes implementation-plan.md for the agreed rung only, in chunks with a pinned model. No second gate."
---

# Writing Plans

## Overview

Write the implementation plan for an engineer who has not seen this codebase or this plan. Assume they write idiomatic code in the project's language once they know the exact interface and the exact test, and that they will make a reasonable choice wherever the plan leaves one open. What they cannot know is what you decided: which files, which names and signatures, which values from plan.md, which tests prove each step. Document those. Give them the agreed rung only, as right-sized steps. DRY. YAGNI. TDD. Frequent commits.

**Who writes it:** the orchestrator never writes the plan. It continues the plan writer that brainstorming dispatched (the general-purpose opus subagent briefed by `../brainstorming/plan-writer-prompt.md`) with SendMessage, in implementation mode, carrying the user's gate answer verbatim and nothing else. A plan prepared in another session gets a fresh opus subagent with the same prompt and the plan path.

**Input:** the user's gate answer verbatim: the rung per plan and the answers to the open questions. It is binding; never re-ask it.

**Output:** `ticket.py path <plan> implementation` (`ticket.py` is `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/ticket.py`; a subagent gets its absolute path), written from `${CLAUDE_PLUGIN_ROOT}/templates/implementation-plan.md`, for the agreed rung only. Plans live in `docs/plans/{todo,in-progress,done}/<plan>/`, next to plan.md.

## Record the Agreed Scope

In plan.md, in one edit:

- Agreed scope: the rung the user picked and every modification they made, verbatim where it binds.
- Each open question's `[recommended: ...]` becomes `[answer: ...]` with the user's answer.
- Frontmatter `rung` is set to the picked rung number.

`ticket.py move <plan> in-progress` later refuses a plan whose `rung` is empty or that has no implementation-plan.md: that is the mechanical form of the gate.

## Scope Check

The agreed rung is the scope. Every item of it is covered by at least one step; nothing outside it gets a step. If the rung covers several independent subsystems that the brainstorming gate did not split, the chunks follow those subsystem lines, and each chunk leaves the tree green on its own.

## File Structure

Before defining steps, map out which files will be created or modified and what each one is responsible for. This is where decomposition decisions get locked in.

- Design units with clear boundaries and well-defined interfaces. Each file should have one clear responsibility.
- You reason best about code you can hold in context at once, and your edits are more reliable when files are focused. Prefer smaller, focused files over large ones that do too much.
- Files that change together should live together. Split by responsibility, not by technical layer.
- In existing codebases, follow established patterns. If the codebase uses large files, don't unilaterally restructure - but if a file you're modifying has grown unwieldy, including a split in the plan is reasonable.

This structure informs the step decomposition. Each step should produce self-contained changes that make sense independently.

## Task Right-Sizing

A step is the smallest unit that carries its own test cycle and its own commit: one test file's worth of behaviour, at most 8 files. When drawing step boundaries: fold setup, configuration, scaffolding, and documentation into the step whose deliverable needs them; split only where a reviewer could meaningfully reject one step while approving its neighbor. Each step ends with an independently testable deliverable and one commit.

A chunk is one implementer: the chunks run in order, one after the other, in the same plan tree. A chunk is opus when it adds a module or touches more than five files, else sonnet. A small plan has one chunk.

## Plan Document Shape

The template's sections, in order:

```markdown
# <title> implementation plan

## Agreed rung
The rung of plan.md this plan delivers, its item numbers and the gate modifications; nothing outside them is built.

## Approach
Mode (meta or component), the tree and branch, the order of chunks and the rules every chunk follows.

## Chunk <k>: <name> (model: <sonnet|opus>)

### S<n>: <title>

- **Files**: every file the step creates, edits or deletes.
- **Covers**: the plan.md items (<n>.<m>) this step delivers.
- **Test first**: the test written and seen failing before the change, or the named exception.
- **Change**: what the step changes, concretely.
- **Verify**: the exact command and the summary line to expect.

## Files to delete
Every path the plan removes, grouped by chunk; "none" if none.

## Final verify
The repo's full test and lint command, run on the last commit.

## After merge
Steps that run in the main checkout after the merge, in order; "none" if none.
```

## What a Step Contains

A step is done when the implementer can write exactly one reasonable thing from it. That is the whole requirement: unambiguous, not complete. Each field carries what makes it unambiguous and nothing more:

- **Test first:** the test file, the test's name and its assertions, with plan.md's exact values in them, and the reason it fails before the change. The exceptions are narrow and named: pure formatting, a comment or doc edit, a dependency bump with no behaviour change, or a deletion pinned by a retirement test (which asserts on `git ls-files <path>`, never the filesystem).
- **Change:** the exact signature (name, parameters, return type), the file it lives in, and the specific values plan.md pins. The implementer writes the body. A body appears only for an algorithm the signature and tests do not determine, or for exact copy plan.md fixes.
- **Verify:** the command to run and the output that means it passed; targeted (the named test files or a component suite plus lint), never the full suite. Use the exact command the repo runs it with.
- **A reference to another step:** name the step (`S<n>`); the plan does not repeat that step's code.

Never plan a step that edits, deletes, skips or xfails a test to make it pass, unless the test itself is no longer accurate; then the step names which test and why. No backward compatibility in a step unless the user asked for it.

A plan is the set of decisions the implementer cannot make alone. A plan longer than the code it describes has written the code instead. Lines that decide nothing ("TBD", "handle edge cases", "add appropriate validation", "write tests for the above", a type or function no step defines) are the opposite failure, and the self-review catches both.

## Self-Review

After writing the complete plan, look at plan.md's agreed rung with fresh eyes and check the plan against it. This is a checklist you run yourself - not a subagent dispatch.

**1. Rung coverage:** Take each item of the agreed rung. Can you point to a step whose Covers names it? Add a step for any gap.

**2. Over-coverage:** Does any step build something no agreed item asks for? Remove it; the reviewer would report it as over-delivery.

**3. Step scan:** Every step must let the implementer write exactly one reasonable thing, and no step may carry more than that: a line that decides nothing is a gap, a function body the signature and tests already determine is a transcript. Fix both.

**4. Type consistency:** Do the types, method signatures, and property names you used in later steps match what you defined in earlier steps? A function called `clearLayers()` in S3 but `clearFullLayers()` in S7 is a bug.

**5. Failure modes:** For each input class or failure mode plan.md implies but no step's test exercises, the one most likely to bite a person using this software gets its test added to the Test first of the step that owns the code.

**6. Proportion:** A plan several times longer than plan.md is a transcript of the program, not a plan. Replace bodies with signatures, test names and assertions, and check that each step is still unambiguous.

If you find issues, fix them inline. No need to re-review - just fix and move on.

## Hand-off

Commit plan.md and implementation-plan.md together as `docs(plan): <plan> implementation plan`, then return at most 200 words: the chunk count and order, and the commit.

There is no second gate: the user's answer at the brainstorming gate approved the run, and implementation-plan.md is the contract the reviewer checks the whole diff against. The orchestrator goes straight on with superpowers:subagent-driven-development.
