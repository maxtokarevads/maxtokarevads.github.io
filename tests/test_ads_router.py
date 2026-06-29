"""Tests for AdsAgent router — no API calls required."""
import pytest
from agents.ads.skills.prompt import build_ads_prompt, SUPPORTED_PLATFORMS, SUPPORTED_MODES, _ROUTER


BASE = {
    "product": "Test SaaS",
    "budget": 1000,
    "audience": {"age": "25-45"},
    "goal": "signups",
}

METRICS = {
    "ctr": 1.5, "cpc": 2.0, "cpa": 40, "roas": 2.5,
    "impressions": 10000, "clicks": 150, "conversions": 37, "spend": 1500,
}


@pytest.mark.parametrize("platform,mode", [
    ("google",    "plan"),
    ("google",    "analyze"),
    ("google",    "copy"),
    ("google",    "retargeting"),
    ("google",    "ab_test"),
    ("meta",      "plan"),
    ("meta",      "analyze"),
    ("meta",      "copy"),
    ("meta",      "retargeting"),
    ("meta",      "ab_test"),
    ("tiktok",    "plan"),
    ("tiktok",    "analyze"),
    ("tiktok",    "copy"),
    ("tiktok",    "retargeting"),
    ("tiktok",    "ab_test"),
])
def test_router_returns_non_empty_prompt(platform, mode):
    payload = {**BASE, "platform": platform, "mode": mode, "metrics": METRICS}
    prompt = build_ads_prompt(payload)
    assert isinstance(prompt, str)
    assert len(prompt) > 100


def test_budget_mode_ignores_platform():
    payload = {**BASE, "mode": "budget", "platforms": ["google", "meta"]}
    prompt = build_ads_prompt(payload)
    assert "бюджет" in prompt.lower() or "budget" in prompt.lower()


def test_platform_aliases():
    for alias, canonical in [("facebook", "meta"), ("instagram", "meta"), ("fb", "meta"), ("google_ads", "google")]:
        p = {**BASE, "platform": alias, "mode": "plan"}
        prompt = build_ads_prompt(p)
        assert len(prompt) > 100, f"alias '{alias}' should resolve to '{canonical}'"


def test_unknown_platform_returns_fallback():
    payload = {**BASE, "platform": "linkedin", "mode": "plan"}
    prompt = build_ads_prompt(payload)
    assert "linkedin" in prompt.lower() or "не поддерживается" in prompt.lower()


def test_unknown_mode_falls_back_to_plan():
    payload = {**BASE, "platform": "google", "mode": "nonexistent_mode"}
    prompt = build_ads_prompt(payload)
    # Should fall back to plan — Google Ads plan prompt contains "Google Ads"
    assert "google" in prompt.lower()


def test_supported_constants():
    assert set(SUPPORTED_PLATFORMS) == {"google", "meta", "tiktok"}
    assert "plan" in SUPPORTED_MODES
    assert "analyze" in SUPPORTED_MODES
    assert "budget" in SUPPORTED_MODES


def test_router_structure_complete():
    for platform in SUPPORTED_PLATFORMS:
        for mode in ["plan", "analyze", "copy", "retargeting", "ab_test"]:
            assert mode in _ROUTER[platform], f"Missing {platform}/{mode}"


def test_analyze_prompt_includes_metrics():
    payload = {**BASE, "platform": "google", "mode": "analyze", "metrics": METRICS}
    prompt = build_ads_prompt(payload)
    assert "CTR" in prompt or "ctr" in prompt.lower()


def test_copy_prompt_includes_limits():
    payload = {**BASE, "platform": "google", "mode": "copy"}
    prompt = build_ads_prompt(payload)
    assert "30" in prompt  # headline limit


def test_tiktok_copy_mentions_vertical():
    payload = {**BASE, "platform": "tiktok", "mode": "copy"}
    prompt = build_ads_prompt(payload)
    assert "9:16" in prompt


def test_meta_copy_has_character_limits():
    payload = {**BASE, "platform": "meta", "mode": "copy"}
    prompt = build_ads_prompt(payload)
    assert "125" in prompt  # primary text limit


def test_budget_prompt_mentions_all_platforms():
    payload = {**BASE, "mode": "budget", "platforms": ["google", "meta", "tiktok"]}
    prompt = build_ads_prompt(payload)
    prompt_lower = prompt.lower()
    assert "google" in prompt_lower
    assert "meta" in prompt_lower or "facebook" in prompt_lower
    assert "tiktok" in prompt_lower
