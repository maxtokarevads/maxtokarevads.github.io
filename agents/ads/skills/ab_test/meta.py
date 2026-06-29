from typing import Any, Dict


def build_meta_abtest_prompt(payload: Dict[str, Any]) -> str:
    product      = payload.get("product", "product")
    what_to_test = payload.get("what_to_test", "")
    current_perf = payload.get("current_performance", {})
    budget       = payload.get("budget", 0)
    objective    = payload.get("goal", "conversions")

    perf_text = ""
    if current_perf:
        perf_text = "\nCurrent performance:\n" + "\n".join(f"  {k}: {v}" for k, v in current_perf.items())

    test_hint = f"What to test: {what_to_test}" if what_to_test else \
        "What to test: determine based on goal and current account structure"

    return f"""Platform: Meta Ads — A/B Test Design
Product: {product}
Objective: {objective}
Test budget: ${budget}/mo
{test_hint}{perf_text}

Task — develop a structured A/B testing plan:

1. META TESTING TOOLS

   A) Meta A/B Test (Experiments):
   — Official tool: Ads Manager → Experiments → A/B Test
   — Splits audience randomly, no overlap (cookie-level split)
   — Tests: Creative, Audience, Placement, Budget Strategy
   — Minimum budget: Meta recommends; typically $500–1,000 per branch
   — Result: statistically significant winner within 7–14 days

   B) ABO vs CBO (Budget Strategy):
   — Control: Ad Set Budget Optimization (ABO) — budget at Ad Set level
   — Variant: Campaign Budget Optimization (CBO) — budget at Campaign level
   — Key for scaling: CBO wins at 3+ Ad Sets

   C) Holdout Test (Incrementality):
   — 10–15% of audience sees no ads at all
   — Measures true incremental lift (not attributed)
   — Set up via Experiments → Holdout

2. WHAT AND HOW TO TEST

   HIGH PRIORITY:

   Test 1: CREATIVE (most common Meta test)
   — Control: current best ad
   — Variant A: different format (Image → Video)
   — Variant B: different hook approach (pain vs result vs question)
   — Variant C: UGC vs professional content
   — Tool: A/B Test → Creative variable
   — Duration: 7 days minimum
   — Win metric: CTR + CVR; CPA

   Test 2: AUDIENCE
   — Control: detailed targeting (interests)
   — Variant A: Advantage+ Audience (broad, no interests)
   — Variant B: Lookalike 1–3%
   — Variant C: Broad (age + geo only)
   — Tool: A/B Test → Audience variable
   — Duration: 7–14 days
   — Win metric: CPA, ROAS, volume

   MEDIUM PRIORITY:

   Test 3: PLACEMENT
   — Control: Advantage+ Placements (automatic)
   — Variant: Feed only (Facebook + Instagram)
   — Variant: Feed + Reels vs Reels only
   — Metric: CPA per placement — don't stop too early

   Test 4: OBJECTIVE
   — Control: Conversions (Purchase)
   — Variant: Catalog Sales (DPA)
   — Variant: Traffic (optimised for Landing Page Views)
   — Only if sufficient budget for ≥50 events/week per branch

   Test 5: ABO vs CBO
   — Control: ABO with manual budget allocation
   — Variant: CBO with same total budget
   — Duration: 14 days (CBO needs time to optimise)

3. LEARNING PHASE AND TESTING
   — Each new Ad Set enters Learning Phase (~50 conversions in 7 days)
   — Do not make changes during Learning Phase
   — Test budget: enough for ≥50 events per branch per 7 days
   — If conversion event is rare (Purchase): consider optimising on AddToCart

4. STATISTICAL SIGNIFICANCE AND SAMPLE SIZE

   Required sample size formula (per branch):
     n = 16 × p × (1 − p) / δ²
   Where:
     p = baseline CVR (or CTR) as a decimal  (e.g. 1.5% = 0.015)
     δ = MDE in absolute terms  (20% rel. shift from 0.015 = 0.003)
   Parameters: 95% confidence, 80% power

   Quick reference (sessions per branch):
   | Baseline CVR | MDE 10% (rel) | MDE 20% (rel) | MDE 30% (rel) |
   |---|---|---|---|
   | 0.9%  | ~68,200 | ~17,100 | ~7,600 |
   | 1.5%  | ~41,200 | ~10,300 | ~4,600 |
   | 2.2%  | ~27,900 | ~7,000  | ~3,100 |
   | 5.0%  | ~11,800 | ~2,900  | ~1,300 |

   Steps BEFORE launching a test:
   1. Calculate baseline CVR/CTR from last 14–30 days of data
   2. Set MDE: typically 15–25% relative for Meta
   3. At current daily traffic: n / (sessions/day) = minimum test duration
   4. If volume is insufficient: use a higher-funnel event (AddToCart instead of Purchase)

   Meta-specific rules:
   — Meta shows confidence level in Experiments automatically — trust it
   — Minimum 95% confidence before declaring a winner
   — Do not stop before the recommended period ends (typically 7–14 days)
   — If 7 days pass with no winner: extend by another 7 days
   — Budget: ensure ≥50 events per branch per 7 days (Learning Phase requirement)

5. CREATIVE TESTING FRAMEWORK (systematic rotation)
   — Always running: 3–5 active ads per Ad Set
   — Replacement rule: if ad has ≥500 impressions and CTR <0.5% → pause
   — Winner: CTR + CVR better than control by ≥15% at ≥100 clicks
   — New creative cadence: 2–3 new ads per week

6. DOCUMENTATION
   — Hypothesis → Variable → Control → Variant → Date → Result → Action
"""
