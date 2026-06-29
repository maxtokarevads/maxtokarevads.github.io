"""Tests for StrategyAgent — no API calls required."""
import pytest
from agents.strategy.agent import StrategyAgent
from agents.strategy.skills.prompt import SUPPORTED_MODES


class MockAnalyzer:
    def chat_with_agent(self, user_message, system_prompt=None, history=None, **kwargs):
        return "mock strategy response"


BASE = {"product": "TestSaaS", "goal": "grow revenue", "industry": "saas"}


@pytest.mark.parametrize("mode", SUPPORTED_MODES)
def test_prepare_run_valid_modes(mode):
    agent = StrategyAgent("strategy", MockAnalyzer())
    ctx, err = agent._prepare_run({**BASE, "mode": mode})
    assert err is None
    assert ctx is not None
    assert ctx.mode == mode


def test_prepare_run_invalid_mode():
    agent = StrategyAgent("strategy", MockAnalyzer())
    ctx, err = agent._prepare_run({**BASE, "mode": "nonexistent_mode"})
    assert ctx is None
    assert err is not None
    assert "error" in err


def test_prepare_run_no_analyzer():
    agent = StrategyAgent("strategy", None)
    ctx, err = agent._prepare_run(BASE)
    assert ctx is None
    assert "error" in err


def test_run_no_analyzer():
    agent = StrategyAgent("strategy", None)
    result = agent.run(BASE)
    assert "error" in result


def test_supported_modes_contains_required():
    modes = StrategyAgent.supported_modes()
    for m in ["general", "gtm", "positioning", "channel_mix", "kpi"]:
        assert m in modes, f"'{m}' missing from supported_modes"


def test_supported_modes_matches_constant():
    assert set(StrategyAgent.supported_modes()) == set(SUPPORTED_MODES)


def test_no_dependencies():
    assert StrategyAgent.dependencies == []


def test_default_mode_is_general():
    agent = StrategyAgent("strategy", MockAnalyzer())
    ctx, err = agent._prepare_run(BASE)
    assert err is None
    assert ctx.mode == "general"


def test_system_prompt_per_mode():
    agent = StrategyAgent("strategy", MockAnalyzer())
    general = agent.get_system_prompt("general")
    gtm     = agent.get_system_prompt("gtm")
    audit   = agent.get_system_prompt("audit")
    assert general != gtm
    assert general != audit
    assert "Chief Marketing Officer" in general or "CMO" in general


def test_prompt_has_content():
    agent = StrategyAgent("strategy", MockAnalyzer())
    for mode in ["general", "gtm", "positioning"]:
        ctx, _ = agent._prepare_run({**BASE, "mode": mode})
        assert ctx is not None
        assert len(ctx.final_prompt) > 50, f"mode '{mode}' produced too short a prompt"
