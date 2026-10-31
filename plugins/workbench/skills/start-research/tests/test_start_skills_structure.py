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


# The flow skills moved to plugins/superpowers; these references stay with the tooling.
MOVED_REFERENCES = tuple(
    ROOT / "references" / f"{n}.md"
    for n in ("hooks", "merge-hosts", "user-run-steps", "workbench-config", "worktrees")
)


def references_text():
    """Every tooling reference the flow skills point at, joined."""
    return "\n".join(r.read_text() for r in MOVED_REFERENCES)


def test_start_research_feeds_brainstorming():
    text = _flat((START_RESEARCH / "SKILL.md").read_text())
    assert "superpowers:brainstorming" in text
    assert "start-" + "development" not in text


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



def test_boy_scout_rule_ships_with_the_plugin():
    rule = ROOT / "rules" / "boy-scout.md"
    assert rule.is_file(), "rules/boy-scout.md missing"
    text = rule.read_text()
    for clause in ("Simplify what you touch", "uncommitted", "adjacent commits"):
        assert clause in text, f"boy-scout rule does not cover {clause!r}"



def test_cartographer_can_actually_use_lsp():
    """Lane 2 is inert unless the agent holds the LSP tool, not just the binary."""
    fm = frontmatter(ROOT / "agents" / "codebase-cartographer.md")
    tools = str(fm.get("tools"))
    assert "LSP" in tools, "cartographer cannot run the LSP lane without the LSP tool"


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
    skill = references_text()
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
    text = references_text()
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
        ROOT / "references" / "merge-hosts.md",
        ROOT / "README.md",
    )
    for doc in docs:
        text = doc.read_text()
        found = OLD_SCM_SKILL_NAME.search(text)
        assert not found, f"{doc.name} still names {found.group(0)}"
    merge_hosts = (ROOT / "references" / "merge-hosts.md").read_text()
    assert "WORKBENCH_SCM_HOSTS" in merge_hosts








FRESHNESS_SENTENCE = (
    "a subagent cannot end a turn in a worktree whose last test run was not on its HEAD"
)


def _flat(text):
    """Collapse line wrapping so a sentence matches however the prose is wrapped."""
    return re.sub(r"\s+", " ", text)



def test_hooks_section_names_the_freshness_guard():
    combined = _flat((ROOT / "references" / "hooks.md").read_text())
    assert "verification-freshness" in combined
    assert "commit guard" in combined
    assert FRESHNESS_SENTENCE in combined





def test_worktrees_reference_covers_helpers_for_every_role():
    text = _flat((ROOT / "references" / "worktrees.md").read_text())
    for term in (
        "A helper spawned by an implementer",
        "spawned by the reviewer",
        "read-only like its parent",
        "merge helper",
        "never in another",
    ):
        assert term in text, f"references/worktrees.md does not say {term!r}"







def test_topic_focus_goes_to_practitioner():
    text = re.sub(r"\s+", " ", (START_RESEARCH / "SKILL.md").read_text())
    assert "topic-specific persona" not in text
    assert "security-auditor" not in text
    assert "focus line" in text and "workbench:research-practitioner" in text
