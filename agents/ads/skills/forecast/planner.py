from typing import Any, Dict
from ..benchmarks import GOOGLE, META, TIKTOK, benchmark_summary


def build_forecast_prompt(payload: Dict[str, Any]) -> str:
    product   = payload.get("product", "product")
    platform  = payload.get("platform", "")
    budget    = payload.get("budget", 0)
    goal      = payload.get("goal", "conversions")
    market    = payload.get("market", "")
    months    = payload.get("months", 3)
    cpm       = payload.get("cpm", None)        # custom override
    ctr       = payload.get("ctr", None)        # custom override
    cvr       = payload.get("cvr", None)        # custom override
    aov       = payload.get("aov", None)        # average order value (ecom)
    context   = payload.get("context", "")

    platform_line = f"\nPlatform: {platform}" if platform else "\nPlatform: (multi-platform)"
    market_line   = f"\nMarket: {market}" if market else ""
    aov_line      = f"\nAOV (avg order value): ${aov}" if aov else ""
    context_line  = f"\nContext: {context}" if context else ""
    months_line   = f"\nForecast horizon: {months} months"

    # Build custom override block
    overrides = []
    if cpm:  overrides.append(f"CPM override: ${cpm}")
    if ctr:  overrides.append(f"CTR override: {ctr}%")
    if cvr:  overrides.append(f"CVR override: {cvr}%")
    override_block = "\nCustom rate overrides: " + " | ".join(overrides) if overrides else ""

    # Build benchmark reference
    bench_block = ""
    if platform:
        bench_block = "\n" + benchmark_summary(platform)

    monthly = budget / max(months, 1)

    return f"""## Ad Forecast & Media Plan
Product: {product}{platform_line}{market_line}
Total budget: ${budget:,}{months_line}
Monthly budget: ${monthly:,.0f}
Goal: {goal}{aov_line}{override_block}{context_line}
{bench_block}
---

## Task

Build a bottom-up media plan using the CPM → CTR → CVR funnel model.
Run three scenarios: Conservative, Base, Optimistic.
If custom rate overrides are provided, use them for Base; adjust ±20% for Conservative/Optimistic.
If no overrides, use platform benchmarks above with the low end for Conservative and high end for Optimistic.

---

## Step 1 — Funnel Math (per month, per scenario)

Formula chain:
  Impressions  = (Budget / CPM) × 1,000
  Clicks       = Impressions × CTR%
  Conversions  = Clicks × CVR%
  Revenue      = Conversions × AOV        (ecom only)
  ROAS         = Revenue / Budget
  CPA          = Budget / Conversions
  CPC          = Budget / Clicks

Output as table:

| Scenario    | Monthly Budget | CPM  | CTR  | CVR  | Impressions | Clicks | Conversions | CPA   | CPC   | ROAS |
|-------------|---------------|------|------|------|-------------|--------|-------------|-------|-------|------|
| Conservative | ${monthly:,.0f} | — | — | — | — | — | — | — | — | — |
| Base         | ${monthly:,.0f} | — | — | — | — | — | — | — | — | — |
| Optimistic   | ${monthly:,.0f} | — | — | — | — | — | — | — | — | — |

---

## Step 2 — {months}-Month Cumulative Projection

Account for ramp-up: most campaigns under-perform in month 1 (learning phase).

Ramp-up multipliers:
- Month 1: ×0.60 (learning phase, algo calibrating)
- Month 2: ×0.85 (exiting learning, optimisation kicking in)
- Month 3+: ×1.00 (steady state)

Output cumulative table:

| Month | Budget | Expected Conversions (Base) | CPA (Base) | Cumulative Revenue (Base) |
|-------|--------|-----------------------------|-----------|-----------------------------|
| 1     | — | — | — | — |
| 2     | — | — | — | — |
| 3     | — | — | — | — |
| Total | — | — | — | — |

---

## Step 3 — Break-even & ROI Analysis

Break-even CPA = AOV × gross margin% (if AOV provided)
Break-even ROAS = 1 / gross margin% (if margin provided or assumed)

Current Base scenario vs break-even:
- Is the Base CPA below break-even? → profitable or loss
- What CVR improvement is needed to reach break-even at current CPM + CTR?
- What CPM reduction would make the plan profitable without touching conversion rate?

---

## Step 4 — Platform Mix (multi-platform budget split)

If platform is not specified or budget allows multi-channel, recommend allocation:

| Platform | Budget % | Rationale | Expected volume |
|----------|----------|-----------|-----------------|
| Google Search | — | High intent, fast learner | — |
| Google Display / YouTube | — | Retargeting + brand | — |
| Meta | — | Volume + creative testing | — |
| TikTok | — | Discovery + younger demo | — |

Rules for allocation:
- New account: concentrate 70%+ in one platform until ≥50 conv/mo before splitting
- Established: diversify once primary platform hits diminishing returns
- Search (Google) always gets priority if the product has active search demand

---

## Step 5 — Sensitivity Analysis

Show which lever has the biggest impact on CPA:

| Lever | Change | CPA impact | Action to achieve |
|-------|--------|------------|-------------------|
| CPM -20% | Audience broadening or off-peak scheduling | — | — |
| CTR +30% | Creative refresh / headline test | — | — |
| CVR +50% | Landing page CRO (LP audit) | — | — |
| Budget +2× | Scale budget on winning Ad Sets | — | — |

Rank levers: which has highest CPA leverage for this product/platform?

---

## Step 6 — Risks & Flags

List 3–5 most likely risks that could push performance to the Conservative scenario:
- Learning phase extension (if conversion event is rare)
- Audience saturation (small market or hyper-targeted)
- Creative fatigue (especially TikTok)
- Seasonality / auction competition (Q4, holidays)
- Tracking gaps (pixel fires but under-reports)

For each risk: mitigation action.

---

## Done Criteria
- [ ] Three scenario table complete with all funnel metrics
- [ ] Monthly ramp-up table complete for full forecast horizon
- [ ] Break-even CPA/ROAS calculated
- [ ] Platform split recommended (if multi-platform or no platform specified)
- [ ] Sensitivity top lever identified
- [ ] 3–5 risks + mitigations listed
"""
