"""
Tests for error paths across agents.

Covers: budget validation, payload size guard, unknown mode/platform,
structured fallback signal, no-analyzer guard, drift metrics warnings.
"""
import logging
import pytest


class MockAnalyzer:
    def chat_with_agent(self, user_message, system_prompt=None, **kwargs):
        return "mock response"

    def call_tool(self, user_message, tool, system_prompt=None, **kwargs):
        return None  # simulates call_tool failure


# ── AdsAgent error paths ───────────────────────────────────────────────────────

class TestAdsAgentErrorPaths:
    def _agent(self):
        from agents.ads.agent import AdsAgent
        return AdsAgent("ads", MockAnalyzer())

    def test_negative_budget_rejected(self):
        result = self._agent().run({"platform": "google", "mode": "plan", "budget": -500})
        assert "error" in result
        assert "negative" in result["error"].lower()

    def test_zero_budget_allowed(self):
        result = self._agent().run({"platform": "google", "mode": "plan", "budget": 0})
        assert "error" not in result

    def test_payload_too_large(self):
        huge_context = "x" * 90_000
        result = self._agent().run({"platform": "google", "mode": "plan", "context": huge_context})
        assert "error" in result
        assert "too large" in result["error"].lower()

    def test_unknown_platform_rejected(self):
        result = self._agent().run({"platform": "snapchat", "mode": "plan"})
        assert "error" in result
        assert "snapchat" in result["error"].lower()

    def test_unknown_mode_rejected(self):
        result = self._agent().run({"platform": "google", "mode": "hype"})
        assert "error" in result
        assert "hype" in result["error"].lower()

    def test_no_analyzer_returns_error(self):
        from agents.ads.agent import AdsAgent
        agent = AdsAgent("ads", None)
        result = agent.run({"platform": "google", "mode": "plan"})
        assert "error" in result

    def test_call_tool_none_sets_structured_fallback(self):
        result = self._agent().run({"platform": "google", "mode": "analyze", "metrics": {"ctr": 2.5}})
        assert result.get("structured_fallback") is True

    def test_valid_payload_has_no_error(self):
        result = self._agent().run({"platform": "google", "mode": "plan", "product": "SaaS"})
        assert "error" not in result
        assert "result" in result
        assert result["agent"] == "ads"
        assert result["platform"] == "google"
        assert result["mode"] == "plan"


# ── SEOAgent error paths ───────────────────────────────────────────────────────

class TestSEOAgentErrorPaths:
    def _agent(self):
        from agents.seo.agent import SEOAgent
        return SEOAgent("seo", MockAnalyzer())

    def test_payload_too_large(self):
        huge = "y" * 90_000
        result = self._agent().run({"mode": "seo", "site": "example.com", "context": huge})
        assert "error" in result
        assert "too large" in result["error"].lower()

    def test_unknown_mode_rejected(self):
        result = self._agent().run({"mode": "magic", "site": "example.com"})
        assert "error" in result

    def test_no_analyzer_returns_error(self):
        from agents.seo.agent import SEOAgent
        agent = SEOAgent("seo", None)
        result = agent.run({"mode": "seo", "site": "example.com"})
        assert "error" in result

    def test_valid_run_returns_correct_shape(self, monkeypatch):
        monkeypatch.setenv("SEO_SKIP_ENRICHMENT", "true")
        result = self._agent().run({"mode": "seo", "site": "example.com"})
        assert "error" not in result
        assert "result" in result
        assert result["agent"] == "seo"
        assert result["mode"] == "seo"

    def test_drift_empty_metrics_logs_warning(self, monkeypatch, caplog):
        monkeypatch.setenv("SEO_SKIP_ENRICHMENT", "true")
        with caplog.at_level(logging.WARNING, logger="agents.seo.agent"):
            result = self._agent().run({"mode": "drift", "site": "example.com", "metrics": {}})
        assert any("drift" in r.message.lower() and "metrics" in r.message.lower()
                   for r in caplog.records)

    def test_drift_non_numeric_metrics_logs_warning(self, monkeypatch, caplog):
        monkeypatch.setenv("SEO_SKIP_ENRICHMENT", "true")
        with caplog.at_level(logging.WARNING, logger="agents.seo.agent"):
            result = self._agent().run({
                "mode": "drift",
                "site": "example.com",
                "metrics": {"clicks": "many", "impressions": 1000},
            })
        assert any("non-numeric" in r.message.lower() for r in caplog.records)


# ── Manager error paths ────────────────────────────────────────────────────────

class TestManagerErrorPaths:
    def test_unknown_agent_returns_error(self):
        from agents.manager import AgentsManager
        m = AgentsManager(MockAnalyzer())
        result = m.run("nonexistent", {})
        assert "error" in result

    def test_no_analyzer_orchestrate_returns_error(self):
        from agents.manager import AgentsManager
        m = AgentsManager(None)
        result = m.orchestrate("build campaign", {})
        assert "error" in result

    def test_circular_dependency_logs_warning(self, caplog):
        from agents.manager import AgentsManager, _DEPENDENCIES
        m = AgentsManager(MockAnalyzer())

        # Temporarily create an unresolvable order by requesting an agent with missing dep
        # We test the internal resolver directly
        with caplog.at_level(logging.WARNING, logger="agents.manager"):
            # Force circular: both agents depend on each other (mock via direct call)
            original = dict(_DEPENDENCIES)
            try:
                _DEPENDENCIES["strategy"] = ["ads"]  # create circular
                batches = m._resolve_execution_order(["ads", "strategy"])
            finally:
                _DEPENDENCIES["strategy"] = original.get("strategy", [])

        assert any("circular" in r.message.lower() or "unresolvable" in r.message.lower()
                   for r in caplog.records)


# ── BaseAgent history persistence logging ─────────────────────────────────────

class TestBaseAgentHistoryLogging:
    def test_history_failure_logs_warning(self, monkeypatch, caplog):
        from agents.ads.agent import AdsAgent

        agent = AdsAgent("ads", MockAnalyzer())

        # Make storage.save_history raise
        import agents.base_agent as ba

        def _bad_save(*a, **kw):
            raise OSError("disk full")

        monkeypatch.setattr("storage.save_history", _bad_save)

        with caplog.at_level(logging.WARNING, logger="agents.base_agent"):
            agent.chat("hello", chat_id=999)

        assert any("persistence failed" in r.message.lower() for r in caplog.records)


# ── split_structured_result does not mutate input ─────────────────────────────

class TestSplitStructuredResultNoMutation:
    def test_ads_no_mutation(self):
        from agents.ads.skills.structured import split_structured_result
        raw = {"narrative": "hello", "findings": [{"metric": "CTR"}], "overall_health": "good", "missing_data": []}
        original_keys = set(raw.keys())
        split_structured_result(raw)
        assert set(raw.keys()) == original_keys  # original dict untouched

    def test_seo_no_mutation(self):
        from agents.seo.skills.structured import split_seo_structured_result
        raw = {"narrative": "seo report", "fixlist": [], "health_score": 80}
        original_keys = set(raw.keys())
        split_seo_structured_result(raw)
        assert set(raw.keys()) == original_keys

    def test_empty_raw_returns_empty(self):
        from agents.ads.skills.structured import split_structured_result
        text, data = split_structured_result(None)
        assert text == "" and data == {}

        text, data = split_structured_result({})
        assert text == "" and data == {}

    def test_narrative_extracted_correctly(self):
        from agents.ads.skills.structured import split_structured_result
        raw = {"narrative": "  my report  ", "score": 42}
        text, data = split_structured_result(raw)
        assert text == "my report"
        assert data == {"score": 42}
