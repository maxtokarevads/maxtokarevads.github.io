"""Tests for consistent response format across all agents."""
from agents.manager import AgentsManager


class MockAnalyzer:
    def chat_with_agent(self, user_message, system_prompt=None, history=None, **kwargs):
        return "mock response"


def _make_mgr():
    return AgentsManager(MockAnalyzer())


def test_seo_response_has_result_and_agent():
    mgr = _make_mgr()
    r = mgr.run("seo", {"site": "example.com", "keywords": ["seo"], "query": "grow traffic"})
    assert "result" in r
    assert r.get("agent") == "seo"


def test_strategy_response_has_result_and_agent():
    mgr = _make_mgr()
    r = mgr.run("strategy", {"goal": "grow", "timeline": "3 months", "resources": {}})
    assert "result" in r
    assert r.get("agent") == "strategy"


def test_creative_response_has_result_and_agent():
    mgr = _make_mgr()
    r = mgr.run("creative", {"product": "App", "tone": "bold", "format": "banner"})
    assert "result" in r
    assert r.get("agent") == "creative"


def test_ads_response_has_result_agent_platform_mode():
    mgr = _make_mgr()
    r = mgr.run("ads", {"product": "CRM", "platform": "google", "mode": "plan"})
    assert "result" in r
    assert r.get("agent") == "ads"
    assert r.get("platform") == "google"
    assert r.get("mode") == "plan"


def test_all_agents_have_result_key():
    mgr = _make_mgr()
    payloads = {
        "seo":      {"site": "x.com", "keywords": [], "query": "test"},
        "ads":      {"product": "X", "platform": "google"},
        "strategy": {"goal": "grow", "timeline": "1 month", "resources": {}},
        "creative": {"product": "X", "tone": "bold", "format": "banner"},
    }
    for agent_type, payload in payloads.items():
        r = mgr.run(agent_type, payload)
        assert "result" in r, f"Agent '{agent_type}' missing 'result' key"


def test_error_format_on_missing_analyzer():
    mgr = AgentsManager(None)
    for agent_type in ["seo", "ads", "strategy", "creative"]:
        r = mgr.run(agent_type, {})
        assert "error" in r, f"Agent '{agent_type}' should return error without analyzer"
