"""
Structured output tool schemas for SEOAgent modes.

Used with ClaudeHTTPAnalyzer.call_tool() so Claude fills both the human-readable
narrative AND a typed JSON object in a single API call.

Result shape for every tool:
    {
        "narrative": str,   -> goes into result["result"]
        ...mode fields...   -> goes into result["structured"]
    }
"""
from typing import Any, Dict, Optional

# ── Audit ─────────────────────────────────────────────────────────────────────

SEO_AUDIT_TOOL: Dict[str, Any] = {
    "name": "report_seo_audit",
    "description": (
        "Report a structured Canon SEO audit: fixlist per rule, health score, and halt signal. "
        "P0 rules must always appear first. If any P0 fails, set halt=true."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "narrative": {
                "type": "string",
                "description": "Full audit summary in the user's language.",
            },
            "fixlist": {
                "type": "array",
                "description": "One entry per rule checked. P0 first, then P1, then P2.",
                "items": {
                    "type": "object",
                    "properties": {
                        "rule_id":  {"type": "string", "description": "e.g. SEO-P0-01"},
                        "area":     {"type": "string", "description": "e.g. indexability, Core Web Vitals, E-E-A-T"},
                        "status":   {"type": "string", "enum": ["pass", "fail", "warning", "cannot_assess"]},
                        "finding":  {"type": "string", "description": "What was found, with specific data point"},
                        "fix":      {"type": "string", "description": "Exact fix with implementation detail"},
                        "priority": {"type": "string", "enum": ["P0", "P1", "P2"]},
                        "verify":   {"type": "string", "description": "How to verify the fix worked"},
                    },
                    "required": ["rule_id", "area", "status", "finding", "fix", "priority"],
                },
            },
            "p0_count":    {"type": "integer"},
            "p1_count":    {"type": "integer"},
            "p2_count":    {"type": "integer"},
            "health_score": {
                "type": "integer",
                "description": "SEO health score 0-100 (weighted by severity).",
            },
            "halt": {
                "type": "boolean",
                "description": "true if any P0 gate failed — halt all optimisation until resolved.",
            },
        },
        "required": ["narrative", "fixlist", "p0_count", "p1_count", "p2_count", "health_score", "halt"],
    },
}

# ── Technical ─────────────────────────────────────────────────────────────────

SEO_TECHNICAL_TOOL: Dict[str, Any] = {
    "name": "report_technical_seo",
    "description": (
        "Report a technical SEO audit across 9 categories with a weighted health score. "
        "Assign severity to every finding. Include a specific fix and verification method."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "narrative": {
                "type": "string",
                "description": "Full technical audit in user's language.",
            },
            "categories": {
                "type": "array",
                "description": "One entry per audit category (9 total).",
                "items": {
                    "type": "object",
                    "properties": {
                        "name":  {"type": "string", "description": "e.g. Core Web Vitals, Crawlability, Structured Data"},
                        "score": {"type": "integer", "description": "Category score 0-100"},
                        "findings": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "severity": {"type": "string", "enum": ["Critical", "High", "Medium", "Low"]},
                                    "issue":    {"type": "string"},
                                    "fix":      {"type": "string"},
                                    "verify":   {"type": "string"},
                                },
                                "required": ["severity", "issue", "fix"],
                            },
                        },
                    },
                    "required": ["name", "score", "findings"],
                },
            },
            "health_score": {"type": "integer", "description": "Overall SEO health score 0-100."},
            "critical_count": {"type": "integer"},
            "high_count":     {"type": "integer"},
        },
        "required": ["narrative", "categories", "health_score", "critical_count"],
    },
}

# ── Content ───────────────────────────────────────────────────────────────────

SEO_CONTENT_TOOL: Dict[str, Any] = {
    "name": "report_content_seo",
    "description": (
        "Report an E-E-A-T content quality assessment: issues, actions, and overall quality tier."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "narrative": {
                "type": "string",
                "description": "Full content assessment in user's language.",
            },
            "issues": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "type":            {"type": "string", "description": "e.g. thin_content, keyword_cannibalization, missing_author"},
                        "severity":        {"type": "string", "enum": ["Critical", "High", "Medium", "Low"]},
                        "affected_pages":  {"type": "string", "description": "URL or page pattern"},
                        "issue":           {"type": "string"},
                        "fix":             {"type": "string"},
                        "expected_impact": {"type": "string"},
                    },
                    "required": ["type", "severity", "issue", "fix"],
                },
            },
            "eeat_scores": {
                "type": "object",
                "description": "Score 0-10 per E-E-A-T dimension.",
                "properties": {
                    "experience":    {"type": "integer"},
                    "expertise":     {"type": "integer"},
                    "authoritativeness": {"type": "integer"},
                    "trustworthiness":   {"type": "integer"},
                },
            },
            "quality_tier": {
                "type": "string",
                "enum": ["Fails QRG", "Needs Work", "Acceptable", "High Quality", "Exceptional"],
            },
            "quick_wins": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Actions that can be done in <1 week for immediate E-E-A-T lift.",
            },
        },
        "required": ["narrative", "issues", "eeat_scores", "quality_tier", "quick_wins"],
    },
}

# ── Backlinks ──────────────────────────────────────────────────────────────────

SEO_BACKLINKS_TOOL: Dict[str, Any] = {
    "name": "report_backlinks_seo",
    "description": (
        "Report a backlink audit: toxic links to disavow, link gaps, and acquisition strategy."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "narrative": {
                "type": "string",
                "description": "Full backlink analysis in user's language.",
            },
            "toxic_links": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "domain":  {"type": "string"},
                        "reason":  {"type": "string", "description": "e.g. PBN, link_farm, over_optimized_anchor"},
                        "action":  {"type": "string", "enum": ["disavow", "remove_request", "monitor"]},
                    },
                    "required": ["domain", "reason", "action"],
                },
            },
            "anchor_health": {
                "type": "object",
                "properties": {
                    "branded_pct":    {"type": "number", "description": "% branded/URL anchors (target 40-60%)"},
                    "generic_pct":    {"type": "number", "description": "% generic anchors (target 10-20%)"},
                    "exact_match_pct":{"type": "number", "description": "% exact-match (keep <5%)"},
                    "status":         {"type": "string", "enum": ["healthy", "over_optimized", "needs_diversification"]},
                },
                "required": ["branded_pct", "exact_match_pct", "status"],
            },
            "acquisition_tactics": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "tactic":         {"type": "string"},
                        "effort":         {"type": "string", "enum": ["low", "medium", "high"]},
                        "expected_links_per_month": {"type": "integer"},
                        "target_dr_gain": {"type": "string"},
                    },
                    "required": ["tactic", "effort"],
                },
            },
            "disavow_count": {"type": "integer"},
        },
        "required": ["narrative", "toxic_links", "anchor_health", "acquisition_tactics", "disavow_count"],
    },
}

# ── Cluster ────────────────────────────────────────────────────────────────────

SEO_CLUSTER_TOOL: Dict[str, Any] = {
    "name": "report_cluster_seo",
    "description": (
        "Report a topical cluster architecture: one pillar page and 5-12 spoke pages "
        "with internal linking plan and keyword assignments."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "narrative": {
                "type": "string",
                "description": "Full cluster strategy in user's language.",
            },
            "pillar": {
                "type": "object",
                "properties": {
                    "title":         {"type": "string"},
                    "target_keyword":{"type": "string"},
                    "search_volume": {"type": "string"},
                    "intent":        {"type": "string", "enum": ["informational", "commercial", "transactional"]},
                    "word_count_target": {"type": "integer"},
                },
                "required": ["title", "target_keyword", "intent"],
            },
            "spokes": {
                "type": "array",
                "description": "5-12 spoke pages supporting the pillar.",
                "items": {
                    "type": "object",
                    "properties": {
                        "title":          {"type": "string"},
                        "target_keyword": {"type": "string"},
                        "search_volume":  {"type": "string"},
                        "intent":         {"type": "string", "enum": ["informational", "commercial", "transactional"]},
                        "links_to_pillar":{"type": "boolean"},
                        "priority":       {"type": "string", "enum": ["high", "medium", "low"]},
                    },
                    "required": ["title", "target_keyword", "intent", "priority"],
                },
            },
            "total_keyword_volume": {"type": "string"},
            "estimated_traffic_lift": {"type": "string"},
            "content_calendar": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "month": {"type": "integer"},
                        "pages": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["month", "pages"],
                },
            },
        },
        "required": ["narrative", "pillar", "spokes", "total_keyword_volume"],
    },
}

# ── Schema ─────────────────────────────────────────────────────────────────────

SEO_SCHEMA_TOOL: Dict[str, Any] = {
    "name": "report_schema_seo",
    "description": (
        "Report a schema markup audit: missing types, implementation errors, "
        "and copy-paste ready JSON-LD for every missing schema."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "narrative": {
                "type": "string",
                "description": "Full schema audit in user's language.",
            },
            "existing_schemas": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "type":   {"type": "string", "description": "e.g. Organization, Product"},
                        "status": {"type": "string", "enum": ["valid", "errors", "deprecated"]},
                        "issues": {"type": "string"},
                    },
                    "required": ["type", "status"],
                },
            },
            "missing_schemas": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "type":              {"type": "string"},
                        "priority":          {"type": "string", "enum": ["P0", "P1", "P2"]},
                        "reason":            {"type": "string", "description": "Why this schema is valuable here"},
                        "ai_overview_boost": {"type": "boolean", "description": "true if this schema increases AI Overview probability"},
                        "json_ld":           {"type": "string", "description": "Copy-paste ready JSON-LD snippet"},
                    },
                    "required": ["type", "priority", "reason", "json_ld"],
                },
            },
            "ai_overview_probability": {
                "type": "string",
                "enum": ["low", "medium", "high"],
                "description": "Current probability of appearing in AI Overviews based on schema coverage.",
            },
        },
        "required": ["narrative", "existing_schemas", "missing_schemas", "ai_overview_probability"],
    },
}

# ── Registry ──────────────────────────────────────────────────────────────────

SEO_STRUCTURED_TOOLS: Dict[str, Dict[str, Any]] = {
    "audit":     SEO_AUDIT_TOOL,
    "technical": SEO_TECHNICAL_TOOL,
    "content":   SEO_CONTENT_TOOL,
    "backlinks": SEO_BACKLINKS_TOOL,
    "cluster":   SEO_CLUSTER_TOOL,
    "schema":    SEO_SCHEMA_TOOL,
}


def split_seo_structured_result(raw: Optional[Dict[str, Any]]) -> tuple:
    """
    Split call_tool() output into (narrative: str, structured: dict).
    Returns ("", {}) if raw is None or empty.
    """
    if not raw or not isinstance(raw, dict):
        return "", {}
    data       = dict(raw)  # copy so we don't mutate the caller's dict
    narrative  = str(data.pop("narrative", "")).strip()
    structured = data
    return narrative, structured
