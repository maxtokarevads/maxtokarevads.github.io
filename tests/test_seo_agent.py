"""Tests for SEOAgent — no API calls required."""
import pytest
from agents.seo.agent import SEOAgent
from agents.seo.skills import SUPPORTED_MODES


class MockAnalyzer:
    def chat_with_agent(self, user_message, system_prompt=None, history=None, **kwargs):
        return "mock seo response"


BASE = {"site": "example.com", "query": "SEO audit", "mode": "seo"}
_BUILDER_MODES = [
    "seo", "aeo", "technical", "content",
    "local", "schema", "backlinks", "cluster", "sxo", "audit",
]


@pytest.mark.parametrize("mode", _BUILDER_MODES)
def test_prepare_run_valid_modes(mode):
    agent = SEOAgent("seo", MockAnalyzer())
    ctx, err = agent._prepare_run({**BASE, "mode": mode})
    assert err is None
    assert ctx is not None
    assert ctx.mode == mode


def test_prepare_run_drift_no_metrics():
    agent = SEOAgent("seo", MockAnalyzer())
    ctx, err = agent._prepare_run({"site": "example.com", "mode": "drift"})
    assert err is None
    assert ctx is not None
    assert ctx.mode == "drift"


def test_prepare_run_invalid_mode():
    agent = SEOAgent("seo", MockAnalyzer())
    ctx, err = agent._prepare_run({**BASE, "mode": "nonexistent_mode"})
    assert ctx is None
    assert err is not None
    assert "error" in err


def test_prepare_run_no_analyzer():
    agent = SEOAgent("seo", None)
    ctx, err = agent._prepare_run(BASE)
    assert ctx is None
    assert "error" in err


def test_prepare_run_payload_too_large():
    agent = SEOAgent("seo", MockAnalyzer())
    huge = {**BASE, "context": "x" * 90_000}
    ctx, err = agent._prepare_run(huge)
    assert ctx is None
    assert "too large" in err["error"]


def test_run_no_analyzer():
    agent = SEOAgent("seo", None)
    result = agent.run(BASE)
    assert "error" in result


def test_supported_modes_contains_required():
    modes = SEOAgent.supported_modes()
    for m in ["seo", "aeo", "technical", "audit", "drift"]:
        assert m in modes, f"'{m}' missing from supported_modes"


def test_supported_modes_matches_constant():
    assert set(SEOAgent.supported_modes()) == set(SUPPORTED_MODES)


def test_dependencies_include_strategy():
    assert "strategy" in SEOAgent.dependencies


def test_prompt_has_content_seo_mode():
    agent = SEOAgent("seo", MockAnalyzer())
    ctx, _ = agent._prepare_run({**BASE, "mode": "seo"})
    assert ctx is not None
    assert len(ctx.final_prompt) > 50


def test_prompt_has_content_technical_mode():
    agent = SEOAgent("seo", MockAnalyzer())
    ctx, _ = agent._prepare_run({**BASE, "mode": "technical"})
    assert ctx is not None
    assert len(ctx.final_prompt) > 50


def test_system_prompt_per_mode():
    agent = SEOAgent("seo", MockAnalyzer())
    seo_prompt = agent.get_system_prompt("seo")
    aeo_prompt = agent.get_system_prompt("aeo")
    assert seo_prompt != aeo_prompt
    assert "SEO" in seo_prompt
    assert "AEO" in aeo_prompt or "Answer Engine" in aeo_prompt
