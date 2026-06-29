"""
Structured output tool schemas for StrategyAgent modes.

Used with ClaudeHTTPAnalyzer.call_tool() so Claude fills both the human-readable
narrative AND a typed JSON object in a single API call.
"""
from typing import Any, Dict, Optional

# ── Channel Mix ───────────────────────────────────────────────────────────────

CHANNEL_MIX_TOOL: Dict[str, Any] = {
    "name": "report_channel_mix",
    "description": (
        "Report a structured channel allocation and media mix strategy. "
        "allocation entries must represent a complete, prioritised channel plan. "
        "narrative must be the full strategy in the user's language."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "narrative": {
                "type": "string",
                "description": "Full channel strategy in the user's language.",
            },
            "allocation": {
                "type": "array",
                "description": "One entry per recommended channel.",
                "items": {
                    "type": "object",
                    "properties": {
                        "channel":          {"type": "string", "description": "e.g. Google Search, Meta, TikTok, SEO, Email"},
                        "funnel_stage":     {"type": "string", "enum": ["TOFU", "MOFU", "BOFU", "Retention", "Full-funnel"]},
                        "budget_pct":       {"type": "number", "description": "Percentage of total budget (0–100)"},
                        "primary_kpi":      {"type": "string", "description": "e.g. CPL, ROAS, Reach, LTV"},
                        "kpi_target":       {"type": "string", "description": "Specific target value or range"},
                        "min_budget_usd":   {"type": ["number", "null"], "description": "Minimum monthly spend to exit learning phase"},
                        "priority":         {"type": "string", "enum": ["launch_first", "phase_2", "phase_3", "optional"]},
                        "rationale":        {"type": "string", "description": "Why this channel at this allocation"},
                    },
                    "required": ["channel", "funnel_stage", "budget_pct", "primary_kpi", "rationale", "priority"],
                },
            },
            "sequencing": {
                "type": "array",
                "description": "Activation order with dependencies.",
                "items": {
                    "type": "object",
                    "properties": {
                        "phase":      {"type": "integer", "description": "Phase number (1, 2, 3...)"},
                        "channels":   {"type": "array", "items": {"type": "string"}},
                        "rationale":  {"type": "string"},
                        "depends_on": {"type": "array", "items": {"type": "string"}, "description": "Channels that must be active first"},
                    },
                    "required": ["phase", "channels", "rationale"],
                },
            },
            "marginal_roas_note": {
                "type": "string",
                "description": "Where the next $1 of incremental budget should go and why.",
            },
            "attribution_model": {
                "type": "string",
                "description": "Recommended attribution model and rationale.",
            },
        },
        "required": ["narrative", "allocation", "sequencing", "marginal_roas_note"],
    },
}

# ── KPI Framework ─────────────────────────────────────────────────────────────

KPI_TOOL: Dict[str, Any] = {
    "name": "report_kpi_framework",
    "description": (
        "Report a structured KPI framework with north star metric, OKRs, "
        "leading/lagging indicators, and alert thresholds. "
        "narrative must be the full framework in the user's language."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "narrative": {
                "type": "string",
                "description": "Full KPI framework in the user's language.",
            },
            "north_star": {
                "type": "object",
                "properties": {
                    "metric":   {"type": "string"},
                    "baseline": {"type": "string", "description": "Current value or 'unknown'"},
                    "target":   {"type": "string"},
                    "rationale":{"type": "string"},
                },
                "required": ["metric", "target", "rationale"],
            },
            "okrs": {
                "type": "array",
                "description": "OKR structure for the specified timeline.",
                "items": {
                    "type": "object",
                    "properties": {
                        "objective": {"type": "string"},
                        "key_results": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "kr":       {"type": "string"},
                                    "target":   {"type": "string"},
                                    "source":   {"type": "string", "description": "Data source / tool"},
                                },
                                "required": ["kr", "target"],
                            },
                        },
                    },
                    "required": ["objective", "key_results"],
                },
            },
            "leading_indicators": {
                "type": "array",
                "description": "Weekly metrics that predict the outcome.",
                "items": {
                    "type": "object",
                    "properties": {
                        "metric":   {"type": "string"},
                        "target":   {"type": "string"},
                        "source":   {"type": "string"},
                        "cadence":  {"type": "string", "enum": ["daily", "weekly"]},
                    },
                    "required": ["metric", "target", "cadence"],
                },
            },
            "lagging_indicators": {
                "type": "array",
                "description": "Monthly business result metrics.",
                "items": {
                    "type": "object",
                    "properties": {
                        "metric":  {"type": "string"},
                        "target":  {"type": "string"},
                        "source":  {"type": "string"},
                    },
                    "required": ["metric", "target"],
                },
            },
            "alert_thresholds": {
                "type": "array",
                "description": "P0/P1/P2 alert definitions.",
                "items": {
                    "type": "object",
                    "properties": {
                        "severity": {"type": "string", "enum": ["P0", "P1", "P2"]},
                        "metric":   {"type": "string"},
                        "trigger":  {"type": "string", "description": "Condition that fires the alert"},
                        "action":   {"type": "string"},
                    },
                    "required": ["severity", "metric", "trigger", "action"],
                },
            },
        },
        "required": ["narrative", "north_star", "okrs", "leading_indicators", "lagging_indicators", "alert_thresholds"],
    },
}

# ── Registry ──────────────────────────────────────────────────────────────────

STRATEGY_STRUCTURED_TOOLS: Dict[str, Dict[str, Any]] = {
    "channel_mix": CHANNEL_MIX_TOOL,
    "kpi":         KPI_TOOL,
}


def split_strategy_result(raw: Optional[Dict[str, Any]]) -> tuple:
    """Split call_tool() output into (narrative: str, structured: dict)."""
    if not raw or not isinstance(raw, dict):
        return "", {}
    data       = dict(raw)
    narrative  = str(data.pop("narrative", "")).strip()
    structured = data
    return narrative, structured
