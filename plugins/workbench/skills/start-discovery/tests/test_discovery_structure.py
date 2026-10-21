from pathlib import Path

SKILLS = Path(__file__).resolve().parents[2]
RESEARCH = (SKILLS / "start-research" / "SKILL.md").read_text()
DISCOVERY = (SKILLS / "start-discovery" / "SKILL.md").read_text()


def test_start_research_mentions_lenses_and_plan_inputs():
    for needle in (
        "lenses",
        "paper-scout",
        "doc_path.sh",
        "## Plan inputs",
        "do-not-build",
        "fix-as-ac",
        "ideas",
        "reuse",
    ):
        assert needle in RESEARCH, f"start-research missing {needle!r}"


def test_start_research_keeps_brief_path_and_personas():
    assert "brief_path.sh" in RESEARCH
    assert "workbench:research-docs-purist" in RESEARCH
    assert "personas/" not in RESEARCH


def test_start_discovery_has_reuse_hunt_lane():
    for needle in (
        "### Lane 4",
        "research-code-internal",
        "shared-parts map",
        "Plan inputs",
        "prior-art-scout",
        "docs-purist",
        "paper-scout",
    ):
        assert needle in DISCOVERY, f"start-discovery missing {needle!r}"


def test_start_discovery_under_200_lines():
    assert len(DISCOVERY.splitlines()) < 200


def test_codebase_lane_is_lsp_and_grep():
    lane = DISCOVERY.split("### Lane 1")[1].split("### Lane 2")[0]
    assert "LSP" in lane
    assert "grep is the codebase fallback" in lane
    assert "### Lane 5" not in DISCOVERY
    assert "five lanes" not in DISCOVERY and "four lanes" in DISCOVERY


def test_no_graphify_in_discovery_docs():
    root = SKILLS.parent
    for rel in (
        "skills/start-discovery/SKILL.md",
        "agents/codebase-cartographer.md",
        "agents/reuse-hunter.md",
    ):
        assert "graphify" not in (root / rel).read_text().lower(), rel


def test_discovery_has_no_graph_build_instructions():
    assert "--mode deep" not in DISCOVERY
    assert "~/.local/bin/graphify" not in DISCOVERY
    assert "info/exclude" not in DISCOVERY
    assert "build one, then query it" not in DISCOVERY
