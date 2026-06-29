import logging
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..base_agent import BaseAgent, _slugify
from vault_labels import (
    CREATIVE_MODE_LABELS as _CREATIVE_MODE_LABELS,
    FIELD_MODE, FIELD_PRODUCT, FIELD_PLATFORM, FIELD_TONE, FIELD_FUNNEL, FIELD_DATE,
)
from .skills import (
    build_concept_prompt, build_copy_prompt,
    build_script_prompt, build_ugc_brief_prompt,
    SUPPORTED_MODES,
)
from .skills.structured import CREATIVE_STRUCTURED_TOOLS, split_creative_result
from .router   import route_creative_intent
from .enricher import enrich_creative_payload
from integrations.vault_reader import agent_kb_context_block

logger = logging.getLogger(__name__)

_VAULT_CAMPAIGNS = Path(__file__).parent.parent.parent / "vault" / "campaigns"

_SYSTEM_PROMPTS: Dict[str, str] = {
    "concept": (
        "You are a Creative Director at a top performance marketing agency. "
        "You develop campaign concepts that stop the scroll AND convert. "
        "You always generate 3 distinct variants with different emotional hooks — never just reformulations. "
        "Every concept includes a visual direction, not just copy. "
        "You know that a great concept is platform-native: what works on TikTok fails on LinkedIn."
    ),
    "copy": (
        "You are a senior performance copywriter. "
        "You write ad copy that converts — direct, specific, benefit-led. "
        "You know platform character limits by heart and verify every piece before submitting. "
        "You always provide multiple variants with different hook strategies. "
        "You never write vague copy ('Amazing product!') — every claim is specific and provable."
    ),
    "script": (
        "You are a video script writer specialising in short-form paid ads for TikTok, Reels, and YouTube. "
        "You know that the first 3 seconds decide everything — hook rate is your north star metric. "
        "You write for speech, not reading: short sentences, contractions, one idea per line. "
        "Every script is timecoded and includes delivery notes. "
        "You never open with 'Hey guys', 'So today', or 'I wanted to talk about'."
    ),
    "ugc_brief": (
        "You are a UGC strategy director who has briefed 500+ creators. "
        "You know that creators need freedom in delivery but precision in claims. "
        "Your briefs give exact talking points (not scripts) and specific shot requirements. "
        "You understand that the best-performing UGC looks accidental but is carefully engineered. "
        "You always flag brand safety risks and banned claims proactively."
    ),
}

_CHAT_SYSTEM_PROMPT = (
    "You are a creative consultant specialising in ad creative for digital marketing. "
    "You advise on hooks, copy, video scripts, and creative strategy. "
    "You give specific, actionable answers with examples — not generic advice."
)

@dataclass
class CreativeRequest:
    """Typed, normalised payload for CreativeAgent.run()."""
    mode:         str            = "concept"
    product:      str            = ""
    platform:     str            = ""
    tone:         str            = ""
    funnel_stage: str            = "mofu"
    usp:          str            = ""
    duration:     int            = 30
    format:       str            = ""
    audience:     Dict[str, Any] = field(default_factory=dict)
    context:      str            = ""

    def __post_init__(self) -> None:
        self.mode     = (self.mode or "concept").lower().strip()
        self.platform = (self.platform or "").lower().strip()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CreativeRequest":
        allowed = {f.name for f in cls.__dataclass_fields__.values()}
        return cls(**{k: v for k, v in data.items() if k in allowed})


@dataclass
class _CreativeCtx:
    mode:            str
    final_prompt:    str
    system:          str
    structured_tool: Optional[Dict[str, Any]]
    cached_kb:       Optional[str]
    payload:         Dict[str, Any]


_BUILDERS = {
    "concept":   build_concept_prompt,
    "copy":      build_copy_prompt,
    "script":    build_script_prompt,
    "ugc_brief": build_ugc_brief_prompt,
}

_KB_MODES = set(SUPPORTED_MODES)
_STRUCTURED_MODES = {"copy", "script", "ugc_brief"}


def _build_creative_vault_content(
    mode: str, payload: Dict[str, Any], result_text: str, prompt_hash: str
) -> tuple:
    today        = date.today().isoformat()
    platform     = payload.get("platform", "")
    product      = payload.get("product", "creative")
    tone         = payload.get("tone", "")
    funnel_stage = payload.get("funnel_stage", "")
    slug         = (f"{_slugify(platform)}-" if platform else "") + _slugify(product)
    filename     = f"{today}-creative-{mode}-{slug}.md"
    mode_label   = _CREATIVE_MODE_LABELS.get(mode, mode.capitalize())
    title        = f"{mode_label} — {product}" + (f" ({platform})" if platform else "")

    frontmatter = f"""---
title: "{title}"
date: {today}
agent: creative
mode: {mode}
product: "{product}"
platform: "{platform}"
tone: "{tone}"
funnel_stage: "{funnel_stage}"
tags:
  - creative
  - {mode}
---"""

    content  = f"""{frontmatter}

# {title}

**{FIELD_MODE}:** {mode_label}
**{FIELD_PRODUCT}:** {product or "—"}
**{FIELD_PLATFORM}:** {platform or "—"}
**{FIELD_TONE}:** {tone or "—"}
**{FIELD_FUNNEL}:** {funnel_stage or "—"}
**{FIELD_DATE}:** {today}

---

## {mode_label}

{result_text}
"""
    return filename, content


class CreativeAgent(BaseAgent):
    """Creative and ad content agent.

    Modes:
      concept   — creative concept: 3 variants, core message, visual direction (default)
      copy      — platform ad copy with character counts and compliance check
      script    — video script: hook -> problem -> solution -> CTA
      ugc_brief — UGC creator brief: talking points, shot list, dos/don'ts
    """

    dependencies = ["strategy", "ads"]

    def get_system_prompt(self, mode: Optional[str] = None) -> str:
        return _SYSTEM_PROMPTS.get(mode or "concept", _CHAT_SYSTEM_PROMPT)

    def _prepare_run(self, payload: Dict[str, Any]) -> "Tuple[Optional[_CreativeCtx], Optional[Dict[str, Any]]]":
        if not self.analyzer:
            return None, {"error": "No analyzer configured"}

        _MAX_PAYLOAD_CHARS = 80_000
        try:
            payload_size = len(str(payload))
        except Exception:
            payload_size = 0
        if payload_size > _MAX_PAYLOAD_CHARS:
            return None, {"error": f"Payload too large ({payload_size:,} chars). Max {_MAX_PAYLOAD_CHARS:,}.",
                          "agent": self.name}

        raw_mode = str(payload.get("mode", "concept")).lower().strip()
        if raw_mode and raw_mode not in SUPPORTED_MODES:
            return None, {"error": f"Unknown mode: '{raw_mode}'. Supported: {SUPPORTED_MODES}",
                          "agent": self.name}
        mode = raw_mode or "concept"

        payload, enricher_block = enrich_creative_payload(mode, payload)
        base_prompt = _BUILDERS[mode](payload)
        if enricher_block:
            base_prompt = enricher_block + base_prompt

        final_prompt = (
            base_prompt if mode in _STRUCTURED_MODES
            else self._build_prompt_with_contract(base_prompt)
        )
        cached_kb = agent_kb_context_block("creative") if mode in _KB_MODES else None
        system    = self.get_system_prompt(mode)

        return _CreativeCtx(
            mode=mode, final_prompt=final_prompt, system=system,
            structured_tool=CREATIVE_STRUCTURED_TOOLS.get(mode),
            cached_kb=cached_kb, payload=payload,
        ), None

    def _build_creative_response(self, ctx: _CreativeCtx, result_text: str,
                                  structured: Dict[str, Any]) -> Dict[str, Any]:
        filename, content = _build_creative_vault_content(
            ctx.mode, ctx.payload, result_text,
            self._prompt_hash(ctx.system),
        )
        self._save_to_vault(filename, content, _VAULT_CAMPAIGNS)
        response: Dict[str, Any] = {"result": result_text, "agent": self.name, "mode": ctx.mode}
        if structured:
            response["structured"] = structured
        return response

    def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        ctx, err = self._prepare_run(payload)
        if err is not None:
            return err
        if ctx is None:
            return {"error": "Internal error: _prepare_run returned None", "agent": self.name}

        result_text = ""
        structured: Dict[str, Any] = {}

        if ctx.structured_tool and callable(getattr(self.analyzer, "call_tool", None)):
            raw = self.analyzer.call_tool(
                user_message=ctx.final_prompt, tool=ctx.structured_tool,
                system_prompt=ctx.system, cached_context=ctx.cached_kb,
            )
            if raw:
                result_text, structured = split_creative_result(raw)
            else:
                logger.warning("call_tool returned None for creative mode=%s, falling back", ctx.mode)

        if not result_text:
            result_text = self.analyzer.chat_with_agent(
                ctx.final_prompt, system_prompt=ctx.system, cached_context=ctx.cached_kb,
                agent_name=self.name, agent_mode=ctx.mode,
            )

        return self._build_creative_response(ctx, result_text, structured)

    async def arun(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """True async run — uses acall_tool / achat_with_agent for real I/O concurrency."""
        ctx, err = self._prepare_run(payload)
        if err is not None:
            return err
        if ctx is None:
            return {"error": "Internal error: _prepare_run returned None", "agent": self.name}

        result_text = ""
        structured: Dict[str, Any] = {}

        if ctx.structured_tool and callable(getattr(self.analyzer, "acall_tool", None)):
            raw = await self.analyzer.acall_tool(
                user_message=ctx.final_prompt, tool=ctx.structured_tool,
                system_prompt=ctx.system, cached_context=ctx.cached_kb,
            )
            if raw:
                result_text, structured = split_creative_result(raw)
            else:
                logger.warning("acall_tool returned None for creative mode=%s, falling back", ctx.mode)

        if not result_text:
            result_text = await self.analyzer.achat_with_agent(
                ctx.final_prompt, system_prompt=ctx.system, cached_context=ctx.cached_kb,
                agent_name=self.name, agent_mode=ctx.mode,
            )

        return self._build_creative_response(ctx, result_text, structured)

    def smart_chat(
        self,
        message: str,
        chat_id: int = 0,
        extra_payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Route a free-form message to the right creative mode via Sonnet intent classifier."""
        intent     = route_creative_intent(self.analyzer, message)
        mode       = intent["mode"]
        confidence = intent["confidence"]
        extracted  = intent.get("extracted_context", {})

        logger.debug("creative smart_chat: mode=%s confidence=%s", mode, confidence)

        if confidence in ("high", "medium") and mode:
            payload: dict = {"mode": mode, **extracted}
            if extra_payload:
                payload.update(extra_payload)
            result = self.run(payload)
            result["_routed"] = {"mode": mode, "confidence": confidence}

            self._persist_routed_history(chat_id, message, result.get("result", ""))
            return result

        return self.chat(message, chat_id=chat_id, mode=mode)

    @staticmethod
    def supported_modes() -> list:
        return list(SUPPORTED_MODES)
