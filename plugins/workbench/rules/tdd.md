# Test-driven development

Every behaviour change is written test-first. Not "tested afterwards" - the test
comes first and is seen failing before the code that makes it pass exists.

1. **Red.** Write the test and run it. Watch it fail, and check it fails for the
   reason you expect. A test that passes before the implementation exists is
   asserting nothing, and this is the step that catches that.
2. **Green.** Write the smallest implementation that passes it.
3. **Refactor.** Clean up with the test still green.

This is not optional because the change is small, urgent, or "obviously
correct". Those are the changes that ship broken.

Legitimate exceptions, and they are narrow: pure formatting, a comment or doc
edit, a dependency bump with no behaviour change, a spike you are going to
throw away, or a deletion pinned by a retirement test (the diff's non-test
changes are deletions only and it adds or changes a test that pins the removal). If you skip the cycle, say which exception applied - do not claim a
red-green cycle you did not run.

## Verify before reporting back

Never report work as done, passing, or complete without having run the check and
read its output. This applies especially when handing work back to an
orchestrating agent, which cannot see your terminal and will take the claim at
face value.

- Run the repo's own command (`mise run test`, or whatever the repo defines).
- Quote the real output, including the pass/fail summary line.
- "Should pass", "the change is straightforward", and a green diff are not
  evidence. An unread command is an unrun command.

If verification fails and you cannot fix it, say so with the output. A named
failure is useful; a false pass costs the next agent hours.
