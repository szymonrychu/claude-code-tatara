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
    "git-worktrees-create",
    "workbench:plan-execute",
    "scope-auditor",
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
    "heartbeat",
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
    "heartbeat",
)


_MOVED = ("phases-1-3.md", "phase-4-execute.md", "phases-5-7.md", "non-negotiables.md")


def sd_text(skill):
    """SKILL.md plus the reference files its blocks moved to. References come first, so a section
    heading resolves to its full text rather than to the pointer left in SKILL.md."""
    refs = skill.parent / "references"
    return "\n".join([*((refs / n).read_text() for n in _MOVED), skill.read_text()])


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


def test_plan_execute_workflow_exists():
    wf = ROOT / "workflows" / "plan-execute.js"
    assert wf.is_file(), "workflows/plan-execute.js missing"
    text = wf.read_text()
    assert "export const meta" in text
    assert "plan-execute" in text
    for key in ("tasks", "planText"):
        assert key in text, f"plan-execute.js does not read args.{key}"


def test_new_agents_exist_and_are_read_only():
    for name in ("scope-auditor", "codebase-cartographer"):
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
    text = sd_text(START_DEVELOPMENT / "SKILL.md")
    assert "## Delivery is not optional" in text
    assert "## Boy scout rule" in text
    assert "uncapped" in text, "the uncapped review loop must be stated, not implied"


def test_boy_scout_rule_ships_with_the_plugin():
    rule = ROOT / "rules" / "boy-scout.md"
    assert rule.is_file(), "rules/boy-scout.md missing"
    text = rule.read_text()
    for clause in ("Simplify what you touch", "uncommitted", "adjacent commits"):
        assert clause in text, f"boy-scout rule does not cover {clause!r}"


def test_plan_execute_prompts_carry_the_standing_rules():
    text = (ROOT / "workflows" / "plan-execute.js").read_text()
    implementer = (ROOT / "agents" / "implementer.md").read_text()
    assert "workbench:implementer" in text
    assert "Boy scout rule" in implementer, "the implementer agent lost the boy scout rule"
    assert "Escalating is not dropping the work" in text, (
        "the review cap must hand work back to the orchestrator, never drop it"
    )


def test_plan_execute_is_invoked_with_its_plugin_namespace():
    """Plugin workflows resolve as <plugin>:<meta.name>; a bare name does not exist."""
    text = sd_text(START_DEVELOPMENT / "SKILL.md")
    assert "workbench:plan-execute" in text
    bare = re.findall(r"name: '(?!workbench:)[^']*plan-execute'", text)
    assert not bare, f"bare plan-execute Workflow name would not resolve: {bare}"


def test_plan_execute_runs_are_named_copies():
    """A run gets its own name only via a named copy launched by scriptPath."""
    text = sd_text(START_DEVELOPMENT / "SKILL.md")
    assert "${CLAUDE_PLUGIN_ROOT}/workflows/named-copy.mjs plan-execute" in text
    assert "scriptPath:" in text
    assert (ROOT / "workflows" / "named-copy.mjs").is_file()


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


def test_mutating_agents_are_pinned_to_their_own_worktree():
    """Isolation is enforced by the flow: one named worktree per agent, entered on start."""
    text = (ROOT / "workflows" / "plan-execute.js").read_text()
    assert "EnterWorktree with path" not in text, (
        "the built-in EnterWorktree relocates the permission root and prompts on every"
        " skill-created tree; agents address their tree by absolute path instead"
    )
    assert "absolute path" in text
    assert "isolation: 'worktree'" not in text, (
        "harness isolation would create a second tree and strand the work"
    )
    skill = sd_text(START_DEVELOPMENT / "SKILL.md")
    assert "worktree-create" in skill and "worktree-merge" in skill


def test_deliverable_schema_forces_tdd_and_verification():
    """A task cannot be returned without test evidence and an observed passing run."""
    text = (ROOT / "workflows" / "plan-execute.js").read_text()
    for field in ("'tests'", "'verification'", "wroteTestFirst", "evidence"):
        assert field in text, f"deliverable schema is missing {field}"
    assert "function verified(" in text, "verification must be checked in code"
    assert "verified(impl)" in text, "the review loop must gate clean on verification"


def test_tdd_rule_ships_with_the_plugin():
    text = (ROOT / "rules" / "tdd.md").read_text()
    for clause in ("Red", "Green", "Refactor", "Verify before reporting back"):
        assert clause in text, f"tdd rule does not cover {clause!r}"


def test_workflow_loops_until_the_audit_is_clean():
    """One pass then reporting gaps is not delivery; the workflow re-dispatches."""
    text = (ROOT / "workflows" / "plan-execute.js").read_text()
    assert "Remediation round" in text, "no outer remediation loop"
    assert "finished" in text, "callers need an explicit finished flag to loop on"
    assert "escalated" in text, "what the loop could not close must be returned, not spun on"


def test_orchestrator_is_told_to_delegate_and_to_stop_at_75_percent():
    text = sd_text(START_DEVELOPMENT / "SKILL.md")
    assert "## Orchestrate. Do not implement." in text
    assert "75%" in text, "the context stop condition must be explicit"
    assert "## Loop until it is actually finished" in text


def test_nested_subagents_are_permitted_with_conditions():
    """Nesting is allowed; the file-partition condition is what keeps it safe."""
    wf = (ROOT / "workflows" / "plan-execute.js").read_text()
    assert "MAY spawn helper subagents" in wf
    assert "Partition their work by file" in wf
    skill = sd_text(START_DEVELOPMENT / "SKILL.md")
    assert "Nesting is allowed" in skill
    assert "Sub-subagents do not get worktrees" in skill


def test_implementers_are_denied_the_for_later_escape_hatches():
    text = (ROOT / "workflows" / "plan-execute.js").read_text()
    for hatch in ("for later", "TODO", "phase 2"):
        assert hatch in text, f"the {hatch!r} escape hatch is not closed explicitly"


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


def test_every_workflow_meta_is_a_pure_literal():
    """A non-literal meta makes the whole workflow fail to register, silently.

    This cost two live runs: the workflow existed, was syntactically valid, and
    simply never appeared in the registry because whenToUse used ' + ' string
    concatenation. There is no error message for it anywhere.
    """
    workflows = sorted((ROOT / "workflows").glob("*.js"))
    assert workflows, "no workflows found"
    for wf in workflows:
        meta = _meta_block(wf.read_text())
        # Punctuation inside a quoted string is fine; only the structure matters.
        outside = re.sub(r"'(?:[^'\\]|\\.)*'|\"(?:[^\"\\]|\\.)*\"", "''", meta)
        assert "+" not in outside, f"{wf.name}: meta must be a pure literal, found concatenation"
        assert "`" not in outside, f"{wf.name}: meta must not use template literals"
        assert "..." not in outside, f"{wf.name}: meta must not spread"
        assert "(" not in outside, f"{wf.name}: meta must not call functions"


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
    assert "builder check" in text
    assert "## Phase 3 - Detailed" not in text, "the post-gate question round must be gone"


def test_skill_body_fits_the_documented_cap():
    lines = (START_DEVELOPMENT / "SKILL.md").read_text().splitlines()
    assert len(lines) <= 500, f"SKILL.md is {len(lines)} lines; the cap is 500"


def test_every_reference_and_template_named_exists():
    text = (START_DEVELOPMENT / "SKILL.md").read_text()
    named = set(re.findall(r"references/[a-z-]+\.md", text))
    named |= set(re.findall(r"templates/[a-z]+\.md", text))
    assert named, "SKILL.md names no references or templates"
    for rel in sorted(named):
        assert (START_DEVELOPMENT / rel).is_file(), f"SKILL.md names a missing file: {rel}"


def test_research_steps_table():
    text = sd_text(START_DEVELOPMENT / "SKILL.md")
    assert "## Research steps" in text
    section = text[text.index("## Research steps") :]
    section = section[: section.index("\n## ", 1)]
    for name in RESEARCH_SKILLS:
        assert name in section, f"research steps do not name {name}"
    assert "Skip when" in section


def test_record_phase():
    text = sd_text(START_DEVELOPMENT / "SKILL.md")
    assert "## Phase 7 - Record" in text
    assert "record-writer" in text
    assert "doc_path.sh record" in text


def test_execute_passes_doc_paths():
    text = sd_text(START_DEVELOPMENT / "SKILL.md")
    for key in ("designDoc", "planDoc", "existing", "validate-tasks.mjs"):
        assert key in text, f"SKILL.md does not mention {key}"


CONTRACT_RULE = (
    "A contract is a shared part: its owner task lists it in owns, every consumer in uses, and"
    " it is defined in exactly one file; the plan's Contracts table names all three."
)
FRESHNESS_SENTENCE = (
    "a subagent cannot end a turn in a worktree whose last test run was not on its HEAD"
)
LESSONS_SENTENCE = (
    "Each lesson names the check to add (a test, hook or lint rule) when the violation is"
    " mechanical, and the skill or rule to edit only when it is a judgement call."
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


def test_phase_three_lints_the_documents():
    phase3 = _flat(_section(_skill(), "## Phase 3 - Plan doc and tasks"))
    assert ("validate-tasks.mjs --epic <epic dir>") in phase3
    assert CONTRACT_RULE in phase3


def test_gate_questions_carry_recommended_answers():
    gate = _flat(_section(_skill(), "## The gate"))
    wording = 'numbered, each with a recommended answer, worded so that "yes" accepts it'
    assert wording in gate
    builder = _flat((START_DEVELOPMENT / "references" / "builder-check.md").read_text())
    assert "recommended answer" in builder
    assert wording in builder


def test_phase4_names_epic_base_ref_and_main_checkout():
    phase4 = _flat(_section(_skill(), "## Phase 4 - Execute"))
    for term in ("baseRef", "mainCheckout", "epic branch"):
        assert term in phase4, f"Phase 4 does not name {term!r}"


def test_execute_names_the_verifier_and_red_evidence():
    phase4 = _flat(_section(_skill(), "## Phase 4 - Execute"))
    for term in (
        "independent verifier",
        "tests.red",
        "TDD skipped",
        "forward-merge",
        "declined",
        "cannotVerify",
        "forward-merge-failed",
        "verify-agent-died",
        "epic branch",
        "verification.head",
    ):
        assert term in phase4, f"Phase 4 does not name {term!r}"


def test_phase_five_uses_start_review():
    text = _skill()
    phase5 = _section(text, "## Phase 5 - Verify")
    assert "start-review" in phase5
    assert "workbench:interrogate" in phase5
    assert "/code-review" not in text, "the native /code-review is replaced by start-review"


def test_phase_six_routes_to_start_debugging():
    phase6 = _section(_skill(), "## Phase 6 - Merge")
    assert "start-debugging" in phase6
    assert "health" in phase6


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


def test_merge_is_a_prompt_role_and_verify_is_the_verifier_agent():
    agents = (START_DEVELOPMENT / "references" / "agents.md").read_text()
    assert re.search(r"^\| `verifier` \| .* \| 4 \|$", agents, re.M), "no verifier row"
    flat = _flat(agents)
    assert (
        "The merge role in workbench:plan-execute is a prompt role, not an agent file;"
        " verify runs as the verifier agent."
    ) in flat
    assert "`verify` and `merge` roles" not in flat


def test_run_handback_covers_new_keys():
    text = (START_DEVELOPMENT / "references" / "run-handback.md").read_text()
    for key in (
        "`declined`",
        "`cannotVerify`",
        "`forwardMerged`",
        "`forward-merge-failed`",
        "`verify-agent-died`",
        "`selfVerification`",
        "`verification`",
        "`head`",
        "`tests.red`",
        "worktree-merger",
        "start-review",
    ):
        assert key in text, f"run-handback.md does not cover {key}"


def test_record_template_routes_lessons_to_checks():
    text = _flat((START_DEVELOPMENT / "templates" / "record.md").read_text())
    assert LESSONS_SENTENCE in text
    assert "verifier head" in text
    assert (
        "task, status, review rounds, continuations, files, verifier head SHA, verification tail"
        in text
    )


def test_record_writer_reads_verifier_heads():
    text = (ROOT / "agents" / "record-writer.md").read_text()
    for term in (
        "verification.head",
        "unverified",
        "tests.red",
        "declined",
        "cannotVerify",
        "forwardMerged",
    ):
        assert term in text, f"record-writer.md does not mention {term}"


def test_red_evidence_finding_labels_match_the_workflow():
    """The docs name each TDD finding by the summary plan-execute.js emits for it."""
    workflow = (ROOT / "workflows" / "plan-execute.js").read_text()
    assert "summary: 'No red evidence:" in workflow
    assert "summary: `TDD skipped without a listed exception" in workflow
    phase4 = _flat(_section(_skill(), "## Phase 4 - Execute"))
    handback = _flat((START_DEVELOPMENT / "references" / "run-handback.md").read_text())
    for name, text in (("SKILL.md Phase 4", phase4), ("run-handback.md", handback)):
        assert "`No red evidence`" in text, f"{name} does not name the No red evidence finding"
        assert "`TDD skipped`" in text, f"{name} does not name the TDD skipped finding"
        assert "`wroteTestFirst: false`" in text, f"{name} does not say when TDD skipped fires"
        assert "no `tests.red` came back with a `TDD skipped`" not in text
        assert "missing it, or skipping the cycle" not in text


def _ref(name):
    return (START_DEVELOPMENT / "references" / name).read_text()


def test_gate_writes_the_approval_ledger():
    gate = _flat(_section(_skill(), "## The gate"))
    for term in (
        "doc_path.sh approvals",
        "approves every entry by id",
        "never kept as later",
        "the project brief (what, how, why)",
    ):
        assert term in gate, f"the gate does not say {term!r}"
    ref = START_DEVELOPMENT / "references" / "approvals.md"
    assert ref.is_file(), "references/approvals.md missing"
    text = ref.read_text()
    assert text.startswith("# The approval ledger")
    for term in (
        "delivered",
        "blocked",
        "escalated",
        "unverified",
        "--approvals",
        "=== APPROVED ITEMS",
        "whoCanClear",
        "Approved item",
        "finished",
    ):
        assert term in text, f"references/approvals.md does not mention {term!r}"


def test_execute_passes_brief_value_and_approvals():
    phase4 = _section(_skill(), "## Phase 4 - Execute")
    for term in (
        "brief:",
        "value",
        "approvals:",
        "verifierAgent",
        "`Approved item`",
        "approvals[].status",
        "agents/verifier.md",
        "maxTurns",
        "`Tests changed in a fix round`",
        "references/worktrees.md",
    ):
        assert term in phase4, f"Phase 4 does not name {term!r}"


def test_worktrees_reference_covers_helpers_for_every_role():
    text = _flat((START_DEVELOPMENT / "references" / "worktrees.md").read_text())
    for term in (
        "A helper spawned by an implementer",
        "review, verify or audit",
        "read-only like its parent",
        "merge helper",
        "never in another",
    ):
        assert term in text, f"references/worktrees.md does not say {term!r}"


def test_phase_four_names_heartbeat():
    phase4 = _flat(_section(_skill(), "## Phase 4 - Execute"))
    for term in (
        "heartbeat",
        "keepalive off by default",
        "skills/heartbeat/SKILL.md",
        "references/run-handback.md",
    ):
        assert term in phase4, f"Phase 4 does not name {term!r}"


def test_scope_section_forbids_later_parking():
    scope = _flat(_section(_skill(), "## Scope is not negotiable"))
    for term in ('No "later" parking', "named blocker", "in one line", "4. The approval ledger"):
        assert term in scope, f"the Scope section does not say {term!r}"


def test_closing_message_is_short():
    phase7 = _flat(_section(_skill(), "## Phase 7 - Record"))
    assert "three lines at most" in phase7
    assert "concise-orchestrator" in phase7


def test_run_handback_covers_approvals_and_reply_short():
    text = _flat(_ref("run-handback.md"))
    for term in (
        "`approvals`",
        "Approved item",
        "Tests changed in a fix round",
        "## Reply short",
        "Never paste logs",
        "three lines at most",
        "one line",
        "capped",
    ):
        assert term in text, f"run-handback.md does not cover {term!r}"


def test_record_template_has_the_approvals_table():
    text = _flat((START_DEVELOPMENT / "templates" / "record.md").read_text())
    assert "approvals table" in text
    assert "status (delivered, blocked: who can clear it, escalated)" in text
    assert (
        "task, status, review rounds, continuations, files, verifier head SHA, verification tail"
        in text
    )


def test_record_writer_reads_approvals():
    text = (ROOT / "agents" / "record-writer.md").read_text()
    assert "approvals" in text
    assert "unknown" in text
    assert "approvals table" in text


def test_task_fields_reference_lists_value():
    ref = START_DEVELOPMENT / "references" / "task-fields.md"
    assert ref.is_file(), "references/task-fields.md missing"
    text = ref.read_text()
    assert "| `value` | one line: what this task is worth to the user; required |" in text
    assert "`requirement`" in text
    assert "references/task-fields.md" in _skill()


def test_verifier_agent_file():
    f = ROOT / "agents" / "verifier.md"
    assert f.is_file()
    fm = frontmatter(f)
    assert fm.get("name") == "verifier"
    assert fm.get("model") == "haiku"
    assert fm.get("maxTurns")
    tools = str(fm.get("tools"))
    for forbidden in ("Edit", "Write"):
        assert forbidden not in tools, f"verifier must stay read-only, got {tools}"
    flat = re.sub(r"\s+", " ", f.read_text())
    assert "judged by its `exit` field only" in flat
    assert "0 is met and passed" in flat
    assert "Never set `passed` or `met` differently from the script" in flat
    assert "no gloss or note of your own" in flat


def test_phase_five_reap_line_has_no_conditional_parking():
    flat = _flat(_section(_skill(), "## Phase 5"))
    assert "removes the rest on request" not in flat
    assert "(`ticket.py reap --epic <epic>`) removes every remaining worktree of the epic" in flat


def test_topic_focus_goes_to_practitioner():
    text = re.sub(r"\s+", " ", (START_RESEARCH / "SKILL.md").read_text())
    assert "topic-specific persona" not in text
    assert "security-auditor" not in text
    assert "focus line" in text and "workbench:research-practitioner" in text
