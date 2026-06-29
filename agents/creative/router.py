"""
Creative Intent Router — classifies a free-form user message into {mode}.
"""
from __future__ import annotations

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

_ROUTER_MODEL = "claude-sonnet-4-6"

_MODES = ["concept", "copy", "script", "ugc_brief"]

_SYSTEM = (
    "You are an intent classifier for a creative advertising AI agent. "
    "Output ONLY a valid JSON object — no explanation, no markdown."
)

_PROMPT_TEMPLATE = """\
Classify this message from a marketing or creative professional.

Message: {message}

Return a JSON object:
- mode: one of {modes} — or null if generic chat
- confidence: "high" | "medium" | "low"
- extracted_context: dict with useful fields (product, platform, tone, funnel_stage, duration, usp) — empty {{}} if nothing

Mode guide:
  concept   — creative concept development, campaign idea, 3 variants, visual direction
  copy      — ad copy writing: headlines, descriptions, CTAs for a specific platform
  script    — video script: hook-to-CTA structure for TikTok/Reels/YouTube
  ugc_brief — UGC creator brief: talking points, shot list, dos/don'ts

Examples:
  "Write Meta ad copy for my SaaS" -> {{"mode":"copy","confidence":"high","extracted_context":{{"platform":"meta"}}}}
  "Create a TikTok video script" -> {{"mode":"script","confidence":"high","extracted_context":{{"platform":"tiktok"}}}}
  "Brief for UGC creators on Instagram" -> {{"mode":"ugc_brief","confidence":"high","extracted_context":{{"platform":"instagram"}}}}
  "Develop a creative concept for our campaign" -> {{"mode":"concept","confidence":"high","extracted_context":{{}}}}
  "What is a good hook?" -> {{"mode":null,"confidence":"low","extracted_context":{{}}}}

Respond with ONLY the JSON object:""".format(
    message="{message}",
    modes=_MODES,
)

_TOOL = {
    "name": "classify_creative_intent",
    "description": "Classify the user's creative request into a mode.",
    "input_schema": {
        "type": "object",
        "properties": {
            "mode": {
                "type": ["string", "null"],
                "enum": _MODES + [None],
            },
            "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
            "extracted_context": {"type": "object", "additionalProperties": True},
        },
        "required": ["mode", "confidence", "extracted_context"],
    },
}

_FALLBACK: Dict[str, Any] = {"mode": None, "confidence": "low", "extracted_context": {}}


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


def route_creative_intent(analyzer: Any, message: str) -> Dict[str, Any]:
    from agents.base_router import route
    return route(
        analyzer, message,
        prompt_template=_PROMPT_TEMPLATE,
        tool=_TOOL,
        system_prompt=_SYSTEM,
        validate=_validate,
        fallback=_FALLBACK,
        model=_ROUTER_MODEL,
        name="creative_router",
    )
