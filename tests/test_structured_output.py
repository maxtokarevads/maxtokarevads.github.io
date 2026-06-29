"""Tests for structured output in AdsAgent.run() — no API calls."""
import pytest
from agents.ads.agent import AdsAgent
from agents.ads.skills.structured import (
    STRUCTURED_TOOLS, split_structured_result,
    ANALYZE_TOOL, COPY_TOOL, BUDGET_TOOL,
    PLAN_TOOL, RETARGETING_TOOL, AB_TEST_TOOL,
    RESEARCH_TOOL, LANDING_TOOL, FORECAST_TOOL,
)


# ── Mock analyzers ────────────────────────────────────────────────────────────

class AnalyzerWithCallTool:
    model_name = "claude-sonnet-4-6"

    def __init__(self, tool_result: dict):
        self._tool_result = dict(tool_result)  # copy so pop() doesn't mutate fixture

    def call_tool(self, user_message, tool, system_prompt=None,
                  model_override=None, cached_context=None):
        return dict(self._tool_result)

    def chat_with_agent(self, user_message, system_prompt=None, **kwargs):
        return "fallback narrative"


class AnalyzerNoCallTool:
    model_name = "claude-haiku-4-5-20251001"

    def chat_with_agent(self, user_message, system_prompt=None, **kwargs):
        return "plain text response"


class AnalyzerCallToolFails:
    model_name = "claude-sonnet-4-6"

    def call_tool(self, *args, **kwargs):
        return None  # simulates API failure / no tool_use block

    def chat_with_agent(self, user_message, system_prompt=None, **kwargs):
        return "fallback after call_tool failure"


# ── split_structured_result ───────────────────────────────────────────────────

def test_split_extracts_narrative():
    raw = {"narrative": "Good analysis", "findings": [], "missing_data": [], "overall_health": "good"}
    narrative, structured = split_structured_result(raw)
    assert narrative == "Good analysis"
    assert "findings" in structured
    assert "narrative" not in structured  # popped out


def test_split_none_returns_empty():
    narrative, structured = split_structured_result(None)
    assert narrative == ""
    assert structured == {}


def test_split_non_dict_returns_empty():
    narrative, structured = split_structured_result("oops")
    assert narrative == ""
    assert structured == {}


# ── Structured output in AdsAgent.run() ──────────────────────────────────────

_ANALYZE_RESULT = {
    "narrative":      "CTR is low at 0.8%, below the 2% benchmark.",
    "findings":       [{"metric": "CTR", "severity": "P1", "issue": "Low CTR",
                        "action": "Test new headlines", "confidence": "high"}],
    "missing_data":   ["ADS__ImpressionShare"],
    "overall_health": "fair",
}

_COPY_RESULT = {
    "narrative":       "Three variants with different hooks.",
    "platform":        "google",
    "variants":        [{"hook_type": "urgency", "headline": "Save 30% Today",
                         "description": "Limited offer.", "cta": "Shop Now",
                         "char_counts": {"headline": 15, "description": 15},
                         "compliant": True}],
    "platform_limits": {"headline": 30, "description": 90},
}

_BUDGET_RESULT = {
    "narrative":         "Google takes 60% for bottom-funnel conversions.",
    "allocation":        [{"platform": "google", "amount_usd": 3000, "percentage": 60,
                           "rationale": "Highest ROAS", "min_threshold_met": True}],
    "total_budget":      5000,
    "break_even_roas":   2.0,
    "marginal_roas_note": "Next $1 to Google Search.",
}


@pytest.mark.parametrize("mode,tool_result,expected_key", [
    ("analyze", _ANALYZE_RESULT, "findings"),
    ("copy",    _COPY_RESULT,    "variants"),
    ("budget",  _BUDGET_RESULT,  "allocation"),
])
def test_structured_modes_return_structured_key(mode, tool_result, expected_key):
    agent = AdsAgent("ads", AnalyzerWithCallTool(tool_result))
    payload = {"platform": "google", "mode": mode, "product": "SaaS CRM", "budget": 5000}
    result = agent.run(payload)

    assert "result" in result
    assert "structured" in result, f"mode={mode} should have 'structured' key"
    assert expected_key in result["structured"], f"structured missing '{expected_key}' for mode={mode}"


def test_analyze_structured_has_overall_health():
    agent = AdsAgent("ads", AnalyzerWithCallTool(_ANALYZE_RESULT))
    result = agent.run({"platform": "google", "mode": "analyze", "product": "SaaS"})
    assert result["structured"]["overall_health"] == "fair"


def test_copy_structured_has_platform_limits():
    agent = AdsAgent("ads", AnalyzerWithCallTool(_COPY_RESULT))
    result = agent.run({"platform": "google", "mode": "copy", "product": "SaaS"})
    assert result["structured"]["platform_limits"]["headline"] == 30


def test_budget_structured_has_break_even():
    agent = AdsAgent("ads", AnalyzerWithCallTool(_BUDGET_RESULT))
    result = agent.run({"mode": "budget", "platforms": ["google"], "budget": 5000})
    assert result["structured"]["break_even_roas"] == 2.0


# ── Fallback paths ────────────────────────────────────────────────────────────

def test_no_call_tool_falls_back_to_text():
    agent = AdsAgent("ads", AnalyzerNoCallTool())
    result = agent.run({"platform": "google", "mode": "analyze", "product": "SaaS"})
    assert result["result"] == "plain text response"
    assert "structured" not in result


def test_call_tool_returns_none_falls_back():
    agent = AdsAgent("ads", AnalyzerCallToolFails())
    result = agent.run({"platform": "google", "mode": "analyze", "product": "SaaS"})
    assert result["result"] == "fallback after call_tool failure"
    assert "structured" not in result


# ── Non-structured modes not affected ────────────────────────────────────────

def test_plan_mode_has_no_structured_key():
    agent = AdsAgent("ads", AnalyzerWithCallTool({}))
    result = agent.run({"platform": "google", "mode": "plan", "product": "SaaS"})
    # plan is not in STRUCTURED_TOOLS — should use chat_with_agent
    assert "result" in result
    assert "structured" not in result


def test_audit_mode_has_no_structured_key():
    agent = AdsAgent("ads", AnalyzerWithCallTool({}))
    result = agent.run({"platform": "google", "mode": "audit", "product": "SaaS"})
    assert "result" in result
    assert "structured" not in result


# ── Tool schema integrity ─────────────────────────────────────────────────────

def test_all_tools_have_required_fields():
    for mode, tool in STRUCTURED_TOOLS.items():
        assert "name" in tool, f"{mode} tool missing 'name'"
        assert "input_schema" in tool, f"{mode} tool missing 'input_schema'"
        schema = tool["input_schema"]
        assert "narrative" in schema["properties"], f"{mode} schema missing 'narrative'"
        assert "narrative" in schema["required"], f"{mode} schema: narrative not required"


def test_structured_tools_registry_covers_key_modes():
    for mode in ("analyze", "copy", "budget", "plan", "retargeting", "ab_test",
                 "research", "landing", "forecast"):
        assert mode in STRUCTURED_TOOLS, f"STRUCTURED_TOOLS missing mode: {mode}"


# ── New schemas: run() integration ────────────────────────────────────────────

_PLAN_RESULT = {
    "narrative": "Launch Google Search + PMax in week 1.",
    "campaigns": [{"name": "Brand Search", "type": "Search", "objective": "conversions",
                   "budget_usd": 3000, "targeting": "branded keywords", "bid_strategy": "tCPA"}],
    "launch_timeline": [{"week": 1, "action": "Set up campaigns", "owner": "media buyer"}],
    "success_criteria": {"target_cpa": 25, "target_roas": 3.0, "review_at_days": 14, "kpis": ["CPA", "ROAS"]},
}

_RETARGETING_RESULT = {
    "narrative": "Three-stage remarketing funnel.",
    "segments": [{"name": "Cart abandoners", "funnel_stage": "BOFU", "signal": "add_to_cart no purchase",
                  "message": "You left something behind", "cta": "Complete purchase"}],
    "pixel_events": ["ViewContent", "AddToCart", "Purchase"],
    "budget_split": {"tofu_pct": 20, "mofu_pct": 30, "bofu_pct": 50},
}

_AB_TEST_RESULT = {
    "narrative": "Test headline vs benefit-led headline.",
    "hypothesis": "Benefit-led headline will improve CTR by 15%.",
    "variable_tested": "headline",
    "variants": [{"label": "control", "description": "Current headline"},
                 {"label": "variant_A", "description": "Benefit-led", "change": "Add '30% cheaper'"}],
    "sample_size_per_variant": 5000,
    "duration_days": 14,
    "success_metric": "CTR",
    "native_tool": "Ad Variations",
}

_RESEARCH_RESULT = {
    "narrative": "Keyword universe for SaaS CRM.",
    "keywords": [{"keyword": "crm software", "match_type": "exact", "intent": "commercial", "priority": "high"}],
    "negative_keywords": ["free", "tutorial"],
    "audience_segments": [],
    "creative_insights": [],
}

_LANDING_RESULT = {
    "narrative": "Page has critical above-fold issues.",
    "fixlist": [{"priority": "P0", "layer": "above_fold", "issue": "No clear headline",
                 "fix": "Add benefit-led H1", "expected_lift": "+10% CVR"}],
    "ab_test_shortlist": [{"element": "CTA button color", "hypothesis": "Green CTA lifts clicks",
                            "sample_size_est": 2000}],
    "overall_score": 42,
    "p0_count": 1, "p1_count": 2, "p2_count": 3,
}

_FORECAST_RESULT = {
    "narrative": "Base scenario: 50 conversions/month at $20 CPA.",
    "assumptions": {"cpm": 5.0, "ctr": 0.02, "cvr": 0.03, "avg_order": 100},
    "scenarios": {
        "conservative": {"impressions": 80000, "clicks": 1200, "conversions": 30, "spend_usd": 1000, "cpa": 33},
        "base":         {"impressions": 100000, "clicks": 1500, "conversions": 50, "spend_usd": 1000, "cpa": 20},
        "optimistic":   {"impressions": 120000, "clicks": 2000, "conversions": 80, "spend_usd": 1000, "cpa": 12},
    },
    "break_even_cpa": 35,
    "break_even_roas": 2.0,
    "biggest_cpa_lever": "CVR",
    "learning_phase_days": 7,
    "risk_factors": [{"risk": "Seasonality", "mitigation": "Increase budget in peak weeks"}],
}


@pytest.mark.parametrize("mode,tool_result,expected_key,platform", [
    ("plan",        _PLAN_RESULT,        "campaigns",  "google"),
    ("retargeting", _RETARGETING_RESULT, "segments",   "meta"),
    ("ab_test",     _AB_TEST_RESULT,     "variants",   "google"),
    ("research",    _RESEARCH_RESULT,    "keywords",   "tiktok"),
    ("landing",     _LANDING_RESULT,     "fixlist",    "google"),
    ("forecast",    _FORECAST_RESULT,    "scenarios",  "google"),
])
def test_new_structured_modes(mode, tool_result, expected_key, platform):
    agent = AdsAgent("ads", AnalyzerWithCallTool(tool_result))
    payload = {"platform": platform, "mode": mode, "product": "SaaS CRM", "budget": 5000}
    result = agent.run(payload)

    assert "result" in result
    assert "structured" in result, f"mode={mode} missing 'structured'"
    assert expected_key in result["structured"], f"mode={mode} missing '{expected_key}' in structured"


def test_plan_has_success_criteria():
    agent = AdsAgent("ads", AnalyzerWithCallTool(_PLAN_RESULT))
    result = agent.run({"platform": "google", "mode": "plan", "product": "SaaS"})
    assert "success_criteria" in result["structured"]
    assert result["structured"]["success_criteria"]["review_at_days"] == 14


def test_retargeting_has_budget_split():
    agent = AdsAgent("ads", AnalyzerWithCallTool(_RETARGETING_RESULT))
    result = agent.run({"platform": "meta", "mode": "retargeting", "product": "SaaS"})
    split = result["structured"]["budget_split"]
    assert split["bofu_pct"] == 50


def test_ab_test_has_sample_size():
    agent = AdsAgent("ads", AnalyzerWithCallTool(_AB_TEST_RESULT))
    result = agent.run({"platform": "google", "mode": "ab_test", "product": "SaaS"})
    assert result["structured"]["sample_size_per_variant"] == 5000
    assert result["structured"]["native_tool"] == "Ad Variations"


def test_landing_has_overall_score():
    agent = AdsAgent("ads", AnalyzerWithCallTool(_LANDING_RESULT))
    result = agent.run({"mode": "landing", "url": "https://example.com"})
    assert result["structured"]["overall_score"] == 42


def test_forecast_has_three_scenarios():
    agent = AdsAgent("ads", AnalyzerWithCallTool(_FORECAST_RESULT))
    result = agent.run({"mode": "forecast", "budget": 1000, "months": 3})
    scenarios = result["structured"]["scenarios"]
    assert all(k in scenarios for k in ("conservative", "base", "optimistic"))


def test_forecast_biggest_cpa_lever():
    agent = AdsAgent("ads", AnalyzerWithCallTool(_FORECAST_RESULT))
    result = agent.run({"mode": "forecast", "budget": 1000})
    assert result["structured"]["biggest_cpa_lever"] == "CVR"


# ── audit still excluded from structured ─────────────────────────────────────

def test_audit_still_has_no_structured():
    agent = AdsAgent("ads", AnalyzerWithCallTool({}))
    result = agent.run({"platform": "google", "mode": "audit", "product": "SaaS"})
    assert "structured" not in result
