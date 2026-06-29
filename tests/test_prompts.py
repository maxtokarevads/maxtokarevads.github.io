"""Tests for SEO/Strategy/Creative prompts and AdsAgent dynamic system_prompt."""
import pytest
from agents.seo.skills.prompt import build_seo_prompt
from agents.strategy.skills.prompt import build_strategy_prompt
from agents.creative.skills.prompt import build_concept_prompt as build_creative_prompt
from agents.ads.agent import AdsAgent, _SYSTEM_PROMPTS


# ---------------------------------------------------------------------------
# SEO prompt
# ---------------------------------------------------------------------------

def test_seo_uses_site_and_query():
    p = build_seo_prompt({"site": "mysite.io", "query": "grow organic traffic", "keywords": ["seo"]})
    assert "mysite.io" in p
    assert "grow organic traffic" in p
    assert "seo" in p


def test_seo_includes_sections():
    p = build_seo_prompt({"site": "x.com", "keywords": ["k"]})
    for section in ["TECHNICAL SEO", "KEYWORD RESEARCH", "CONTENT STRATEGY",
                    "LINK PROFILE", "MEASUREMENT AND KPIS", "ACTION PLAN"]:
        assert section in p, f"SEO prompt missing section: {section}"


def test_seo_includes_industry():
    p = build_seo_prompt({"site": "x.com", "industry": "saas"})
    assert "saas" in p.lower()


def test_seo_includes_funnel_stage_tofu():
    p = build_seo_prompt({"site": "x.com", "funnel_stage": "tofu"})
    assert "TOFU" in p


def test_seo_funnel_stage_bofu():
    p = build_seo_prompt({"site": "x.com", "funnel_stage": "bofu"})
    assert "BOFU" in p


def test_seo_usp_included():
    p = build_seo_prompt({"site": "x.com", "usp": "fastest deployment"})
    assert "fastest deployment" in p


def test_seo_defaults_work():
    p = build_seo_prompt({})
    assert len(p) > 200


# ---------------------------------------------------------------------------
# Strategy prompt
# ---------------------------------------------------------------------------

def test_strategy_uses_goal_and_timeline():
    p = build_strategy_prompt({"goal": "30% lead growth", "timeline": "2 months"})
    assert "30% lead growth" in p
    assert "2 months" in p


def test_strategy_includes_sections():
    p = build_strategy_prompt({"goal": "grow"})
    for section in ["POSITIONING AND DIFFERENTIATION", "CHANNEL MIX",
                    "FUNNEL AND CUSTOMER JOURNEY", "KPIS AND SUCCESS METRICS", "EXECUTION PLAN"]:
        assert section in p, f"Strategy prompt missing section: {section}"


def test_strategy_saas_benchmarks():
    p = build_strategy_prompt({"goal": "grow", "industry": "saas"})
    assert "CAC" in p or "LTV" in p or "churn" in p.lower()


def test_strategy_ecom_benchmarks():
    p = build_strategy_prompt({"goal": "grow", "industry": "ecom"})
    assert "ROAS" in p or "AOV" in p


def test_strategy_funnel_stage_included():
    p = build_strategy_prompt({"goal": "sell", "funnel_stage": "bofu"})
    assert "BOFU" in p


def test_strategy_resources_included():
    p = build_strategy_prompt({"goal": "g", "resources": {"team": "3 people", "budget": 5000}})
    assert "3 people" in p
    assert "5000" in p


# ---------------------------------------------------------------------------
# Creative prompt
# ---------------------------------------------------------------------------

def test_creative_uses_product_and_tone():
    p = build_creative_prompt({"product": "AI CRM", "tone": "bold"})
    assert "AI CRM" in p
    assert "bold" in p


def test_creative_includes_sections():
    p = build_creative_prompt({"product": "X"})
    for section in ["CORE MESSAGE", "CREATIVE CONCEPT", "READY COPY BY FORMAT",
                    "HEADLINES AND CTAS", "VISUAL DIRECTION", "A/B TEST PAIRS"]:
        assert section in p, f"Creative prompt missing section: {section}"


def test_creative_platform_google():
    p = build_creative_prompt({"product": "X", "platform": "google"})
    assert "Google" in p
    assert "30" in p  # headline limit


def test_creative_platform_tiktok():
    p = build_creative_prompt({"product": "X", "platform": "tiktok"})
    assert "TikTok" in p or "tiktok" in p.lower()
    assert "9:16" in p or "100" in p  # caption limit


def test_creative_platform_meta():
    p = build_creative_prompt({"product": "X", "platform": "meta"})
    assert "125" in p  # primary text limit


def test_creative_funnel_stage():
    p_tofu = build_creative_prompt({"product": "X", "funnel_stage": "tofu"})
    assert "TOFU" in p_tofu
    p_bofu = build_creative_prompt({"product": "X", "funnel_stage": "bofu"})
    assert "BOFU" in p_bofu


def test_creative_usp_in_prompt():
    p = build_creative_prompt({"product": "X", "usp": "10x faster"})
    assert "10x faster" in p


def test_creative_unknown_platform_no_crash():
    p = build_creative_prompt({"product": "X", "platform": "pinterest"})
    assert len(p) > 200


# ---------------------------------------------------------------------------
# AdsAgent dynamic system prompt
# ---------------------------------------------------------------------------

def test_ads_system_prompt_differs_per_mode():
    agent = AdsAgent("ads", None)
    prompts = {mode: agent.get_system_prompt(mode) for mode in _SYSTEM_PROMPTS}
    unique = set(prompts.values())
    assert len(unique) == len(_SYSTEM_PROMPTS), "All mode prompts must be unique"


def test_ads_copy_mode_mentions_copywriter():
    agent = AdsAgent("ads", None)
    p = agent.get_system_prompt("copy")
    assert "копирайтер" in p.lower() or "copywriter" in p.lower() or "лимит" in p.lower()


def test_ads_analyze_mode_mentions_data():
    agent = AdsAgent("ads", None)
    p = agent.get_system_prompt("analyze")
    assert "analyst" in p.lower() or "data" in p.lower() or "metric" in p.lower()


def test_ads_budget_mode_mentions_cmo():
    agent = AdsAgent("ads", None)
    p = agent.get_system_prompt("budget")
    assert "CMO" in p or "budget" in p.lower() or "media" in p.lower()


def test_ads_default_mode_is_plan():
    """Default (no mode) is chat consultant, intentionally different from plan."""
    agent = AdsAgent("ads", None)
    assert "consultant" in agent.get_system_prompt().lower()
    assert agent.get_system_prompt() != agent.get_system_prompt("plan")


def test_ads_unknown_mode_falls_back_to_plan():
    """Unknown mode falls back to the chat consultant system prompt."""
    agent = AdsAgent("ads", None)
    assert agent.get_system_prompt("unknown_mode") == agent.get_system_prompt()


# ---------------------------------------------------------------------------
# orchestrate _build_payload passes shared fields
# ---------------------------------------------------------------------------

def test_build_payload_seo_gets_industry_and_funnel():
    from agents.manager import AgentsManager
    mgr = AgentsManager(None)
    ctx = {"industry": "saas", "funnel_stage": "tofu", "usp": "fast", "site": "x.io"}
    p = mgr._build_payload("seo", "task", ctx)
    assert p["industry"] == "saas"
    assert p["funnel_stage"] == "tofu"
    assert p["usp"] == "fast"
    assert p["site"] == "x.io"


def test_build_payload_strategy_gets_shared_fields():
    from agents.manager import AgentsManager
    mgr = AgentsManager(None)
    ctx = {"industry": "ecom", "funnel_stage": "bofu", "product": "Shop"}
    p = mgr._build_payload("strategy", "task", ctx)
    assert p["industry"] == "ecom"
    assert p["funnel_stage"] == "bofu"
    assert p["product"] == "Shop"


def test_build_payload_creative_gets_platform():
    from agents.manager import AgentsManager
    mgr = AgentsManager(None)
    ctx = {"platform": "tiktok", "tone": "fun", "industry": "app"}
    p = mgr._build_payload("creative", "task", ctx)
    assert p["platform"] == "tiktok"
    assert p["tone"] == "fun"
    assert p["industry"] == "app"
