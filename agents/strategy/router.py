import logging
from typing import Any, Dict

from .skills.prompt import SUPPORTED_MODES

logger = logging.getLogger(__name__)

_ROUTER_MODEL = "claude-sonnet-4-6"

_ROUTER_SYSTEM = (
    "You are an intent classifier for a marketing strategy AI agent. "
    "Output ONLY a valid JSON object — no explanation, no markdown."
)

_ROUTER_PROMPT = """\
Classify this message from a marketing professional.

Message: {message}

Return a JSON object:
- mode: one of ["general","gtm","positioning","channel_mix","kpi","audit"] — or null if generic chat
- confidence: "high" | "medium" | "low"
- extracted_context: dict with useful fields (goal, product, industry, budget, timeline) — empty {{}} if nothing

Mode guide:
  general     — full marketing plan, strategy overview
  gtm         — go-to-market, product launch, new market entry
  positioning — brand positioning, messaging, differentiation, ICP
  channel_mix — channel selection, budget allocation, media mix
  kpi         — KPIs, OKRs, metrics, measurement, attribution
  audit       — strategy audit, plan review, Canon check, validate my strategy

Respond with ONLY the JSON object:"""

_ROUTER_TOOL = {
    "name": "classify_strategy_intent",
    "description": "Classify the user's marketing strategy question into a mode.",
    "input_schema": {
        "type": "object",
        "properties": {
            "mode": {
                "type": ["string", "null"],
                "enum": list(SUPPORTED_MODES) + [None],
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
    if mode not in SUPPORTED_MODES:
        mode = None
    if confidence not in ("high", "medium", "low"):
        confidence = "medium" if mode else "low"
    return {
        "mode":              mode,
        "confidence":        confidence,
        "extracted_context": extracted if isinstance(extracted, dict) else {},
    }


def route_strategy_intent(analyzer: Any, message: str) -> Dict[str, Any]:
    """Classify message into {mode, confidence, extracted_context}."""
    from agents.base_router import route
    return route(
        analyzer, message,
        prompt_template=_ROUTER_PROMPT,
        tool=_ROUTER_TOOL,
        system_prompt=_ROUTER_SYSTEM,
        validate=_validate,
        fallback=_FALLBACK,
        model=_ROUTER_MODEL,
        name="strategy_router",
    )
