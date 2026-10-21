import pytest
from harness.models import model_for


@pytest.mark.parametrize("target", ["cursor", "gemini", "antigravity"])
def test_inherit_default(target):
    assert model_for(target, "opus", {}) == "inherit"


@pytest.mark.parametrize("target", ["copilot", "codex"])
def test_omitted_default(target):
    assert model_for(target, "sonnet", {}) is None


def test_override_by_alias_full_mapping():
    overrides = {"cursor": {"opus": "gpt-x"}, "codex": {"haiku": "mini"}}
    assert model_for("cursor", "opus", overrides) == "gpt-x"
    assert model_for("cursor", "sonnet", overrides) == "inherit"
    assert model_for("codex", "haiku", overrides) == "mini"
    assert model_for("codex", "opus", overrides) is None


def test_override_by_alias_target_mapping():
    assert model_for("copilot", "opus", {"opus": "m"}) == "m"


def test_none_overrides():
    assert model_for("gemini", "opus", None) == "inherit"


def test_unknown_target():
    with pytest.raises(ValueError, match="unknown target"):
        model_for("vim", "opus", {})


def test_defaults_and_overrides():
    assert model_for("cursor", "opus", {}) == "inherit"
    assert model_for("codex", "opus", {}) is None
    assert model_for("cursor", "opus", {"cursor": {"opus": "x"}}) == "x"
