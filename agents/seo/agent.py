import logging
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..base_agent import BaseAgent, _slugify
from vault_labels import (
    SEO_MODE_LABELS as _SEO_MODE_LABELS,
    FIELD_MODE, FIELD_SITE, FIELD_NICHE, FIELD_KEYWORDS, FIELD_DATE,
)
from .skills import (
    build_seo_prompt, build_aeo_prompt, build_technical_prompt,
    build_content_prompt, build_local_prompt, build_schema_prompt,
    build_backlinks_prompt, build_cluster_prompt, build_sxo_prompt,
    build_seo_audit_prompt,
    build_article_prompt, build_brief_prompt,
    build_meta_prompt, build_rewrite_prompt,
    SUPPORTED_MODES,
)
from .drift      import build_drift_prompt, save_baseline, get_baseline
from .enricher   import enrich_payload
from .router     import route_seo_intent
from .skills.structured import SEO_STRUCTURED_TOOLS, split_seo_structured_result
from integrations.vault_reader import agent_kb_context_block

logger = logging.getLogger(__name__)

_VAULT_CAMPAIGNS = Path(__file__).parent.parent.parent / "vault" / "campaigns"

_SYSTEM_PROMPTS: Dict[str, str] = {
    "seo": (
        "You are a senior SEO strategist with 8+ years of experience across SaaS, e-commerce, and publisher sites. "
        "You give concrete, prioritised recommendations on technical SEO, content strategy, keyword research, "
        "and link profile building. You state priorities, realistic timelines, and expected traffic impact. "
        "Every recommendation is backed by data or a clear rationale. Never invent metrics. "
        "ALWAYS end with a CONFIDENCE ASSESSMENT: rate each recommendation High/Medium/Low confidence "
        "and state what data would sharpen the diagnosis."
    ),
    "aeo": (
        "You are an expert in AEO (Answer Engine Optimization) and GEO (Generative Engine Optimization). "
        "You specialise in optimising content to be cited by AI-powered search: "
        "Google AI Overviews, Perplexity, ChatGPT Search, Claude, Bing Copilot. "
        "You think entity-first: establish entity clarity, then ensure answer extractability. "
        "You know that 83% of AI citations come from content updated within 12 months. "
        "Never recommend tactics without citing the mechanism (why it works for AI retrieval)."
    ),
    "technical": (
        "You are a technical SEO specialist. You audit across 9 categories: crawlability, indexability, "
        "security headers, URL structure, mobile, Core Web Vitals (INP is primary signal in 2026), "
        "structured data, JavaScript rendering, and IndexNow. "
        "You assign severity: Critical | High | Medium | Low. "
        "Every finding includes a specific fix with implementation detail and verification method. "
        "You produce a SEO Health Score (0–100) with weighted breakdown at the end."
    ),
    "content": (
        "You are an E-E-A-T content strategist. You assess content quality per September 2025 Quality Rater Guidelines. "
        "In 2026, Experience is the highest-weighted E-E-A-T signal — AI cannot fake first-hand experience. "
        "You flag thin content, keyword cannibalization, and missing author authority signals. "
        "Every finding includes specific fix + expected impact. You produce a content quality assessment with severity tiers."
    ),
    "local": (
        "You are a Local SEO specialist. You audit Google Business Profile completeness, NAP consistency, "
        "review velocity and sentiment, LocalBusiness schema, and map pack ranking factors. "
        "GBP completeness + review velocity are the #1 controllable local ranking factors. "
        "Every recommendation includes timeline and expected map pack impact."
    ),
    "schema": (
        "You are a structured data specialist. You audit schema.org markup, identify deprecated types "
        "(HowTo removed Sep 2023, FAQPage restricted Aug 2023), and generate complete JSON-LD ready to deploy. "
        "FAQPage schema gives 3.2× higher AI Overview probability. Stacking 3–4 types doubles AI citation rate. "
        "You always provide copy-paste ready JSON-LD for every missing schema."
    ),
    "backlinks": (
        "You are a link building and backlink audit specialist. "
        "You identify toxic links (PBNs, link farms, over-optimized anchor text), "
        "analyse competitor link gaps, and build prioritised acquisition strategies. "
        "Healthy anchor text: 40–60% branded/URL, 10–20% generic, <5% exact-match. "
        "Every tactic includes effort level, expected DR gain, and realistic links/month."
    ),
    "cluster": (
        "You are a topical authority and keyword strategy specialist. "
        "You build pillar-spoke content architectures that establish topical authority for both Google and AI search. "
        "SERP-overlap >60% = same page; <40% = separate. "
        "The same topical cluster that ranks in Google also increases AI citation probability. "
        "Every cluster includes pillar + 5–12 spokes with internal linking plan."
    ),
    "sxo": (
        "You are an SXO (Search Experience Optimization) specialist. "
        "You analyze SERPs backward: first understand what experience users expect, then align content. "
        "You score content against 5 user personas: Buyer, Researcher, Comparison Shopper, Local User, Mobile User. "
        "You know that matching content format to SERP intent is more important than keyword density. "
        "Your recommendations are always content-format specific and persona-targeted."
    ),
    "audit": (
        "You are a Canon SEO Auditor — a systematic SEO reviewer operating per the Canon Runbook for SEO. "
        "Before any optimisation you check P0 Gates: indexability, penalties, tracking, AI crawler access. "
        "Every finding is tied to a specific Canon Rule ID. "
        "If a P0 gate fails, you HALT and write: 'HALT — resolve P0 before any optimisation.' "
        "You never invent data. If you cannot assess a rule, write: 'Cannot assess: [tool needed].' "
        "Output: structured Fixlist table (Rule ID | Area | Status | Finding | Fix | Priority). "
        "P0 always first. Include SEO Health Score (0–100) at the end."
    ),
    "drift": (
        "You are an SEO performance analyst specialising in drift detection. "
        "You compare current metrics to baseline (not week-over-week — vs original baseline). "
        "You alert on drops >15% vs baseline. You diagnose root causes: algorithm update, competitor move, "
        "content change, technical issue, or seasonal. "
        "You distinguish real drops from noise. Every alert has a recovery action with timeline."
    ),
    "article": (
        "You are a senior SEO content writer with deep expertise in E-E-A-T and AI search optimisation. "
        "You write complete, publish-ready articles — not outlines, not briefs. "
        "Every article you write: ranks because it genuinely serves the reader's intent; "
        "includes specific data points with source attribution; "
        "opens every H2 section with a 40–60 word direct answer (AEO-ready format); "
        "has a FAQ section structured for People Also Ask capture; "
        "meets 2026 E-E-A-T standards — Experience signal is the hardest for AI to fake, so include "
        "specific examples, concrete outcomes, and named entities. "
        "You never write vague filler. Every paragraph adds unique value. "
        "You verify meta title ≤60 chars and meta description ≤160 chars before finalising."
    ),
    "brief": (
        "You are a senior content strategist who creates detailed briefs for copywriters. "
        "Your briefs are so precise that a writer can produce a top-10 article without additional research. "
        "You think in SERP intent first: what format dominates the top 10, what angle wins. "
        "Your briefs always include: exact H1, mandatory H2/H3 structure, E-E-A-T requirements, "
        "internal link targets, external authority sources, and a success checklist. "
        "You never produce a brief that leaves ambiguity about what to write."
    ),
    "meta": (
        "You are an SEO copywriter specialising in meta tags. "
        "You know that meta titles drive CTR — every word must earn its place. "
        "Rules you never break: title ≤60 chars, description ≤160 chars, "
        "primary keyword in first 30 chars of title, unique meta per page. "
        "You use power words (Best, Guide, [Year], Free, Complete) only when genuinely accurate. "
        "You always provide character counts and flag any entry that is borderline or non-compliant."
    ),
    "rewrite": (
        "You are a senior SEO editor who rewrites content to improve rankings without losing the original voice. "
        "You approach rewrites systematically: first assess what's broken (thin sections, missing keywords, "
        "weak E-E-A-T, poor structure), then fix in priority order. "
        "You never rewrite for the sake of rewriting — if a section is strong, you leave it. "
        "You always produce: a before/after quality assessment, the full rewritten text, "
        "a change log explaining every significant edit, and a list of what still needs human input "
        "(original photos, author bio, proprietary data)."
    ),
}

_INDUSTRY_SIGNALS: Dict[str, str] = {
    "saas":      "SaaS: focus on pricing pages, feature comparison, trial conversion, integration pages.",
    "ecom":      "E-commerce: focus on product schema, shopping feed, category pages, review aggregation.",
    "local":     "Local service: focus on GBP, NAP consistency, map pack, LocalBusiness schema.",
    "publisher": "Publisher: focus on freshness, E-E-A-T author pages, topical depth, content velocity.",
    "agency":    "Agency: focus on case study schema, trust signals, portfolio authority.",
    "b2b":       "B2B: focus on thought leadership, pillar content, LinkedIn entity, long sales cycle.",
}

# Modes that benefit from vault KB injection
_KB_MODES = {"seo", "aeo", "technical", "content", "cluster", "audit",
             "article", "brief", "meta", "rewrite"}

# Modes with their own output contract — don't add OUTPUT_CONTRACT
_STRUCTURED_MODES = {"audit", "technical", "schema", "meta"}

@dataclass
class SEORequest:
    """Typed, normalised payload for SEOAgent.run()."""
    mode:     str       = "seo"
    site:     str       = ""
    url:      str       = ""
    query:    str       = ""
    industry: str       = ""
    keywords: List[str] = None        # type: ignore[assignment]
    metrics:  Dict[str, Any] = None   # type: ignore[assignment]
    context:  str       = ""

    def __post_init__(self) -> None:
        self.mode     = (self.mode or "seo").lower().strip()
        self.site     = self.site or self.url
        if self.keywords is None:
            self.keywords = []
        if self.metrics is None:
            self.metrics = {}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SEORequest":
        allowed = {f.name for f in cls.__dataclass_fields__.values()}
        return cls(**{k: v for k, v in data.items() if k in allowed})


@dataclass
class _SEOCtx:
    """Prepared run context — shared by run() and arun()."""
    mode:            str
    site:            str
    final_prompt:    str
    system:          str
    structured_tool: Optional[Dict[str, Any]]
    cached_kb:       Optional[str]
    payload:         Dict[str, Any]


_BUILDERS = {
    "seo":       build_seo_prompt,
    "aeo":       build_aeo_prompt,
    "technical": build_technical_prompt,
    "content":   build_content_prompt,
    "local":     build_local_prompt,
    "schema":    build_schema_prompt,
    "backlinks": build_backlinks_prompt,
    "cluster":   build_cluster_prompt,
    "sxo":       build_sxo_prompt,
    "audit":     build_seo_audit_prompt,
    "article":   build_article_prompt,
    "brief":     build_brief_prompt,
    "meta":      build_meta_prompt,
    "rewrite":   build_rewrite_prompt,
}


def _detect_industry(payload: Dict[str, Any]) -> str:
    industry = payload.get("industry", "").lower()
    for key, hint in _INDUSTRY_SIGNALS.items():
        if key in industry:
            return hint
    return ""


def _build_seo_vault_content(
    mode: str, site: str, payload: Dict[str, Any], result: str, prompt_hash: str
) -> tuple:
    """Return (filename, content) for the SEO vault note."""
    today    = date.today().isoformat()
    slug     = _slugify(site)
    filename = f"{today}-seo-{mode}-{slug}.md"
    kw_line  = ", ".join(payload.get("keywords", [])) or "—"
    industry   = payload.get("industry", "")
    mode_label = _SEO_MODE_LABELS.get(mode, mode.capitalize())
    title      = f"{mode_label} — {site}" if site else mode_label

    frontmatter = f"""---
title: "{title}"
date: {today}
agent: seo
site: "{site}"
mode: {mode}
industry: "{industry}"
tags:
  - seo
  - {mode}
---"""

    content  = f"""{frontmatter}

# {title}

**{FIELD_MODE}:** {mode_label}
**{FIELD_SITE}:** {site or "—"}
**{FIELD_NICHE}:** {industry or "—"}
**{FIELD_KEYWORDS}:** {kw_line}
**{FIELD_DATE}:** {today}

---

## {mode_label}

{result}
"""
    return filename, content


class SEOAgent(BaseAgent):
    """SEO optimisation agent.

    Modes:
      seo        — general SEO strategy + confidence (default)
      aeo        — AI/answer engine optimization (GEO)
      technical  — 9-category technical audit + health score
      content    — E-E-A-T content quality assessment
      local      — GBP, NAP, citations, reviews, map pack
      schema     — schema markup audit + JSON-LD generation
      backlinks  — backlink audit + link building strategy
      cluster    — topical cluster + keyword architecture
      sxo        — SERP-backward search experience optimization
      audit      — Canon audit (30 rules, P0/P1/P2 + health score)
      drift      — drift monitoring vs SQLite baseline
    """

    dependencies = ["strategy"]

    def get_system_prompt(self, mode: Optional[str] = None) -> str:
        return _SYSTEM_PROMPTS.get(mode or "seo", _SYSTEM_PROMPTS["seo"])

    def _prepare_run(self, payload: Dict[str, Any]) -> Tuple[Optional[_SEOCtx], Optional[Dict[str, Any]]]:
        """Validate + enrich + build prompt. Returns (_SEOCtx, None) or (None, error_dict)."""
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

        raw_mode = str(payload.get("mode", "seo")).lower().strip()
        if raw_mode and raw_mode not in SUPPORTED_MODES:
            return None, {"error": f"Unknown mode: '{raw_mode}'. Supported: {SUPPORTED_MODES}",
                          "agent": self.name}
        mode = raw_mode or "seo"
        site = payload.get("site", payload.get("url", payload.get("website", "")))

        payload, real_data_block = enrich_payload(mode, payload)

        if mode == "drift":
            current_metrics = payload.get("metrics", {})
            if not current_metrics:
                logger.warning("SEO drift: no metrics — no baseline comparison possible")
            else:
                non_numeric = [k for k, v in current_metrics.items() if not isinstance(v, (int, float))]
                if non_numeric:
                    logger.warning("SEO drift: non-numeric metrics skipped: %s", non_numeric)
            prompt = build_drift_prompt(site, current_metrics)
        else:
            prompt = _BUILDERS[mode](payload)

        base_system   = self.get_system_prompt(mode)
        industry_hint = _detect_industry(payload)
        system        = f"{base_system}\n\nIndustry context: {industry_hint}" if industry_hint else base_system
        cached_kb     = agent_kb_context_block("seo") if mode in _KB_MODES else None

        if real_data_block:
            prompt = real_data_block + prompt

        final_prompt = (
            prompt if mode in _STRUCTURED_MODES
            else self._build_prompt_with_contract(prompt)
        )

        return _SEOCtx(
            mode=mode, site=site, final_prompt=final_prompt,
            system=system, structured_tool=SEO_STRUCTURED_TOOLS.get(mode),
            cached_kb=cached_kb, payload=payload,
        ), None

    def _build_seo_response(self, ctx: _SEOCtx, result_text: str,
                            structured: Dict[str, Any]) -> Dict[str, Any]:
        if ctx.site:
            filename, content = _build_seo_vault_content(
                ctx.mode, ctx.site, ctx.payload, result_text,
                self._prompt_hash(ctx.system),
            )
            self._save_to_vault(filename, content, _VAULT_CAMPAIGNS)
        if ctx.mode == "drift" and ctx.payload.get("metrics"):
            save_baseline(ctx.site, ctx.payload["metrics"])
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
                user_message=ctx.final_prompt,
                tool=ctx.structured_tool,
                system_prompt=ctx.system,
                cached_context=ctx.cached_kb,
            )
            if raw:
                result_text, structured = split_seo_structured_result(raw)
            else:
                logger.warning("call_tool returned None for seo mode=%s, falling back", ctx.mode)

        if not result_text:
            result_text = self.analyzer.chat_with_agent(
                ctx.final_prompt,
                system_prompt=ctx.system,
                cached_context=ctx.cached_kb,
                agent_name=self.name,
                agent_mode=ctx.mode,
            )

        return self._build_seo_response(ctx, result_text, structured)

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
                user_message=ctx.final_prompt,
                tool=ctx.structured_tool,
                system_prompt=ctx.system,
                cached_context=ctx.cached_kb,
            )
            if raw:
                result_text, structured = split_seo_structured_result(raw)
            else:
                logger.warning("acall_tool returned None for seo mode=%s, falling back", ctx.mode)

        if not result_text:
            result_text = await self.analyzer.achat_with_agent(
                ctx.final_prompt,
                system_prompt=ctx.system,
                cached_context=ctx.cached_kb,
                agent_name=self.name,
                agent_mode=ctx.mode,
            )

        return self._build_seo_response(ctx, result_text, structured)

    def smart_chat(
        self,
        message: str,
        chat_id: int = 0,
        extra_payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Route a free-form message to the right SEO mode via Sonnet intent classifier."""
        intent     = route_seo_intent(self.analyzer, message)
        mode       = intent["mode"]
        confidence = intent["confidence"]
        extracted  = intent.get("extracted_context", {})

        logger.debug("seo smart_chat: mode=%s confidence=%s", mode, confidence)

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
