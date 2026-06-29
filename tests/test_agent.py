"""
Tests for the current AdvertisingAnalyticsAgent API.
Run: pytest tests/test_agent.py -v
"""
import pytest
from unittest.mock import MagicMock, patch

from agents.ads.skills.prompt import AdsRequest, build_ads_prompt, SUPPORTED_PLATFORMS, SUPPORTED_MODES
from agents.ads.skills.canon.demo_payload import get_demo_payload


# ── AdsRequest normalization ──────────────────────────────────────────────────

def test_ads_request_platform_alias_facebook():
    req = AdsRequest.from_dict({"platform": "facebook", "mode": "plan"})
    assert req.platform == "meta"


def test_ads_request_platform_alias_instagram():
    req = AdsRequest.from_dict({"platform": "instagram", "mode": "audit"})
    assert req.platform == "meta"


def test_ads_request_platform_alias_google_ads():
    req = AdsRequest.from_dict({"platform": "google_ads", "mode": "copy"})
    assert req.platform == "google"


def test_ads_request_mode_normalised_to_lowercase():
    req = AdsRequest.from_dict({"platform": "google", "mode": "AUDIT"})
    assert req.mode == "audit"


def test_ads_request_unknown_keys_ignored():
    req = AdsRequest.from_dict({"platform": "meta", "mode": "plan", "unknown_field": "x"})
    assert req.platform == "meta"


# ── Prompt router ─────────────────────────────────────────────────────────────

def test_router_returns_string_for_all_platforms_and_audit():
    for plat in SUPPORTED_PLATFORMS:
        result = build_ads_prompt({"platform": plat, "mode": "audit", "command": "/audit"})
        assert isinstance(result, str)
        assert len(result) > 100


def test_router_unsupported_platform_gives_friendly_fallback():
    result = build_ads_prompt({"platform": "snapchat", "mode": "plan"})
    assert isinstance(result, str)
    assert "snapchat" in result.lower() or "not supported" in result.lower()


def test_router_unsupported_mode_returns_error():
    result = build_ads_prompt({"platform": "google", "mode": "xyz_unknown"})
    assert result.startswith("ERROR:")


def test_budget_mode_platform_agnostic():
    result = build_ads_prompt({"mode": "budget", "budget": 5000, "platforms": ["google", "meta"]})
    assert isinstance(result, str)
    assert "budget" in result.lower() or "allocation" in result.lower()


def test_landing_mode_platform_agnostic():
    result = build_ads_prompt({"mode": "landing", "product": "SaaS", "url": "https://example.com"})
    assert isinstance(result, str)
    assert "cro" in result.lower() or "landing" in result.lower()


# ── Canon rules injection ─────────────────────────────────────────────────────

def test_google_audit_prompt_includes_p0_gates():
    result = build_ads_prompt({"platform": "google", "mode": "audit", "command": "/audit"})
    assert "P0" in result
    assert "auto-tagging" in result.lower()


def test_meta_audit_prompt_includes_capi():
    result = build_ads_prompt({"platform": "meta", "mode": "audit", "command": "/audit"})
    assert "CAPI" in result or "capi" in result.lower()


def test_tiktok_audit_prompt_includes_hook_rate():
    result = build_ads_prompt({"platform": "tiktok", "mode": "audit", "command": "/audit"})
    assert "hook rate" in result.lower() or "hook_rate" in result.lower()


# ── SOP coverage ─────────────────────────────────────────────────────────────

def test_google_sops_all_canon_commands_have_entry():
    from agents.ads.skills.canon.sops import get_sop_steps
    google_commands = [
        "/audit", "/weekly", "/monthly", "/tracking", "/incident",
        "/feed", "/pmax", "/quarterly", "/searchterms", "/launch",
        "/semantic", "/fixlist", "/measurement", "/b2b",
    ]
    for cmd in google_commands:
        result = get_sop_steps(cmd)
        assert isinstance(result, str) and len(result) > 20, f"SOP missing for {cmd}"


def test_meta_sops_all_canon_commands_have_entry():
    from agents.ads.skills.canon.meta_sops import get_meta_sop_steps
    meta_commands = [
        "/audit", "/tracking", "/weekly", "/creative", "/scale",
        "/audiences", "/asc", "/incident", "/launch", "/retargeting",
        "/measurement", "/b2b", "/attribution", "/ios14", "/dpa",
        "/abtest", "/seasonal",
    ]
    for cmd in meta_commands:
        result = get_meta_sop_steps(cmd)
        assert "No dedicated SOP" not in result, f"Meta SOP missing for {cmd}"


def test_tiktok_sops_hookrate_and_smartplus():
    from agents.ads.skills.canon.tiktok_sops import get_tiktok_sop_steps
    for cmd in ["/hookrate", "/smartplus"]:
        result = get_tiktok_sop_steps(cmd)
        assert "No SOP" not in result, f"TikTok SOP missing for {cmd}"


# ── Demo payloads ─────────────────────────────────────────────────────────────

def test_demo_google_has_required_fields():
    p = get_demo_payload("google")
    assert p["platform"] == "google"
    assert p["project"]
    assert p["inputs"]
    assert p["metrics"]


def test_demo_meta_alias_facebook():
    p = get_demo_payload("facebook")
    assert p["platform"] == "meta"


def test_demo_tiktok():
    p = get_demo_payload("tiktok")
    assert p["platform"] == "tiktok"
    assert len(p["inputs"]) >= 5


# ── Canon rules count sanity ──────────────────────────────────────────────────

def test_google_canon_has_at_least_33_rules():
    from agents.ads.skills.canon.rules import CANON_RULES
    assert len(CANON_RULES) >= 33


def test_meta_canon_has_at_least_20_rules():
    from agents.ads.skills.canon.meta_rules import META_CANON_RULES
    assert len(META_CANON_RULES) >= 20


def test_tiktok_canon_has_at_least_20_rules():
    from agents.ads.skills.canon.tiktok_rules import TIKTOK_CANON_RULES
    assert len(TIKTOK_CANON_RULES) >= 20


# ── Benchmarks ────────────────────────────────────────────────────────────────

def test_benchmarks_have_2026_dates():
    from agents.ads.skills.benchmarks import benchmark_summary
    summary = benchmark_summary("google")
    assert "2026" in summary


def test_all_platform_benchmarks_return_strings():
    from agents.ads.skills.benchmarks import benchmark_summary
    for plat in ["google", "meta", "tiktok"]:
        result = benchmark_summary(plat)
        assert isinstance(result, str) and len(result) > 50
