import re
from pathlib import Path

SKILLS = Path(__file__).resolve().parents[2]
ROOT = Path(__file__).resolve().parents[3]
START_RESEARCH = SKILLS / "start-research"
PERSONAS = START_RESEARCH / "personas"


def frontmatter(path):
    text = path.read_text()
    assert text.startswith("---\n"), f"{path.name} missing YAML frontmatter"
    end = text.index("\n---", 4)
    fm = {}
    for line in text[4:end].splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            fm[key.strip()] = value.strip().strip('"')
    return fm


def test_personas_dir_is_gone():
    assert not PERSONAS.exists()


def test_start_research_frontmatter():
    fm = frontmatter(START_RESEARCH / "SKILL.md")
    assert fm.get("name") == "start-research"
    assert fm.get("description")


def test_start_research_references_its_assets():
    text = (START_RESEARCH / "SKILL.md").read_text()
    assert "scripts/brief_path.sh" in text
    assert "personas/" not in text
    assert "workbench:research-<persona>" in text
    assert "workbench:research-reviewer" in text
    assert (START_RESEARCH / "scripts" / "brief_path.sh").is_file()


def _procedure():
    text = (START_RESEARCH / "SKILL.md").read_text()
    start = text.index("2. **Research (parallel).**")
    return re.sub(r"\s+", " ", text[start : text.index("4. **Follow-up", start)])


def test_dispatches_persona_agents():
    step = _procedure()
    research, review = step.split("3. **Review")
    assert "subagent_type: workbench:research-<persona>" in research
    assert "model: sonnet" in research
    assert "subagent_type: workbench:research-reviewer" in review
    assert "model: sonnet" in review
    for persona in ("docs-purist", "practitioner", "prior-art-scout", "paper-scout"):
        assert (ROOT / "agents" / f"research-{persona}.md").is_file()
    assert (ROOT / "agents" / "research-reviewer.md").is_file()


def test_prompts_carry_only_inputs_and_say_where_paths_come_from():
    step = _procedure()
    assert "carries only the topic and the output path" in step
    assert "carries only the topic, every lens brief path, and its own output path" in step
    assert 'doc_path.sh research "<topic>-<persona>"' in step
    assert 'doc_path.sh research "<topic>-review"' in step


def test_no_reasoning_depth_instruction_in_prompts():
    text = (START_RESEARCH / "SKILL.md").read_text()
    assert "reasoning depth" not in text
    assert "explicitly" in text and "model: sonnet" in text


START_DEVELOPMENT = SKILLS / "start-development"

EXPECTED_SKILL_MENTIONS = (
    "git-submodules-refresh",
    "start-discovery",
    "plan-run",
    "git-worktrees-commit",
    "git-worktrees-push",
    "pullrequests-update",
    "pullrequests-watch",
    "start-research",
    "research-code-internal",
    "research-code-external",
    "research-papers",
    "research-docs",
    "start-review",
    "start-debugging",
)

RESEARCH_SKILLS = (
    "research-code-internal",
    "research-code-external",
    "research-papers",
    "research-docs",
)

LOCAL_SKILL_DIRS = (
    "git-submodules-refresh",
    "start-research",
    "start-discovery",
    "plan-run",
    "git-worktrees-create",
    "git-worktrees-commit",
    "git-worktrees-push",
    "pullrequests-update",
    "pullrequests-watch",
    "research-code-internal",
    "research-code-external",
    "research-papers",
    "research-docs",
    "start-review",
    "start-debugging",
)


def sd_text(skill):
    """SKILL.md plus every reference file, for rules that live in a reference."""
    refs = sorted((skill.parent / "references").glob("*.md"))
    return "\n".join([*(r.read_text() for r in refs), skill.read_text()])


def skill_with_references():
    """SKILL.md plus every references/*.md, for rules that moved out of the body."""
    parts = [(START_DEVELOPMENT / "SKILL.md").read_text()]
    for ref in sorted((START_DEVELOPMENT / "references").glob("*.md")):
        parts.append(ref.read_text())
    return "\n".join(parts)


def test_start_development_frontmatter():
    fm = frontmatter(START_DEVELOPMENT / "SKILL.md")
    assert fm.get("name") == "start-development"
    assert fm.get("description")


def test_start_development_mentions_every_chained_skill():
    text = sd_text(START_DEVELOPMENT / "SKILL.md")
    for name in EXPECTED_SKILL_MENTIONS:
        assert name in text, f"SKILL.md does not mention {name}"


def test_start_development_local_skill_references_resolve():
    for name in LOCAL_SKILL_DIRS:
        assert (SKILLS / name).is_dir(), f"referenced local skill missing: {name}"


def test_start_development_does_not_chain_superpowers():
    """start-development owns its own flow; superpowers is not a dependency."""
    text = sd_text(START_DEVELOPMENT / "SKILL.md")
    invocations = re.findall(r"[Ii]nvoke `superpowers:[a-z-]+`", text)
    assert not invocations, f"start-development still invokes superpowers: {invocations}"


def test_new_agents_exist_and_are_read_only():
    for name in ("codebase-cartographer",):
        f = ROOT / "agents" / f"{name}.md"
        assert f.is_file(), f"agents/{name}.md missing"
        fm = frontmatter(f)
        assert fm.get("name") == name
        assert fm.get("description")
        tools = fm.get("tools") or ""
        for forbidden in ("Edit", "Write"):
            assert forbidden not in str(tools), f"{name} must stay read-only, got {tools}"


def test_start_development_states_delivery_is_mandatory():
    """Requested scope ships regardless of how many rounds it takes."""
    text = _flat(sd_text(START_DEVELOPMENT / "SKILL.md"))
    assert "## Delivery is not optional" in text
    assert "## Boy scout rule" in text
    assert "bounds a loop, never the delivery" in text, "the fix-round cap must not cap delivery"


def test_boy_scout_rule_ships_with_the_plugin():
    rule = ROOT / "rules" / "boy-scout.md"
    assert rule.is_file(), "rules/boy-scout.md missing"
    text = rule.read_text()
    for clause in ("Simplify what you touch", "uncommitted", "adjacent commits"):
        assert clause in text, f"boy-scout rule does not cover {clause!r}"


def test_execution_goes_through_plan_run():
    """Phase 4 invokes the plan-run skill; the retired workflow is not named."""
    text = sd_text(START_DEVELOPMENT / "SKILL.md")
    assert "`plan-run`" in text
    assert "plan-execute" not in text


def test_cartographer_can_actually_use_lsp():
    """Lane 2 is inert unless the agent holds the LSP tool, not just the binary."""
    fm = frontmatter(ROOT / "agents" / "codebase-cartographer.md")
    tools = str(fm.get("tools"))
    assert "LSP" in tools, "cartographer cannot run the LSP lane without the LSP tool"


def test_start_discovery_never_builds_a_graph():
    text = (SKILLS / "start-discovery" / "SKILL.md").read_text()
    assert "--mode deep" not in text, "discovery must not build a graph"
    assert "graphify" not in text.lower()


def _agent_body(name):
    return (ROOT / "agents" / f"{name}.md").read_text()


def test_no_graphify_in_discovery_agents():
    for name in ("codebase-cartographer", "reuse-hunter"):
        text = _agent_body(name)
        assert "graphify" not in text.lower(), f"{name} still mentions graphify"
        body = text.split("\n---", 1)[1]
        assert "LSP" in body and "grep" in body.lower()


def test_guard_bash_protects_the_shared_stash_stack():
    text = (ROOT / "hooks" / "lib" / "core.py").read_text()
    assert "stash" in text, "guard-bash must cover git stash pop/drop/clear"


def test_tdd_rule_ships_with_the_plugin():
    text = (ROOT / "rules" / "tdd.md").read_text()
    for clause in ("Red", "Green", "Refactor", "Verify before reporting back"):
        assert clause in text, f"tdd rule does not cover {clause!r}"


def test_orchestrator_is_told_to_delegate_and_to_stop_at_75_percent():
    text = sd_text(START_DEVELOPMENT / "SKILL.md")
    assert "## Orchestrate. Do not implement." in text
    assert "75%" in text, "the context stop condition must be explicit"
    assert "## Loop until it is actually finished" in text


def test_worktree_skills_ship_with_scripts_and_refuse_reuse():
    for name, script in (("worktree-create", "create.py"), ("worktree-merge", "merge.py")):
        d = SKILLS / name
        assert (d / "SKILL.md").is_file(), f"{name} has no SKILL.md"
        assert (d / "scripts" / script).is_file(), f"{name} has no {script}"
        fm = frontmatter(d / "SKILL.md")
        assert fm.get("name") == name
    create = (SKILLS / "worktree-create" / "scripts" / "create.py").read_text()
    assert "already exists" in create, "create must refuse a name already in use"
    merge = (SKILLS / "worktree-merge" / "scripts" / "merge.py").read_text()
    assert "merged_into" in merge, "merge must verify the work landed before cleaning up"


def test_orchestrator_delegates_merges_to_a_sized_agent():
    """Merges are the most context-expensive step; the orchestrator must not do them."""
    skill = skill_with_references()
    assert "worktree-merger" in skill
    assert "Never merge a worktree yourself" in skill
    assert "--assess" in skill, "model choice must come from the assessment, not a guess"

    agent = ROOT / "agents" / "worktree-merger.md"
    assert agent.is_file()
    fm = frontmatter(agent)
    assert fm.get("name") == "worktree-merger"
    assert fm.get("model") in ("sonnet", "opus")
    # this agent legitimately writes: it resolves conflicts and lands the merge
    assert "Bash" in str(fm.get("tools"))


def test_assess_reports_a_model_without_leaking_the_diff():
    text = (SKILLS / "worktree-merge" / "scripts" / "merge.py").read_text()
    assert "def assess(" in text
    assert '"model"' in text and "opus" in text and "sonnet" in text
    assert "merge-tree" in text, "conflict prediction should not touch a worktree"


def _meta_block(text: str) -> str:
    start = text.index("export const meta = {")
    depth, i = 0, text.index("{", start)
    for j in range(i, len(text)):
        if text[j] == "{":
            depth += 1
        elif text[j] == "}":
            depth -= 1
            if depth == 0:
                return text[i : j + 1]
    raise AssertionError("unterminated meta block")


def test_phase_seven_picks_the_host_instead_of_assuming_gitlab():
    """A workbench can hold GitHub and GitLab repos; the merge phase must resolve per repo."""
    text = skill_with_references()
    assert "remote get-url origin" in text, "the host must be detected, not assumed"
    for skill in (
        "pullrequests-update",
        "pullrequests-watch",
    ):
        assert skill in text, f"phase 7 does not offer {skill}"
        assert (SKILLS / skill).is_dir(), f"referenced skill does not exist: {skill}"


OLD_SCM_SKILL_NAME = re.compile(r"(?:github-pull|gitlab-merge)(?:request)s?-\w")


def test_no_retired_scm_skill_names_in_flow_docs():
    docs = (
        START_DEVELOPMENT / "SKILL.md",
        START_DEVELOPMENT / "references" / "merge-hosts.md",
        ROOT / "README.md",
    )
    for doc in docs:
        text = doc.read_text()
        found = OLD_SCM_SKILL_NAME.search(text)
        assert not found, f"{doc.name} still names {found.group(0)}"
    merge_hosts = (START_DEVELOPMENT / "references" / "merge-hosts.md").read_text()
    assert "WORKBENCH_SCM_HOSTS" in merge_hosts


def test_one_gate_only():
    """All human review happens once, up front; everything after runs unattended."""
    text = sd_text(START_DEVELOPMENT / "SKILL.md")
    headings = re.findall(r"^## The gate\s*$", text, re.M)
    assert len(headings) == 1, f"expected exactly one '## The gate' heading, got {len(headings)}"
    assert not re.search(r"^#+ .*Gate 1", text, re.M), "a 'Gate 1' heading remains"
    assert not re.search(r"^#+ .*Gate 2", text, re.M), "a 'Gate 2' heading remains"
    assert "runs unattended to merge" in text
    assert "recommended answer" in text
    assert "## Phase 3 - Detailed" not in text, "the post-gate question round must be gone"


def test_skill_body_fits_the_documented_cap():
    lines = (START_DEVELOPMENT / "SKILL.md").read_text().splitlines()
    assert len(lines) <= 150, f"SKILL.md is {len(lines)} lines; the cap is 150"


def test_every_reference_and_template_named_exists():
    text = (START_DEVELOPMENT / "SKILL.md").read_text()
    prefix = r"(?:\$\{CLAUDE_PLUGIN_ROOT\}/|plugins/[\w-]+/)?"
    named = set(re.findall(prefix + r"references/[a-z-]+\.md", text))
    named |= set(re.findall(prefix + r"templates/[a-z]+\.md", text))
    assert named, "SKILL.md names no references or templates"
    for rel in sorted(named):
        if rel.startswith("${CLAUDE_PLUGIN_ROOT}/"):
            path = ROOT / rel.removeprefix("${CLAUDE_PLUGIN_ROOT}/")
        elif rel.startswith("plugins/"):
            path = ROOT.parents[1] / rel
        else:
            path = START_DEVELOPMENT / rel
        assert path.is_file(), f"SKILL.md names a missing file: {rel}"


def test_research_steps_table():
    text = sd_text(START_DEVELOPMENT / "SKILL.md")
    section = " ".join(_section(text, "## Phase 1 - Discovery").split())
    for name in RESEARCH_SKILLS:
        assert name in section, f"phase 1 does not name {name}"
    assert "skipped" in section and "Run when" in section


def test_closing_phase_relays_the_retro():
    phase4 = " ".join(_section(sd_text(START_DEVELOPMENT / "SKILL.md"), "## Phase 4 - Run").split())
    assert "retro.md" in phase4
    assert "closing message" in phase4
    assert "recommendations" in phase4


def test_run_passes_the_plan_path_and_tree():
    phase4 = _flat(_section(_skill(), "## Phase 4 - Run"))
    for key in ("the plan path", "its chunk number", "references/worktrees.md"):
        assert key in phase4, f"Phase 4 does not mention {key}"


FRESHNESS_SENTENCE = (
    "a subagent cannot end a turn in a worktree whose last test run was not on its HEAD"
)


def _flat(text):
    """Collapse line wrapping so a sentence matches however the prose is wrapped."""
    return re.sub(r"\s+", " ", text)


def _section(text, heading):
    start = text.index(heading)
    end = text.find("\n## ", start + 1)
    return text[start:] if end == -1 else text[start:end]


def _skill():
    return sd_text(START_DEVELOPMENT / "SKILL.md")


def test_phase_three_writes_the_implementation_plan():
    phase3 = _flat(_section(_skill(), "## Phase 3 - Implementation plan"))
    assert "implementation-plan.md" in phase3
    assert "agreed rung only" in phase3


def test_gate_questions_carry_recommended_answers():
    gate = _flat(_section(_skill(), "## The gate"))
    wording = 'numbered, each with a recommended answer, worded so that "yes" accepts it'
    assert wording in gate


def test_phase4_names_plan_branch_and_main_checkout():
    phase4 = _flat(_section(_skill(), "## Phase 4 - Run"))
    for term in ("branch `<plan>`", "main checkout"):
        assert term in phase4, f"Phase 4 does not name {term!r}"


def test_run_names_the_reviewer_and_the_whole_diff():
    phase4 = _flat(_section(_skill(), "## Phase 4 - Run"))
    for term in ("workbench:reviewer", "`git diff <base>...HEAD`", "under-delivery"):
        assert term in phase4, f"Phase 4 does not name {term!r}"


def test_run_uses_start_review_and_start_debugging():
    text = _skill()
    phase4 = _section(text, "## Phase 4 - Run")
    assert "start-review" in phase4
    assert "start-debugging" in phase4
    assert "health" in phase4
    assert "/code-review" not in text, "the native /code-review is replaced by start-review"


def test_hooks_section_names_the_freshness_guard():
    text = _flat(_skill())
    assert "## Hooks that hold the line" in text
    hooks = START_DEVELOPMENT / "references" / "hooks.md"
    assert "references/hooks.md" in text
    assert hooks.is_file()
    combined = text + " " + _flat(hooks.read_text())
    assert "verification-freshness" in combined
    assert "commit guard" in combined
    assert FRESHNESS_SENTENCE in combined


def test_tdd_section_requires_red_evidence_and_independent_verification():
    tdd = _flat(_section(_skill(), "## Test-driven, and verified before it is believed"))
    assert "the red run is part of the deliverable" in tdd
    assert "verified on HEAD <sha> by an agent that did not write it" in tdd


def _ref(name):
    return (START_DEVELOPMENT / "references" / name).read_text()


def test_gate_answer_is_the_only_approval():
    gate = _flat(_section(_skill(), "## The gate"))
    for term in ("Pick a rung per plan", "The user's answer is the only approval"):
        assert term in gate, f"the gate does not say {term!r}"
    assert "approvals" not in gate


def test_worktrees_reference_covers_helpers_for_every_role():
    text = _flat((START_DEVELOPMENT / "references" / "worktrees.md").read_text())
    for term in (
        "A helper spawned by an implementer",
        "spawned by the reviewer",
        "read-only like its parent",
        "merge helper",
        "never in another",
    ):
        assert term in text, f"references/worktrees.md does not say {term!r}"


def test_phase_four_dispatches_in_the_background():
    phase4 = _flat(_section(_skill(), "## Phase 4 - Run"))
    assert "in the background" in phase4


def test_scope_section_forbids_later_parking():
    scope = _flat(_section(_skill(), "## Scope is not negotiable"))
    for term in ('No "later" parking', "named blocker", "recommended, never built"):
        assert term in scope, f"the Scope section does not say {term!r}"


def test_closing_message_is_short():
    phase4 = _flat(_section(_skill(), "## Phase 4 - Run"))
    assert "three lines at most" in phase4
    assert "concise-orchestrator" in phase4


def test_tickets_reference_is_linked():
    assert "references/tickets.md" in _skill()


def test_phase_four_reap_line_has_no_conditional_parking():
    flat = _flat(_section(_skill(), "## Phase 4 - Run"))
    assert "removes the rest on request" not in flat
    assert "`ticket.py reap --plan <plan>` sweeps any left over" in flat


def test_topic_focus_goes_to_practitioner():
    text = re.sub(r"\s+", " ", (START_RESEARCH / "SKILL.md").read_text())
    assert "topic-specific persona" not in text
    assert "security-auditor" not in text
    assert "focus line" in text and "workbench:research-practitioner" in text
