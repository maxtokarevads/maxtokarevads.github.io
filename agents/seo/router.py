"""
SEO Intent Router — classifies a free-form user message into {mode, site}.

Prefers call_tool() on ClaudeHTTPAnalyzer for guaranteed structured output.
Falls back to JSON-prompt parsing if the analyzer doesn't support call_tool.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

_ROUTER_MODEL = "claude-sonnet-4-6"

_MODES = [
    "seo", "aeo", "technical", "content", "local",
    "schema", "backlinks", "cluster", "sxo", "audit", "drift",
    "article", "brief", "meta", "rewrite",
]

_SYSTEM = (
    "You are an intent classifier for an SEO AI agent. "
    "Output ONLY a valid JSON object — no explanation, no markdown."
)

_PROMPT_TEMPLATE = """\
Classify this message from a marketing or SEO professional.

Message: {message}

Return a JSON object with these fields:
- mode: one of {modes} — or null if unclear / generic chat
- confidence: "high" if mode is clear, "medium" if inferred, "low" if generic
- extracted_context: dict with useful fields from the message (site, keywords, industry, query) — empty {{}} if nothing found

Mode guide:
  seo        — general SEO strategy (default when topic is SEO but mode unclear)
  aeo        — AI/answer engine optimization, GEO, AI Overviews, Perplexity citations
  technical  — Core Web Vitals, crawlability, indexability, INP, rendering
  content    — E-E-A-T, content quality, thin content, author authority
  local      — Google Business Profile, NAP, map pack, local rankings
  schema     — schema.org markup, JSON-LD, structured data
  backlinks  — link building, backlink audit, toxic links, DR
  cluster    — topical clusters, pillar pages, keyword architecture
  sxo        — search experience optimization, SERP intent, user journey
  audit      — full Canon SEO audit (30 rules, P0/P1/P2)
  drift      — SEO performance drop, traffic decline, ranking loss monitoring
  article    — write a complete SEO article (full text, not outline)
  brief      — content brief for a copywriter (structure, keywords, E-E-A-T requirements)
  meta       — write or optimise meta titles and descriptions
  rewrite    — rewrite existing content for better E-E-A-T, keywords, or readability

Examples:
  "Run a technical audit of site.com" -> {{"mode":"technical","confidence":"high","extracted_context":{{"site":"site.com"}}}}
  "How to improve Core Web Vitals?" -> {{"mode":"technical","confidence":"high","extracted_context":{{}}}}
  "Build a topical cluster for CRM" -> {{"mode":"cluster","confidence":"high","extracted_context":{{"query":"CRM"}}}}
  "Why did traffic drop?" -> {{"mode":"drift","confidence":"medium","extracted_context":{{}}}}
  "Write an article about CRM software" -> {{"mode":"article","confidence":"high","extracted_context":{{"keywords":["CRM software"]}}}}
  "Create a content brief for project management" -> {{"mode":"brief","confidence":"high","extracted_context":{{"topic":"project management"}}}}
  "Optimise meta tags for these pages" -> {{"mode":"meta","confidence":"high","extracted_context":{{}}}}
  "Rewrite this blog post for E-E-A-T" -> {{"mode":"rewrite","confidence":"high","extracted_context":{{}}}}
  "Hello, how are you?" -> {{"mode":null,"confidence":"low","extracted_context":{{}}}}

Respond with ONLY the JSON object:""".format(
    message="{message}",
    modes=_MODES,
)

_FALLBACK: Dict[str, Any] = {
    "mode":              None,
    "confidence":        "low",
    "extracted_context": {},
}

_TOOL = {
    "name": "classify_seo_intent",
    "description": (
        "Classify the user's SEO question into a mode. "
        "Set confidence='low' if the message is a generic chat question "
        "not tied to a specific SEO task."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "mode": {
                "type": ["string", "null"],
                "enum": _MODES + [None],
                "description": "SEO task type the user wants to perform, or null if unclear.",
            },
            "confidence": {
                "type": "string",
                "enum": ["high", "medium", "low"],
                "description": (
                    "high — mode is clear; "
                    "medium — mode is inferred; "
                    "low — generic question, route to plain chat."
                ),
            },
            "extracted_context": {
                "type": "object",
                "description": "Key fields from the message (site, keywords, industry, query). Empty {} if nothing useful.",
                "additionalProperties": True,
            },
        },
        "required": ["mode", "confidence", "extracted_context"],
    },
}


def _validate(result: Dict[str, Any]) -> Dict[str, Any]:
    mode       = result.get("mode")
    confidence = result.get("confidence", "low")
    extracted  = result.get("extracted_context", {})

    if mode not in _MODES:
        mode = None
    if confidence not in ("high", "medium", "low"):
        confidence = "medium" if mode else "low"

    return {
        "mode":              mode,
        "confidence":        confidence,
        "extracted_context": extracted if isinstance(extracted, dict) else {},
    }


def route_seo_intent(analyzer: Any, message: str) -> Dict[str, Any]:
    """
    Classify a user message into {mode, confidence, extracted_context}.

    Uses call_tool() when available (guaranteed structured output).
    Falls back to JSON-prompt parsing for analyzers that don't support it.
    Returns low-confidence fallback on any error.
    """
    from agents.base_router import route
    return route(
        analyzer, message,
        prompt_template=_PROMPT_TEMPLATE,
        tool=_TOOL,
        system_prompt=_SYSTEM,
        validate=_validate,
        fallback=_FALLBACK,
        model=_ROUTER_MODEL,
        name="seo_router",
    )
