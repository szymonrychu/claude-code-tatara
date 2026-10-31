# Plan inputs

Every research brief and the reuse-hunter answer end in `## Plan inputs`: four lists,
"none" when empty, one line per entry.

- `reuse`: name - file:symbol - which design or plan items need it.
- `do-not-build`: item - what provides it instead - source.
- `fix-as-ac`: anti-pattern - where - the test or verify step that pins the fix.
- `ideas`: adopted / rejected, one line each, with the source.

The briefs are discovery input to `superpowers:brainstorming`: the design it writes in
`docs/superpowers/specs/` and the plan `superpowers:writing-plans` writes from it in
`docs/superpowers/plans/` place every entry. Keep the brief paths, never their contents.
