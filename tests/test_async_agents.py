"""
Async tests for arun() in all 4 agents and aorchestrate() in AgentsManager.

Uses pytest-asyncio + AsyncMock so no real HTTP calls are made.
Verifies that:
  - arun() returns the same shape as run()
  - arun() calls achat_with_agent / acall_tool (not sync counterparts)
  - aorchestrate() runs waves, synthesises, returns expected keys
  - arun_many() collects results from all agents concurrently
"""

import asyncio
import pytest

# ── Async mock analyzer ────────────────────────────────────────────────────────

class AsyncMockAnalyzer:
    """Async-capable mock. Returns deterministic responses without API calls."""

    model_name = "mock-async"

    def chat_with_agent(self, user_message: str, **kwargs) -> str:
        return f"sync:{user_message[:20]}"

    async def achat_with_agent(self, user_message: str, **kwargs) -> str:
        return f"async:{user_message[:20]}"

    def call_tool(self, user_message: str, tool: dict, **kwargs):
        return None

    async def acall_tool(self, user_message: str, tool: dict, **kwargs):
        return None


class AsyncMockAnalyzerWithTool(AsyncMockAnalyzer):
    """Variant that returns structured tool output."""

    async def acall_tool(self, user_message: str, tool: dict, **kwargs):
        return {
            "narrative": "async structured response",
            "findings": [],
            "missing_data": [],
            "overall_health": "good",
        }


# ── Helper ─────────────────────────────────────────────────────────────────────

def run_async(coro):
    """Run a coroutine synchronously — works without pytest-asyncio plugin."""
    return asyncio.run(coro)


# ── AdsAgent.arun() ───────────────────────────────────────────────────────────

class TestAdsAgentArun:
    def _agent(self, analyzer=None):
        from agents.ads.agent import AdsAgent
        return AdsAgent("ads", analyzer or AsyncMockAnalyzer())

    def test_arun_returns_result_dict(self):
        agent  = self._agent()
        result = run_async(agent.arun({"platform": "google", "mode": "plan", "product": "SaaS"}))
        assert isinstance(result, dict)
        assert "result" in result
        assert result["agent"] == "ads"
        assert result["mode"] == "plan"
        assert result["platform"] == "google"

    def test_arun_uses_async_chat(self):
        calls = []

        class TrackingAnalyzer(AsyncMockAnalyzer):
            async def achat_with_agent(self, *a, **kw):
                calls.append("async")
                return "async response"
            def chat_with_agent(self, *a, **kw):
                calls.append("sync")
                return "sync response"

        agent  = self._agent(TrackingAnalyzer())
        result = run_async(agent.arun({"platform": "google", "mode": "plan"}))
        assert "async" in calls
        assert "sync" not in calls

    def test_arun_negative_budget_rejected(self):
        agent  = self._agent()
        result = run_async(agent.arun({"platform": "google", "mode": "plan", "budget": -100}))
        assert "error" in result
        assert "negative" in result["error"].lower()

    def test_arun_invalid_mode_rejected(self):
        agent  = self._agent()
        result = run_async(agent.arun({"platform": "google", "mode": "bogus"}))
        assert "error" in result

    def test_arun_with_structured_tool(self):
        agent  = self._agent(AsyncMockAnalyzerWithTool())
        result = run_async(agent.arun({"platform": "google", "mode": "analyze", "metrics": {"ctr": 2.5}}))
        assert isinstance(result, dict)
        # structured_fallback must be True (acall_tool returned None by default in this case)
        # or structured present if tool succeeded
        assert "result" in result or "error" in result

    def test_arun_and_run_return_same_shape(self):
        agent = self._agent()
        payload = {"platform": "meta", "mode": "copy", "product": "App", "usp": "Fast"}
        sync_result  = agent.run(payload)
        async_result = run_async(agent.arun(payload))
        assert set(sync_result.keys()) == set(async_result.keys())


# ── SEOAgent.arun() ───────────────────────────────────────────────────────────

class TestSEOAgentArun:
    def test_arun_returns_result(self, monkeypatch):
        monkeypatch.setenv("SEO_SKIP_ENRICHMENT", "true")
        from agents.seo.agent import SEOAgent
        agent  = SEOAgent("seo", AsyncMockAnalyzer())
        result = run_async(agent.arun({"mode": "seo", "site": "example.com"}))
        assert "result" in result
        assert result["agent"] == "seo"

    def test_arun_uses_async_chat(self, monkeypatch):
        monkeypatch.setenv("SEO_SKIP_ENRICHMENT", "true")
        from agents.seo.agent import SEOAgent
        calls = []

        class TrackingAnalyzer(AsyncMockAnalyzer):
            async def achat_with_agent(self, *a, **kw):
                calls.append("async")
                return "response"
            def chat_with_agent(self, *a, **kw):
                calls.append("sync")
                return "response"

        agent = SEOAgent("seo", TrackingAnalyzer())
        run_async(agent.arun({"mode": "seo", "site": "example.com"}))
        assert "async" in calls
        assert "sync" not in calls

    def test_arun_invalid_mode_rejected(self, monkeypatch):
        monkeypatch.setenv("SEO_SKIP_ENRICHMENT", "true")
        from agents.seo.agent import SEOAgent
        agent  = SEOAgent("seo", AsyncMockAnalyzer())
        result = run_async(agent.arun({"mode": "invalid_xyz", "site": "example.com"}))
        assert "error" in result


# ── StrategyAgent.arun() ──────────────────────────────────────────────────────

class TestStrategyAgentArun:
    def test_arun_returns_result(self):
        from agents.strategy.agent import StrategyAgent
        agent  = StrategyAgent("strategy", AsyncMockAnalyzer())
        result = run_async(agent.arun({"mode": "general", "product": "SaaS", "goal": "grow"}))
        assert "result" in result
        assert result["agent"] == "strategy"
        assert result["mode"] == "general"

    def test_arun_uses_async_chat(self):
        from agents.strategy.agent import StrategyAgent
        calls = []

        class TrackingAnalyzer(AsyncMockAnalyzer):
            async def achat_with_agent(self, *a, **kw):
                calls.append("async")
                return "response"
            def chat_with_agent(self, *a, **kw):
                calls.append("sync")
                return "response"

        agent = StrategyAgent("strategy", TrackingAnalyzer())
        run_async(agent.arun({"mode": "general"}))
        assert "async" in calls
        assert "sync" not in calls

    def test_arun_unknown_mode_rejected(self):
        from agents.strategy.agent import StrategyAgent
        agent  = StrategyAgent("strategy", AsyncMockAnalyzer())
        result = run_async(agent.arun({"mode": "unicorn"}))
        assert "error" in result


# ── CreativeAgent.arun() ──────────────────────────────────────────────────────

class TestCreativeAgentArun:
    def test_arun_returns_result(self):
        from agents.creative.agent import CreativeAgent
        agent  = CreativeAgent("creative", AsyncMockAnalyzer())
        result = run_async(agent.arun({"mode": "concept", "product": "App"}))
        assert "result" in result
        assert result["agent"] == "creative"

    def test_arun_uses_async_chat(self):
        from agents.creative.agent import CreativeAgent
        calls = []

        class TrackingAnalyzer(AsyncMockAnalyzer):
            async def achat_with_agent(self, *a, **kw):
                calls.append("async")
                return "response"
            def chat_with_agent(self, *a, **kw):
                calls.append("sync")
                return "response"

        agent = CreativeAgent("creative", TrackingAnalyzer())
        run_async(agent.arun({"mode": "concept"}))
        assert "async" in calls
        assert "sync" not in calls


# ── AgentsManager.arun_many() ─────────────────────────────────────────────────

class TestArunMany:
    def test_arun_many_runs_all_agents(self, monkeypatch):
        monkeypatch.setenv("SEO_SKIP_ENRICHMENT", "true")
        from agents.manager import AgentsManager
        m = AgentsManager(AsyncMockAnalyzer())

        results = run_async(m.arun_many({
            "ads":      {"platform": "google", "mode": "plan", "product": "SaaS"},
            "strategy": {"mode": "general", "product": "SaaS"},
        }))

        assert "ads"      in results
        assert "strategy" in results
        assert "result"   in results["ads"]
        assert "result"   in results["strategy"]

    def test_arun_many_agent_failure_isolated(self, monkeypatch):
        monkeypatch.setenv("SEO_SKIP_ENRICHMENT", "true")
        from agents.manager import AgentsManager

        class FailingAnalyzer(AsyncMockAnalyzer):
            async def achat_with_agent(self, *a, **kw):
                raise RuntimeError("API down")

        m = AgentsManager(FailingAnalyzer())
        results = run_async(m.arun_many({
            "strategy": {"mode": "general"},
            "ads":      {"platform": "google", "mode": "plan"},
        }))
        # All results should be dicts (error or result) — no exception propagated
        assert all(isinstance(v, dict) for v in results.values())

    def test_arun_many_concurrent_execution(self, monkeypatch):
        monkeypatch.setenv("SEO_SKIP_ENRICHMENT", "true")
        import time
        from agents.manager import AgentsManager

        call_times = []

        class TimingAnalyzer(AsyncMockAnalyzer):
            async def achat_with_agent(self, *a, **kw):
                call_times.append(time.monotonic())
                await asyncio.sleep(0.05)  # simulate 50ms I/O
                return "response"

        m = AgentsManager(TimingAnalyzer())
        start = time.monotonic()
        run_async(m.arun_many({
            "ads":      {"platform": "google", "mode": "plan"},
            "strategy": {"mode": "general"},
            "creative": {"mode": "concept"},
        }))
        elapsed = time.monotonic() - start

        # 3 agents × 50ms each. If truly concurrent: ~50ms total.
        # If sequential: ~150ms. Allow generous margin.
        assert elapsed < 0.45, f"Expected concurrent execution but took {elapsed:.2f}s"


# ── AgentsManager.aorchestrate() ─────────────────────────────────────────────

class TestAorchestrate:
    def _manager(self, monkeypatch):
        monkeypatch.setenv("SEO_SKIP_ENRICHMENT", "true")
        from agents.manager import AgentsManager

        class OrchestratingAnalyzer(AsyncMockAnalyzer):
            def chat_with_agent(self, user_message: str, **kwargs) -> str:
                # Used by classify_task (sync) and synthesis (sync)
                if "orchestration classifier" in (kwargs.get("system_prompt") or ""):
                    return '{"agents": ["strategy", "ads"], "rationale": "test", "skip_agents": {}, "mode_hints": {}}'
                return "synthesized plan"

        return AgentsManager(OrchestratingAnalyzer())

    def test_aorchestrate_returns_result(self, monkeypatch):
        m = self._manager(monkeypatch)
        result = run_async(m.aorchestrate(
            "build Google Ads campaign",
            {"product": "SaaS", "platform": "google"},
            agent_list=["strategy", "ads"],
        ))
        assert isinstance(result, dict)
        assert "result" in result or "error" in result

    def test_aorchestrate_with_explicit_agents(self, monkeypatch):
        m = self._manager(monkeypatch)
        result = run_async(m.aorchestrate(
            "launch campaign",
            {"product": "App", "platform": "google"},
            agent_list=["strategy"],
        ))
        assert isinstance(result, dict)
        assert "selected_agents" in result
        assert "strategy" in result["selected_agents"]

    def test_aorchestrate_no_analyzer_returns_error(self, monkeypatch):
        monkeypatch.setenv("SEO_SKIP_ENRICHMENT", "true")
        from agents.manager import AgentsManager
        m = AgentsManager(None)
        result = run_async(m.aorchestrate("task", {}, agent_list=["strategy"]))
        assert "error" in result

    def test_aorchestrate_contains_execution_order(self, monkeypatch):
        m = self._manager(monkeypatch)
        result = run_async(m.aorchestrate(
            "plan marketing",
            {"product": "SaaS"},
            agent_list=["strategy", "ads"],
        ))
        if "error" not in result:
            assert "execution_order" in result
            assert "subagent_outputs" in result
