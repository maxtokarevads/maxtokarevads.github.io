import functools
import logging
import os
from datetime import date
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from ..base_agent import BaseAgent
from .skills.prompt import build_ads_prompt, SUPPORTED_PLATFORMS, SUPPORTED_MODES, AdsRequest
from .skills.structured import STRUCTURED_TOOLS, split_structured_result
from .router import route_intent
from integrations.vault_reader import kb_context_block, KB_MODES
from vault_labels import (
    ADS_MODE_LABELS as _MODE_LABELS,
    ADS_PLATFORM_LABELS as _PLATFORM_LABELS,
    FIELD_PLATFORM, FIELD_MODE, FIELD_PRODUCT, FIELD_GOAL,
    FIELD_DATE, FIELD_PREV, FIELD_METRICS,
)

logger = logging.getLogger(__name__)

# Whitelists for input validation — prevents prompt injection via payload fields
_VALID_PLATFORMS = set(SUPPORTED_PLATFORMS) | {"facebook", "instagram", "fb", "google_ads"}
_VALID_MODES     = set(SUPPORTED_MODES)

# Model routing by task complexity (used when MODEL_ROUTING=true in .env)
_OPUS_MODES = {"audit"}


def _route_model(mode: str) -> Optional[str]:
    """Return model override based on task complexity, or None to use env default."""
    if os.getenv("MODEL_ROUTING", "false").lower() != "true":
        return None
    if mode in _OPUS_MODES:
        return os.getenv("AUDIT_MODEL", "claude-opus-4-8")
    return None  # Sonnet from ANTHROPIC_MODEL

_VAULT_CAMPAIGNS = Path(__file__).parent.parent.parent / "vault" / "campaigns"


@functools.lru_cache(maxsize=64)
def _cached_glob(pattern: str) -> tuple:
    """Cache glob results for 1 process lifetime. Returns sorted tuple (immutable → cacheable)."""
    return tuple(sorted(Path(pattern).parent.glob(Path(pattern).name), reverse=True))


def _find_previous_campaign(platform: str, mode: str, today: str) -> str:
    """Return an Obsidian link to the most recent same-platform campaign, or ''.
    Uses a cached glob to avoid repeated filesystem scans on each vault save.
    """
    try:
        pattern = str(_VAULT_CAMPAIGNS / f"*-{platform}-{mode}.md")
        files   = _cached_glob(pattern)
        for f in files:
            if not Path(f).name.startswith(today):
                return f"[[campaigns/{Path(f).stem}]]"
    except Exception:
        pass
    return ""


def _build_vault_content(
    mode: str, platform: str, payload: Dict[str, Any],
    result_text: str, prompt_hash: str,
) -> tuple:
    """Return (filename, content) for the vault Markdown note."""
    today    = date.today().isoformat()
    filename = f"{today}-{platform}-{mode}.md"

    product  = payload.get("product", "")
    goal     = payload.get("goal", "")
    budget   = payload.get("budget", "")

    platform_label = _PLATFORM_LABELS.get(platform, platform.capitalize())
    mode_label     = _MODE_LABELS.get(mode, mode.capitalize())
    title          = f"{platform_label} / {mode_label}" + (f" — {product}" if product else "")

    metrics = payload.get("metrics", {})
    metrics_lines = "\n".join(f"- **{k}:** {v}" for k, v in metrics.items()) if metrics else ""
    metrics_block = f"\n## {FIELD_METRICS}\n\n{metrics_lines}\n" if metrics_lines else ""

    previous      = _find_previous_campaign(platform, mode, today)
    related_block = f"\n**{FIELD_PREV}:** {previous}\n" if previous else ""

    frontmatter = f"""---
title: "{title}"
date: {today}
agent: ads
platform: {platform}
mode: {mode}
product: "{product}"
goal: "{goal}"
budget: {budget if budget else '""'}
tags:
  - ads
  - {platform}
  - {mode}
---"""

    content = f"""{frontmatter}

# {title}

**{FIELD_PLATFORM}:** {platform_label}
**{FIELD_MODE}:** {mode_label}
**{FIELD_PRODUCT}:** {product or "—"}
**{FIELD_GOAL}:** {goal or "—"}
**{FIELD_DATE}:** {today}{related_block}{metrics_block}
---

## {mode_label}

{result_text}
"""
    return filename, content


_SYSTEM_PROMPTS: Dict[str, str] = {
    "plan": (
        "You are a senior performance marketer with 8+ years of experience "
        "specialising in Google Ads, Meta, and TikTok Ads. "
        "You build campaigns from scratch: structure, bidding, targeting, ad copy. "
        "You deliver concrete plans with specific numbers, timelines, and success criteria."
    ),
    "analyze": (
        "You are a data-driven marketing analyst. "
        "You diagnose ad campaigns using metrics: CTR, ROAS, CPA, Quality Score, Frequency. "
        "You find root causes of problems, not symptoms. "
        "Every recommendation is backed by data and an expected impact estimate. "
        "CRITICAL: End every analysis with a CONFIDENCE ASSESSMENT section: "
        "rate each recommendation High/Medium/Low confidence, "
        "state what data is missing that would sharpen the diagnosis, "
        "and flag any assumptions you are making. Never invent data."
    ),
    "copy": (
        "You are a senior copywriter at a performance marketing agency. "
        "You write ad copy that converts. "
        "You know exact character limits for every platform by heart. "
        "You always provide multiple variants with different hook strategies. "
        "You verify every piece of copy against platform limits before responding."
    ),
    "retargeting": (
        "You are a CRM and lifecycle marketing specialist. "
        "You build remarketing funnels: audience segmentation by intent temperature, "
        "messaging for each TOFU/MOFU/BOFU stage, pixel strategies. "
        "You know how to avoid wasting budget on existing buyers while capturing high-intent users."
    ),
    "ab_test": (
        "You are a CRO specialist and A/B testing expert. "
        "You design statistically sound experiments: one variable at a time, "
        "correct sample size, proper test duration. "
        "You know the native testing tools for each platform: "
        "Ad Variations, Drafts & Experiments, Split Test."
    ),
    "budget": (
        "You are a CMO and media planner with experience managing multi-channel budgets. "
        "You allocate budget across platforms based on goals, funnel stage, and industry benchmarks. "
        "You know the minimum thresholds for algorithm learning and scaling. "
        "You think in Marginal ROAS: where should the next $1 go."
    ),
    "audit": (
        "You are a Canon Audit Assistant — a senior performance marketing auditor "
        "operating per the Canon Runbook for Google Ads, Meta Ads, and TikTok Ads. "
        "Before any optimisation you check P0 Gates: tracking, conversions, account health. "
        "Every finding is tied to a specific data point. "
        "If an input is missing you write 'Missing input: [CODE]' — you never invent data. "
        "Output: Fixlist table (Rule ID | Severity | Where | Issue | What to do | Verify | Rollback). "
        "P0 always first. Halt optimisation if any P0 gate fails. "
        "For TikTok: always include Hook Rate audit and over-attribution factor."
    ),
    "landing": (
        "You are a senior CRO (Conversion Rate Optimisation) specialist. "
        "You audit landing pages across six layers: speed, above-the-fold, mobile UX, "
        "form/checkout friction, trust signals, and copy clarity. "
        "Every finding is backed by a specific metric or UX heuristic. "
        "You output a prioritised Fixlist (P0 = conversion blocker, P1 = significant lift, P2 = incremental) "
        "and an A/B test shortlist with sample-size estimates. "
        "You never invent page data — if the URL is inaccessible, you list the checks as a manual checklist."
    ),
    "research": (
        "You are a paid media research specialist. "
        "For Google Ads: keyword universe mapping, match type strategy, negative keyword mining, competitor SERP analysis. "
        "For Meta: audience taxonomy, Custom Audiences, Lookalike seed quality, creative intelligence from Ad Library. "
        "For TikTok: creative research via Creative Center, hook pattern analysis, sound strategy, organic competitive audit. "
        "You always output actionable artefacts: keyword lists, audience matrices, creative briefs — not generic advice."
    ),
    "forecast": (
        "You are a media planning specialist and performance forecaster. "
        "You build bottom-up projections using the CPM → CTR → CVR funnel model. "
        "You run three scenarios (conservative, base, optimistic), account for learning phase ramp-up, "
        "and calculate break-even CPA/ROAS. "
        "You flag data assumptions clearly and identify which lever has the biggest CPA impact. "
        "Every forecast includes risk factors and mitigations."
    ),
}

_CHAT_SYSTEM_PROMPT = (
    "You are a performance marketing consultant specialising in Google Ads, Meta, and TikTok Ads. "
    "You are talking to a client or colleague in Telegram. "
    "Answer directly and concisely — like a senior colleague, not a formal report. "
    "Give specific, actionable answers. Skip preambles like 'Great question!' or 'Of course!'. "
    "If you need context to give a good answer, ask one focused question."
)

_DEFAULT_SYSTEM_PROMPT = _CHAT_SYSTEM_PROMPT


from dataclasses import dataclass as _dataclass


@_dataclass
class _AdsCtx:
    """Prepared run context — shared by run() and arun()."""
    mode:            str
    platform:        str
    final_prompt:    str
    structured_tool: Optional[Dict[str, Any]]
    model_override:  Optional[str]
    cached_kb:       Optional[str]
    model_used:      str
    payload:         Dict[str, Any]


class AdsAgent(BaseAgent):
    """Ads agent — Google Ads, Meta, TikTok.

    Modes:
      plan        — campaign launch strategy (default)
      analyze     — diagnose metrics for an existing campaign
      copy        — generate ad copy / scripts
      retargeting — remarketing funnel strategy
      ab_test     — A/B test design
      budget      — cross-platform budget allocation
      audit       — Canon audit (platform-specific rules + SOPs)
      research    — keyword / audience research
      landing     — landing page CRO audit
      forecast    — media plan + scenario projections
    """

    dependencies = ["strategy"]

    def get_system_prompt(self, mode: Optional[str] = None) -> str:
        if not mode:
            return _CHAT_SYSTEM_PROMPT
        return _SYSTEM_PROMPTS.get(mode, _CHAT_SYSTEM_PROMPT)

    def _prepare_run(self, payload: Dict[str, Any]) -> "Tuple[Optional[_AdsCtx], Optional[Dict[str, Any]]]":
        """Validate inputs and build prompt. Returns (_AdsCtx, None) or (None, error_dict)."""
        if not self.analyzer:
            return None, {"error": "No analyzer configured"}

        _MAX_PAYLOAD_CHARS = 80_000
        try:
            payload_size = len(str(payload))
        except Exception:
            payload_size = 0
        if payload_size > _MAX_PAYLOAD_CHARS:
            return None, {
                "error": f"Payload too large ({payload_size:,} chars). Max {_MAX_PAYLOAD_CHARS:,}.",
                "agent": self.name,
            }

        budget_raw = payload.get("budget", 0)
        try:
            if float(budget_raw) < 0:
                return None, {"error": "Budget cannot be negative.", "agent": self.name}
        except (TypeError, ValueError):
            pass

        metrics = payload.get("metrics", {})
        if metrics and isinstance(metrics, dict):
            _issues = []
            for key, lo, hi in [("ctr", 0, 100), ("roas", 0, None), ("cpa", 0, None)]:
                val = metrics.get(key)
                if val is not None:
                    try:
                        fval = float(val)
                        if lo is not None and fval < lo:
                            _issues.append(f"{key}={val} < {lo}")
                        if hi is not None and fval > hi:
                            _issues.append(f"{key}={val} > {hi}")
                    except (TypeError, ValueError):
                        _issues.append(f"{key}={val!r} not numeric")
            if _issues:
                logger.warning("AdsAgent: suspicious metrics: %s", "; ".join(_issues))

        raw_platform = str(payload.get("platform", "")).lower().strip()
        raw_mode     = str(payload.get("mode", "plan")).lower().strip()
        if raw_platform and raw_platform not in _VALID_PLATFORMS:
            return None, {"error": f"Unknown platform: '{raw_platform}'. Supported: {sorted(SUPPORTED_PLATFORMS)}",
                          "agent": self.name, "mode": raw_mode}
        if raw_mode and raw_mode not in _VALID_MODES:
            return None, {"error": f"Unknown mode: '{raw_mode}'. Supported: {sorted(_VALID_MODES)}",
                          "agent": self.name, "platform": raw_platform}

        req    = AdsRequest.from_dict(payload)
        merged = {**payload, **req.to_dict()}
        mode   = req.mode
        prompt = build_ads_prompt(merged)

        if prompt.startswith("ERROR:"):
            return None, {"error": prompt, "agent": self.name,
                          "platform": req.platform or payload.get("platform", "unknown"),
                          "mode": mode}

        _AUDIT_MODES = {"audit", "landing", "forecast"}
        final_prompt = prompt if mode in _AUDIT_MODES else self._build_prompt_with_contract(prompt)

        cached_kb      = kb_context_block(req.platform) if mode in KB_MODES and req.platform else None
        model_override = _route_model(mode)
        platform       = req.platform or payload.get("platform", "unknown")
        model_used     = getattr(self.analyzer, "model_name", "unknown")

        return _AdsCtx(
            mode=mode, platform=platform, final_prompt=final_prompt,
            structured_tool=STRUCTURED_TOOLS.get(mode),
            model_override=model_override, cached_kb=cached_kb,
            model_used=model_used, payload=payload,
        ), None

    def _build_run_response(
        self,
        ctx: "_AdsCtx",
        result_text: str,
        structured: Dict[str, Any],
        used_structured: bool,
    ) -> Dict[str, Any]:
        """Vault save + assemble response dict. Shared by run() and arun()."""
        _NO_SAVE_MODES = {"budget", "forecast"}
        if ctx.mode not in _NO_SAVE_MODES and ctx.platform and ctx.platform != "unknown":
            filename, content = _build_vault_content(
                ctx.mode, ctx.platform, ctx.payload, result_text,
                self._prompt_hash(self.get_system_prompt(ctx.mode)),
            )
            self._save_to_vault(filename, content, _VAULT_CAMPAIGNS)

        response: Dict[str, Any] = {
            "result":     result_text,
            "agent":      self.name,
            "platform":   ctx.platform,
            "mode":       ctx.mode,
            "model_used": ctx.model_used,
        }
        if structured:
            response["structured"] = structured
        if ctx.structured_tool and not used_structured:
            response["structured_fallback"] = True
        return response

    def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        ctx, err = self._prepare_run(payload)
        if err is not None:
            return err
        if ctx is None:
            return {"error": "Internal error: _prepare_run returned None", "agent": self.name}

        result_text     = ""
        structured:     Dict[str, Any] = {}
        used_structured = False

        if ctx.structured_tool and callable(getattr(self.analyzer, "call_tool", None)):
            raw = self.analyzer.call_tool(
                user_message=ctx.final_prompt,
                tool=ctx.structured_tool,
                system_prompt=self.get_system_prompt(ctx.mode),
                model_override=ctx.model_override,
                cached_context=ctx.cached_kb,
            )
            if raw:
                result_text, structured = split_structured_result(raw)
                used_structured = bool(structured)
            else:
                logger.warning("call_tool returned None for mode=%s, falling back", ctx.mode)

        if not result_text:
            result_text = self.analyzer.chat_with_agent(
                ctx.final_prompt,
                system_prompt=self.get_system_prompt(ctx.mode),
                model_override=ctx.model_override,
                cached_context=ctx.cached_kb,
                agent_name=self.name,
                agent_mode=ctx.mode,
            )

        return self._build_run_response(ctx, result_text, structured, used_structured)

    async def arun(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """True async run — uses acall_tool / achat_with_agent for real I/O concurrency."""
        ctx, err = self._prepare_run(payload)
        if err is not None:
            return err
        if ctx is None:
            return {"error": "Internal error: _prepare_run returned None", "agent": self.name}

        result_text     = ""
        structured:     Dict[str, Any] = {}
        used_structured = False

        if ctx.structured_tool and callable(getattr(self.analyzer, "acall_tool", None)):
            raw = await self.analyzer.acall_tool(
                user_message=ctx.final_prompt,
                tool=ctx.structured_tool,
                system_prompt=self.get_system_prompt(ctx.mode),
                model_override=ctx.model_override,
                cached_context=ctx.cached_kb,
            )
            if raw:
                result_text, structured = split_structured_result(raw)
                used_structured = bool(structured)
            else:
                logger.warning("acall_tool returned None for mode=%s, falling back", ctx.mode)

        if not result_text:
            result_text = await self.analyzer.achat_with_agent(
                ctx.final_prompt,
                system_prompt=self.get_system_prompt(ctx.mode),
                model_override=ctx.model_override,
                cached_context=ctx.cached_kb,
                agent_name=self.name,
                agent_mode=ctx.mode,
            )

        return self._build_run_response(ctx, result_text, structured, used_structured)

    def smart_chat(
        self,
        message: str,
        chat_id: int = 0,
        extra_payload: dict | None = None,
    ) -> dict:
        """
        Chat entry-point with automatic intent routing.

        1. Classify the message → {platform, mode, extracted_context}.
        2. If confidence is high/medium AND both platform+mode found → call run().
        3. Otherwise fall back to generic chat() with mode-aware system prompt.

        Returns the same shape as chat() and run():
            {"result": str, "agent": str, ...}
        """
        intent = route_intent(self.analyzer, message)
        platform   = intent["platform"]
        mode       = intent["mode"]
        confidence = intent["confidence"]
        extracted  = intent.get("extracted_context", {})

        logger.debug(
            "smart_chat intent: platform=%s mode=%s confidence=%s",
            platform, mode, confidence,
        )

        if confidence in ("high", "medium") and platform and mode:
            # extracted goes first so router-validated platform/mode always win
            payload: dict = {
                **extracted,
                "platform": platform,
                "mode":     mode,
            }
            if extra_payload:
                payload.update(extra_payload)
            result = self.run(payload)
            result["_routed"] = {"platform": platform, "mode": mode, "confidence": confidence}

            self._persist_routed_history(chat_id, message, result.get("result", ""))
            return result

        # Generic chat — use mode-specific system prompt if mode was detected
        return self.chat(message, chat_id=chat_id, mode=mode)

    @staticmethod
    def supported_platforms() -> list:
        return SUPPORTED_PLATFORMS

    @staticmethod
    def supported_modes() -> list:
        return SUPPORTED_MODES
