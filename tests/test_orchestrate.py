"""Tests for AgentsManager.orchestrate — mocked analyzer."""
from agents.manager import AgentsManager


class MockAnalyzer:
    def chat_with_agent(self, user_message, system_prompt=None, history=None, **kwargs):
        return f"synthesized: {user_message[:40]}"


def test_orchestrate_no_analyzer():
    mgr = AgentsManager(None)
    result = mgr.orchestrate("task", {})
    assert "error" in result


def test_orchestrate_returns_result_and_subagents():
    mgr = AgentsManager(MockAnalyzer())
    result = mgr.orchestrate("Grow SaaS", {"product": "CRM", "platform": "google"}, ["ads"])
    assert "result" in result
    assert "subagent_outputs" in result
    assert "selected_agents" in result
    assert "ads" in result["selected_agents"]


def test_orchestrate_filters_unknown_agents():
    mgr = AgentsManager(MockAnalyzer())
    result = mgr.orchestrate("task", {}, ["ads", "nonexistent"])
    assert "nonexistent" not in result["selected_agents"]
    assert "ads" in result["selected_agents"]


def test_orchestrate_uses_all_agents_when_no_list():
    mgr = AgentsManager(MockAnalyzer())
    result = mgr.orchestrate("task", {})
    assert set(result["selected_agents"]) == set(mgr.agents.keys())


def test_build_payload_ads_passes_mode():
    mgr = AgentsManager(None)
    payload = mgr._build_payload("ads", "launch", {"ads_mode": "copy", "funnel_stage": "bofu", "usp": "fast"})
    assert payload["mode"] == "copy"
    assert payload["funnel_stage"] == "bofu"
    assert payload["usp"] == "fast"


def test_build_payload_ads_defaults():
    mgr = AgentsManager(None)
    payload = mgr._build_payload("ads", "task", {})
    assert payload["mode"] == "plan"
    assert payload["funnel_stage"] == "mofu"
    assert payload["platform"] == "google"


def test_build_payload_seo_uses_site_and_query():
    mgr = AgentsManager(None)
    payload = mgr._build_payload("seo", "improve traffic", {"site": "mysite.io", "keywords": ["seo"]})
    assert payload["site"] == "mysite.io"
    assert payload["keywords"] == ["seo"]
    assert payload["query"] == "improve traffic"


def test_run_many_parallel():
    mgr = AgentsManager(MockAnalyzer())
    results = mgr.run_many({"ads": {"product": "X", "platform": "google"}, "seo": {"site": "x.com"}})
    assert "ads" in results
    assert "seo" in results
    assert "result" in results["ads"]
    assert "result" in results["seo"]
