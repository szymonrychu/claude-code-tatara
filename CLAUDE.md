@AGENTS.md

## Claude Code only

- Plugin skills are namespaced: `superpowers:<skill>` for vanilla superpowers, `workbench:<skill>`
  for the workbench helpers (for example `workbench:init`). Other harnesses use the bare skill
  name.
- After editing a plugin, run `/reload-plugins` to pick up the change.
- The first run in a clone shows the trust dialog; accept it so project settings and the
  workbench plugins load.
- In a Claude Code cloud session the trust dialog and `/reload-plugins` do not exist: the
  project SessionStart hook installs the plugins instead. Setup and limits:
  `docs/claude-cloud.md`.
