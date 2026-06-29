"""
Intent Router — classifies a free-form user message into {platform, mode}.

Prefers call_tool() on ClaudeHTTPAnalyzer for guaranteed structured output.
Falls back to JSON-prompt parsing if the analyzer doesn't support call_tool.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

_ROUTER_MODEL = "claude-sonnet-4-6"

_PLATFORMS = ["google", "meta", "tiktok"]
_MODES = [
    "plan", "analyze", "audit", "copy",
    "retargeting", "ab_test", "budget",
    "research", "landing", "forecast",
]

_SYSTEM = (
    "You are an intent classifier for an advertising AI agent. "
    "Output ONLY a valid JSON object — no explanation, no markdown."
)

_PROMPT_TEMPLATE = """\
Classify this message from an advertising professional.

Message: {message}

Return a JSON object with these fields:
- platform: one of {platforms} — or null if unclear
- mode: one of {modes} — or null if unclear
- confidence: "high" if both platform and mode are clear, "medium" if one is inferred, "low" if generic
- extracted_context: dict with any useful fields from the message (product, budget, goal, audience, url, etc.) — empty {{}} if nothing found

Mode guide:
  plan        — launch a new campaign
  analyze     — diagnose existing campaign metrics (CTR, ROAS, CPA…)
  audit       — full account audit with Canon runbook
  copy        — write ad copy / scripts
  retargeting — remarketing / lookalike funnel
  ab_test     — A/B test design
  budget      — cross-platform budget allocation
  research    — keyword / audience / creative research
  landing     — landing page CRO audit
  forecast    — media plan / performance projections

Examples:
  "How to improve ROAS in Google Ads?" -> {{"platform":"google","mode":"analyze","confidence":"high","extracted_context":{{}}}}
  "Write ad copy for Meta" -> {{"platform":"meta","mode":"copy","confidence":"high","extracted_context":{{}}}}
  "How much budget for TikTok?" -> {{"platform":"tiktok","mode":"budget","confidence":"medium","extracted_context":{{}}}}
  "Hello, how are you?" -> {{"platform":null,"mode":null,"confidence":"low","extracted_context":{{}}}}

Respond with ONLY the JSON object:""".format(
    message="{message}",
    platforms=_PLATFORMS,
    modes=_MODES,
)

_FALLBACK: Dict[str, Any] = {
    "platform": None,
    "mode": None,
    "confidence": "low",
    "extracted_context": {},
}

_TOOL = {
    "name": "classify_intent",
    "description": (
        "Classify the user's advertising question into a platform and mode. "
        "Set confidence='low' if the message is a generic chat question "
        "not tied to a specific ad platform or task."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "platform": {
                "type": ["string", "null"],
                "enum": _PLATFORMS + [None],
                "description": "Ad platform the user is asking about, or null if unclear.",
            },
            "mode": {
                "type": ["string", "null"],
                "enum": _MODES + [None],
                "description": "Task type the user wants to perform, or null if unclear.",
            },
            "confidence": {
                "type": "string",
                "enum": ["high", "medium", "low"],
                "description": (
                    "high — platform and mode are clear; "
                    "medium — one is inferred; "
                    "low — generic question, route to plain chat."
                ),
            },
            "extracted_context": {
                "type": "object",
                "description": "Key fields extracted from the message (product, budget, goal, audience, url). Empty {} if nothing useful.",
                "additionalProperties": True,
            },
        },
        "required": ["platform", "mode", "confidence", "extracted_context"],
    },
}


def _validate(result: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and sanitise a raw classification dict."""
    platform   = result.get("platform")
    mode       = result.get("mode")
    confidence = result.get("confidence", "low")
    extracted  = result.get("extracted_context", {})

    if platform not in _PLATFORMS:
        platform = None
    if mode not in _MODES:
        mode = None
    if confidence not in ("high", "medium", "low"):
        confidence = "medium" if (platform or mode) else "low"

    return {
        "platform":          platform,
        "mode":              mode,
        "confidence":        confidence,
        "extracted_context": extracted if isinstance(extracted, dict) else {},
    }


def route_intent(analyzer: Any, message: str) -> Dict[str, Any]:
    """
    Classify a user message into {platform, mode, confidence, extracted_context}.

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
        name="ads_router",
    )
