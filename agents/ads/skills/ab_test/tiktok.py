from typing import Any, Dict


def build_tiktok_abtest_prompt(payload: Dict[str, Any]) -> str:
    product      = payload.get("product", "product")
    what_to_test = payload.get("what_to_test", "")
    current_perf = payload.get("current_performance", {})
    budget       = payload.get("budget", 0)
    objective    = payload.get("goal", "conversions")

    perf_text = ""
    if current_perf:
        perf_text = "\nCurrent performance:\n" + "\n".join(f"  {k}: {v}" for k, v in current_perf.items())

    test_hint = f"What to test: {what_to_test}" if what_to_test else \
        "What to test: determine based on goal and current performance"

    return f"""Platform: TikTok Ads — A/B Test Design (Split Testing)
Product: {product}
Objective: {objective}
Test budget: ${budget}/mo
{test_hint}{perf_text}

Task — develop a structured A/B testing plan:

1. TOOL: TIKTOK SPLIT TEST

   TikTok Ads Manager → Campaigns → Split Test
   — Splits audience randomly, no overlap (cookie-level)
   — Up to 5 variables in one test (but test ONE at a time!)
   — 7 testable variables:
     1. Audience
     2. Placement
     3. Bidding & Optimization
     4. Budget Strategy (daily vs total budget)
     5. Creative
     6. Catalog (for Shopping)
     7. Smart+ Automation Level

   Requirements:
   — Minimum budget: $20–50/day per branch (more recommended)
   — Duration: 7–14 days
   — TikTok determines the winner and confidence level automatically

2. WHAT AND HOW TO TEST

   HIGH PRIORITY (TikTok = content platform → creative decides everything):

   Test 1: CREATIVE — the most important test
   — Control: current best-performing video
   — Variant A: different hook (first 3 seconds)
     Hook variant 1: visual scroll-stop (unexpected action)
     Hook variant 2: provocative statement + text overlay
     Hook variant 3: before/after in first 3 seconds
   — Variant B: different style (UGC selfie vs polished studio)
   — Variant C: different length (9 sec vs 15 sec vs 30 sec)
   — Tool: Split Test → Creative variable
   — Win metric: Hook Rate >30%, Video Completion Rate >25%, CTR >1.5%

   Test 2: AUDIENCE
   — Control: Interest targeting (interests + behaviours)
   — Variant A: Broad (age + geo only, no interests) — let algorithm find the audience
   — Variant B: Lookalike 1–3% from buyers
   — Variant C: Custom Audience (retargeting) if MOFU/BOFU
   — Duration: 7–14 days
   — Metric: CPA, CVR, ROAS

   MEDIUM PRIORITY:

   Test 3: BIDDING STRATEGY
   — Control: Maximum Delivery (spend-based)
   — Variant: Cost Cap with target CPA = X
   — Condition: enough data (≥50 conversions in history) for Cost Cap
   — Metric: conversion volume and CPA stability

   Test 4: SMART+ vs STANDARD
   — Control: standard campaign with manual settings
   — Variant: Smart+ Campaign (full automation)
   — Duration: 14 days (Smart+ needs time to learn)
   — Metric: CPA, ROAS, volume at the same budget

   Test 5: PLACEMENT
   — Control: TikTok Only (In-Feed)
   — Variant: All Placements (TikTok + Pangle partner network)
   — Metric: CPM, CTR, CPA by placement

3. TIKTOK-SPECIFIC TESTING NOTES

   Creative burnout speed:
   — An ad "burns out" in 1–2 weeks (algorithm shows it to the same people)
   — Test continuously: 15–30 new assets/week
   — After a winner: immediately launch the next test with its variations

   Nativity = primary quality signal:
   — Test: branded video vs UGC (UGC almost always wins)
   — Test: TikTok library sound vs original audio
   — Test: subtitles vs no subtitles (subtitles typically +10–20% CVR)

   Minimum budget for meaningful results:
   — $1,500–3,000/mo total test budget
   — If budget is lower: test only one element (e.g. hook only)

4. STATISTICAL SIGNIFICANCE AND SAMPLE SIZE

   Required sample size formula (per branch):
     n = 16 × p × (1 − p) / δ²
   Where:
     p = baseline CVR (or CTR) as a decimal  (e.g. 1.0% = 0.01)
     δ = MDE in absolute terms  (25% rel. shift from 0.01 = 0.0025)
   Parameters: 95% confidence, 80% power

   Quick reference (sessions / impressions per branch):
   | Baseline CVR | MDE 10% (rel) | MDE 20% (rel) | MDE 30% (rel) |
   |---|---|---|---|
   | 0.5%  | ~126,000 | ~31,500 | ~14,000 |
   | 1.0%  | ~62,800  | ~15,700 | ~7,000  |
   | 1.5%  | ~41,200  | ~10,300 | ~4,600  |
   | 2.5%  | ~24,300  | ~6,100  | ~2,700  |

   TikTok-specific rules:
   — TikTok shows confidence level in Split Test Results automatically — trust it
   — 80% confidence for quick CREATIVE decisions (high rotation needed)
   — 95% confidence for structural decisions (audience, bidding strategy)
   — Do not stop before the TikTok-recommended period ends
   — If traffic is low: use Hook Rate (3-sec) instead of CVR — faster data accumulation
   — Minimum budget for a meaningful test: $1,500–3,000/mo

5. ITERATION PLAN
   — Week 1–2: test Hook (A vs B vs C)
   — Week 3–4: test Audience (Interest vs Broad vs LAL)
   — Week 5–6: test Video Length with the winning hook
   — Week 7–8: test Bidding Strategy with best audience and creative

6. DOCUMENTATION
   — Hypothesis → Variable → Control → Variant → Result → Next step
"""
