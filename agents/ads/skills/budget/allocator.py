from typing import Any, Dict, List
from .._shared import get_stage_hint
from ..benchmarks import GOOGLE, META, TIKTOK


def build_budget_prompt(payload: Dict[str, Any]) -> str:
    total_budget  = payload.get("budget", 0)
    platforms     = payload.get("platforms", ["google", "meta", "tiktok"])
    goal          = payload.get("goal", "conversions")
    industry      = payload.get("industry", "")
    funnel_stage  = payload.get("funnel_stage", "mofu")
    audience      = payload.get("audience", {})
    product       = payload.get("product", "product")
    has_data      = payload.get("has_historical_data", False)

    platforms_text = ", ".join(p.capitalize() for p in platforms)
    industry_text  = f"\nIndustry: {industry}" if industry else ""
    audience_text  = ", ".join(f"{k}: {v}" for k, v in audience.items() if v) or "not specified"
    data_text      = "Historical data: available — factor it into the allocation" if has_data \
                     else "Historical data: none — use recommended benchmarks"
    stage_hint     = get_stage_hint(funnel_stage, "default")

    return f"""Task: Cross-platform Ad Budget Allocation
Product: {product}
Total budget: ${total_budget}/mo
Platforms: {platforms_text}
Goal: {goal}
Funnel stage: {funnel_stage.upper()} — {stage_hint}
Audience: {audience_text}{industry_text}
{data_text}

Task — deliver a justified budget allocation plan:

1. RECOMMENDED ALLOCATION (% and $)

   For each platform specify:
   — Budget share: XX% = $X,XXX/mo
   — Justification: why this amount
   — Minimum budget needed for meaningful data on this platform

   Minimum budget benchmarks (from benchmarks.py, 2025):
   Google Ads Search:  ${GOOGLE['budget_min_usd']:,}+/mo (≥{GOOGLE['learning_conv_min']} conv in {GOOGLE['learning_days']} days for Smart Bidding)
   Meta Ads:           ${META['budget_min_usd']:,}+/mo (≥{META['learning_conv_min']} conv in {META['learning_days']} days for Learning Phase)
   TikTok Ads:         ${TIKTOK['budget_min_usd']:,}–{TIKTOK['budget_test_min']:,}/mo (for statistically meaningful data)

2. ALLOCATION LOGIC BY GOAL

   Conversions / ROAS:
   — Google Search: intent already exists (user is actively searching) → highest priority
   — Meta: broad reach + remarketing → medium priority
   — TikTok: discovery, lower CVR but cheaper CPM → smaller share for direct conversions

   Awareness / Reach:
   — TikTok: low CPM ($3–8) → highest priority for reach
   — Meta: medium CPM ($8–18), strong targeting → medium priority
   — Google Display: cheap reach but lower engagement

   Lead Generation (B2B / SaaS):
   — Google Search: highest quality leads (intent-based) → 50–60%
   — Meta Lead Ads: cheaper but lower quality → 30–40%
   — TikTok: only if audience skews younger → 10–20%

   E-commerce:
   — Google Shopping + Search: high ROAS → 40–50%
   — Meta DPA (remarketing) + Prospecting → 35–40%
   — TikTok Shopping: if target audience is 18–35 → 10–25%

3. PHASED ALLOCATION

   Phase 1 — Test (month 1–2): minimal budget, learning
   — Platform breakdown with specific dollar amounts
   — What to test: audiences, formats, offers

   Phase 2 — Optimise (month 3–4): scale winners
   — Reallocation based on data
   — Scale criteria: ROAS >X, CPA <Y

   Phase 3 — Scale (month 5+): maximise ROAS
   — Final allocation after algorithm learning completes

4. WHEN TO REBALANCE
   — Platform consistently exceeds ROAS target: increase budget by 20–30%/week
   — Platform fails to exit Learning Phase in 14 days: review account structure
   — Seasonality: how to adjust allocation during peak periods

5. EFFECTIVENESS METRICS
   — CPA by platform
   — ROAS by platform
   — Marginal ROAS: is adding $1 to platform X better than platform Y?
   — Audience overlap: avoid double-counting conversions across platforms

6. SUMMARY TABLE
   Platform | Budget $ | % | Expected conversions | Target CPA | Target ROAS
"""
