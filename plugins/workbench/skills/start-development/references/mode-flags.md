# Mode flags: verify the blast radius before the gate

Read from Phase 2 of `start-development` when the change turns on a runtime mode.

If the change turns on a runtime mode - a multiplexing flag, a new isolation or
tenancy mode, a scoping or sandboxing switch, a different execution or storage
backend - then the design is not ready for the gate until you have answered,
from the source rather than by inference:

**what does this flag change about the configuration contract that already
works today?**

A mode flag rarely just adds behaviour. It usually re-scopes how existing
settings, credentials and env are resolved, and everything currently delivered
the old way silently resolves to a default. Defaults are where this bites:
an empty allowlist means deny, an absent model means no provider, an empty
scope is still a scope.

Verify all four before the gate, read-only, against the running system:

1. **Env and secrets.** Does the flag change which env the process sees? Does
   anything stop falling back to the process environment? List every variable
   the deployment supplies the old way and confirm each one still resolves.
2. **Inheritance.** Does the new mode inherit existing config, or does each
   unit start empty? "Independent islands" is common and catastrophic when the
   chart only writes part of the contract.
3. **Sibling state.** Stores, caches and state dirs that were global may become
   per-unit. Writers and readers can end up on opposite sides of the split.
4. **The disable path.** Turning it off must be as clean as turning it on.
   Config appliers that merge do NOT remove keys they stop rendering, so a
   values-level `enabled: false` can leave the runtime still in the new mode.
   If there is no prune path, build one as part of the feature.

This is cheap - one read-only probe of the resolution code - and it is the
difference between finding the defect in a probe and finding it in production.
Rendered-manifest tests cannot catch any of it: they assert what the chart
writes, never what the runtime resolves. If nothing in the plan exercises
resolution inside the real process, say so at the gate as a known risk.
