"""Tests for AEO skill and SEOAgent mode routing."""
from agents.seo.skills.aeo import build_aeo_prompt
from agents.seo.skills import SUPPORTED_MODES
from agents.seo.agent import SEOAgent, _SYSTEM_PROMPTS


# ---------------------------------------------------------------------------
# AEO prompt content
# ---------------------------------------------------------------------------

def test_aeo_prompt_not_empty():
    p = build_aeo_prompt({"site": "mysite.io", "query": "get cited by AI"})
    assert len(p) > 500


def test_aeo_mentions_key_platforms():
    p = build_aeo_prompt({"site": "x.com"})
    for platform in ["Perplexity", "ChatGPT", "Google AI Overviews", "Bing"]:
        assert platform in p, f"AEO prompt missing platform: {platform}"


def test_aeo_includes_sections():
    p = build_aeo_prompt({"site": "x.com"})
    for section in ["ENTITY", "SCHEMA", "E-E-A-T", "FAQ", "MONITORING", "ACTION PLAN"]:
        assert section in p, f"AEO prompt missing section: {section}"


def test_aeo_mentions_robots_txt_and_ai_bots():
    p = build_aeo_prompt({"site": "x.com"})
    assert "GPTBot" in p or "ClaudeBot" in p or "robots" in p.lower()


def test_aeo_includes_faq_schema():
    p = build_aeo_prompt({"site": "x.com"})
    assert "FAQPage" in p or "schema" in p.lower()


def test_aeo_site_in_prompt():
    p = build_aeo_prompt({"site": "example.io"})
    assert "example.io" in p


def test_aeo_industry_in_prompt():
    p = build_aeo_prompt({"site": "x.com", "industry": "saas"})
    assert "saas" in p.lower()


def test_aeo_product_in_prompt():
    p = build_aeo_prompt({"site": "x.com", "product": "AI CRM"})
    assert "AI CRM" in p


def test_aeo_keywords_in_prompt():
    p = build_aeo_prompt({"site": "x.com", "keywords": ["crm", "saas", "ai"]})
    assert "crm" in p and "saas" in p


def test_aeo_competitors_in_prompt():
    p = build_aeo_prompt({"site": "x.com", "competitors": ["Competitor A"]})
    assert "Competitor A" in p


# ---------------------------------------------------------------------------
# SEOAgent mode routing
# ---------------------------------------------------------------------------

def test_seo_supported_modes():
    assert "seo" in SUPPORTED_MODES
    assert "aeo" in SUPPORTED_MODES


def test_seo_system_prompts_differ():
    agent = SEOAgent("seo", None)
    assert agent.get_system_prompt("seo") != agent.get_system_prompt("aeo")


def test_seo_aeo_system_prompt_mentions_llm():
    agent = SEOAgent("seo", None)
    p = agent.get_system_prompt("aeo")
    assert any(w in p for w in ["LLM", "AI", "Perplexity", "ChatGPT", "AEO", "GEO"])


def test_seo_default_mode_is_seo():
    agent = SEOAgent("seo", None)
    assert agent.get_system_prompt() == _SYSTEM_PROMPTS["seo"]


class MockAnalyzer:
    def chat_with_agent(self, user_message=None, system_prompt=None, history=None, **kw):
        return f"response|system={system_prompt[:30] if system_prompt else ''}"


def test_seo_run_uses_seo_mode_by_default():
    agent = SEOAgent("seo", MockAnalyzer())
    r = agent.run({"site": "x.com", "keywords": []})
    assert r["mode"] == "seo"
    assert r["agent"] == "seo"


def test_seo_run_aeo_mode():
    agent = SEOAgent("seo", MockAnalyzer())
    r = agent.run({"site": "x.com", "mode": "aeo"})
    assert r["mode"] == "aeo"
    assert "aeo" in r.get("result", "").lower() or len(r["result"]) > 0


def test_seo_run_unknown_mode_returns_error():
    """Unknown mode now returns validation error (not silent fallback)."""
    agent = SEOAgent("seo", MockAnalyzer())
    r = agent.run({"site": "x.com", "mode": "unknown"})
    assert "error" in r


def test_seo_run_no_analyzer():
    agent = SEOAgent("seo", None)
    r = agent.run({"site": "x.com", "mode": "aeo"})
    assert "error" in r
