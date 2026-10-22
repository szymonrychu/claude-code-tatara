# MEMORY

Dated entries, newest last. Supersede an entry rather than deleting it. One line per non-obvious decision.

2026-10-20: plugins/workbench imported from the workbench plugin v2.1.0 at 116541b by git archive, without docs/, the grafana incident reports, the personal topology note and uv.lock; baseline suite: components 25, assertions 2100.

2026-10-20: scripts/probes/claude-plugin-load.sh on Claude Code 2.1.304: a git-archive copy with hasTrustDialogAccepted loads workbench@workbench-template from <dir>/plugins/workbench (init event plugins[]), no other workbench plugin; exit 0. Root marketplace entries carry the core manifest version (2.1.0; manifest, entry and plugin-local marketplace move together); packs are 1.0.0.
2026-10-20: scripts/probes/claude-plugin-load.sh on Claude Code 2.1.304: a git-archive copy with hasTrustDialogAccepted loads workbench@workbench-template from <dir>/plugins/workbench (init event plugins[]), no other workbench plugin; exit 0. Root marketplace entries carry the core manifest version (2.1.0); packs are 1.0.0.

2026-10-22: prompt-cache probe (run wf_c93a609a-e42, hook-probe.js args.probe=cache, read with hook-evidence.py --cache). cache_creation / cache_read per agent: static#1 21830/0; static#2 14855/6975; static#3 14855/6975; task#1 14855/6975; task#2 14855/6975; task#3 14855/6975. Verdict `CACHE none static=14855,14855 task=14855,14855`: static-first ordering reads no more cache than task-first. Decision: implPrompt and verifyPrompt are not reordered (design D6); plugins/workbench/workflows/tests/plan-execute-prompt-prefix.test.mjs pins the current order so a later reorder is deliberate.
