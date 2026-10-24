"""Claude-only hooks stay out of every other harness's emitted config (design D14)."""

from pathlib import Path

from harness.emit import registry
from harness.sources import load_sources

REPO = Path(__file__).resolve().parents[3]
TARGETS = ("copilot", "codex", "gemini", "cursor", "antigravity")


def test_recorder_is_claude_only():
    sources = load_sources(REPO)
    registered = {h.hook for p in sources.plugins for h in p.hooks}
    # The real plugin registers the recorder, so its absence below is a real exclusion.
    assert "agent-usage-recorder" in registered
    emitters = registry()
    for target in TARGETS:
        out = emitters[target].render(sources)
        assert out, target
        leaked = sorted(rel for rel, text in out.items() if "agent-usage-recorder" in text)
        assert not leaked, (target, leaked)
