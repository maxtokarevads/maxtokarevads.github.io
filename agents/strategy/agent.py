import logging
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..base_agent import BaseAgent, _slugify
from vault_labels import (
    STRATEGY_MODE_LABELS as _STRATEGY_MODE_LABELS,
    FIELD_MODE, FIELD_GOAL, FIELD_PRODUCT, FIELD_NICHE, FIELD_HORIZON, FIELD_DATE,
)
from .skills.prompt import (
    build_strategy_prompt,
    build_gtm_prompt,
    build_positioning_prompt,
    build_channel_mix_prompt,
    build_kpi_prompt,
    SUPPORTED_MODES,
)
from .skills.canon import build_strategy_audit_prompt
from .skills.structured import STRATEGY_STRUCTURED_TOOLS, split_strategy_result
from .router import route_strategy_intent
from integrations.vault_reader import agent_kb_context_block

logger = logging.getLogger(__name__)

_VAULT_CAMPAIGNS = Path(__file__).parent.parent.parent / "vault" / "campaigns"

_SYSTEM_PROMPTS: Dict[str, str] = {
    "general": (
        "You are a Chief Marketing Officer with experience launching products to market. "
        "You think strategically: define positioning, channel mix, growth stages, and success metrics. "
        "You deliver plans with concrete steps, timelines, and ownership. "
        "Every recommendation is backed by data or a clear rationale. "
        "End with a CONFIDENCE ASSESSMENT: rate each major recommendation High/Medium/Low confidence."
    ),
    "gtm": (
        "You are a go-to-market specialist who has launched 20+ B2B and B2C products. "
        "You build GTM plans from ICP definition through channel sequencing to 90-day launch milestones. "
        "You know that the biggest GTM failure is targeting too broadly too early. "
        "You always define the kill signal — the metric that would trigger a pivot."
    ),
    "positioning": (
        "You are a brand strategist and positioning expert. "
        "You apply STP, JTBD, and Jobs-to-be-Done to find unclaimed white space in the market. "
        "You know that positioning is about trade-offs: what you choose NOT to be matters as much as what you are. "
        "Every positioning statement you write passes the 'could a competitor say this?' test — if yes, it's not differentiating enough."
    ),
    "channel_mix": (
        "You are a media planning and channel strategy specialist. "
        "You allocate budget across channels based on funnel stage, ICP density, and marginal ROAS logic. "
        "You know the minimum thresholds for each channel to exit learning phase. "
        "You think in channel sequencing: which channels depend on others to work, and what must come first."
    ),
    "audit": (
        "You are a Strategy Canon Auditor — a senior marketing strategist operating per the Canon Runbook for Marketing Strategy. "
        "Before any strategic recommendation, you check P0 Gates: ICP definition, North Star Metric, kill signal, budget, timeline. "
        "If a P0 gate fails, you HALT and write: 'HALT — [SAC-XXXX]: [missing input]. Do not proceed until this is provided.' "
        "Every finding is tied to a specific input value — never invent data. "
        "Output: structured Fixlist table (Rule ID | Severity | Category | Finding | Fix | Verify). "
        "P0 always first. End with TELEGRAM_REPORT block. Include confidence assessment for each recommendation."
    ),
    "kpi": (
        "You are a marketing analytics and measurement specialist. "
        "You build KPI trees, OKR structures, and attribution models. "
        "You distinguish leading from lagging indicators and know what to check daily vs monthly. "
        "You never recommend a metric that cannot be measured with available tools. "
        "You always specify the data source and tracking setup required for each KPI."
    ),
}

@dataclass
class StrategyRequest:
    """Typed, normalised payload for StrategyAgent.run()."""
    mode:        str            = "general"
    product:     str            = ""
    goal:        str            = ""
    industry:    str            = ""
    timeline:    str            = "3 months"
    budget:      str            = ""
    competitors: str            = ""
    usp:         str            = ""
    resources:   Dict[str, Any] = field(default_factory=dict)
    audience:    Dict[str, Any] = field(default_factory=dict)
    context:     str            = ""

    def __post_init__(self) -> None:
        self.mode = (self.mode or "general").lower().strip()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StrategyRequest":
        allowed = {f.name for f in cls.__dataclass_fields__.values()}
        return cls(**{k: v for k, v in data.items() if k in allowed})


@dataclass
class _StrategyCtx:
    mode:            str
    final_prompt:    str
    system:          str
    structured_tool: Optional[Dict[str, Any]]
    cached_kb:       Optional[str]
    payload:         Dict[str, Any]


_BUILDERS = {
    "general":     build_strategy_prompt,
    "gtm":         build_gtm_prompt,
    "positioning": build_positioning_prompt,
    "channel_mix": build_channel_mix_prompt,
    "kpi":         build_kpi_prompt,
    "audit":       build_strategy_audit_prompt,
}

_KB_MODES = set(SUPPORTED_MODES)
_STRUCTURED_MODES = set(STRATEGY_STRUCTURED_TOOLS.keys())
# Audit has its own output contract — skip OUTPUT_CONTRACT appending
_AUDIT_MODES = {"audit"}


def _build_strategy_vault_content(
    mode: str, payload: Dict[str, Any], result_text: str, prompt_hash: str
) -> tuple:
    today      = date.today().isoformat()
    product    = payload.get("product", payload.get("goal", "strategy"))
    goal       = payload.get("goal", "")
    industry   = payload.get("industry", "")
    timeline   = payload.get("timeline", "")
    slug       = _slugify(product)
    filename   = f"{today}-strategy-{mode}-{slug}.md"
    mode_label = _STRATEGY_MODE_LABELS.get(mode, mode.capitalize())
    title      = f"{mode_label} — {product}" if product else mode_label

    frontmatter = f"""---
title: "{title}"
date: {today}
agent: strategy
mode: {mode}
product: "{product}"
goal: "{goal}"
industry: "{industry}"
timeline: "{timeline}"
tags:
  - strategy
  - {mode}
---"""

    content  = f"""{frontmatter}

# {title}

**{FIELD_MODE}:** {mode_label}
**{FIELD_GOAL}:** {goal or "—"}
**{FIELD_PRODUCT}:** {product or "—"}
**{FIELD_NICHE}:** {industry or "—"}
**{FIELD_HORIZON}:** {timeline or "—"}
**{FIELD_DATE}:** {today}

---

## {mode_label}

{result_text}
"""
    return filename, content


class StrategyAgent(BaseAgent):
    """Marketing strategy agent.

    Modes:
      general     — full marketing plan (default)
      gtm         — go-to-market launch plan
      positioning — brand positioning & messaging architecture
      channel_mix — channel selection & budget allocation
      kpi         — KPI framework & measurement plan
    """

    dependencies: list = []  # strategy has no upstream dependencies

    def get_system_prompt(self, mode: Optional[str] = None) -> str:
        return _SYSTEM_PROMPTS.get(mode or "general", _SYSTEM_PROMPTS["general"])

    def _prepare_run(self, payload: Dict[str, Any]) -> "Tuple[Optional[_StrategyCtx], Optional[Dict[str, Any]]]":
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

        raw_mode = str(payload.get("mode", "general")).lower().strip()
        if raw_mode and raw_mode not in SUPPORTED_MODES:
            return None, {"error": f"Unknown mode: '{raw_mode}'. Supported: {SUPPORTED_MODES}",
                          "agent": self.name}
        mode = raw_mode or "general"

        builder      = _BUILDERS[mode]
        base_prompt  = builder(payload)
        final_prompt = (
            base_prompt if mode in _STRUCTURED_MODES or mode in _AUDIT_MODES
            else self._build_prompt_with_contract(base_prompt)
        )
        cached_kb = agent_kb_context_block("strategy") if mode in _KB_MODES else None
        system    = self.get_system_prompt(mode)

        return _StrategyCtx(
            mode=mode, final_prompt=final_prompt, system=system,
            structured_tool=STRATEGY_STRUCTURED_TOOLS.get(mode),
            cached_kb=cached_kb, payload=payload,
        ), None

    def _build_strategy_response(self, ctx: _StrategyCtx, result_text: str,
                                  structured: Dict[str, Any]) -> Dict[str, Any]:
        filename, content = _build_strategy_vault_content(
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
                result_text, structured = split_strategy_result(raw)
            else:
                logger.warning("call_tool returned None for strategy mode=%s, falling back", ctx.mode)

        if not result_text:
            result_text = self.analyzer.chat_with_agent(
                ctx.final_prompt, system_prompt=ctx.system, cached_context=ctx.cached_kb,
                agent_name=self.name, agent_mode=ctx.mode,
            )

        return self._build_strategy_response(ctx, result_text, structured)

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
                result_text, structured = split_strategy_result(raw)
            else:
                logger.warning("acall_tool returned None for strategy mode=%s, falling back", ctx.mode)

        if not result_text:
            result_text = await self.analyzer.achat_with_agent(
                ctx.final_prompt, system_prompt=ctx.system, cached_context=ctx.cached_kb,
                agent_name=self.name, agent_mode=ctx.mode,
            )

        return self._build_strategy_response(ctx, result_text, structured)

    def smart_chat(
        self,
        message: str,
        chat_id: int = 0,
        extra_payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Route a free-form message to the right mode via Sonnet intent classifier."""
        intent     = route_strategy_intent(self.analyzer, message)
        mode       = intent["mode"]
        confidence = intent["confidence"]
        extracted  = intent.get("extracted_context", {})

        logger.debug("strategy smart_chat: mode=%s confidence=%s", mode, confidence)

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
