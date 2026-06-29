"""
Structured output tool schemas for CreativeAgent modes.
"""
from typing import Any, Dict, Optional

# ── Copy ──────────────────────────────────────────────────────────────────────

CREATIVE_COPY_TOOL: Dict[str, Any] = {
    "name": "report_creative_copy",
    "description": (
        "Report ad copy variants with exact character counts and platform compliance. "
        "Verify every variant against platform limits before setting compliant=true. "
        "narrative must explain the creative rationale."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "narrative": {
                "type": "string",
                "description": "Creative rationale and summary in user's language.",
            },
            "platform": {"type": "string"},
            "variants": {
                "type": "array",
                "description": "3-5 copy variants with different hook strategies.",
                "items": {
                    "type": "object",
                    "properties": {
                        "hook_type":       {"type": "string", "description": "e.g. urgency, social_proof, result, pain"},
                        "headline":        {"type": "string"},
                        "primary_text":    {"type": "string"},
                        "cta":             {"type": "string"},
                        "char_counts": {
                            "type": "object",
                            "properties": {
                                "headline":     {"type": "integer"},
                                "primary_text": {"type": "integer"},
                            },
                            "required": ["headline", "primary_text"],
                        },
                        "compliant": {
                            "type": "boolean",
                            "description": "true only if all fields are within platform limits.",
                        },
                    },
                    "required": ["hook_type", "headline", "primary_text", "cta", "char_counts", "compliant"],
                },
            },
            "platform_limits": {
                "type": "object",
                "properties": {
                    "headline":     {"type": "integer"},
                    "primary_text": {"type": "integer"},
                },
            },
            "recommended_test_pair": {
                "type": "object",
                "description": "The two variants to A/B test first.",
                "properties": {
                    "variant_a_index": {"type": "integer"},
                    "variant_b_index": {"type": "integer"},
                    "variable_tested": {"type": "string"},
                    "win_metric":      {"type": "string"},
                },
                "required": ["variant_a_index", "variant_b_index", "variable_tested", "win_metric"],
            },
        },
        "required": ["narrative", "platform", "variants", "platform_limits"],
    },
}

# ── Script ────────────────────────────────────────────────────────────────────

CREATIVE_SCRIPT_TOOL: Dict[str, Any] = {
    "name": "report_creative_script",
    "description": (
        "Report video scripts with timecoded structure, delivery notes, "
        "and hook rate predictions."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "narrative": {
                "type": "string",
                "description": "Creative direction summary in user's language.",
            },
            "scripts": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "hook_type":   {"type": "string"},
                        "hook_text":   {"type": "string", "description": "Exact words / action for first 3 seconds"},
                        "problem":     {"type": "string", "description": "3-8s content"},
                        "solution":    {"type": "string", "description": "8-end content"},
                        "proof":       {"type": "string", "description": "Social proof or result statement"},
                        "cta":         {"type": "string"},
                        "delivery_notes": {"type": "string"},
                        "hook_rate_prediction": {
                            "type": "string",
                            "enum": ["excellent", "good", "average", "risky"],
                        },
                    },
                    "required": ["hook_type", "hook_text", "problem", "solution", "cta", "hook_rate_prediction"],
                },
            },
            "recommended_first_test": {"type": "integer", "description": "Index (0-based) of script to test first"},
            "win_metric":             {"type": "string", "description": "e.g. Hook Rate >25%, CVR"},
        },
        "required": ["narrative", "scripts", "recommended_first_test", "win_metric"],
    },
}

# ── UGC Brief ─────────────────────────────────────────────────────────────────

CREATIVE_UGC_TOOL: Dict[str, Any] = {
    "name": "report_ugc_brief",
    "description": (
        "Report UGC creator briefs with talking points, shot list, and dos/don'ts."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "narrative": {
                "type": "string",
                "description": "Strategy rationale in user's language.",
            },
            "briefs": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "hook_approach":   {"type": "string"},
                        "hook_text":       {"type": "string", "description": "Exact opener words or action"},
                        "talking_points":  {"type": "array", "items": {"type": "string"}},
                        "shot_list": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "scene":    {"type": "string"},
                                    "duration": {"type": "string"},
                                },
                                "required": ["scene"],
                            },
                        },
                        "dos":   {"type": "array", "items": {"type": "string"}},
                        "donts": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["hook_approach", "hook_text", "talking_points", "shot_list", "dos", "donts"],
                },
            },
            "priority_brief_index": {"type": "integer", "description": "Index (0-based) of brief to shoot first"},
            "performance_signals":  {
                "type": "array",
                "items": {"type": "string"},
                "description": "Data points to collect from creator to predict performance.",
            },
        },
        "required": ["narrative", "briefs", "priority_brief_index", "performance_signals"],
    },
}

# ── Registry ──────────────────────────────────────────────────────────────────

CREATIVE_STRUCTURED_TOOLS: Dict[str, Dict[str, Any]] = {
    "copy":      CREATIVE_COPY_TOOL,
    "script":    CREATIVE_SCRIPT_TOOL,
    "ugc_brief": CREATIVE_UGC_TOOL,
}


def split_creative_result(raw: Optional[Dict[str, Any]]) -> tuple:
    if not raw or not isinstance(raw, dict):
        return "", {}
    data       = dict(raw)
    narrative  = str(data.pop("narrative", "")).strip()
    structured = data
    return narrative, structured
