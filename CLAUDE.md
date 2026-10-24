@AGENTS.md

## Claude Code only

- Plugin skills are namespaced `workbench:<skill>` (for example `workbench:init`,
  `workbench:start-development`). Other harnesses use the bare skill name.
- After editing a plugin, run `/reload-plugins` to pick up the change.
- `epic-run` dispatches its implementer and reviewer agents in the background.
- The first run in a clone shows the trust dialog; accept it so project settings and the
  workbench plugins load.
