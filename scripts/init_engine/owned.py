"""The one place the template's instance-owned and generated paths are named.

INSTANCE_OWNED: paths the template repo uses for its own development; a new or adopted
workbench must not inherit them and a template update never brings them. Kinds:
  phase      emptied and recreated as an empty dir holding .gitkeep
  delete     removed (file or dir; missing is fine)
  rewritten  left alone here; project_files.memory_and_roadmap writes fresh content

RETIRED: the workbench flow paths retired for plugins/superpowers; a template update drops
whatever the template stages under them so the retired flow never comes back. Names are
built from parts so the retired-name scan does not match this file.

GENERATED_ON_CONFLICT: generated files an update resolves by regeneration instead of
leaving conflict markers. The config-dir entries are relative to workbench.config_dir,
which the caller resolves.
"""

INSTANCE_OWNED: tuple[tuple[str, str], ...] = (
    ("docs/plans/todo", "phase"),
    ("docs/plans/in-progress", "phase"),
    ("docs/plans/done", "phase"),
    ("docs/plans/contracts.json", "delete"),
    ("docs/plans/index.json", "delete"),
    ("docs/plans/facts.md", "delete"),
    ("docs/research", "delete"),
    ("docs/handoffs", "delete"),
    ("MEMORY.md", "rewritten"),
    ("ROADMAP.md", "rewritten"),
)

_START, _PLAN = "start-", "plan-"
RETIRED: tuple[str, ...] = (
    *(
        f"plugins/workbench/skills/{name}"
        for name in (
            _START + "development",
            _START + "discovery",
            _PLAN + "run",
            "interro" + "gate",
            _START + "debugging",
            "debug",
            _START + "review",
            "review",
        )
    ),
    f"plugins/workbench/agents/{_PLAN}writer.md",
)

GENERATED_ON_CONFLICT: tuple[str, ...] = (
    "AGENTS.md",
    ".mise.toml",
    "docs/architecture.md",
    "LICENSE",
    ".claude-plugin/marketplace.json",
    "settings.json",  # in the config dir
    "workbench.json",  # in the config dir
)
