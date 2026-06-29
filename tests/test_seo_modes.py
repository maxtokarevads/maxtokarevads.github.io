"""Tests for new SEO agent modes and Canon Rules."""
import pytest
from agents.seo.agent import SEOAgent
from agents.seo.skills import SUPPORTED_MODES
from agents.seo.skills.technical import build_technical_prompt
from agents.seo.skills.content   import build_content_prompt
from agents.seo.skills.local     import build_local_prompt
from agents.seo.skills.schema    import build_schema_prompt
from agents.seo.skills.backlinks import build_backlinks_prompt
from agents.seo.skills.cluster   import build_cluster_prompt
from agents.seo.skills.sxo      import build_sxo_prompt
from agents.seo.skills.canon     import build_seo_audit_prompt, SEO_CANON_RULES, P0_RULES
from agents.seo.drift            import compute_drift


class MockAnalyzer:
    def chat_with_agent(self, user_message, system_prompt=None, history=None, **kwargs):
        return f"mock:{user_message[:40]}"


_AGENT = lambda: SEOAgent("seo", MockAnalyzer())


# ── SUPPORTED_MODES ───────────────────────────────────────────────────────────

def test_supported_modes_count():
    assert len(SUPPORTED_MODES) == 15


def test_supported_modes_includes_all():
    for mode in ["seo", "aeo", "technical", "content", "local",
                 "schema", "backlinks", "cluster", "sxo", "audit", "drift",
                 "article", "brief", "meta", "rewrite"]:
        assert mode in SUPPORTED_MODES, f"Missing mode: {mode}"


# ── INPUT VALIDATION ─────────────────────────────────────────────────────────

def test_unknown_mode_returns_error():
    r = _AGENT().run({"site": "x.com", "mode": "nonexistent"})
    assert "error" in r


def test_valid_modes_dont_error():
    for mode in ["seo", "aeo", "technical", "content", "local",
                 "schema", "backlinks", "cluster", "sxo", "audit"]:
        r = _AGENT().run({"site": "x.com", "mode": mode})
        assert "error" not in r, f"Mode '{mode}' returned error: {r}"
        assert "result" in r


# ── PROMPT BUILDERS ───────────────────────────────────────────────────────────

def test_technical_prompt_contains_9_categories():
    p = build_technical_prompt({"site": "x.com"})
    for cat in ["CRAWLABILITY", "INDEXABILITY", "SECURITY", "MOBILE",
                "CORE WEB VITALS", "STRUCTURED DATA", "JAVASCRIPT", "INDEXNOW"]:
        assert cat in p.upper(), f"Technical prompt missing: {cat}"


def test_technical_prompt_mentions_inp():
    p = build_technical_prompt({"site": "x.com"})
    assert "INP" in p
    assert "200ms" in p or "200" in p


def test_technical_prompt_requests_health_score():
    p = build_technical_prompt({"site": "x.com"})
    assert "HEALTH SCORE" in p.upper() or "health score" in p.lower()


def test_content_prompt_eeat_sections():
    p = build_content_prompt({"site": "x.com"})
    for signal in ["EXPERIENCE", "EXPERTISE", "AUTHORITATIVENESS", "TRUSTWORTHINESS"]:
        assert signal in p.upper(), f"Content prompt missing E-E-A-T signal: {signal}"


def test_content_prompt_confidence_section():
    p = build_content_prompt({"site": "x.com"})
    assert "CONFIDENCE" in p.upper()


def test_local_prompt_gbp_section():
    p = build_local_prompt({"site": "x.com"})
    assert "GOOGLE BUSINESS PROFILE" in p.upper() or "GBP" in p


def test_local_prompt_nap_section():
    p = build_local_prompt({"site": "x.com"})
    assert "NAP" in p


def test_schema_prompt_json_ld():
    p = build_schema_prompt({"site": "x.com"})
    assert "JSON-LD" in p or "json" in p.lower()


def test_schema_prompt_deprecated_warning():
    p = build_schema_prompt({"site": "x.com"})
    assert "2023" in p or "deprecated" in p.lower() or "HowTo" in p


def test_backlinks_prompt_anchor_text():
    p = build_backlinks_prompt({"site": "x.com"})
    assert "anchor" in p.lower()
    assert "exact-match" in p.lower() or "exact match" in p.lower()


def test_backlinks_prompt_competitor_gap():
    p = build_backlinks_prompt({"site": "x.com", "competitors": ["comp.com"]})
    assert "comp.com" in p
    assert "gap" in p.lower() or "competitor" in p.lower()


def test_cluster_prompt_pillar_spoke():
    p = build_cluster_prompt({"site": "x.com", "seed": ["project management"]})
    assert "PILLAR" in p.upper()
    assert "spoke" in p.lower() or "SPOKE" in p.upper()
    assert "project management" in p.lower()


def test_cluster_prompt_internal_linking():
    p = build_cluster_prompt({"site": "x.com"})
    assert "internal link" in p.lower() or "INTERNAL LINKING" in p.upper()


def test_sxo_prompt_5_personas():
    p = build_sxo_prompt({"site": "x.com", "keyword": "crm software"})
    for persona in ["BUYER", "RESEARCHER", "COMPARISON", "LOCAL", "MOBILE"]:
        assert persona in p.upper(), f"SXO prompt missing persona: {persona}"


def test_sxo_prompt_mentions_keyword():
    p = build_sxo_prompt({"site": "x.com", "keyword": "crm software"})
    assert "crm software" in p.lower()


# ── CANON RULES ───────────────────────────────────────────────────────────────

def test_canon_rules_count():
    assert len(SEO_CANON_RULES) >= 28, f"Expected ≥28 rules, got {len(SEO_CANON_RULES)}"


def test_p0_rules_exist():
    assert len(P0_RULES) >= 6, f"Expected ≥6 P0 rules, got {len(P0_RULES)}"


def test_canon_rules_have_required_fields():
    required = {"id", "severity", "area", "rule", "why", "verify"}
    for rule in SEO_CANON_RULES:
        missing = required - set(rule.keys())
        assert not missing, f"Rule {rule.get('id')} missing fields: {missing}"


def test_canon_rule_ids_unique():
    ids = [r["id"] for r in SEO_CANON_RULES]
    assert len(ids) == len(set(ids)), "Duplicate Canon Rule IDs found"


def test_canon_rule_ids_format():
    for rule in SEO_CANON_RULES:
        assert rule["id"].startswith("SEC-"), f"Bad rule ID format: {rule['id']}"


def test_audit_prompt_contains_p0():
    p = build_seo_audit_prompt({"site": "x.com"})
    assert "P0" in p
    assert "HALT" in p


def test_audit_prompt_contains_health_score():
    p = build_seo_audit_prompt({"site": "x.com"})
    assert "HEALTH SCORE" in p.upper()


def test_audit_prompt_includes_rule_ids():
    p = build_seo_audit_prompt({"site": "x.com"})
    assert "SEC-0001" in p
    assert "SEC-0007" in p  # AI crawlers rule


# ── DRIFT MONITORING ─────────────────────────────────────────────────────────

def test_compute_drift_detects_drop():
    baseline = {"organic_sessions": 1000, "avg_position": 5.0}
    current  = {"organic_sessions":  700, "avg_position": 8.0}
    drift = compute_drift(baseline, current)
    assert "organic_sessions" in drift
    assert drift["organic_sessions"]["delta_pct"] < 0
    assert drift["organic_sessions"]["alert"] is True  # >15% drop


def test_compute_drift_detects_gain():
    baseline = {"organic_sessions": 1000}
    current  = {"organic_sessions": 1200}
    drift = compute_drift(baseline, current)
    assert drift["organic_sessions"]["delta_pct"] > 0
    assert drift["organic_sessions"]["alert"] is False


def test_compute_drift_stable():
    baseline = {"organic_sessions": 1000}
    current  = {"organic_sessions": 1010}
    drift = compute_drift(baseline, current)
    assert drift["organic_sessions"]["alert"] is False
    assert "STABLE" in drift["organic_sessions"]["status"]


def test_compute_drift_ignores_missing_keys():
    baseline = {"organic_sessions": 1000, "ctr": 0.05}
    current  = {"organic_sessions": 900}  # ctr missing
    drift = compute_drift(baseline, current)
    assert "organic_sessions" in drift
    assert "ctr" not in drift  # missing current value → skipped


# ── SYSTEM PROMPTS ────────────────────────────────────────────────────────────

def test_system_prompts_unique_per_mode():
    agent = SEOAgent("seo", None)
    prompts = {mode: agent.get_system_prompt(mode) for mode in SUPPORTED_MODES if mode != "drift"}
    unique = set(prompts.values())
    assert len(unique) == len(prompts), "Some SEO modes share identical system prompts"


def test_audit_system_prompt_mentions_halt():
    agent = SEOAgent("seo", None)
    p = agent.get_system_prompt("audit")
    assert "HALT" in p


def test_drift_system_prompt_mentions_baseline():
    agent = SEOAgent("seo", None)
    p = agent.get_system_prompt("drift")
    assert "baseline" in p.lower()
