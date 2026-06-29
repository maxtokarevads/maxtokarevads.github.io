"""
Structured output tool schemas for AdsAgent modes.

Used with ClaudeHTTPAnalyzer.call_tool() so Claude fills both the human-readable
narrative AND a typed JSON object in a single API call.

Result shape for every tool:
    {
        "narrative": str,   -> goes into result["result"]
        ...mode fields...   -> goes into result["structured"]
    }
"""
from typing import Any, Dict, Optional

# ── Analyze ───────────────────────────────────────────────────────────────────

ANALYZE_TOOL: Dict[str, Any] = {
    "name": "report_analysis",
    "description": (
        "Report a structured diagnosis of ad campaign metrics. "
        "narrative must be the full analysis in the user's language. "
        "findings must cover every KPI with a problem or anomaly."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "narrative": {
                "type": "string",
                "description": "Full diagnosis in the user's language — same quality as a written report.",
            },
            "findings": {
                "type": "array",
                "description": "One entry per KPI issue found. Empty array if no issues.",
                "items": {
                    "type": "object",
                    "properties": {
                        "metric":          {"type": "string", "description": "e.g. CTR, ROAS, CPA"},
                        "current_value":   {"type": "string", "description": "Exact value from data"},
                        "benchmark":       {"type": "string", "description": "Expected range or industry avg"},
                        "severity":        {"type": "string", "enum": ["P0", "P1", "P2"]},
                        "issue":           {"type": "string", "description": "Root cause in one sentence"},
                        "action":          {"type": "string", "description": "Specific fix with measurable target"},
                        "confidence":      {"type": "string", "enum": ["high", "medium", "low"]},
                    },
                    "required": ["metric", "severity", "issue", "action", "confidence"],
                },
            },
            "missing_data": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Input codes that would sharpen the diagnosis (Canon INPUT_CODE format).",
            },
            "overall_health": {
                "type": "string",
                "enum": ["critical", "poor", "fair", "good", "excellent"],
                "description": "Single-word campaign health rating.",
            },
        },
        "required": ["narrative", "findings", "missing_data", "overall_health"],
    },
}

# ── Copy ──────────────────────────────────────────────────────────────────────

COPY_TOOL: Dict[str, Any] = {
    "name": "report_copy",
    "description": (
        "Report generated ad copy variants with exact character counts and platform compliance. "
        "Verify every variant against platform limits before setting compliant=true."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "narrative": {
                "type": "string",
                "description": "Brief intro and creative rationale in user's language.",
            },
            "platform": {"type": "string", "description": "google | meta | tiktok"},
            "variants": {
                "type": "array",
                "description": "3-5 copy variants with different hook strategies.",
                "items": {
                    "type": "object",
                    "properties": {
                        "hook_type":    {"type": "string", "description": "e.g. urgency, social_proof, problem_solution"},
                        "headline":     {"type": "string"},
                        "description":  {"type": "string"},
                        "cta":          {"type": "string"},
                        "char_counts": {
                            "type": "object",
                            "properties": {
                                "headline":    {"type": "integer"},
                                "description": {"type": "integer"},
                            },
                            "required": ["headline", "description"],
                        },
                        "compliant": {
                            "type": "boolean",
                            "description": "true only if both headline and description are within platform limits.",
                        },
                    },
                    "required": ["hook_type", "headline", "description", "cta", "char_counts", "compliant"],
                },
            },
            "platform_limits": {
                "type": "object",
                "description": "Exact character limits for this platform.",
                "properties": {
                    "headline":    {"type": "integer"},
                    "description": {"type": "integer"},
                },
            },
        },
        "required": ["narrative", "platform", "variants", "platform_limits"],
    },
}

# ── Budget ────────────────────────────────────────────────────────────────────

BUDGET_TOOL: Dict[str, Any] = {
    "name": "report_budget",
    "description": (
        "Report a cross-platform budget allocation with rationale for each split. "
        "allocation entries must sum to total_budget."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "narrative": {
                "type": "string",
                "description": "Full reasoning in user's language.",
            },
            "allocation": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "platform":     {"type": "string"},
                        "amount_usd":   {"type": "number"},
                        "percentage":   {"type": "number"},
                        "primary_goal": {"type": "string", "description": "e.g. awareness, conversions, retargeting"},
                        "rationale":    {"type": "string"},
                        "min_threshold_met": {
                            "type": "boolean",
                            "description": "true if amount meets platform learning-phase minimum.",
                        },
                    },
                    "required": ["platform", "amount_usd", "percentage", "rationale", "min_threshold_met"],
                },
            },
            "total_budget":      {"type": "number"},
            "break_even_roas":   {"type": ["number", "null"]},
            "marginal_roas_note": {
                "type": "string",
                "description": "Where the next $1 should go and why.",
            },
        },
        "required": ["narrative", "allocation", "total_budget", "marginal_roas_note"],
    },
}

# ── Plan ─────────────────────────────────────────────────────────────────────

PLAN_TOOL: Dict[str, Any] = {
    "name": "report_plan",
    "description": (
        "Report a structured campaign launch plan with campaign structure, "
        "targeting, timeline, and success criteria."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "narrative": {
                "type": "string",
                "description": "Full plan in the user's language.",
            },
            "campaigns": {
                "type": "array",
                "description": "One entry per campaign (or campaign type).",
                "items": {
                    "type": "object",
                    "properties": {
                        "name":         {"type": "string"},
                        "type":         {"type": "string", "description": "e.g. Search, PMax, Advantage+, TopView"},
                        "objective":    {"type": "string"},
                        "budget_usd":   {"type": "number"},
                        "targeting":    {"type": "string", "description": "Audience / keywords summary"},
                        "bid_strategy": {"type": "string"},
                        "ad_formats":   {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["name", "type", "objective", "budget_usd", "targeting", "bid_strategy"],
                },
            },
            "launch_timeline": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "week":   {"type": "integer"},
                        "action": {"type": "string"},
                        "owner":  {"type": "string", "description": "Role responsible (e.g. media buyer, creative team)"},
                    },
                    "required": ["week", "action"],
                },
            },
            "success_criteria": {
                "type": "object",
                "properties": {
                    "target_cpa":      {"type": ["number", "null"]},
                    "target_roas":     {"type": ["number", "null"]},
                    "review_at_days":  {"type": "integer"},
                    "kpis":            {"type": "array", "items": {"type": "string"}},
                },
                "required": ["review_at_days", "kpis"],
            },
        },
        "required": ["narrative", "campaigns", "launch_timeline", "success_criteria"],
    },
}

# ── Retargeting ───────────────────────────────────────────────────────────────

RETARGETING_TOOL: Dict[str, Any] = {
    "name": "report_retargeting",
    "description": (
        "Report a remarketing funnel strategy with audience segments, "
        "messages per funnel stage, and budget split."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "narrative": {
                "type": "string",
                "description": "Full strategy in the user's language.",
            },
            "segments": {
                "type": "array",
                "description": "One entry per audience segment.",
                "items": {
                    "type": "object",
                    "properties": {
                        "name":             {"type": "string"},
                        "funnel_stage":     {"type": "string", "enum": ["TOFU", "MOFU", "BOFU"]},
                        "signal":           {"type": "string", "description": "What behaviour defines this audience"},
                        "window_days":      {"type": "integer", "description": "Lookback window in days"},
                        "message":          {"type": "string", "description": "Core message / angle for this segment"},
                        "cta":              {"type": "string"},
                        "exclusions":       {"type": "string", "description": "Who to exclude from this segment"},
                        "est_audience_size":{"type": "string", "description": "Rough size estimate (e.g. small/medium/large)"},
                    },
                    "required": ["name", "funnel_stage", "signal", "message", "cta"],
                },
            },
            "pixel_events": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Pixel / tracking events needed for this strategy.",
            },
            "budget_split": {
                "type": "object",
                "properties": {
                    "tofu_pct":  {"type": "number"},
                    "mofu_pct":  {"type": "number"},
                    "bofu_pct":  {"type": "number"},
                },
                "required": ["tofu_pct", "mofu_pct", "bofu_pct"],
            },
        },
        "required": ["narrative", "segments", "pixel_events", "budget_split"],
    },
}

# ── A/B Test ──────────────────────────────────────────────────────────────────

AB_TEST_TOOL: Dict[str, Any] = {
    "name": "report_ab_test",
    "description": (
        "Report a statistically sound A/B test design: one variable, "
        "correct sample size, duration, and native platform tool to use."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "narrative": {
                "type": "string",
                "description": "Full test design in user's language.",
            },
            "hypothesis": {
                "type": "string",
                "description": "If we change X, we expect Y to improve by Z% because...",
            },
            "variable_tested": {"type": "string"},
            "variants": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "label":       {"type": "string", "description": "control or variant_A / variant_B"},
                        "description": {"type": "string"},
                        "change":      {"type": "string", "description": "What is different vs. control (empty for control)"},
                    },
                    "required": ["label", "description"],
                },
            },
            "sample_size_per_variant": {"type": "integer"},
            "duration_days":           {"type": "integer"},
            "minimum_detectable_effect": {
                "type": "string",
                "description": "e.g. 10% lift in CVR",
            },
            "success_metric":  {"type": "string"},
            "native_tool":     {"type": "string", "description": "e.g. Ad Variations, Drafts & Experiments, Split Test"},
            "confidence_level":{"type": "number", "description": "Statistical confidence level, e.g. 0.95"},
        },
        "required": [
            "narrative", "hypothesis", "variable_tested", "variants",
            "sample_size_per_variant", "duration_days", "success_metric", "native_tool",
        ],
    },
}

# ── Research ──────────────────────────────────────────────────────────────────

RESEARCH_TOOL: Dict[str, Any] = {
    "name": "report_research",
    "description": (
        "Report actionable research artefacts: keyword clusters, audience segments, "
        "or creative insights depending on the platform."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "narrative": {
                "type": "string",
                "description": "Full research summary in user's language.",
            },
            "keywords": {
                "type": "array",
                "description": "Keyword universe (Google) or search-style terms.",
                "items": {
                    "type": "object",
                    "properties": {
                        "keyword":    {"type": "string"},
                        "match_type": {"type": "string", "enum": ["broad", "phrase", "exact"]},
                        "intent":     {"type": "string", "enum": ["informational", "commercial", "transactional", "navigational"]},
                        "cluster":    {"type": "string", "description": "Thematic group"},
                        "priority":   {"type": "string", "enum": ["high", "medium", "low"]},
                    },
                    "required": ["keyword", "match_type", "intent", "priority"],
                },
            },
            "negative_keywords": {
                "type": "array",
                "items": {"type": "string"},
            },
            "audience_segments": {
                "type": "array",
                "description": "Audience taxonomy (Meta / TikTok).",
                "items": {
                    "type": "object",
                    "properties": {
                        "name":        {"type": "string"},
                        "type":        {"type": "string", "description": "e.g. interest, custom_audience, lookalike"},
                        "description": {"type": "string"},
                        "priority":    {"type": "string", "enum": ["high", "medium", "low"]},
                    },
                    "required": ["name", "type", "priority"],
                },
            },
            "creative_insights": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Hook patterns, formats, or sound trends (TikTok).",
            },
            "competitors_found": {
                "type": "array",
                "items": {"type": "string"},
            },
        },
        "required": ["narrative", "keywords", "negative_keywords", "audience_segments"],
    },
}

# ── Landing ───────────────────────────────────────────────────────────────────

LANDING_TOOL: Dict[str, Any] = {
    "name": "report_landing_audit",
    "description": (
        "Report a landing page CRO audit: prioritised fixlist and A/B test shortlist."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "narrative": {
                "type": "string",
                "description": "Full audit summary in user's language.",
            },
            "fixlist": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "priority": {"type": "string", "enum": ["P0", "P1", "P2"]},
                        "layer":    {"type": "string", "enum": ["speed", "above_fold", "mobile", "form", "trust", "copy"]},
                        "issue":    {"type": "string"},
                        "fix":      {"type": "string"},
                        "expected_lift": {"type": "string", "description": "e.g. +5-10% CVR"},
                    },
                    "required": ["priority", "layer", "issue", "fix"],
                },
            },
            "ab_test_shortlist": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "element":          {"type": "string"},
                        "hypothesis":       {"type": "string"},
                        "sample_size_est":  {"type": ["integer", "null"]},
                    },
                    "required": ["element", "hypothesis"],
                },
            },
            "overall_score": {
                "type": "integer",
                "description": "CRO health score 0-100.",
            },
            "p0_count": {"type": "integer"},
            "p1_count": {"type": "integer"},
            "p2_count": {"type": "integer"},
        },
        "required": ["narrative", "fixlist", "ab_test_shortlist", "overall_score"],
    },
}

# ── Forecast ──────────────────────────────────────────────────────────────────

FORECAST_TOOL: Dict[str, Any] = {
    "name": "report_forecast",
    "description": (
        "Report a media plan with three scenarios (conservative/base/optimistic), "
        "break-even metrics, and risk factors."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "narrative": {
                "type": "string",
                "description": "Full forecast in user's language.",
            },
            "assumptions": {
                "type": "object",
                "description": "Key inputs used for the model.",
                "properties": {
                    "cpm":        {"type": "number"},
                    "ctr":        {"type": "number"},
                    "cvr":        {"type": "number"},
                    "avg_order":  {"type": ["number", "null"]},
                },
            },
            "scenarios": {
                "type": "object",
                "properties": {
                    "conservative": {"$ref": "#/$defs/scenario"},
                    "base":         {"$ref": "#/$defs/scenario"},
                    "optimistic":   {"$ref": "#/$defs/scenario"},
                },
                "required": ["conservative", "base", "optimistic"],
                "$defs": {
                    "scenario": {
                        "type": "object",
                        "properties": {
                            "impressions":   {"type": "integer"},
                            "clicks":        {"type": "integer"},
                            "conversions":   {"type": "integer"},
                            "spend_usd":     {"type": "number"},
                            "cpa":           {"type": "number"},
                            "roas":          {"type": ["number", "null"]},
                        },
                        "required": ["impressions", "clicks", "conversions", "spend_usd", "cpa"],
                    },
                },
            },
            "break_even_cpa":  {"type": ["number", "null"]},
            "break_even_roas": {"type": ["number", "null"]},
            "biggest_cpa_lever": {
                "type": "string",
                "description": "Which funnel variable (CPM/CTR/CVR) has the biggest CPA impact.",
            },
            "learning_phase_days": {"type": "integer"},
            "risk_factors": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "risk":       {"type": "string"},
                        "mitigation": {"type": "string"},
                    },
                    "required": ["risk", "mitigation"],
                },
            },
        },
        "required": ["narrative", "scenarios", "break_even_cpa", "biggest_cpa_lever", "risk_factors"],
    },
}

# ── Registry ──────────────────────────────────────────────────────────────────

STRUCTURED_TOOLS: Dict[str, Dict[str, Any]] = {
    "analyze":    ANALYZE_TOOL,
    "copy":       COPY_TOOL,
    "budget":     BUDGET_TOOL,
    "plan":       PLAN_TOOL,
    "retargeting":RETARGETING_TOOL,
    "ab_test":    AB_TEST_TOOL,
    "research":   RESEARCH_TOOL,
    "landing":    LANDING_TOOL,
    "forecast":   FORECAST_TOOL,
}


def _verify_copy_char_counts(structured: Dict[str, Any]) -> Dict[str, Any]:
    """
    Post-processing for copy mode: verify that LLM-reported char_counts match
    actual text lengths and that `compliant` is accurate.

    Corrects char_counts in-place and recomputes `compliant` against platform_limits.
    Returns the corrected dict.
    """
    import logging as _logging
    _log = _logging.getLogger(__name__)

    limits  = structured.get("platform_limits", {})
    variants = structured.get("variants", [])
    if not variants:
        return structured

    headline_limit    = limits.get("headline")
    description_limit = limits.get("description")
    corrected         = False

    for v in variants:
        headline    = v.get("headline", "")
        description = v.get("description", "")
        actual_h    = len(headline)
        actual_d    = len(description)

        reported_h = v.get("char_counts", {}).get("headline")
        reported_d = v.get("char_counts", {}).get("description")

        if reported_h != actual_h or reported_d != actual_d:
            _log.warning(
                "copy mode: char_count mismatch — "
                "headline reported=%s actual=%s, description reported=%s actual=%s. Correcting.",
                reported_h, actual_h, reported_d, actual_d,
            )
            v.setdefault("char_counts", {})
            v["char_counts"]["headline"]    = actual_h
            v["char_counts"]["description"] = actual_d
            corrected = True

        # Recompute compliance with actual lengths
        if headline_limit and description_limit:
            real_compliant = actual_h <= headline_limit and actual_d <= description_limit
            if v.get("compliant") != real_compliant:
                _log.warning(
                    "copy mode: compliance flag corrected from %s → %s "
                    "(headline %d/%d, description %d/%d)",
                    v.get("compliant"), real_compliant,
                    actual_h, headline_limit, actual_d, description_limit,
                )
                v["compliant"] = real_compliant
                corrected = True

    if corrected:
        structured["_char_counts_corrected"] = True

    return structured


def split_structured_result(raw: Optional[Dict[str, Any]]) -> tuple:
    """
    Split call_tool() output into (narrative: str, structured: dict).
    For copy mode, also verifies and corrects char_counts and compliance flags.
    Returns ("", {}) if raw is None or empty.
    """
    if not raw or not isinstance(raw, dict):
        return "", {}
    data       = dict(raw)  # copy so we don't mutate the caller's dict
    narrative  = str(data.pop("narrative", "")).strip()
    structured = data
    # Auto-correct copy mode char counts if platform_limits and variants present
    if "variants" in structured and "platform_limits" in structured:
        structured = _verify_copy_char_counts(structured)
    return narrative, structured
