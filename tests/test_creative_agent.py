"""Tests for CreativeAgent — no API calls required."""
import pytest
from agents.creative.agent import CreativeAgent
from agents.creative.skills import SUPPORTED_MODES


class MockAnalyzer:
    def chat_with_agent(self, user_message, system_prompt=None, history=None, **kwargs):
        return "mock creative response"


BASE = {"product": "TestApp", "platform": "tiktok", "tone": "energetic"}


@pytest.mark.parametrize("mode", SUPPORTED_MODES)
def test_prepare_run_valid_modes(mode):
    agent = CreativeAgent("creative", MockAnalyzer())
    ctx, err = agent._prepare_run({**BASE, "mode": mode})
    assert err is None
    assert ctx is not None
    assert ctx.mode == mode


def test_prepare_run_invalid_mode():
    agent = CreativeAgent("creative", MockAnalyzer())
    ctx, err = agent._prepare_run({**BASE, "mode": "nonexistent_mode"})
    assert ctx is None
    assert err is not None
    assert "error" in err


def test_prepare_run_no_analyzer():
    agent = CreativeAgent("creative", None)
    ctx, err = agent._prepare_run(BASE)
    assert ctx is None
    assert "error" in err


def test_run_no_analyzer():
    agent = CreativeAgent("creative", None)
    result = agent.run(BASE)
    assert "error" in result


def test_supported_modes():
    modes = CreativeAgent.supported_modes()
    assert set(modes) == {"concept", "copy", "script", "ugc_brief"}


def test_supported_modes_matches_constant():
    assert set(CreativeAgent.supported_modes()) == set(SUPPORTED_MODES)


def test_dependencies_include_strategy_and_ads():
    assert "strategy" in CreativeAgent.dependencies
    assert "ads" in CreativeAgent.dependencies


def test_default_mode_is_concept():
    agent = CreativeAgent("creative", MockAnalyzer())
    ctx, err = agent._prepare_run(BASE)
    assert err is None
    assert ctx.mode == "concept"


def test_system_prompt_per_mode():
    agent = CreativeAgent("creative", MockAnalyzer())
    concept = agent.get_system_prompt("concept")
    script  = agent.get_system_prompt("script")
    assert concept != script
    assert "Creative Director" in concept or "creative" in concept.lower()


def test_prompt_has_content_all_modes():
    agent = CreativeAgent("creative", MockAnalyzer())
    for mode in SUPPORTED_MODES:
        ctx, _ = agent._prepare_run({**BASE, "mode": mode})
        assert ctx is not None
        assert len(ctx.final_prompt) > 50, f"mode '{mode}' produced too short a prompt"


def test_platform_normalised_in_request():
    """CreativeRequest normalises platform to lowercase — test the dataclass directly."""
    from agents.creative.agent import CreativeRequest
    req = CreativeRequest.from_dict({"platform": "TikTok", "mode": "concept"})
    assert req.platform == "tiktok"
